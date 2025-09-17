from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QFrame, QSizePolicy, QComboBox, QFormLayout, QSpacerItem, QMessageBox, QListWidgetItem, QInputDialog, QFileDialog, QDialog, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import pyautogui  # Adicionada importação
import mss  # Adicionada importação
import cv2  # Adicionada importação
import numpy as np  # Adicionada importação
import os  # Adicionada importação
import re # Para sanitizar nomes de arquivo
import shutil # Adicionada importação para cópia de arquivos
# import NDIlib as NDI # Adicionada importação para NDI
try:
    import NDIlib as NDI
    NDI_AVAILABLE = True
except Exception:
    NDI = None
    NDI_AVAILABLE = False

from .action_config_dialog import ActionConfigDialog # Adicionada importação

class ReferenceManagerWidget(QWidget):
    """Widget para gerenciar as imagens de referência para monitoramento."""
    # Sinal para notificar a MainWindow ou outro controller sobre mudanças nas referências
    references_updated = pyqtSignal(list)

    def __init__(self, parent=None, main_controller=None):
        super().__init__(parent)
        self.main_controller = main_controller # <--- Armazenar main_controller
        self.selected_pgm_details = None # (type: 'monitor'/'window', id: monitor_idx/window_obj, roi: (x,y,w,h))
        self.references_data = [] # Lista para armazenar dados das referências {'name': str, 'path': str, 'actions': []}
        self._setup_ui()
        self._ensure_references_dir()

    def _ensure_references_dir(self):
        self.references_dir = os.path.join("switchpilot", "references")
        os.makedirs(self.references_dir, exist_ok=True)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # Margens menores para docks

        # --- Seção de Ações Globais ---
        actions_group = QFrame(self)  # Usando QFrame para agrupar visualmente
        actions_group.setObjectName("actionsGroupFrame")  # Para estilização específica se necessário
        # actions_group.setFrameShape(QFrame.StyledPanel) # Estilo do painel via QSS
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(10)

        # --- Fonte de Captura ---
        source_capture_layout = QFormLayout()
        source_capture_layout.setSpacing(8)

        self.source_type_label = QLabel("Fonte de Captura:")
        self.source_type_combo = QComboBox()
        # Se NDI indisponível, não exibir a opção
        if NDI_AVAILABLE:
            self.source_type_combo.addItems(["Monitor", "Janela", "NDI"])
        else:
            self.source_type_combo.addItems(["Monitor", "Janela"])
        source_capture_layout.addRow(self.source_type_label, self.source_type_combo)

        # --- Combo para seleção de monitor específico ---
        self.monitor_list_label = QLabel("Monitor Específico:")
        self.monitor_list_combo = QComboBox()
        self.monitor_list_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.btn_refresh_monitors = QPushButton("Atualizar")
        self.btn_refresh_monitors.setToolTip("Recarrega a lista de monitores")
        self.btn_refresh_monitors.setFixedWidth(90)
        self.monitor_field_container = QWidget(self)
        _mon_layout = QHBoxLayout(self.monitor_field_container)
        _mon_layout.setContentsMargins(0, 0, 0, 0)
        _mon_layout.setSpacing(6)
        _mon_layout.addWidget(self.monitor_list_combo, 1)
        _mon_layout.addWidget(self.btn_refresh_monitors, 0)
        self.monitor_list_label.setVisible(True) # Visível por padrão para monitores
        self.monitor_field_container.setVisible(True)
        source_capture_layout.addRow(self.monitor_list_label, self.monitor_field_container)

        self.window_list_label = QLabel("Janela Específica:")
        self.window_list_combo = QComboBox()  # Usaremos ComboBox para janelas por ser mais compacto
        self.window_list_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.btn_refresh_windows = QPushButton("Atualizar")
        self.btn_refresh_windows.setToolTip("Recarrega a lista de janelas visíveis")
        self.btn_refresh_windows.setFixedWidth(90)
        self.window_field_container = QWidget(self)
        _win_layout = QHBoxLayout(self.window_field_container)
        _win_layout.setContentsMargins(0, 0, 0, 0)
        _win_layout.setSpacing(6)
        _win_layout.addWidget(self.window_list_combo, 1)
        _win_layout.addWidget(self.btn_refresh_windows, 0)
        self.window_list_label.setVisible(False)  # Inicialmente oculto
        self.window_field_container.setVisible(False)  # Inicialmente oculto
        source_capture_layout.addRow(self.window_list_label, self.window_field_container)

        # --- Combo para seleção de fonte NDI ---
        self.ndi_list_label = QLabel("Fonte NDI:")
        self.ndi_list_combo = QComboBox()
        self.ndi_list_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.btn_refresh_ndi = QPushButton("Atualizar")
        self.btn_refresh_ndi.setToolTip("Redescobrir fontes NDI")
        self.btn_refresh_ndi.setFixedWidth(90)
        self.ndi_field_container = QWidget(self)
        _ndi_layout = QHBoxLayout(self.ndi_field_container)
        _ndi_layout.setContentsMargins(0, 0, 0, 0)
        _ndi_layout.setSpacing(6)
        _ndi_layout.addWidget(self.ndi_list_combo, 1)
        _ndi_layout.addWidget(self.btn_refresh_ndi, 0)
        self.ndi_list_label.setVisible(False)  # Inicialmente oculto
        self.ndi_field_container.setVisible(False)  # Inicialmente oculto
        # Só adicionar ao layout se NDI estiver disponível
        if NDI_AVAILABLE:
            source_capture_layout.addRow(self.ndi_list_label, self.ndi_field_container)
        else:
            # Apenas placeholder: se quiser, poderíamos exibir uma dica que NDI não está instalado
            pass
        
        actions_layout.addLayout(source_capture_layout)
        actions_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Região PGM ---
        self.pgm_region_label = QLabel("Região PGM: Não definida")
        self.pgm_region_label.setStyleSheet("font-style: italic; color: #d8dee9;")
        actions_layout.addWidget(self.pgm_region_label)

        self.select_region_button = QPushButton("Selecionar Região PGM")
        self.select_region_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        actions_layout.addWidget(self.select_region_button)
        
        actions_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Adicionar Referências (Unificado) ---
        self.add_reference_button = QPushButton("Adicionar Referência...")
        self.add_reference_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.add_reference_menu = QMenu(self)
        
        self.add_image_action = QAction("Imagem de Arquivo...", self)
        self.add_image_action.triggered.connect(self._handle_add_existing_reference)
        self.add_reference_menu.addAction(self.add_image_action)
        
        self.add_sequence_action = QAction("Vídeo/GIF (Sequência) de Arquivo...", self)
        self.add_sequence_action.triggered.connect(self._handle_add_video_gif_sequence)
        self.add_reference_menu.addAction(self.add_sequence_action)
        
        self.add_reference_button.setMenu(self.add_reference_menu)
        actions_layout.addWidget(self.add_reference_button)
        
        main_layout.addWidget(actions_group)

        # --- Seção da Lista de Referências (Simplificada) ---
        list_label = QLabel("Imagens de Referência Atuais:")
        list_label.setProperty("heading", True)
        main_layout.addWidget(list_label)  # Adicionado diretamente ao main_layout

        self.reference_list_widget = QListWidget()
        self.reference_list_widget.setAlternatingRowColors(True)
        self.reference_list_widget.setMinimumHeight(150)  # Manter para garantir algum espaço inicial
        self.reference_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.reference_list_widget, 1)  # Adicionado diretamente ao main_layout com stretch
        
        list_actions_layout = QHBoxLayout()
        self.configure_actions_button = QPushButton("Configurar Ações da Selecionada")
        self.remove_reference_button = QPushButton("Remover Selecionada")
        self.configure_actions_button.setEnabled(False)
        self.remove_reference_button.setEnabled(False)

        list_actions_layout.addWidget(self.configure_actions_button)
        list_actions_layout.addWidget(self.remove_reference_button)
        main_layout.addLayout(list_actions_layout)  # Adicionado diretamente ao main_layout

        # main_layout.addWidget(list_group)  # Comentado/Removido pois list_group foi removido
        main_layout.addStretch(1)  # Manter stretch global para empurrar esta seção para cima, se necessário

        # Conectar sinais
        self.source_type_combo.currentIndexChanged.connect(self._on_source_type_changed)
        self.reference_list_widget.currentItemChanged.connect(self._on_current_item_changed)
        self.select_region_button.clicked.connect(self._handle_select_pgm_region)
        self.remove_reference_button.clicked.connect(self._handle_remove_reference)
        self.configure_actions_button.clicked.connect(self._handle_configure_actions)
        self.btn_refresh_monitors.clicked.connect(self._populate_monitor_list)
        self.btn_refresh_windows.clicked.connect(self._populate_window_list)
        if NDI_AVAILABLE:
            self.btn_refresh_ndi.clicked.connect(self._populate_ndi_list)
        # self.btn_pick_window.clicked.connect(self._pick_window_by_click)  # Removido para simplificar
        
        # Inicializar lista de monitores por padrão (já que "Monitor" é o primeiro item)
        self._populate_monitor_list()

    def set_main_controller(self, main_controller):
        """Define o main_controller para este widget."""
        self.main_controller = main_controller
        # REMOVIDO: print(f"DEBUG: ReferenceManagerWidget - main_controller definido: {self.main_controller}")

    def _handle_select_pgm_region(self):
        """Permite ao usuário selecionar uma região da tela, janela ou fonte NDI para monitoramento PGM."""
        try:
            source_type = self.source_type_combo.currentText()
            print(f"[DEBUG] Tipo de fonte selecionado: {source_type}")
            
            if source_type == "Monitor":
                print("[DEBUG] Iniciando captura de Monitor...")
                selected_monitor_idx = self.monitor_list_combo.currentIndex()
                print(f"[DEBUG] Índice do monitor selecionado: {selected_monitor_idx}")
                
                if selected_monitor_idx < 0 or self.monitor_list_combo.itemText(selected_monitor_idx) == "Nenhum monitor encontrado":
                    QMessageBox.warning(self, "Seleção de Monitor", "Por favor, selecione um monitor válido na lista.")
                    return

                import mss
                with mss.mss() as sct:
                    monitor_number = selected_monitor_idx + 1  # sct.monitors[0] é informação geral
                    if monitor_number >= len(sct.monitors):
                        QMessageBox.warning(self, "Erro de Monitor", "Monitor selecionado não está disponível.")
                        return
                    
                    monitor = sct.monitors[monitor_number]
                    print(f"[DEBUG] Monitor selecionado: {monitor}")
                    
                    screenshot = sct.grab(monitor)
                    img_to_show = np.array(screenshot)
                    img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_BGRA2BGR)
                    print(f"[DEBUG] Screenshot capturado: {img_to_show.shape}")
                    
                capture_source_name = f"Monitor {monitor_number}"
                source_id = monitor_number
                source_kind = 'monitor'
                
            elif source_type == "Janela":
                print("[DEBUG] Iniciando captura de Janela...")
                selected_window_idx = self.window_list_combo.currentIndex()
                print(f"[DEBUG] Índice da janela selecionada: {selected_window_idx}")
                
                if selected_window_idx < 0 or self.window_list_combo.itemText(selected_window_idx) in ["Nenhuma janela encontrada", "Erro ao listar janelas"]:
                    QMessageBox.warning(self, "Seleção de Janela", "Por favor, selecione uma janela válida na lista.")
                    return

                window_obj = self.window_list_combo.itemData(selected_window_idx)
                print(f"[DEBUG] Objeto da janela: {window_obj}")
                
                if not window_obj:
                    QMessageBox.warning(self, "Seleção de Janela", "Não foi possível obter dados da janela selecionada.")
                    return

                # pyautogui.screenshot pode falhar se a janela for minimizada ou não tiver área.
                # Usar as coordenadas da janela para o screenshot
                # É importante que window_obj.left, top, width, height sejam válidos
                # Alguns sistemas/janelas podem retornar coordenadas relativas ou (0,0,0,0) se não estiverem visíveis/ativas
                # Adicionando uma verificação extra
                print(f"[DEBUG] Coordenadas da janela: left={window_obj.left}, top={window_obj.top}, width={window_obj.width}, height={window_obj.height}")
                
                if window_obj.left is None or window_obj.top is None or window_obj.width is None or window_obj.height is None:
                    QMessageBox.warning(self, "Seleção de Janela", f"Não foi possível obter as coordenadas da janela '{window_obj.title}'. Tente trazê-la para frente.")
                    return

                region_capture = (window_obj.left, window_obj.top, window_obj.width, window_obj.height)
                print(f"[DEBUG] Região de captura: {region_capture}")
                
                pil_img = pyautogui.screenshot(region=region_capture)
                img_to_show = np.array(pil_img)
                img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_RGB2BGR)
                print(f"[DEBUG] Screenshot da janela capturado: {img_to_show.shape}")
                
                capture_source_name = f"Janela: {window_obj.title}"
                source_id = window_obj  # Ou window_obj._hWnd se precisarmos de um ID simples e tiver no objeto
                source_kind = 'window'
                
            elif source_type == "NDI":
                print("[DEBUG] Iniciando captura NDI...")
                selected_ndi_idx = self.ndi_list_combo.currentIndex()
                print(f"[DEBUG] Índice da fonte NDI selecionada: {selected_ndi_idx}")
                
                if selected_ndi_idx < 0 or self.ndi_list_combo.itemText(selected_ndi_idx) in ["Carregando fontes NDI...", "Nenhuma fonte NDI encontrada", "Erro ao listar fontes NDI"]:
                    QMessageBox.warning(self, "Seleção de Fonte", "Por favor, selecione uma fonte NDI válida na lista.")
                    return
                
                ndi_source = self.ndi_list_combo.itemData(selected_ndi_idx)
                print(f"[DEBUG] Dados da fonte NDI: {ndi_source}")
                
                if not ndi_source:
                    QMessageBox.warning(self, "Seleção de Fonte", "Não foi possível obter dados da fonte NDI selecionada.")
                    return

                print("[DEBUG] Chamando _capture_ndi_frame...")
                # Capturar frame da fonte NDI
                img_to_show = self._capture_ndi_frame(ndi_source)
                print(f"[DEBUG] Resultado da captura NDI: {img_to_show.shape if img_to_show is not None else 'None'}")
                
                if img_to_show is None:
                    QMessageBox.warning(self, "Erro NDI", "Não foi possível capturar frame da fonte NDI selecionada.")
                    return
                
                capture_source_name = f"NDI: {self.ndi_list_combo.itemText(selected_ndi_idx)}"
                source_id = ndi_source
                source_kind = 'ndi'
            else:
                QMessageBox.warning(self, "Seleção de Fonte", "Tipo de fonte de captura desconhecido.")
                return

            print(f"[DEBUG] Imagem capturada com sucesso: {img_to_show.shape}")
            print(f"[DEBUG] Fonte: {capture_source_name}")

            if img_to_show is not None:
                try:
                    # Verificar se a imagem é válida
                    if img_to_show.size == 0:
                        QMessageBox.warning(self, "Erro de Imagem", "A imagem capturada está vazia.")
                        return
                    
                    # Verificar se a imagem é contígua na memória
                    if not img_to_show.flags['C_CONTIGUOUS']:
                        img_to_show = np.ascontiguousarray(img_to_show)
                    
                    window_name = f"Selecione a Região PGM - {capture_source_name}"
                    # Reduzir para caber na tela sem perder proporção e depois remapear a ROI
                    h, w = img_to_show.shape[:2]
                    # Tentar manter 1:1 se couber na tela atual
                    try:
                        screen_w, screen_h = pyautogui.size()
                    except Exception:
                        screen_w, screen_h = (1920, 1080)
                    margin = 120  # espaço para bordas/OSD
                    max_w, max_h = max(640, screen_w - margin), max(360, screen_h - margin)
                    if w <= max_w and h <= max_h:
                        scale = 1.0
                        display_img = img_to_show
                    else:
                        scale = min(max_w / float(w), max_h / float(h))
                        # Interpolation voltada à nitidez (nearest) na visualização
                        display_img = cv2.resize(img_to_show, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_NEAREST)
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
                    roi_disp = cv2.selectROI(window_name, display_img, False, False)
                    # Remapear de volta para o frame original usado na análise
                    roi = (int(roi_disp[0] / scale), int(roi_disp[1] / scale), int(roi_disp[2] / scale), int(roi_disp[3] / scale))
                    
                    cv2.destroyAllWindows()
                    
                except Exception as cv_error:
                    try:
                        cv2.destroyAllWindows()
                    except Exception:
                        pass
                    
                    QMessageBox.critical(self, "Erro OpenCV", f"Erro ao selecionar região: {cv_error}")
                    return

                if roi and roi[2] > 0 and roi[3] > 0:  # roi = (x, y, w, h)
                    self.selected_pgm_details = {
                        'kind': source_kind,
                        'id': source_id,
                        'roi': roi,
                        'source_name': capture_source_name
                    }
                    self.pgm_region_label.setText(f"Região PGM: ({roi[0]},{roi[1]},{roi[2]},{roi[3]}) em {capture_source_name}")
                    self.pgm_region_label.setStyleSheet("color: #a3be8c;")
                    # REMOVIDO: print(f"Região PGM selecionada: {self.selected_pgm_details}")

                    # --- Adicionar automaticamente a primeira referência ---
                    first_ref_image = img_to_show[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
                    
                    if first_ref_image.size == 0:
                        QMessageBox.warning(self, "Erro de Captura Automática", "A região selecionada resultou em uma imagem vazia.")
                    else:
                        # Gerar um nome padrão sugerido
                        temp_idx = 1
                        while True:
                            suggested_base_name = f"ref_{temp_idx:02d}"
                            # Verificar se já existe com esse nome base (sem sufixo numérico ainda)
                            # Esta verificação de nome padrão é só para o QInputDialog
                            potential_default_path = os.path.join(self.references_dir, f"{suggested_base_name}.png")
                            if not os.path.exists(potential_default_path):
                                break
                            temp_idx += 1

                        text, ok = QInputDialog.getText(self, "Nome da Referência",
                                                        "Digite o nome para a imagem de referência (sem extensão):",
                                                        text=suggested_base_name)
                        
                        if ok and text:
                            # Sanitizar o nome do arquivo
                            base_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', text.strip())  # Permitir pontos para extensões futuras, mas vamos adicionar .png
                            if not base_filename:  # Se o nome se tornar vazio após sanitização
                                base_filename = suggested_base_name  # Usar o padrão

                            # Adicionar extensão .png se não estiver lá (ou forçar para consistência)
                            if base_filename.lower().endswith('.png'):
                                base_filename = base_filename[:-4]
                            
                            # Lógica para evitar sobrescrever (nome_01.png, nome_02.png)
                            final_filename = f"{base_filename}.png"
                            filepath = os.path.join(self.references_dir, final_filename)
                            count = 1
                            while os.path.exists(filepath):
                                final_filename = f"{base_filename}_{count:02d}.png"
                                filepath = os.path.join(self.references_dir, final_filename)
                                count += 1
                            
                            if cv2.imwrite(filepath, first_ref_image):
                                new_ref_data = {'name': final_filename, 'type': 'static', 'path': filepath, 'actions': []}
                                self.references_data.append(new_ref_data)
                                
                                self._display_reference_in_list(new_ref_data)
                                self.reference_list_widget.setCurrentRow(self.reference_list_widget.count() - 1)
                                self.references_updated.emit(self.get_all_references_data())  # Usar getter
                                QMessageBox.information(self, "Referência Salva", f"Referência '{final_filename}' salva com sucesso.")
                            else:
                                QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar a imagem de referência em {filepath}")
                        elif ok and not text:  # Usuário clicou OK mas deixou o nome vazio
                            QMessageBox.warning(self, "Nome Inválido", "O nome da referência não pode ser vazio. Referência não salva.")
                        else:  # Usuário cancelou o QInputDialog
                            QMessageBox.information(self, "Captura Cancelada", "Seleção de região PGM mantida, mas a referência não foi salva.")
                    # --- Fim da adição automática ---
                else:
                    self.selected_pgm_details = None
                    self.pgm_region_label.setText("Região PGM: Seleção cancelada ou inválida")
                    self.pgm_region_label.setStyleSheet("font-style: italic; color: #bf616a;")  # Vermelho para erro/aviso
            else:
                QMessageBox.warning(self, "Erro de Captura", "Não foi possível capturar a imagem da fonte selecionada.")

        except mss.exception.ScreenShotError as e:
            QMessageBox.critical(self, "Erro MSS", f"Erro ao capturar tela com MSS: {e}\nVerifique se há permissões ou se outro app está bloqueando.")
            self.selected_pgm_details = None
            self.pgm_region_label.setText("Região PGM: Erro na captura")
            self.pgm_region_label.setStyleSheet("font-style: italic; color: #bf616a;")
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", f"Ocorreu um erro ao selecionar a região: {e}")
            self.selected_pgm_details = None
            self.pgm_region_label.setText("Região PGM: Erro na seleção")
            self.pgm_region_label.setStyleSheet("font-style: italic; color: #bf616a;")
            # REMOVIDO: import traceback
            # REMOVIDO: traceback.print_exc()

    def _pick_window_by_click(self):
        """Seleciona automaticamente a janela sob o cursor após um pequeno atraso."""
        QMessageBox.information(self, "Selecionar Janela", "Função removida para simplificar. Use a lista de janelas e o botão Atualizar.")

    def _on_source_type_changed(self, index):
        source_name = self.source_type_combo.itemText(index)
        if source_name == "Monitor":
            self.monitor_list_label.setVisible(True)
            self.monitor_field_container.setVisible(True)
            self.window_list_label.setVisible(False)
            self.window_field_container.setVisible(False)
            self.ndi_list_label.setVisible(False)
            if NDI_AVAILABLE:
                self.ndi_field_container.setVisible(False)
            self._populate_monitor_list()
        elif source_name == "Janela":
            self.monitor_list_label.setVisible(False)
            self.monitor_field_container.setVisible(False)
            self.window_list_label.setVisible(True)
            self.window_field_container.setVisible(True)
            self.ndi_list_label.setVisible(False)
            if NDI_AVAILABLE:
                self.ndi_field_container.setVisible(False)
            self._populate_window_list()
        elif source_name == "NDI":
            self.monitor_list_label.setVisible(False)
            self.monitor_field_container.setVisible(False)
            self.window_list_label.setVisible(False)
            self.window_field_container.setVisible(False)
            self.ndi_list_label.setVisible(True)
            if NDI_AVAILABLE:
                self.ndi_field_container.setVisible(True)
            self._populate_ndi_list()

    def _populate_monitor_list(self):
        """Popula a lista de monitores disponíveis."""
        self.monitor_list_combo.clear()
        try:
            import mss
            with mss.mss() as sct:
                # sct.monitors[0] é informação geral, monitores reais começam do índice 1
                for i in range(1, len(sct.monitors)):
                    monitor = sct.monitors[i]
                    width = monitor['width']
                    height = monitor['height']
                    self.monitor_list_combo.addItem(f"Monitor {i} ({width}x{height})")
            
            if self.monitor_list_combo.count() == 0:
                self.monitor_list_combo.addItem("Nenhum monitor encontrado")
                
        except Exception as e:
            self.monitor_list_combo.addItem("Erro ao listar monitores")
            print(f"Erro ao listar monitores: {e}")

    def _populate_window_list(self):
        self.window_list_combo.clear()
        try:
            windows = pyautogui.getAllWindows()
            found_windows = False
            for window in windows:
                # Adicionar apenas janelas com título, visíveis e com área
                if window.title and window.visible and getattr(window, 'width', 0) > 0 and getattr(window, 'height', 0) > 0:
                    # Evitar listar a própria janela do SwitchPilot para reduzir acidentes
                    try:
                        if 'SwitchPilot' in window.title:
                            continue
                    except Exception:
                        pass
                    # Guardar o título e, se possível, um identificador (como o HWND ou o objeto)
                    # Por enquanto, apenas o título para simplicidade.
                    # Poderíamos usar window.title como texto e o objeto window como userData.
                    self.window_list_combo.addItem(window.title, userData=window) # Armazenando o objeto window
                    found_windows = True
            
            if not found_windows:
                self.window_list_combo.addItem("Nenhuma janela encontrada")
                # Aqui você poderia emitir um sinal ou logar se preferir
                # REMOVIDO: print("Nenhuma janela de aplicativo encontrada para captura.")

        except Exception as e:
            self.window_list_combo.addItem("Erro ao listar janelas")
            # REMOVIDO: print(f"Erro ao tentar listar janelas de aplicativos: {e}")
            # Logar o erro aqui também seria bom

    def _populate_ndi_list(self):
        """Popula a lista de fontes NDI disponíveis."""
        self.ndi_list_combo.clear()
        try:
            # Inicializar NDI
            if not NDI.initialize():
                self.ndi_list_combo.addItem("Erro: NDI não pode ser inicializado")
                return
            
            # Criar um finder para descobrir fontes NDI (usando configuração padrão)
            ndi_find = NDI.find_create_v2()
            if not ndi_find:
                self.ndi_list_combo.addItem("Erro: Não foi possível criar NDI finder")
                NDI.destroy()
                return
            
            # Aguardar um pouco para descobrir fontes
            import time
            time.sleep(2)  # Aguardar 2 segundos para descoberta
            
            # Obter lista de fontes NDI
            sources = NDI.find_get_current_sources(ndi_find)
            
            if sources and len(sources) > 0:
                for source in sources:
                    source_name = source.ndi_name if hasattr(source, 'ndi_name') else str(source)
                    # Armazenar apenas os dados necessários como string
                    source_data = {
                        'ndi_name': source_name,
                        'url_address': getattr(source, 'url_address', '')
                    }
                    self.ndi_list_combo.addItem(source_name, userData=source_data)
                print(f"Encontradas {len(sources)} fontes NDI")
            else:
                self.ndi_list_combo.addItem("Nenhuma fonte NDI encontrada")
                print("Nenhuma fonte NDI descoberta")
            
            # Limpar recursos NDI
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            
        except Exception as e:
            self.ndi_list_combo.addItem("Erro ao listar fontes NDI")
            print(f"Erro ao tentar listar fontes NDI: {e}")
            try:
                NDI.destroy()
            except Exception:
                pass

    def _on_current_item_changed(self, current, previous):
        is_item_selected = current is not None
        self.configure_actions_button.setEnabled(is_item_selected)
        self.remove_reference_button.setEnabled(is_item_selected)

    def _handle_add_existing_reference(self):
        # Filtros para os tipos de arquivo de imagem mais comuns
        image_filters = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;Todos os Arquivos (*)"
        
        # Abrir o diálogo para selecionar um ou mais arquivos
        # O diretório inicial pode ser o último usado ou um padrão
        filepaths, _ = QFileDialog.getOpenFileNames(self, 
                                                    "Selecionar Imagens de Referência Existentes", 
                                                    "", # Diretório inicial (vazio usa o padrão)
                                                    image_filters)
        
        if not filepaths: # Usuário cancelou o diálogo
            return

        added_count = 0
        for original_filepath in filepaths:
            if not os.path.exists(original_filepath):
                QMessageBox.warning(self, "Arquivo Não Encontrado", f"O arquivo selecionado não foi encontrado:\n{original_filepath}")
                continue

            original_filename = os.path.basename(original_filepath)
            base_name, ext = os.path.splitext(original_filename)
            
            # Sanitizar o nome base do arquivo
            sanitized_base_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base_name.strip())
            if not sanitized_base_name:
                sanitized_base_name = "imported_ref" # Fallback se o nome ficar vazio

            # Garantir que a extensão seja .png para consistência interna, ou manter original se preferir
            # Por enquanto, vamos manter a extensão original, mas o ideal seria converter para PNG.
            # Para simplificar agora, apenas copiamos. Poderíamos adicionar conversão depois.
            # final_display_name = f"{sanitized_base_name}.png" 
            final_display_name = f"{sanitized_base_name}{ext}"

            target_filepath = os.path.join(self.references_dir, final_display_name)
            count = 1
            while os.path.exists(target_filepath):
                final_display_name = f"{sanitized_base_name}_{count:02d}{ext}"
                target_filepath = os.path.join(self.references_dir, final_display_name)
                count += 1
            
            try:
                shutil.copy2(original_filepath, target_filepath) # copy2 preserva metadados
                
                new_ref_data = {'name': final_display_name, 'type': 'static', 'path': target_filepath, 'actions': []}
                self.references_data.append(new_ref_data)
                
                self._display_reference_in_list(new_ref_data)
                self.reference_list_widget.setCurrentRow(self.reference_list_widget.count() - 1)
                added_count += 1
                # REMOVIDO: print(f"DEBUG: QListWidget count after adding existing: {self.reference_list_widget.count()}")

            except Exception as e:
                QMessageBox.critical(self, "Erro ao Copiar Arquivo", 
                                     f"Não foi possível copiar o arquivo '{original_filename}' para '{self.references_dir}'.\nErro: {e}")
                continue # Pular para o próximo arquivo se houver erro
        
        if added_count > 0:
            self.references_updated.emit(self.get_all_references_data()) # Usar getter
            QMessageBox.information(self, "Referências Adicionadas", 
                                  f"{added_count} imagem(ns) de referência adicionada(s) com sucesso.")

    def _handle_remove_reference(self):
        current_item = self.reference_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Remover Referência", "Nenhuma referência selecionada para remover.")
            return

        reply = QMessageBox.question(self, 'Confirmar Remoção',
                                     f"Tem certeza que deseja remover a referência '{current_item.text()}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            row = self.reference_list_widget.row(current_item)
            self.reference_list_widget.takeItem(row)
            removed_ref_data = self.references_data.pop(row)
            
            # Opcional: remover o arquivo físico (MANTIDO COMENTADO POR PADRÃO)
            # try:
            #     if os.path.exists(removed_ref_data['path']):
            #         os.remove(removed_ref_data['path'])
            #         # print(f"Arquivo removido: {removed_ref_data['path']}") # Log de debug se descomentado
            # except Exception as e:
            #     # print(f"Erro ao remover arquivo {removed_ref_data['path']}: {e}") # Log de debug se descomentado
            #     QMessageBox.warning(self, "Erro ao Remover Arquivo", f"Não foi possível remover o arquivo físico {removed_ref_data['path']}. Verifique as permissões.")

            self.references_updated.emit(self.get_all_references_data()) # Usar getter
            # REMOVIDO: print(f"Referência removida: {removed_ref_data}")

    def _handle_configure_actions(self):
        current_item = self.reference_list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Configurar Ações", "Nenhuma imagem de referência selecionada.")
            return

        # O texto do item pode ser "nome.png" ou "[Sequência] nome_seq"
        # Precisamos do nome original armazenado nos dados da referência
        
        selected_ref_data = None
        current_row = self.reference_list_widget.row(current_item)
        if 0 <= current_row < len(self.references_data):
            selected_ref_data = self.references_data[current_row]
        
        if not selected_ref_data:
            QMessageBox.warning(self, "Erro", f"Não foi possível encontrar os dados para a referência selecionada '{current_item.text()}'.")
            return
        
        # REMOVIDO: print(f"[RMW DEBUG] Antes de abrir ActionConfigDialog, selected_ref_data['actions']: {selected_ref_data.get('actions')}") 

        if not self.main_controller:
            QMessageBox.critical(self, "Erro Crítico", "MainController não está disponível no ReferenceManagerWidget. Não é possível abrir o diálogo de ações.")
            return
            
        dialog = ActionConfigDialog(selected_ref_data, self.main_controller, self)
        if dialog.exec_() == QDialog.Accepted:
            updated_actions = dialog.get_action_config()
            selected_ref_data['actions'] = updated_actions
            # REMOVIDO: print(f"[RMW DEBUG] Após ActionConfigDialog, selected_ref_data['actions'] atualizado para: {selected_ref_data['actions']}") 
            # REMOVIDO: print(f"[RMW DEBUG] self.references_data COMPLETA após atualização: {self.references_data}") 
            self.references_updated.emit(self.get_all_references_data()) 
            # REMOVIDO: print(f"Ações para '{ref_name}' atualizadas: {updated_actions}")

    def load_references(self, references_data_list):
        """Carrega as referências na lista a partir de uma lista de dicionários."""
        self.references_data = list(references_data_list) # Garantir que é uma cópia e é uma lista
        self.reference_list_widget.clear()
        for ref_data in self.references_data:
            self._display_reference_in_list(ref_data)
        self.references_updated.emit(self.references_data)

    def _display_reference_in_list(self, ref_data):
        """Adiciona um item ao QListWidget com base nos dados da referência."""
        name = ref_data.get('name', 'Referência Desconhecida')
        ref_type = ref_data.get('type', 'static') # Padrão para 'static' se não especificado

        display_text = name
        user_data_payload = None # O que será armazenado no item para identificação

        if ref_type == 'sequence':
            frame_paths = ref_data.get('frame_paths', [])
            display_text = f"[Sequência] {name} ({len(frame_paths)} frames)"
            # Para sequências, podemos armazenar o nome da sequência ou o dict inteiro
            # Por simplicidade e consistência com 'static', podemos armazenar o nome.
            # Ou, para fácil acesso aos frames, o primeiro frame.
            # Para identificação na lista, o nome da sequência é suficiente.
            # A lógica de `_handle_configure_actions` precisará encontrar `ref_data` por nome/índice.
            user_data_payload = name # Usar o nome da sequência como identificador no UserRole
        
        elif ref_type == 'static':
            display_text = name # O nome já inclui a extensão .png, etc.
            user_data_payload = ref_data.get('path') # Para estático, o caminho é um bom UserRole
        
        else: # Tipo desconhecido, apenas mostrar o nome
            display_text = f"[Desconhecido] {name}"
            user_data_payload = name


        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, user_data_payload) # Armazena o caminho (estático) ou nome (sequência)

        # Adicionar Tooltip com detalhes das ações (se houver)
        actions = ref_data.get('actions', [])
        if actions:
            action_descriptions = []
            if self.main_controller and hasattr(self.main_controller, 'get_action_description'):
                for action in actions:
                    action_descriptions.append(self.main_controller.get_action_description(action))
            else: # Fallback se o controller ou método não estiver disponível
                action_descriptions = [f"{a.get('integration', '')}: {a.get('action_type', '')}" for a in actions]
            
            tooltip_text = f"{display_text}\nAções:\n- " + "\n- ".join(action_descriptions)
            item.setToolTip(tooltip_text)
        else:
            item.setToolTip(display_text)
            
        self.reference_list_widget.addItem(item)

    def get_selected_reference_data(self):
        """Retorna os dados da referência atualmente selecionada da self.references_data."""
        current_row = self.reference_list_widget.currentRow()
        if 0 <= current_row < len(self.references_data):
            return self.references_data[current_row]
        return None

    def get_all_references_data(self):
        return list(self.references_data)

    def _handle_add_video_gif_sequence(self):
        video_filters = "Vídeos e GIFs (*.mp4 *.avi *.mov *.gif);;Todos os Arquivos (*)"
        filepath, _ = QFileDialog.getOpenFileName(self,
                                                  "Selecionar Vídeo ou GIF para Sequência",
                                                  "",
                                                  video_filters)
        if not filepath:
            return

        original_filename = os.path.basename(filepath)
        base_name, _ = os.path.splitext(original_filename)
        sanitized_base_name = re.sub(r'[^a-zA-Z0-9_\\-]', '_', base_name.strip())
        if not sanitized_base_name:
            sanitized_base_name = "seq_ref"

        # Sugerir nome para a sequência
        sequence_name_suggestion = f"{sanitized_base_name}_seq"
        temp_idx = 1
        # Verificar se já existe uma sequência com esse nome para sugerir nome_01, nome_02 etc.
        while any(ref.get('name') == sequence_name_suggestion and ref.get('type') == 'sequence' for ref in self.references_data):
            sequence_name_suggestion = f"{sanitized_base_name}_seq_{temp_idx:02d}"
            temp_idx += 1

        sequence_name, ok = QInputDialog.getText(self, "Nome da Sequência de Referência",
                                                 "Digite o nome para a sequência:",
                                                 text=sequence_name_suggestion)
        if not (ok and sequence_name):
            QMessageBox.information(self, "Adição Cancelada", "A criação da sequência de referência foi cancelada.")
            return
        
        # Sanitizar o nome da sequência também
        sequence_name = re.sub(r'[^a-zA-Z0-9_\\-]', '_', sequence_name.strip())
        if not sequence_name:
            QMessageBox.warning(self, "Nome Inválido", "O nome da sequência não pode ser vazio após sanitização. Usando nome padrão.")
            sequence_name = sequence_name_suggestion # Reverter para o sugerido se o usuário fornecer algo que se torna vazio

        # Verificar novamente se o nome da sequência já existe (após sanitização do usuário)
        if any(ref.get('name') == sequence_name and ref.get('type') == 'sequence' for ref in self.references_data):
            QMessageBox.warning(self, "Nome Duplicado", f"Uma sequência com o nome '{sequence_name}' já existe. Por favor, escolha outro nome.")
            # Poderia re-abrir o QInputDialog ou adicionar sufixo automaticamente, mas por ora só avisa.
            return

        frame_paths = self._extract_frames_from_video_gif(filepath, sequence_name)

        if frame_paths:
            new_ref_data = {
                'name': sequence_name,
                'type': 'sequence',
                'frame_paths': frame_paths,
                'actions': []
            }
            self.references_data.append(new_ref_data)
            self._display_reference_in_list(new_ref_data)
            self.reference_list_widget.setCurrentRow(self.reference_list_widget.count() - 1)
            self.references_updated.emit(self.get_all_references_data())
            QMessageBox.information(self, "Sequência Adicionada",
                                  f"Sequência '{sequence_name}' com {len(frame_paths)} frames adicionada com sucesso.")
        else:
            QMessageBox.warning(self, "Falha na Extração",
                                f"Não foi possível extrair frames de '{original_filename}'. A sequência não foi adicionada.")

    def _extract_frames_from_video_gif(self, video_path, sequence_base_name):
        """Extrai frames de um vídeo/GIF e os salva na pasta de referências."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            QMessageBox.critical(self, "Erro ao Abrir Vídeo", f"Não foi possível abrir o arquivo: {video_path}")
            return []

        frame_paths = []
        frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Limitar o número de frames para não sobrecarregar, ex: 1 frame a cada N ou máx de M frames
        # Por agora, vamos extrair um número limitado de frames, por exemplo, a cada 10 frames, até um máximo de 50.
        # Ou, podemos pegar X frames no total, espaçados uniformemente.
        # Exemplo: pegar no máximo 20 frames, espaçados.
        
        max_frames_to_extract = 20 
        desired_interval = 1 # Extrair todos os frames se <= max_frames_to_extract
        if frame_count_total > max_frames_to_extract:
            desired_interval = frame_count_total // max_frames_to_extract
            if desired_interval == 0 : desired_interval = 1 # Evitar divisão por zero se for um vídeo muito curto
        
        extracted_count = 0
        current_frame_idx = 0

        while extracted_count < max_frames_to_extract:
            ret, frame = cap.read()
            if not ret:
                break # Fim do vídeo ou erro de leitura

            # Processar apenas os frames no intervalo desejado
            if current_frame_idx % desired_interval == 0:
                frame_filename = f"{sequence_base_name}_frame_{extracted_count:03d}.png"
                frame_filepath = os.path.join(self.references_dir, frame_filename)
                
                # Lógica para evitar sobrescrever se já existir um arquivo com esse nome exato
                # (embora o sequence_base_name já deva ser único)
                temp_frame_count = 0
                while os.path.exists(frame_filepath):
                    temp_frame_count +=1
                    frame_filename = f"{sequence_base_name}_frame_{extracted_count:03d}_{temp_frame_count}.png"
                    frame_filepath = os.path.join(self.references_dir, frame_filename)

                if cv2.imwrite(frame_filepath, frame):
                    frame_paths.append(frame_filepath)
                    extracted_count += 1
                else:
                    # REMOVIDO: print(f"Falha ao salvar frame {frame_filepath} para sequência {sequence_base_name}")
                    # Poderia adicionar um QMessageBox.warning aqui se muitas falhas ocorrerem
                    pass
            
            current_frame_idx += 1
        
        cap.release()
        
        if not frame_paths:
             QMessageBox.warning(self, "Extração de Frames", f"Nenhum frame foi extraído de {video_path}. Verifique o arquivo.")
        elif extracted_count < frame_count_total // desired_interval if desired_interval > 0 else frame_count_total : # Se menos frames que o esperado foram extraidos
            QMessageBox.information(self, "Extração Parcial", f"Foram extraídos {extracted_count} frames de {video_path}. Esperava-se mais, verifique o vídeo.")
            
        return frame_paths

    def _capture_ndi_frame(self, ndi_source_data):
        """Captura um frame da fonte NDI especificada."""
        try:
            source_name = ndi_source_data.get('ndi_name', 'Fonte Desconhecida')
            
            # Inicializar NDI
            if not NDI.initialize():
                print("Erro: NDI não pode ser inicializado")
                return None
            
            # Descobrir fontes NDI novamente para obter o objeto correto
            ndi_find = NDI.find_create_v2()
            if not ndi_find:
                print("Erro: Não foi possível criar NDI finder")
                NDI.destroy()
                return None
            
            # Aguardar descoberta
            import time
            time.sleep(1)
            
            # Obter fontes
            sources = NDI.find_get_current_sources(ndi_find)
            target_source = None
            
            for source in sources:
                if source.ndi_name == source_name:
                    target_source = source
                    break
            
            NDI.find_destroy(ndi_find)
            
            if not target_source:
                NDI.destroy()
                return None
            
            # Criar configuração do receiver
            recv_create = NDI.RecvCreateV3()
            recv_create.source_to_connect_to = target_source
            recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
            recv_create.allow_video_fields = True
            
            # Criar receiver para a fonte NDI
            ndi_recv = NDI.recv_create_v3(recv_create)
            if not ndi_recv:
                print("Erro: Não foi possível criar NDI receiver")
                NDI.destroy()
                return None
            
            # Aguardar e capturar frame
            timeout_seconds = 25  # Aumentado para 25 segundos
            start_time = time.time()
            print(f"[DEBUG] Iniciando captura NDI, timeout: {timeout_seconds}s")
            frames_attempted = 0
            
            while (time.time() - start_time) < timeout_seconds:
                try:
                    # A função recv_capture_v2 retorna uma tupla
                    result = NDI.recv_capture_v2(ndi_recv, 200)  # Aumentado timeout
                    frame_type, video_frame, audio_frame, metadata_frame = result
                    frames_attempted += 1
                    
                    if frame_type == NDI.FRAME_TYPE_VIDEO:
                        print(f"[DEBUG] Frame de vídeo recebido: {video_frame.xres}x{video_frame.yres}")
                        
                        # Verificar se os dados do frame são válidos
                        if video_frame.data is None or len(video_frame.data) == 0:
                            print(f"[DEBUG] Frame sem dados, continuando...")
                            NDI.recv_free_video_v2(ndi_recv, video_frame)
                            continue
                        
                        # Converter frame NDI para numpy array
                        frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                        
                        # Verificar se o tamanho dos dados é consistente
                        expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                        if len(frame_data) < expected_size:
                            NDI.recv_free_video_v2(ndi_recv, video_frame)
                            continue
                        
                        frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                        
                        # Converter BGRX para BGR (remover canal alpha)
                        frame_bgr = frame_data[:, :video_frame.xres, :3].copy()  # Fazer cópia para garantir continuidade
                        
                        # Verificar se o frame resultante é válido
                        if frame_bgr.size == 0:
                            NDI.recv_free_video_v2(ndi_recv, video_frame)
                            continue
                        
                        print(f"[DEBUG] Frame NDI capturado com sucesso: {frame_bgr.shape}")
                        
                        # Liberar o frame
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        
                        # Limpar recursos
                        NDI.recv_destroy(ndi_recv)
                        NDI.destroy()
                        
                        return frame_bgr
                    
                    elif frame_type == NDI.FRAME_TYPE_AUDIO:
                        # Liberar frame de áudio (não precisamos)
                        NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                    
                    elif frame_type == NDI.FRAME_TYPE_METADATA:
                        # Liberar metadata (não precisamos)
                        NDI.recv_free_metadata(ndi_recv, metadata_frame)
                    
                    # Pequena pausa para não sobrecarregar
                    time.sleep(0.01)

                except Exception as inner_e:
                    print(f"[DEBUG] Erro interno na captura NDI: {inner_e}")
                    import traceback
                    traceback.print_exc()
                    break

            # Timeout - não conseguiu capturar frame válido
            print(f"[DEBUG] Timeout de {timeout_seconds}s atingido sem capturar frame válido")
            print(f"[DEBUG] Total de tentativas: {frames_attempted}")
            NDI.recv_destroy(ndi_recv)
            NDI.destroy()
            # Aguardar para liberar recursos NDI adequadamente
            time.sleep(2)
            return None
            
        except Exception as e:
            print(f"Erro ao capturar frame NDI: {e}")
            try:
                NDI.destroy()
            except Exception:
                pass
            # Aguardar antes de retornar para liberar recursos
            time.sleep(1)
            return None

# REMOVIDO BLOCO if __name__ == '__main__':

# REMOVIDO: app = QApplication(sys.argv)
# REMOVIDO: # Para testar o tema, carregar o QSS globalmente se este arquivo for executado sozinho
# REMOVIDO: try:
# REMOVIDO:     # Ajustando o caminho relativo para o QSS no teste individual
# REMOVIDO:     with open('../themes/modern_dark_obs.qss', 'r') as f:
# REMOVIDO:         app.setStyleSheet(f.read())
# REMOVIDO: except FileNotFoundError:
# REMOVIDO:     print("QSS de tema não encontrado para teste individual do widget (../themes/modern_dark_obs.qss).")

# REMOVIDO: widget = ReferenceManagerWidget()
# REMOVIDO: widget.load_references([
# REMOVIDO:     {'name': 'Referencia_Tela_A.png'},
# REMOVIDO:     {'name': 'Referencia_Jogo_B.jpg'},
# REMOVIDO:     {'name': 'Alerta_Stream.png'}
# REMOVIDO: ])
# REMOVIDO: widget.setWindowTitle("Teste ReferenceManagerWidget")
# REMOVIDO: widget.setGeometry(100, 100, 400, 600)
# REMOVIDO: widget.show()
# REMOVIDO: sys.exit(app.exec_())
