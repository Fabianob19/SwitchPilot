from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import mss
import numpy as np
import time
import os # Adicionado para os.path.basename em logs futuros

# Será necessário adicionar a lógica de descrever_acao aqui ou no MainController
# Por enquanto, vamos focar na estrutura da thread.

class MonitorThread(QThread):
    log_signal = pyqtSignal(str, str)  # mensagem, nivel (info, error, success, warning, debug)
    status_signal = pyqtSignal(str) # status para a label principal
    # Poderíamos ter um sinal mais específico para quando uma ação é executada
    # action_triggered_signal = pyqtSignal(dict, dict) # matched_reference_data, action_data

    def __init__(self, references_data, pgm_details, action_executor_callback, 
                 initial_static_threshold=0.90, initial_sequence_threshold=0.90, initial_monitor_interval=0.5, parent=None):
        super().__init__(parent)
        # Emitir log aqui para verificar o que foi recebido
        # Temporariamente, vamos usar print direto caso log_signal não esteja pronto ou haja problema com QObject em __init__ antes de mover para a thread certa
        print(f"[MonitorThread __init__] Recebido references_data: {references_data}") 
        # Se quiser usar log_signal, precisaria de um jeito de emiti-lo de forma segura aqui ou logo no início do run.
        # Para simplificar o debug imediato, print pode ser mais direto.

        self.references_data = list(references_data) # Garantir que é uma cópia e uma lista
        self.pgm_details = pgm_details
        self.action_executor_callback = action_executor_callback # Função do MainController para executar ações
        
        self.running = False
        self.monitor_interval = initial_monitor_interval # Intervalo entre verificações em segundos (agora configurável)
        
        # Configurações para comparação de imagem (podem ser ajustadas/configuráveis)
        self.similarity_threshold_static = initial_static_threshold
        self.similarity_threshold_sequence_frame = initial_sequence_threshold
        
        # Para comparação por histograma (se usada)
        self.hist_size = [256]
        self.hist_ranges = [0, 256]
        self.hist_channels = [0]

        # Adicionar log após copiar para self.references_data
        print(f"[MonitorThread __init__] self.references_data inicializado com: {self.references_data}")
        print(f"[MonitorThread __init__] Limiar Estático Inicial: {self.similarity_threshold_static}") # NOVO PRINT
        print(f"[MonitorThread __init__] Limiar Sequência Inicial: {self.similarity_threshold_sequence_frame}") # NOVO PRINT

    def set_static_threshold(self, threshold):
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold_static = threshold
            self.log_signal.emit(f"Limiar de similaridade ESTÁTICA atualizado para: {threshold:.2f}", "info")
            print(f"[MonitorThread]: Limiar Estático atualizado para {threshold:.2f}")
        else:
            self.log_signal.emit(f"Tentativa de definir limiar ESTÁTICO inválido: {threshold}. Mantendo {self.similarity_threshold_static:.2f}.", "warning")
            print(f"[MonitorThread]: Tentativa de definir limiar ESTÁTICO inválido: {threshold}")

    def set_sequence_threshold(self, threshold):
        print(f"[DEBUG] MonitorThread.set_sequence_threshold chamado com {threshold}")
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold_sequence_frame = threshold
            print(f"[DEBUG] MonitorThread: similarity_threshold_sequence_frame agora = {self.similarity_threshold_sequence_frame}")
            self.log_signal.emit(f"Limiar de similaridade de SEQUÊNCIA atualizado para: {threshold:.2f}", "info")
            print(f"[MonitorThread]: Limiar Sequência atualizado para {threshold:.2f}")
        else:
            self.log_signal.emit(f"Tentativa de definir limiar de SEQUÊNCIA inválido: {threshold}. Mantendo {self.similarity_threshold_sequence_frame:.2f}.", "warning")
            print(f"[MonitorThread]: Tentativa de definir limiar SEQUÊNCIA inválido: {threshold}")

    def set_monitor_interval(self, interval):
        print(f"[DEBUG] MonitorThread.set_monitor_interval chamado com {interval}")
        if 0.1 <= interval <= 5.0:
            self.monitor_interval = interval
            self.log_signal.emit(f"Intervalo de captura atualizado para: {interval:.2f}s", "info")
            print(f"[MonitorThread]: Intervalo de captura atualizado para {interval:.2f}s")
        else:
            self.log_signal.emit(f"Tentativa de definir INTERVALO DE CAPTURA inválido: {interval}. Mantendo {self.monitor_interval:.2f}s.", "warning")
            print(f"[MonitorThread]: Tentativa de definir INTERVALO DE CAPTURA inválido: {interval}")

    def _get_action_description(self, action):
        """Retorna uma descrição legível para a ação. Adaptado de ui/painel.py."""
        action_type = action.get('action_type', 'desconhecido')
        params = action.get('params', {})
        integration = action.get('integration', '')

        desc = f"{integration} - {action_type}"

        if integration == "OBS Studio":
            if action_type == 'Trocar Cena':
                return f"{desc}: '{params.get('scene_name', 'N/A')}'"
            elif action_type == 'Definir Visibilidade da Fonte':
                return f"{desc}: Fonte '{params.get('item_name', 'N/A')}' em Cena '{params.get('scene_name_for_item', 'N/A')}' para {'Visível' if params.get('visible') == 'true' else 'Oculto'}"
            elif action_type == 'Alternar Mudo (Fonte de Áudio)':
                return f"{desc}: Fonte de áudio '{params.get('input_name', 'N/A')}'"
            # Adicionar outras descrições OBS conforme necessário
        
        elif integration == "vMix":
            if action_type == 'Function (Genérico)':
                func_name = params.get('function_name', 'N/A')
                inp = params.get('input')
                val = params.get('value')
                dur = params.get('duration')
                parts = [f"Função: {func_name}"]
                if inp: parts.append(f"Input: {inp}")
                if val: parts.append(f"Valor: {val}")
                if dur: parts.append(f"Duração: {dur}")
                return f"{desc} ({', '.join(parts)})"
            elif action_type == 'SetText':
                return f"{desc}: Input '{params.get('input', 'N/A')}', Campo '{params.get('selected_name', 'N/A')}', Valor '{params.get('text_value', '')[:20]}...'"
            elif action_type == 'Fade' or action_type == 'Cut':
                inp = params.get('input')
                dur = params.get('duration') if action_type == 'Fade' else None
                parts = []
                if inp: parts.append(f"Input: {inp}")
                if dur: parts.append(f"Duração: {dur}ms")
                return f"{desc} ({', '.join(parts) if parts else 'Preview/Program'})"
            elif action_type == 'OverlayInputIn' or action_type == 'OverlayInputOut':
                channel = params.get('overlay_channel', 'N/A')
                inp = params.get('input') if action_type == 'OverlayInputIn' else None
                parts = [f"Canal: {channel}"]
                if inp: parts.append(f"Input: {inp}")
                return f"{desc} ({', '.join(parts)})"
            # Adicionar outras descrições vMix

        # Para ações sem parâmetros detalhados ou tipos simples
        simple_actions = ["Iniciar Gravação", "Parar Gravação", "Iniciar Streaming", "Parar Streaming", 
                          "StartRecording", "StopRecording"]
        if action_type in simple_actions:
            return desc # A descrição já é o tipo de ação

        # Fallback para outros casos
        param_summary = []
        for k, v in params.items():
            param_summary.append(f"{k}='{str(v)[:20]}'") # Limitar tamanho do valor
        if param_summary:
            return f"{desc} ({', '.join(param_summary)})"
        return desc


    def run(self):
        self.running = True
        self.log_signal.emit("Thread de monitoramento iniciada.", "info")
        print("[MonitorThread RUN]: Após emitir 'Thread iniciada'") # NOVO PRINT
        self.status_signal.emit("Monitoramento Ativo")

        if not self.references_data:
            self.log_signal.emit("Nenhuma referência carregada na thread. Parando.", "warning")
            print("[MonitorThread RUN]: Nenhuma referência carregada. Parando.") # NOVO PRINT
            self.running = False
            # return # Não precisa de return, o loop while não vai rodar

        # Preparar referências (ex: carregar imagens estáticas, calcular histogramas)
        # Isso pode ser feito uma vez no início para otimizar.
        prepared_references = []
        max_sequence_len = 0
        print(f"[MonitorThread RUN]: Antes do loop de preparação. N refs na thread: {len(self.references_data)}") # NOVO PRINT
        self.log_signal.emit(f"[Thread Prep] Iniciando preparação de {len(self.references_data)} referências.", "debug") # NOVO LOG

        for ref_index, ref_data in enumerate(self.references_data):
            print(f"[MonitorThread RUN Prep Ref {ref_index}]: Processando {ref_data.get('name')}, Tipo: {ref_data.get('type')}") # NOVO PRINT
            self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Processando: {ref_data.get('name')}, Tipo: {ref_data.get('type')}", "debug") # NOVO LOG
            prep_ref = ref_data.copy() # Copiar para não modificar a original
            if ref_data.get('type') == 'static':
                try:
                    img = cv2.imread(ref_data['path'])
                    if img is None:
                        print(f"[MonitorThread RUN Prep Ref {ref_index}]: Erro ao carregar imagem estática: {ref_data['path']}") # NOVO PRINT
                        self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Erro ao carregar imagem estática: {ref_data['path']}", "error")
                        continue # Pular esta referência
                    prep_ref['image_gray'] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                except Exception as e:
                    print(f"[MonitorThread RUN Prep Ref {ref_index}]: Exceção ao preparar estática {ref_data.get('name')}: {e}") # NOVO PRINT
                    self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Exceção ao preparar referência estática {ref_data.get('name')}: {e}", "error")
                    continue
            elif ref_data.get('type') == 'sequence':
                frame_paths = ref_data.get('frame_paths', [])
                print(f"[MonitorThread RUN Prep Ref {ref_index}]: Preparando sequência '{ref_data.get('name')}' com {len(frame_paths)} paths.") # NOVO PRINT
                self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Preparando sequência '{ref_data.get('name')}' com {len(frame_paths)} paths de frames.", "debug") # NOVO LOG
                if not frame_paths:
                    print(f"[MonitorThread RUN Prep Ref {ref_index}]: Sequência '{ref_data.get('name')}' sem frames. Pulando.") # NOVO PRINT
                    self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Sequência '{ref_data.get('name')}' não tem frames. Pulando.", "warning")
                    continue
                
                prep_ref['sequence_frames_gray'] = []
                valid_sequence = True
                for frame_idx, frame_path in enumerate(frame_paths):
                    try:
                        # print(f"[MonitorThread RUN Prep Ref {ref_index}, Frame {frame_idx}]: Carregando {frame_path}") # NOVO PRINT (muito verboso)
                        # self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Carregando frame {frame_idx}: {frame_path}", "debug") # LOG MUITO VERBOSO, DESATIVADO POR PADRÃO
                        frame_img = cv2.imread(frame_path)
                        if frame_img is None:
                            print(f"[MonitorThread RUN Prep Ref {ref_index}, Frame {frame_idx}]: Erro ao carregar frame '{frame_path}'") # NOVO PRINT
                            self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Erro ao carregar frame '{frame_path}' para sequência '{ref_data.get('name')}' (frame {frame_idx}).", "error")
                            valid_sequence = False
                            break
                        gray_frame = cv2.cvtColor(frame_img, cv2.COLOR_BGR2GRAY)
                        prep_ref['sequence_frames_gray'].append(gray_frame)
                    except Exception as e:
                        print(f"[MonitorThread RUN Prep Ref {ref_index}, Frame {frame_idx}]: Exceção ao preparar frame '{frame_path}': {e}") # NOVO PRINT
                        self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Exceção ao preparar frame '{frame_path}' da sequência {ref_data.get('name')}: {e}", "error")
                        valid_sequence = False
                        break
                if not valid_sequence:
                    print(f"[MonitorThread RUN Prep Ref {ref_index}]: Sequência '{ref_data.get('name')}' inválida.") # NOVO PRINT
                    self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Sequência '{ref_data.get('name')}' marcada como inválida durante preparação de frames.", "warning") # NOVO LOG
                    continue 
                
                current_seq_len = len(prep_ref['sequence_frames_gray'])
                if current_seq_len > 0: 
                    max_sequence_len = max(max_sequence_len, current_seq_len)
                    print(f"[MonitorThread RUN Prep Ref {ref_index}]: Seq '{ref_data.get('name')}' preparada com {current_seq_len} frames gray.") # NOVO PRINT
                    self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Sequência '{ref_data.get('name')}' preparada com {current_seq_len} frames gray.", "debug") # NOVO LOG
                else: 
                    print(f"[MonitorThread RUN Prep Ref {ref_index}]: Seq '{ref_data.get('name')}' vazia após preparação.") # NOVO PRINT
                    self.log_signal.emit(f"[Thread Prep Ref {ref_index}] Sequência '{ref_data.get('name')}' ficou vazia após preparação. Pulando.", "warning")
                    continue
            
            prepared_references.append(prep_ref)
            print(f"[MonitorThread RUN Prep Ref {ref_index}]: Concluída preparação para {ref_data.get('name')}") # NOVO PRINT
        
        print(f"[MonitorThread RUN]: Após loop de preparação. {len(prepared_references)} referências preparadas.") # NOVO PRINT
        self.log_signal.emit(f"[Thread Prep] Preparação concluída. {len(prepared_references)} referências válidas prontas para monitoramento.", "debug") # NOVO LOG

        if not prepared_references:
            print("[MonitorThread RUN]: Nenhuma referência válida pôde ser preparada. Thread parando.") # NOVO PRINT
            self.log_signal.emit("Nenhuma referência válida pôde ser preparada. Thread parando.", "error")
            self.running = False
            # return

        pgm_frame_buffer = []

        # Detalhes da captura PGM
        roi_x, roi_y, roi_w, roi_h = self.pgm_details['roi']
        capture_kind = self.pgm_details['kind']
        capture_id = self.pgm_details['id'] # monitor_idx ou window_obj
        
        print("[MonitorThread RUN]: Antes do loop principal (with mss)") # NOVO PRINT
        with mss.mss() as sct:
            while self.running:
                print("[MonitorThread RUN]: Início do ciclo while(running)") # NOVO PRINT
                start_time_cycle = time.time()
                captured_frame_bgr = None
                try:
                    if capture_kind == 'monitor':
                        monitor_capture_details = sct.monitors[capture_id] # capture_id é o índice do monitor
                         # Captura a ROI diretamente se possível, ou a tela do monitor e recorta
                        grab_area = {"top": monitor_capture_details["top"] + roi_y, 
                                     "left": monitor_capture_details["left"] + roi_x, 
                                     "width": roi_w, "height": roi_h, 
                                     "mon": capture_id}
                        sct_img = sct.grab(grab_area)
                        img_np = np.array(sct_img)
                        captured_frame_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)

                    elif capture_kind == 'window':
                        window_obj = capture_id # capture_id é o objeto da janela pyautogui
                        # Verificar se a janela ainda é válida
                        if not (window_obj and hasattr(window_obj, 'visible') and window_obj.visible and window_obj.width > 0 and window_obj.height > 0):
                            self.log_signal.emit(f"Janela '{window_obj.title if window_obj else 'N/A'}' não está mais válida ou visível. Pausando captura temporariamente.", "warning")
                            time.sleep(self.monitor_interval * 2) # Espera mais antes de tentar de novo
                            continue

                        # As coordenadas da ROI (roi_x, roi_y) são relativas ao canto superior esquerdo da janela.
                        # As coordenadas da janela (window_obj.left, window_obj.top) são globais.
                        # Portanto, a região global para pyautogui.screenshot é:
                        capture_region_global = (window_obj.left + roi_x, 
                                                 window_obj.top + roi_y, 
                                                 roi_w, 
                                                 roi_h)
                        pil_img = pyautogui.screenshot(region=capture_region_global)
                        captured_frame_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    if captured_frame_bgr is None:
                        self.log_signal.emit(f"Falha ao capturar frame PGM ({capture_kind}).", "error")
                        time.sleep(self.monitor_interval)
                        continue

                    captured_frame_gray = cv2.cvtColor(captured_frame_bgr, cv2.COLOR_BGR2GRAY)
                    # captured_frame_hist = cv2.calcHist([captured_frame_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
                    # cv2.normalize(captured_frame_hist, captured_frame_hist)

                    match_found_in_cycle = False
                    for ref_idx_loop, ref in enumerate(prepared_references): # Adicionado ref_idx_loop para logs
                        if not self.running: break # Sair do loop de referências se a thread foi parada

                        ref_name = ref.get('name', 'Desconhecida')
                        print(f"[MonitorThread RUN]: Ciclo Interno - Verificando Ref {ref_idx_loop}: '{ref_name}' Tipo: {ref.get('type')}") # NOVO PRINT

                        if ref.get('type') == 'static':
                            # Comparação de Imagem Estática (ex: Histograma)
                            ref_image_gray = ref.get('image_gray')
                            if ref_image_gray is None: 
                                print(f"[MonitorThread RUN]: Ref '{ref_name}' tipo estática sem image_gray. Pulando.") # NOVO PRINT
                                continue # Já logado durante preparação

                            # Se o histograma foi pré-calculado na preparação:
                            # similarity = cv2.compareHist(ref.get('histogram'), captured_frame_hist, cv2.HISTCMP_CORREL)
                            
                            # Comparação de histograma no momento (pode ser mais lento se muitas refs)
                            hist_ref = cv2.calcHist([ref_image_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
                            cv2.normalize(hist_ref, hist_ref)
                            hist_frame = cv2.calcHist([captured_frame_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
                            cv2.normalize(hist_frame, hist_frame)
                            similarity = cv2.compareHist(hist_ref, hist_frame, cv2.HISTCMP_CORREL)
                            
                            print(f"[MonitorThread RUN]: Comparando com estática '{ref_name}', Similaridade: {similarity:.3f}") # NOVO PRINT
                            self.log_signal.emit(f"Similaridade com estática '{ref_name}': {similarity:.3f}", "debug")

                            if similarity >= self.similarity_threshold_static:
                                print(f"[MonitorThread RUN]: MATCH ESTÁTICO com '{ref_name}' (Similaridade: {similarity:.3f})") # NOVO PRINT
                                self.log_signal.emit(f"Referência ESTÁTICA encontrada: '{ref_name}' (Similaridade: {similarity:.3f})", "success")
                                if self.action_executor_callback and ref.get('actions'):
                                    for action_idx, action in enumerate(ref.get('actions')): # Adicionado action_idx para logs
                                        action_desc_for_log = "Erro ao obter descrição"
                                        try:
                                            action_desc_for_log = self._get_action_description(action)
                                        except Exception as e_desc:
                                            print(f"[MonitorThread RUN]: Exceção em _get_action_description para '{ref_name}': {e_desc}") # NOVO PRINT
                                            self.log_signal.emit(f"Exceção em _get_action_description para '{ref_name}', ação idx {action_idx}: {e_desc}", "error")

                                        print(f"[MonitorThread RUN]: Preparando para chamar callback para ação {action_idx} em '{ref_name}': {action_desc_for_log}") # NOVO PRINT
                                        self.log_signal.emit(f"Executando ação para '{ref_name}': {action_desc_for_log}", "info")
                                        self.action_executor_callback(action)
                                match_found_in_cycle = True
                                break # Processar apenas uma correspondência por ciclo de monitoramento

                        elif ref.get('type') == 'sequence':
                            print(f"[MonitorThread RUN]: Processando tipo sequência '{ref_name}' (max_seq_len: {max_sequence_len})") # NOVO PRINT
                            if max_sequence_len > 0: # Só processa sequências se houver alguma
                                # Adicionar frame atual ao buffer (apenas a imagem gray para economizar memória)
                                pgm_frame_buffer.append(captured_frame_gray)
                                while len(pgm_frame_buffer) > max_sequence_len:
                                    pgm_frame_buffer.pop(0) # Manter o buffer no tamanho máximo
                                
                                print(f"[MonitorThread RUN]: Seq '{ref_name}', Buffer PGM atualizado, len: {len(pgm_frame_buffer)}") # NOVO PRINT

                                sequence_frames_gray = ref.get('sequence_frames_gray', [])
                                # sequence_histograms = ref.get('sequence_histograms', [])
                                current_sequence_len = len(sequence_frames_gray)

                                print(f"[MonitorThread RUN]: Seq '{ref_name}', len_frames_ref: {current_sequence_len}, len_buffer: {len(pgm_frame_buffer)}") # NOVO PRINT
                                if current_sequence_len > 0 and len(pgm_frame_buffer) >= current_sequence_len:
                                    # Comparar os últimos 'current_sequence_len' frames do buffer com a sequência de referência
                                    is_sequence_match = True
                                    # Iterar de trás para frente ou do início, tanto faz
                                    # Aqui, pegamos a sub-lista do buffer que corresponde ao tamanho da sequência atual
                                    buffer_subset_for_comparison = pgm_frame_buffer[-current_sequence_len:]
                                    
                                    frame_similarities = []
                                    for i in range(current_sequence_len):
                                        ref_seq_frame_gray = sequence_frames_gray[i]
                                        buffer_frame_gray = buffer_subset_for_comparison[i]
                                        
                                        hist_ref_seq = cv2.calcHist([ref_seq_frame_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
                                        cv2.normalize(hist_ref_seq, hist_ref_seq)
                                        hist_buffer_seq = cv2.calcHist([buffer_frame_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
                                        cv2.normalize(hist_buffer_seq, hist_buffer_seq)
                                        similarity = cv2.compareHist(hist_ref_seq, hist_buffer_seq, cv2.HISTCMP_CORREL)
                                        frame_similarities.append(similarity)
                                        
                                        # print(f"[MonitorThread RUN]: Seq '{ref_name}', Frame {i}, Similaridade: {similarity:.3f}") # NOVO PRINT (MUITO VERBOSO)

                                        if similarity < self.similarity_threshold_sequence_frame:
                                            is_sequence_match = False
                                            break 
                                    
                                    sim_summary = ", ".join([f"{s:.2f}" for s in frame_similarities])
                                    print(f"[MonitorThread RUN]: Seq '{ref_name}' (len {current_sequence_len}), Similars Frame-a-Frame=[{sim_summary}]") # NOVO PRINT
                                    self.log_signal.emit(f"Seq '{ref_name}' (len {current_sequence_len}), buffer (len {len(pgm_frame_buffer)}): Similars=[{sim_summary}]", "debug")

                                    if is_sequence_match:
                                        print(f"[MonitorThread RUN]: MATCH SEQUÊNCIA com '{ref_name}'") # NOVO PRINT
                                        self.log_signal.emit(f"Referência de SEQUÊNCIA encontrada: '{ref_name}'", "success")
                                        if self.action_executor_callback and ref.get('actions'):
                                             for action_idx, action in enumerate(ref.get('actions')): # Adicionado action_idx
                                                action_desc_for_log = "Erro ao obter descrição"
                                                try:
                                                    action_desc_for_log = self._get_action_description(action)
                                                except Exception as e_desc:
                                                    print(f"[MonitorThread RUN]: Exceção em _get_action_description para seq '{ref_name}': {e_desc}") # NOVO PRINT
                                                    self.log_signal.emit(f"Exceção em _get_action_description para seq '{ref_name}', ação idx {action_idx}: {e_desc}", "error")
                                                
                                                print(f"[MonitorThread RUN]: Preparando para chamar callback para ação {action_idx} em seq '{ref_name}': {action_desc_for_log}") # NOVO PRINT
                                                self.log_signal.emit(f"Executando ação para sequência '{ref_name}': {action_desc_for_log}", "info")
                                                self.action_executor_callback(action)
                                        match_found_in_cycle = True
                                        pgm_frame_buffer.clear() # Limpar buffer após match de sequência para evitar re-trigger imediato
                                        print(f"[MonitorThread RUN]: Buffer PGM limpo após match de sequência.") # NOVO PRINT
                                        break # Processar apenas uma correspondência por ciclo

                        if match_found_in_cycle:
                            print(f"[MonitorThread RUN]: Match encontrado no ciclo com '{ref_name}'. Saindo do loop de refs.") # NOVO PRINT
                            break # Sair do loop de referências
                
                except mss.exception.ScreenShotError as e_mss:
                    print(f"[MonitorThread RUN]: Erro MSS na captura PGM: {e_mss}") # NOVO PRINT
                    self.log_signal.emit(f"Erro MSS na captura PGM: {e_mss}. Verifique se a fonte (monitor/janela) ainda é válida.", "error")
                    time.sleep(self.monitor_interval * 2) # Dar um tempo maior antes de tentar novamente
                except Exception as e:
                    print(f"[MonitorThread RUN]: Erro inesperado no ciclo: {e}") # NOVO PRINT
                    self.log_signal.emit(f"Erro inesperado no ciclo de monitoramento: {e}", "error")
                    import traceback
                    print(traceback.format_exc()) # NOVO PRINT para traceback
                    self.log_signal.emit(traceback.format_exc(), "debug") # Log completo do traceback para depuração
                    # Considerar parar a thread ou apenas logar e continuar? Por ora, logar e continuar.

                if match_found_in_cycle:
                    print("[MonitorThread RUN]: Match encontrado. Aguardando antes do próximo ciclo completo.") # NOVO PRINT
                    self.log_signal.emit("Match encontrado. Aguardando antes do próximo ciclo completo de verificação.", "debug")
                    time.sleep(1.5) # Um delay maior após uma ação ser disparada

                # Tempo de ciclo e sleep
                elapsed_time_cycle = time.time() - start_time_cycle
                sleep_time = self.monitor_interval - elapsed_time_cycle
                # print(f"[MonitorThread RUN]: Fim do ciclo. Elapsed: {elapsed_time_cycle:.3f}s, Sleep: {sleep_time:.3f}s") # NOVO PRINT (pode ser verboso)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                # else:
                #     print(f"[MonitorThread RUN]: Ciclo levou {elapsed_time_cycle:.3f}s, mais que o intervalo de {self.monitor_interval}s.") # NOVO PRINT
                #     self.log_signal.emit(f"Ciclo de monitoramento levou {elapsed_time_cycle:.3f}s, mais que o intervalo de {self.monitor_interval}s.", "debug")

        print("[MonitorThread RUN]: Saindo do loop principal (running is false ou erro no mss)") # NOVO PRINT
        self.log_signal.emit("Thread de monitoramento terminada.", "info")
        self.status_signal.emit("Monitoramento Parado")

    def stop(self):
        print("[MonitorThread STOP]: Método stop chamado.") # NOVO PRINT
        self.running = False
        self.log_signal.emit("Sinal de parada recebido pela thread de monitoramento.", "info")

