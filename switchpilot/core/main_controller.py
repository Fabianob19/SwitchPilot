from PyQt5.QtCore import QObject, pyqtSignal
import cv2
import numpy as np
import mss
import pyautogui
import os
from switchpilot.integrations.obs_controller import OBSController
from switchpilot.integrations.vmix_controller import VMixController
from .monitor_thread import MonitorThread


class MainController(QObject):
    monitoring_status_update = pyqtSignal(str)
    new_log_message = pyqtSignal(str, str)
    monitoring_actually_started = pyqtSignal()
    monitoring_actually_stopped = pyqtSignal(str)
    monitoring_encountered_error = pyqtSignal(str)

    def __init__(self, ref_manager_widget, mon_control_widget, obs_config_widget, vmix_config_widget=None, parent=None):
        super().__init__(parent)
        self.ref_manager_widget = ref_manager_widget
        self.mon_control_widget = mon_control_widget
        self.obs_config_widget = obs_config_widget
        self.vmix_config_widget = vmix_config_widget

        self.monitoring_active = False
        self.references = []
        self.pgm_details = None
        self.obs_is_known_recording = False
        self.monitor_thread_instance = None

        # Valores padrão para os limiares, podem ser atualizados pela UI
        self.current_static_threshold = 0.90
        self.current_sequence_threshold = 0.90
        self.current_monitor_interval = 0.5  # Novo: intervalo de captura em segundos

        self.obs_controller = OBSController()
        if self.obs_controller:
            self.obs_controller.set_log_callback(self.new_log_message.emit)
            self._update_obs_controller_settings()

        self.vmix_controller = VMixController()
        if self.vmix_controller:
            self.vmix_controller.set_log_callback(self.new_log_message.emit)
            self._update_vmix_controller_settings()

        self._connect_ui_signals()

    def _connect_ui_signals(self):
        if self.mon_control_widget:
            self.mon_control_widget.start_monitoring_requested.connect(self.start_monitoring)
            self.mon_control_widget.stop_monitoring_requested.connect(self.stop_monitoring)
            self.mon_control_widget.static_threshold_changed.connect(self.update_static_threshold)
            self.mon_control_widget.sequence_threshold_changed.connect(self.update_sequence_threshold)
            if hasattr(self.mon_control_widget, 'set_static_threshold_value'):
                self.mon_control_widget.set_static_threshold_value(self.current_static_threshold)
            if hasattr(self.mon_control_widget, 'set_sequence_threshold_value'):
                self.mon_control_widget.set_sequence_threshold_value(self.current_sequence_threshold)
        else:
            self._log_internal("[Core CRITICAL] MonitoringControlWidget não foi fornecido.", "error")

        if self.ref_manager_widget:
            self._log_internal(f"Conectando ao ReferenceManagerWidget: {self.ref_manager_widget}", "debug")
            self.ref_manager_widget.references_updated.connect(self.update_references_from_ui)
            self.update_references_from_ui(self.ref_manager_widget.get_all_references_data())
        else:
            self._log_internal("[Core CRITICAL] ReferenceManagerWidget não foi fornecido.", "error")

        if self.obs_config_widget:
            self._log_internal(f"Conectando ao OBSConfigWidget: {self.obs_config_widget}", "debug")
            self.obs_config_widget.config_changed.connect(self._update_obs_controller_settings)
            self.obs_config_widget.test_connection.connect(self._handle_test_obs_connection)
        else:
            self._log_internal("[Core WARNING] OBSConfigWidget não foi fornecido. Controle OBS pode não funcionar.", "warning")

        if self.vmix_config_widget:
            self._log_internal(f"Conectando ao VMixConfigWidget: {self.vmix_config_widget}", "debug")
            self.vmix_config_widget.config_changed.connect(self._update_vmix_controller_settings)
            self.vmix_config_widget.test_connection.connect(self._handle_test_vmix_connection)
        else:
            self._log_internal("[Core WARNING] VMixConfigWidget não foi fornecido. Controle vMix pode não funcionar.", "warning")

    def _log_internal(self, message, level="info"):
        print(f"[MainController - {level.upper()}]: {message}")
        self.new_log_message.emit(message, level)

    def _update_obs_controller_settings(self):
        if not self.obs_config_widget or not self.obs_controller:
            level = "warning" if self.obs_config_widget else "error"
            self._log_internal(f"OBSConfigWidget ou OBSController não disponível/inicializado. Não é possível atualizar config.", level)
            return

        config = self.obs_config_widget.get_config()
        self.obs_controller.host = config.get('host', 'localhost')
        self.obs_controller.port = int(config.get('port', 4455))  # Garantir que porta é int
        self.obs_controller.password = config.get('password', '')
        self._log_internal(f"Configurações do OBSController atualizadas: Host={self.obs_controller.host}, Porta={self.obs_controller.port}", "info")

    def _handle_test_obs_connection(self):
        if not self.obs_controller:
            self._log_internal("OBSController não está inicializado. Não é possível testar a conexão.", "error")
            return
        self._update_obs_controller_settings()
        success, message = self.obs_controller.check_connection()
        log_level = "success" if success else "error"
        self._log_internal(f"Teste de conexão OBS: {'SUCESSO' if success else 'FALHA'}. {message}", log_level)

    def _update_vmix_controller_settings(self):
        if not self.vmix_config_widget or not self.vmix_controller:
            level = "warning" if self.vmix_config_widget else "error"
            self._log_internal(f"VMixConfigWidget ou VMixController não disponível/inicializado. Não é possível atualizar config.", level)
            return

        config = self.vmix_config_widget.get_config()
        self.vmix_controller.host = config.get('host', 'localhost')
        self.vmix_controller.port = int(config.get('port', 8088))  # Garantir que porta é int
        self._log_internal(f"Configurações do VMixController atualizadas: Host={self.vmix_controller.host}, Porta={self.vmix_controller.port}", "info")

    def _handle_test_vmix_connection(self):
        if not self.vmix_controller:
            self._log_internal("VMixController não está inicializado. Não é possível testar a conexão.", "error")
            return
        self._update_vmix_controller_settings()
        success, message = self.vmix_controller.check_connection()
        log_level = "success" if success else "error"
        self._log_internal(f"Teste de conexão vMix: {'SUCESSO' if success else 'FALHA'}. {message}", log_level)

    def update_references_from_ui(self, references_data_list):
        self.references = list(references_data_list)
        if self.ref_manager_widget:
            pgm_details_from_ref_manager = getattr(self.ref_manager_widget, 'selected_pgm_details', None)
            if pgm_details_from_ref_manager:
                self.pgm_details = pgm_details_from_ref_manager

        self._log_internal(f"Referências atualizadas: {len(self.references)} referências.", "debug")
        if self.pgm_details:
            self._log_internal(f"Detalhes PGM atualizados: {self.pgm_details.get('source_name', 'N/A')} ROI: {self.pgm_details.get('roi', 'N/A')}", "debug")
        else:
            self._log_internal("Detalhes PGM ainda não definidos ou não atualizados pela UI.", "debug")

    def start_monitoring(self):
        if self.monitoring_active:
            self._log_internal("Monitoramento já está ativo.", "warning")
            return

        if self.ref_manager_widget:
            self.update_references_from_ui(self.ref_manager_widget.get_all_references_data())

        if not self.references:
            self._log_internal("Nenhuma imagem de referência configurada. Não é possível iniciar.", "error")
            self.monitoring_encountered_error.emit("Nenhuma referência definida.")
            if self.mon_control_widget:
                self.mon_control_widget.monitoring_stopped("Nenhuma referência definida.")
            return

        if not self.pgm_details or not self.pgm_details.get('roi'):
            self._log_internal("Região PGM não definida. Selecione no Gerenciador de Referências.", "error")
            self.monitoring_encountered_error.emit("Região PGM não definida.")
            if self.mon_control_widget:
                self.mon_control_widget.monitoring_stopped("Região PGM não definida.")
            return

        if self.obs_controller:
            try:
                is_currently_recording, _, _ = self.obs_controller.get_record_status()
                self.obs_is_known_recording = is_currently_recording
                self._log_internal(f"Status gravação OBS ao iniciar: {'Ativa' if is_currently_recording else 'Inativa'}", "info")
            except Exception as e:
                self._log_internal(f"Erro ao verificar status de gravação OBS: {e}", "warning")

        self.monitoring_active = True
        self.monitor_thread_instance = MonitorThread(
            references_data=self.references,
            pgm_details=self.pgm_details,
            action_executor_callback=self._execute_actions_from_thread,
            action_description_callback=self.get_action_description,  # Callback para descrever ações
            initial_static_threshold=self.current_static_threshold,        # Passando o limiar
            initial_sequence_threshold=self.current_sequence_threshold,   # Passando o limiar
            initial_monitor_interval=self.current_monitor_interval      # Novo: passando intervalo
        )
        self.monitor_thread_instance.log_signal.connect(self._handle_thread_log)
        self.monitor_thread_instance.status_signal.connect(self._handle_thread_status)
        self.monitor_thread_instance.finished.connect(self._on_monitor_thread_finished)

        self.monitor_thread_instance.start()
        self.monitoring_actually_started.emit()
        self._log_internal("Thread de monitoramento iniciada.", "info")

    def _execute_actions_from_thread(self, action_data):
        self._execute_action(action_data)

    def _handle_thread_log(self, message, level):
        self.new_log_message.emit(message, level)

    def _handle_thread_status(self, status_message):
        if self.mon_control_widget:
            if status_message == "Monitoramento Ativo" and self.monitoring_active:
                self.mon_control_widget.monitoring_started()
            elif status_message == "Monitoramento Parado":  # Não checar self.monitoring_active aqui, pois a thread pode parar sozinha
                reason = "Thread parou"  # Razão genérica se a thread parou por si
                # Se self.monitoring_active for False, significa que foi parada por stop_monitoring(), que já tem uma razão melhor
                if not self.monitoring_active and hasattr(self.monitor_thread_instance, 'stop_reason'):
                    reason = self.monitor_thread_instance.stop_reason if self.monitor_thread_instance else reason

                if self.mon_control_widget:
                    self.mon_control_widget.monitoring_stopped(reason)
                # self.monitoring_actually_stopped.emit(reason) # Emitido por stop_monitoring ou _on_monitor_thread_finished
            else:  # Outros status
                self.mon_control_widget.update_status(status_message)

    def _on_monitor_thread_finished(self):
        thread_was_active_before_finish = self.monitoring_active  # Capturar estado antes de modificar
        self._log_internal("Thread de monitoramento finalizada (sinal finished).", "info")

        # Não redefina os limiares atuais aqui, eles devem persistir como definidos pelo usuário

        if thread_was_active_before_finish:  # Se a thread terminou mas o controller achava que estava ativa
            self.monitoring_active = False
            self._log_internal("Thread de monitoramento parece ter terminado inesperadamente ou por conta própria.", "warning")
            reason = "Thread terminou inesperadamente"
            if self.mon_control_widget:
                self.mon_control_widget.monitoring_stopped(reason)
            self.monitoring_actually_stopped.emit(reason)  # Emitir que parou

        # Limpar a instância da thread se ela realmente terminou
        if self.monitor_thread_instance and not self.monitor_thread_instance.isRunning():
            self.monitor_thread_instance = None

        if self.obs_controller:
            self.obs_is_known_recording = False

    # Slots para atualizar os limiares dinamicamente
    def update_static_threshold(self, threshold):
        self._log_internal(f"Solicitação para atualizar limiar ESTÁTICO para: {threshold:.2f}", "debug")
        if 0.0 <= threshold <= 1.0:
            self.current_static_threshold = threshold
            if self.monitor_thread_instance and self.monitor_thread_instance.isRunning():
                self.monitor_thread_instance.set_static_threshold(threshold)
            self._log_internal(f"Limiar ESTÁTICO definido para: {self.current_static_threshold:.2f}", "info")
        else:
            self._log_internal(f"Valor de limiar ESTÁTICO inválido: {threshold}. Mantendo {self.current_static_threshold:.2f}.", "warning")

    def update_sequence_threshold(self, threshold):
        print(f"[DEBUG] MainController.update_sequence_threshold chamado com {threshold}")
        self._log_internal(f"Solicitação para atualizar limiar SEQUÊNCIA para: {threshold:.2f}", "debug")
        if 0.0 <= threshold <= 1.0:
            self.current_sequence_threshold = threshold
            print(f"[DEBUG] MainController: current_sequence_threshold agora = {self.current_sequence_threshold}")
            if self.monitor_thread_instance and self.monitor_thread_instance.isRunning():
                print(f"[DEBUG] MainController: Chamando set_sequence_threshold na thread...")
                self.monitor_thread_instance.set_sequence_threshold(threshold)
            self._log_internal(f"Limiar SEQUÊNCIA definido para: {self.current_sequence_threshold:.2f}", "info")
        else:
            self._log_internal(f"Valor de limiar SEQUÊNCIA inválido: {threshold}. Mantendo {self.current_sequence_threshold:.2f}.", "warning")

    def update_monitor_interval(self, interval):
        self._log_internal(f"Solicitação para atualizar INTERVALO DE CAPTURA para: {interval:.2f}s", "debug")
        if 0.1 <= interval <= 5.0:
            self.current_monitor_interval = interval
            if self.monitor_thread_instance and self.monitor_thread_instance.isRunning():
                self.monitor_thread_instance.set_monitor_interval(interval)
            self._log_internal(f"Intervalo de captura definido para: {self.current_monitor_interval:.2f}s", "info")
        else:
            self._log_internal(f"Valor de INTERVALO DE CAPTURA inválido: {interval}. Mantendo {self.current_monitor_interval:.2f}s.", "warning")

    def stop_monitoring(self, reason="Solicitado pelo usuário."):
        if not self.monitoring_active:
            self._log_internal("Monitoramento não está ativo para ser parado.", "warning")
            if self.monitor_thread_instance and self.monitor_thread_instance.isRunning():  # Caso raro: thread rodando mas active=False
                self._log_internal("Estado inconsistente: monitor_thread rodando mas monitoring_active=False. Tentando parar thread.", "warning")
            elif self.monitor_thread_instance:  # Se existe instância mas não está rodando (já terminou)
                self.monitor_thread_instance = None  # Apenas limpar
                return
            else:  # Nenhuma thread e não ativo
                return

        self._log_internal(f"Parando monitoramento... Razão: {reason}", "info")
        self.monitoring_active = False

        if self.monitor_thread_instance and self.monitor_thread_instance.isRunning():
            if hasattr(self.monitor_thread_instance, 'stop_reason'):  # Para passar a razão para a thread
                self.monitor_thread_instance.stop_reason = reason
            self.monitor_thread_instance.stop()
            if not self.monitor_thread_instance.wait(5000):
                self._log_internal("Timeout ao aguardar thread, terminando forçadamente.", "warning")
                self.monitor_thread_instance.terminate()
                self.monitor_thread_instance.wait()
            else:
                self._log_internal("Thread de monitoramento finalizada graciosamente.", "debug")

        # Se a thread foi parada/terminou, self.monitor_thread_instance será None após _on_monitor_thread_finished ou aqui
        self.monitor_thread_instance = None
        self._log_internal("Monitoramento efetivamente parado.", "info")
        self.monitoring_actually_stopped.emit(reason)  # Sinaliza para UI
        if self.obs_controller:
            self.obs_is_known_recording = False

    def _execute_action(self, action_data):
        if not action_data:
            self._log_internal("Tentativa de executar ação com action_data vazio.", "warning")
            return

        integration = action_data.get('integration')
        action_type = action_data.get('action_type')
        params = action_data.get('params', {})

        self._log_internal(f"Executando Ação: {integration} - {action_type}, Params: {params}", "action")

        try:
            if integration == "OBS Studio":
                if not self.obs_controller:
                    self._log_internal("OBS Controller não disponível.", "error")
                    return

                if action_type == "Trocar Cena":
                    scene_name = params.get("scene_name")
                    if scene_name:
                        self.obs_controller.set_current_scene(scene_name)
                    else:
                        self._log_internal("OBS: Nome da cena ausente.", "error")

                elif action_type == "Definir Visibilidade da Fonte":
                    scene_name = params.get("scene_name_for_item", params.get("scene_name"))
                    item_name = params.get("item_name")
                    visible_str = str(params.get("visible", "true")).lower()
                    is_visible = visible_str == "true"
                    if scene_name and item_name:
                        self.obs_controller.set_source_visibility(scene_name, item_name, is_visible)
                    else:
                        self._log_internal("OBS: Cena ou nome da fonte ausente para visibilidade.", "error")

                elif action_type == "Alternar Mudo (Fonte de Áudio)":
                    input_name = params.get("input_name")
                    if input_name:
                        self.obs_controller.toggle_mute(input_name)
                    else:
                        self._log_internal("OBS: Nome da fonte de áudio ausente para mudo.", "error")

                elif action_type == "Iniciar Gravação":
                    if self.obs_is_known_recording:
                        self._log_internal("OBS: Gravação já ativa (estado conhecido). Ignorando.", "info")
                    else:
                        is_rec, _, _ = self.obs_controller.get_record_status()
                        if is_rec:
                            self._log_internal("OBS: Gravação já ativa (verificado). Ignorando.", "info")
                            self.obs_is_known_recording = True
                        elif self.obs_controller.start_record():
                            self.obs_is_known_recording = True

                elif action_type == "Parar Gravação":
                    if not self.obs_is_known_recording:
                        self._log_internal("OBS: Gravação já inativa (estado conhecido). Ignorando.", "info")
                    else:
                        is_rec, _, _ = self.obs_controller.get_record_status()
                        if not is_rec:
                            self._log_internal("OBS: Gravação já inativa (verificado). Ignorando.", "info")
                            self.obs_is_known_recording = False
                        elif self.obs_controller.stop_record():
                            self.obs_is_known_recording = False

                elif action_type == "Iniciar Streaming":
                    self.obs_controller.start_stream()  # Adicionar lógica de verificação de estado

                elif action_type == "Parar Streaming":
                    self.obs_controller.stop_stream()  # Adicionar lógica de verificação de estado

                else:
                    self._log_internal(f"OBS: Tipo de ação desconhecido: {action_type}", "warning")

            elif integration == "vMix":
                if not self.vmix_controller:
                    self._log_internal("VMix Controller não disponível.", "error")
                    return

                if action_type == "Function (Genérico)":
                    func_name = params.get("function_name")
                    if func_name:
                        vmix_params = {}
                        input_val = params.get("vmix_input") or params.get("input")
                        if input_val:
                            vmix_params["Input"] = input_val
                        value_val = params.get("vmix_value") or params.get("value")
                        if value_val:
                            vmix_params["Value"] = value_val
                        duration_val = params.get("vmix_duration") or params.get("duration")
                        if duration_val:
                            vmix_params["Duration"] = duration_val
                        mix_idx = params.get("mix_index")
                        if mix_idx is not None:
                            try:
                                vmix_params["Mix"] = int(mix_idx)
                            except Exception:
                                vmix_params["Mix"] = mix_idx
                        self.vmix_controller.send_function(func_name, **vmix_params)
                    else:
                        self._log_internal("vMix: Nome da função genérica ausente.", "error")

                elif action_type == "SetText":
                    input_val = params.get("vmix_input") or params.get("input")
                    sel_name = params.get("selected_name", params.get("vmix_selected_name"))
                    text_val = params.get("text_value")
                    if input_val and sel_name is not None and text_val is not None:
                        self.vmix_controller.set_text(input_val, sel_name, text_val)
                    else:
                        self._log_internal("vMix SetText: Parâmetros ausentes (Input, SelectedName ou Value).", "error")

                elif action_type == "StartRecording":
                    self.vmix_controller.start_recording()
                elif action_type == "StopRecording":
                    self.vmix_controller.stop_recording()

                elif action_type == "Fade":
                    try:
                        duration = int(params.get("vmix_duration_for_fade", params.get("duration", 500)) or 500)
                    except Exception:
                        duration = 500
                    input_val = params.get("vmix_input") or params.get("vmix_input_for_fade") or params.get("input")
                    mix_idx = params.get("mix_index", 1)
                    try:
                        mix_idx = int(mix_idx)
                    except Exception:
                        pass
                    self.vmix_controller.fade(input_val, duration, mix_idx)

                elif action_type == "Cut":
                    input_val = params.get("vmix_input") or params.get("vmix_input_for_cut") or params.get("input")
                    mix_idx = params.get("mix_index", 1)
                    try:
                        mix_idx = int(mix_idx)
                    except Exception:
                        pass
                    self.vmix_controller.cut(input_val, mix_idx)

                elif action_type == "OverlayInputIn":
                    try:
                        channel = int(params.get("overlay_channel", 1))
                    except Exception:
                        channel = 1
                    input_val = params.get("vmix_input") or params.get("vmix_input_for_overlay") or params.get("input")
                    self.vmix_controller.overlay_input_in(channel, input_val)

                elif action_type == "OverlayInputOut":
                    try:
                        channel = int(params.get("overlay_channel", 1))
                    except Exception:
                        channel = 1
                    self.vmix_controller.overlay_input_out(channel)

                else:
                    self._log_internal(f"vMix: Tipo de ação desconhecido: {action_type}", "warning")

            else:
                self._log_internal(f"Integração desconhecida para ação: {integration}", "warning")

        except Exception as e:
            import traceback
            self._log_internal(f"Erro ao executar ação {action_type} para {integration}: {e}", "error")
            self._log_internal(traceback.format_exc(), "debug")

    def get_action_description(self, action_data):
        """Retorna uma descrição legível para a ação. Usado por UI (ex: ReferenceManagerWidget)."""
        action_type = action_data.get('action_type', 'desconhecido')
        params = action_data.get('params', {})
        integration = action_data.get('integration', '')
        desc = f"{integration} - {action_type}"

        if integration == "OBS Studio":
            if action_type == 'Trocar Cena':
                return f"{desc}: '{params.get('scene_name', 'N/A')}'"
            elif action_type == 'Definir Visibilidade da Fonte':
                scene_name = params.get('scene_name_for_item', params.get('scene_name', 'N/A'))
                item_name = params.get('item_name', 'N/A')
                visibility = 'Visível' if str(params.get('visible', 'false')).lower() == 'true' else 'Oculto'
                return f"{desc}: Fonte '{item_name}' em Cena '{scene_name}' para {visibility}"
            elif action_type == 'Alternar Mudo (Fonte de Áudio)':
                return f"{desc}: Fonte de áudio '{params.get('input_name', 'N/A')}'"
        elif integration == "vMix":
            if action_type == 'Function (Genérico)':
                parts = [f"Função: {params.get('function_name', 'N/A')}"]
                if params.get('input'):
                    parts.append(f"Input: {params['input']}")
                if params.get('value'):
                    parts.append(f"Valor: {params['value']}")
                if params.get('duration'):
                    parts.append(f"Duração: {params['duration']}")
                return f"{desc} ({', '.join(parts)})"
            elif action_type == 'SetText':
                return f"{desc}: Input '{params.get('input', 'N/A')}', Campo '{params.get('selected_name', params.get('vmix_selected_name','N/A'))}', Valor '{str(params.get('text_value', ''))[:20]}...'"
            elif action_type == 'Fade' or action_type == 'Cut':
                parts = []
                if params.get('input'):
                    parts.append(f"Input: {params['input']}")
                if action_type == 'Fade' and params.get('duration'):
                    parts.append(f"Duração: {params['duration']}ms")
                return f"{desc} ({', '.join(parts) if parts else 'Preview/Program'})"
            elif action_type == 'OverlayInputIn' or action_type == 'OverlayInputOut':
                parts = [f"Canal: {params.get('overlay_channel', 'N/A')}"]
                if action_type == 'OverlayInputIn' and params.get('input'):
                    parts.append(f"Input: {params['input']}")
                return f"{desc} ({', '.join(parts)})"

        simple_actions = ["Iniciar Gravação", "Parar Gravação", "Iniciar Streaming", "Parar Streaming", "StartRecording", "StopRecording"]
        if action_type in simple_actions:
            return desc

        param_summary = [f"{k}='{str(v)[:20]}...'" for k, v in params.items()]
        return f"{desc} ({', '.join(param_summary)})" if param_summary else desc

    # --- Métodos de Suporte para UI (ex: popular comboboxes no ActionConfigDialog) ---
    def get_obs_scene_list(self):
        if self.obs_controller:
            try:
                return self.obs_controller.get_scene_list()
            except Exception as e:
                self._log_internal(f"Erro ao obter lista de cenas OBS: {e}", "error")
                return []
        self._log_internal("Controlador OBS não disponível para obter lista de cenas.", "warning")
        return []

    def get_obs_scene_item_list(self, scene_name):
        if self.obs_controller and scene_name:
            try:
                return self.obs_controller.get_scene_item_list_from_scene_name(scene_name)
            except Exception as e:
                self._log_internal(f"Erro ao obter lista de itens da cena OBS '{scene_name}': {e}", "error")
                return []
        self._log_internal(f"Controlador OBS não disponível ou nome da cena ausente para obter itens da cena.", "warning")
        return []

    def get_obs_input_list(self):
        if self.obs_controller:
            try:
                return self.obs_controller.get_input_list()  # Lista de fontes de áudio/inputs
            except Exception as e:
                self._log_internal(f"Erro ao obter lista de inputs OBS: {e}", "error")
                return []
        self._log_internal("Controlador OBS não disponível para obter lista de inputs.", "warning")
        return []

    def get_vmix_inputs(self):
        if self.vmix_controller:
            try:
                inputs = self.vmix_controller.get_inputs_list()
                return inputs
            except Exception as e:
                self._log_internal(f"Erro ao obter inputs do vMix: {e}", "error")
                return []
        self._log_internal("Controlador vMix não conectado para obter inputs.", "warning")
        return []

    def get_vmix_title_fields(self, input_id_or_name):
        if self.vmix_controller:
            try:
                fields = self.vmix_controller.get_title_fields(input_id_or_name)
                return fields
            except Exception as e:
                self._log_internal(f"Erro ao obter campos de título do vMix para input '{input_id_or_name}': {e}", "error")
                return []
        self._log_internal(f"Controlador vMix não conectado para obter campos de título.", "warning")
        return []

    # --- Persistência de Configurações (Exemplo) ---
    def load_project_settings(self, filepath):
        # Implementação futura
        self._log_internal(f"Funcionalidade 'Carregar Projeto' ainda não implementada ({filepath}).", "info")
        pass

    def save_project_settings(self, filepath):
        # Implementação futura
        self._log_internal(f"Funcionalidade 'Salvar Projeto' ainda não implementada ({filepath}).", "info")
        pass

    def cleanup(self):
        self._log_internal("Realizando cleanup do MainController...", "info")
        if self.monitoring_active or (self.monitor_thread_instance and self.monitor_thread_instance.isRunning()):
            self.stop_monitoring("Aplicação encerrando.")

        # if self.obs_controller: # A conexão é feita e desfeita por requisição no OBSController atual
        #     # self.obs_controller.disconnect() # Não existe este método, e não é necessário
        #     self._log_internal("OBS Controller - Nenhuma desconexão explícita necessária.", "debug")

        # Adicionar cleanup para vMixController se necessário
        # if self.vmix_controller and hasattr(self.vmix_controller, 'close_connection'):
        #     self.vmix_controller.close_connection()

        self._log_internal("Cleanup do MainController concluído.", "info")

    def connect_to_ui_slots(self):  # Método parece obsoleto dado _connect_ui_signals
        pass
