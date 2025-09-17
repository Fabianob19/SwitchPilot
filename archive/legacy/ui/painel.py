import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QMessageBox, QComboBox, QGroupBox, QSizePolicy, QSpacerItem, QScrollArea, QGraphicsDropShadowEffect, QDialog, QDoubleSpinBox, QGridLayout, QFrame, QGraphicsOpacityEffect, QFileDialog, QListWidget, QListWidgetItem, QMenu, QLineEdit, QCheckBox, QDockWidget, QFormLayout, QStyleOption, QStyle, QSystemTrayIcon
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QSettings, QThread, QCoreApplication
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QImage, QPainter, QPalette
import cv2
import mss
import numpy as np
import requests
import xml.etree.ElementTree as ET
import time
import socket
import urllib.parse
import os
import threading
import unicodedata
import uuid
try:
    import psutil
except ImportError:
    psutil = None
from .obs_config import OBSConfigWidget

def resource_path(relative_path):
    """Retorna o caminho absoluto para recursos, compatível com PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

def descrever_acao(acao):
    """Retorna uma descrição legível para a ação associada a uma referência."""
    if acao['tipo'] == 'cut':
        return f"Cortar para {acao['parametros'].get('entrada', '')}"
    if acao['tipo'] == 'overlay':
        return f"Exibir overlay {acao['parametros'].get('overlay', '')}"
    if acao['tipo'] == 'transition':
        return f"Ativar transição {acao['parametros'].get('transicao', '')}"
    if acao['tipo'] == 'shortcut':
        return f"Executar shortcut '{acao['parametros'].get('nome', '')}'"
    if acao['tipo'] == 'obs_scene':
        return f"Mudar cena do OBS para '{acao['parametros'].get('scene', '')}'"
    if acao['tipo'] == 'obs_source_on':
        return f"Ativar fonte do OBS '{acao['parametros'].get('source', '')}'"
    if acao['tipo'] == 'obs_source_off':
        return f"Desativar fonte do OBS '{acao['parametros'].get('source', '')}'"
    if acao['tipo'] == 'obs_start_record':
        return "Iniciar gravação OBS"
    if acao['tipo'] == 'obs_stop_record':
        return "Parar gravação OBS"
    if acao['tipo'] == 'obs_start_stream':
        return "Iniciar transmissão OBS"
    if acao['tipo'] == 'obs_stop_stream':
        return "Parar transmissão OBS"
    return acao['tipo']

class MonitorThread(QThread):
    """Thread para monitorar a região selecionada e disparar ações conforme as referências."""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    def __init__(self, regiao, referencias, entrada_vmix_nome, entrada_vmix_numero, intervalo=0.5, host_obs='localhost', port_obs='4455'):
        """Inicializa a thread de monitoramento."""
        super().__init__()
        self.regiao = regiao
        self.referencias = referencias
        self.entrada_vmix_nome = entrada_vmix_nome
        self.entrada_vmix_numero = entrada_vmix_numero
        self.intervalo = intervalo
        self.running = True
        self.host_obs = host_obs
        self.port_obs = port_obs
    def run(self):
        """Executa o monitoramento da região e dispara ações conforme as referências."""
        try:
            referencias = []
            for ref in self.referencias:
                img = cv2.imread(ref['path'])
                if img is not None:
                    referencias.append({'path': ref['path'], 'img': img, 'acoes': ref.get('acoes', [])})
            if not referencias:
                self.log_signal.emit('Nenhuma imagem de referência válida encontrada!')
                return
            # Adicionar buffer de quadros capturados
            buffer_seq = []
            max_seq_len = 0
            for ref in self.referencias:
                if 'sequencia' in ref:
                    max_seq_len = max(max_seq_len, len(ref['sequencia']))

            while self.running:
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    img = np.array(sct.grab(monitor))
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                top, left, width, height = self.regiao[:4]
                frame = img[top:top+height, left:left+width]
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                match_found = False
                if max_seq_len > 0:
                    # Salvar o frame atual no buffer
                    buffer_seq.append(frame.copy())
                    if len(buffer_seq) > max_seq_len:
                        buffer_seq.pop(0)

                for ref in referencias:
                    if 'sequencia' in ref:
                        # Comparar buffer_seq com a sequência de quadros da referência
                        if len(buffer_seq) >= len(ref['sequencia']):
                            match_seq = True
                            for i, ref_path in enumerate(ref['sequencia']):
                                ref_img = cv2.imread(ref_path)
                                if ref_img is None:
                                    match_seq = False
                                    break
                                ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
                                buf_gray = cv2.cvtColor(buffer_seq[-len(ref['sequencia']) + i], cv2.COLOR_BGR2GRAY)
                                hist_ref = cv2.calcHist([ref_gray], [0], None, [256], [0, 256])
                                hist_buf = cv2.calcHist([buf_gray], [0], None, [256], [0, 256])
                                hist_ref = cv2.normalize(hist_ref, hist_ref).flatten()
                                hist_buf = cv2.normalize(hist_buf, hist_buf).flatten()
                                similarity = cv2.compareHist(hist_ref, hist_buf, cv2.HISTCMP_CORREL)
                                if similarity < 0.90:
                                    match_seq = False
                                    break
                            if match_seq:
                                for acao in ref['acoes']:
                                    self.log_signal.emit(f"Sequência detectada: {ref['sequencia']}. {descrever_acao(acao)}.")
                                    self._executar_acao(acao)
                                time.sleep(1)
                                match_found = True
                                break
                        continue  # Não comparar como imagem estática
                    ref_gray = cv2.cvtColor(ref['img'], cv2.COLOR_BGR2GRAY)
                    hist_ref = cv2.calcHist([ref_gray], [0], None, [256], [0, 256])
                    hist_frame = cv2.calcHist([frame_gray], [0], None, [256], [0, 256])
                    hist_ref = cv2.normalize(hist_ref, hist_ref).flatten()
                    hist_frame = cv2.normalize(hist_frame, hist_frame).flatten()
                    similarity = cv2.compareHist(hist_ref, hist_frame, cv2.HISTCMP_CORREL)
                    self.log_signal.emit(f'Similaridade com {ref["path"]}: {similarity:.2f}')
                    if similarity > 0.90:
                        match_found = True
                        for acao in ref['acoes']:
                            self.log_signal.emit(f"Tela detectada: {os.path.basename(ref['path'])}. {descrever_acao(acao)}.")
                            self._executar_acao(acao)
                        time.sleep(1)
                        break
                if not match_found:
                    self.log_signal.emit('Tudo normal no PGM.')
                    time.sleep(self.intervalo)
        except Exception as e:
            self.log_signal.emit(f'Erro no monitoramento: {e}')
            import traceback
            self.log_signal.emit(traceback.format_exc())
    def stop(self):
        """Para a thread de monitoramento."""
        self.running = False
        self.wait()
    def _executar_acao(self, acao):
        # A lógica original de requests.get para vMix e self.enviar_comando_obs/set_scene_item_enabled_obs
        # precisaria estar acessível aqui ou ser chamada via sinais para o controller principal.
        # Por ora, apenas um log.
        # self.log_signal.emit(f"Executando ação (lógica a ser portada): {descrever_acao(acao)}")

        # Exemplo de como a lógica de vMix estava:
        if acao['tipo'] == 'cut' and acao['parametros'].get('entrada'):
            entrada = acao['parametros']['entrada']
            try:
                input_encoded = urllib.parse.quote(entrada, safe='')
                url = f'http://localhost:8088/api/?Function=CutDirect&Input={input_encoded}'
                # resp = requests.get(url) # Comentado para evitar requests reais
                self.log_signal.emit(f'Ação vMix {descrever_acao(acao)} (simulada).') # Resposta: {resp.text}')
            except Exception as e:
                self.log_signal.emit(f'Erro ao simular corte no vMix: {e}')
        # ... (lógica similar para outras ações vMix) ...
        
        # Exemplo de como a lógica OBS estava:
        elif acao['tipo'] == 'obs_scene' and acao['parametros'].get('scene'):
            # ok = self.enviar_comando_obs('obs_scene', {'scene': acao['parametros']['scene']}) # Comentado
            ok = True # Simular sucesso
            if ok:
                self.log_signal.emit(f"Ação OBS: Mudou para cena '{acao['parametros']['scene']}' (simulada)")
        # ... (lógica similar para outras ações OBS) ...
        else:
            self.log_signal.emit(f'Ação desconhecida ou sem handler em _executar_acao: {descrever_acao(acao)}')

    def enviar_comando_obs(self, tipo, parametros):
        """Envia um comando para o OBS autenticando antes, usando o protocolo WebSocket 5.x."""
        import websocket, json, uuid
        from PyQt5.QtCore import QSettings
        try:
            ws = websocket.create_connection(f"ws://{self.host_obs}:{self.port_obs}", timeout=2)
            # Buscar senha salva nas configs (PainelVmix usa QSettings)
            settings = QSettings('SwitchPilot', 'PainelVmix')
            senha = settings.value('obs_senha', '')
            # Autenticação (código adaptado do PainelVmix)
            # 1. Recebe Hello (op:0)
            resp = ws.recv()
            self.log_signal.emit(f"[OBS] Resposta Identify (challenge): {resp}")
            data = json.loads(resp)
            identify = {"op": 1, "d": {"rpcVersion": 1}}
            if 'authentication' in data.get('d', {}):
                import base64, hashlib
                challenge = data['d']['authentication']['challenge']
                salt = data['d']['authentication']['salt']
                if not senha:
                    ws.close()
                    raise Exception('O OBS exige senha, mas nenhum valor foi informado.')
                senha = senha.strip()
                secret = base64.b64encode(hashlib.sha256((senha + salt).encode('utf-8')).digest()).decode('utf-8')
                auth = base64.b64encode(hashlib.sha256((secret + challenge).encode('utf-8')).digest()).decode('utf-8')
                self.log_signal.emit(f"[OBS] Hash auth gerado: {auth}")
                identify["d"]["authentication"] = auth
            json_identify = json.dumps(identify)
            self.log_signal.emit(f"[OBS] JSON enviado Identify: {json_identify}")
            ws.send(json_identify)
            try:
                resp2 = ws.recv()
            except websocket._exceptions.WebSocketConnectionClosedException:
                resp2 = ''
            self.log_signal.emit(f"[OBS] Resposta Identify (autenticado): {resp2}")
            if not resp2:
                ws.close()
                raise Exception('A conexão com o OBS foi fechada após tentar autenticar. Verifique se a senha está correta e se o OBS está configurado para aceitar conexões.')
            data2 = json.loads(resp2)
            if data2.get('op') == 2 and data2.get('d', {}).get('negotiatedRpcVersion') == 1:
                # Autenticado, pode enviar comando
                if tipo == 'obs_scene':
                    msg = {"op": 6, "d": {"requestType": "SetCurrentProgramScene", "requestData": {"sceneName": parametros['scene']}, "requestId": str(uuid.uuid4())}}
                elif tipo == 'obs_source_on':
                    msg = {"op": 6, "d": {"requestType": "SetSourceRender", "requestData": {"sourceName": parametros['source'], "sourceRender": True}, "requestId": str(uuid.uuid4())}}
                elif tipo == 'obs_source_off':
                    msg = {"op": 6, "d": {"requestType": "SetSourceRender", "requestData": {"sourceName": parametros['source'], "sourceRender": False}, "requestId": str(uuid.uuid4())}}
                elif tipo == 'obs_start_record':
                    msg = {"op": 6, "d": {"requestType": "StartRecord", "requestId": str(uuid.uuid4())}}
                elif tipo == 'obs_stop_record':
                    msg = {"op": 6, "d": {"requestType": "StopRecord", "requestId": str(uuid.uuid4())}}
                elif tipo == 'obs_start_stream':
                    msg = {"op": 6, "d": {"requestType": "StartStream", "requestId": str(uuid.uuid4())}}
                elif tipo == 'obs_stop_stream':
                    msg = {"op": 6, "d": {"requestType": "StopStream", "requestId": str(uuid.uuid4())}}
                else:
                    ws.close()
                    raise Exception(f'Comando OBS não suportado: {tipo}')
                ws.send(json.dumps(msg))
                self.log_signal.emit(f"[OBS] Comando enviado: {msg}")
                try:
                    resp_cmd = ws.recv()
                    self.log_signal.emit(f"[OBS] Resposta comando: {resp_cmd}")
                except Exception as e:
                    self.log_signal.emit(f"[OBS] Erro ao receber resposta do comando: {e}")
                ws.close()
                return True
            else:
                ws.close()
                raise Exception('Falha na autenticação OBS.')
        except Exception as e:
            self.log_signal.emit(f'Erro ao enviar comando para o OBS: {e}')
            return False

    def set_scene_item_enabled_obs(self, source_name, enabled):
        """Ativa ou desativa uma fonte na cena atual do OBS usando SetSceneItemEnabled."""
        import websocket, json, uuid
        from PyQt5.QtCore import QSettings
        try:
            ws = websocket.create_connection(f"ws://{self.host_obs}:{self.port_obs}", timeout=2)
            settings = QSettings('SwitchPilot', 'PainelVmix')
            senha = settings.value('obs_senha', '')
            # Autenticação
            resp = ws.recv()
            self.log_signal.emit(f"[OBS] Resposta Identify (challenge): {resp}")
            data = json.loads(resp)
            identify = {"op": 1, "d": {"rpcVersion": 1}}
            if 'authentication' in data.get('d', {}):
                import base64, hashlib
                challenge = data['d']['authentication']['challenge']
                salt = data['d']['authentication']['salt']
                if not senha:
                    ws.close()
                    raise Exception('O OBS exige senha, mas nenhum valor foi informado.')
                senha = senha.strip()
                secret = base64.b64encode(hashlib.sha256((senha + salt).encode('utf-8')).digest()).decode('utf-8')
                auth = base64.b64encode(hashlib.sha256((secret + challenge).encode('utf-8')).digest()).decode('utf-8')
                self.log_signal.emit(f"[OBS] Hash auth gerado: {auth}")
                identify["d"]["authentication"] = auth
            json_identify = json.dumps(identify)
            self.log_signal.emit(f"[OBS] JSON enviado Identify: {json_identify}")
            ws.send(json_identify)
            try:
                resp2 = ws.recv()
            except websocket._exceptions.WebSocketConnectionClosedException:
                resp2 = ''
            self.log_signal.emit(f"[OBS] Resposta Identify (autenticado): {resp2}")
            if not resp2:
                ws.close()
                raise Exception('A conexão com o OBS foi fechada após tentar autenticar.')
            data2 = json.loads(resp2)
            if not (data2.get('op') == 2 and data2.get('d', {}).get('negotiatedRpcVersion') == 1):
                ws.close()
                raise Exception('Falha na autenticação OBS.')
            # 1. Descobrir cena atual
            req_id = str(uuid.uuid4())
            msg = {"op": 6, "d": {"requestType": "GetCurrentProgramScene", "requestId": req_id}}
            ws.send(json.dumps(msg))
            resp_scene = ws.recv()
            self.log_signal.emit(f"[OBS] Resposta GetCurrentProgramScene: {resp_scene}")
            data_scene = json.loads(resp_scene)
            scene_name = data_scene.get('d', {}).get('responseData', {}).get('currentProgramSceneName')
            if not scene_name:
                ws.close()
                raise Exception('Não foi possível obter a cena atual do OBS.')
            # 2. Buscar scene items da cena
            req_id2 = str(uuid.uuid4())
            msg2 = {"op": 6, "d": {"requestType": "GetSceneItemList", "requestData": {"sceneName": scene_name}, "requestId": req_id2}}
            ws.send(json.dumps(msg2))
            resp_items = ws.recv()
            self.log_signal.emit(f"[OBS] Resposta GetSceneItemList: {resp_items}")
            data_items = json.loads(resp_items)
            items = data_items.get('d', {}).get('responseData', {}).get('sceneItems', [])
            scene_item_id = None
            for item in items:
                if item.get('sourceName') == source_name:
                    scene_item_id = item.get('sceneItemId')
                    break
            if scene_item_id is None:
                ws.close()
                self.log_signal.emit(f"[OBS] Fonte '{source_name}' não encontrada na cena '{scene_name}'.")
                return False
            # 3. Enviar SetSceneItemEnabled
            req_id3 = str(uuid.uuid4())
            msg3 = {"op": 6, "d": {"requestType": "SetSceneItemEnabled", "requestData": {"sceneName": scene_name, "sceneItemId": scene_item_id, "sceneItemEnabled": enabled}, "requestId": req_id3}}
            ws.send(json.dumps(msg3))
            self.log_signal.emit(f"[OBS] Comando SetSceneItemEnabled enviado: {msg3}")
            try:
                resp_cmd = ws.recv()
                self.log_signal.emit(f"[OBS] Resposta SetSceneItemEnabled: {resp_cmd}")
            except Exception as e:
                self.log_signal.emit(f"[OBS] Erro ao receber resposta do comando: {e}")
            ws.close()
            return True
        except Exception as e:
            self.log_signal.emit(f'Erro ao ativar/desativar fonte no OBS: {e}')
            return False

class PainelVmix(QMainWindow):
    """Janela principal do SwitchPilot. Gerencia interface, temas, referências e monitoramento."""
    def __init__(self):
        """Inicializa o painel principal do SwitchPilot."""
        super().__init__()
        
        # Configurações básicas da janela
        self.setWindowTitle('SwitchPilot | Automação para Streaming')
        self.setWindowIcon(QIcon(resource_path('ICONE.ico')))
        
        # Suporte para QSettings
        QCoreApplication.setOrganizationName('SwitchPilot')
        QCoreApplication.setApplicationName('PainelVmix')
        
        # Variáveis de estado
        self.monitor_thread = None
        self.regiao = None
        self.referencias = []
        
        # Inicializa a interface
        self.init_ui()
        
        # Aplica o tema
        self.aplicar_tema()
        
        # Carregar configurações do OBS
        self.carregar_config_obs()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def aplicar_tema(self):
        """Aplica o tema da aplicação."""
        try:
            # Primeiro limpa qualquer estilo existente
            self.setStyleSheet("")
            
            # Carrega o arquivo QSS
            qss_file = os.path.join(os.path.dirname(__file__), 'themes', 'modern_dark_new.qss')
            if os.path.exists(qss_file):
                with open(qss_file, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
                print("Tema aplicado do arquivo:", qss_file)
            else:
                print("Arquivo de tema não encontrado:", qss_file)
                
        except Exception as e:
            print("Erro ao aplicar tema:", str(e))
            
        # Força atualização da interface
        self.repaint()
        QApplication.processEvents()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(28, 16, 28, 16)
        
        # TOPO FIXO
        header_layout = QHBoxLayout()
        # Logo à esquerda, menor e alinhada
        logo_img = QPixmap(resource_path('LOGO.png')).scaled(350, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        nome = QLabel()
        nome.setPixmap(logo_img)
        nome.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        nome.setMinimumWidth(350)
        nome.setMinimumHeight(100)
        header_layout.addWidget(nome, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        
        self.status_label = QLabel('● Offline')
        self.status_label.setStyleSheet('color: #bf616a; font-weight: bold; margin-left: 18px;')
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        btn_sobre = QPushButton('Sobre')
        btn_sobre.setObjectName("btnSobre")
        btn_sobre.setFixedHeight(28)
        btn_sobre.clicked.connect(self.abrir_sobre)
        btn_sobre.setIcon(QIcon(resource_path('ui/icons/info.png')))
        header_layout.addWidget(btn_sobre)
        main_layout.addLayout(header_layout)

        # SLOGAN E INSTRUÇÃO
        slogan = QLabel('Automação inteligente, integração total')
        slogan.setAlignment(Qt.AlignCenter)
        slogan.setStyleSheet('color: #b48ead; font-size: 15px; margin-bottom: 8px;')
        main_layout.addWidget(slogan)
        
        instrucao = QLabel('<b>Fluxo:</b> 1) Fonte/Captura → 2) Região → 3) Referência/Ação')
        instrucao.setObjectName("labelFluxo")
        instrucao.setAlignment(Qt.AlignCenter)
        instrucao.setStyleSheet('color: #d8dee9; background: #262b36; border-radius: 10px; padding: 10px; margin-bottom: 10px; border: 1.2px solid #5e81ac;')
        main_layout.addWidget(instrucao)

        # COLUNAS PRINCIPAIS
        main_hbox = QHBoxLayout()
        
        # COLUNA ESQUERDA: FLUXO PRINCIPAL
        col_esq = QVBoxLayout()
        col_esq.setSpacing(18)

        # 1. Fonte/Captura
        fonte_card = QGroupBox('Fonte de Captura')
        fonte_card.setProperty('glass', True)
        fonte_layout = QVBoxLayout(fonte_card)
        
        self.combo_fonte = QComboBox()
        self.combo_fonte.setMinimumWidth(120)
        self.combo_fonte.addItem('Monitor')
        self.combo_fonte.addItem('Janela')
        self.combo_fonte.currentIndexChanged.connect(self.on_fonte_changed)
        
        self.combo_monitor = QComboBox()
        self.combo_monitor.setMinimumWidth(180)
        
        self.btn_atualizar_entradas_vmix = QPushButton('Atualizar vMix')
        self.btn_atualizar_entradas_vmix.setMinimumWidth(110)
        self.btn_atualizar_entradas_vmix.setMinimumHeight(28)
        self.btn_atualizar_entradas_vmix.clicked.connect(self.buscar_entradas_vmix)
        self.btn_atualizar_entradas_vmix.setProperty('monitor', True)
        self.btn_atualizar_entradas_vmix.setIcon(QIcon(resource_path('ui/icons/sync.png')))
        
        fonte_layout.addWidget(self.combo_fonte)
        fonte_layout.addWidget(self.combo_monitor)
        fonte_layout.addWidget(self.btn_atualizar_entradas_vmix)
        col_esq.addWidget(fonte_card)

        # 2. Configuração OBS
        self.obs_config = OBSConfigWidget()
        self.obs_config.config_changed.connect(self.salvar_config_obs)
        self.obs_config.test_connection.connect(self.testar_conexao_obs)
        col_esq.addWidget(self.obs_config)

        # Atualizar referências dos campos
        self.input_obs_host = self.obs_config.host_input
        self.input_obs_port = self.obs_config.port_input
        self.input_obs_senha = self.obs_config.password_input
        self.btn_testar_obs = self.obs_config.test_button

        # 3. Região do PGM
        regiao_card = QGroupBox('Região do PGM')
        regiao_card.setProperty('glass', True)
        regiao_layout = QVBoxLayout(regiao_card)
        
        self.btn_selecionar_regiao = QPushButton('Selecionar região do PGM')
        self.btn_selecionar_regiao.setMinimumHeight(28)
        self.btn_selecionar_regiao.clicked.connect(self.selecionar_regiao)
        self.btn_selecionar_regiao.setIcon(QIcon(resource_path('ui/icons/select_region.png')))
        
        self.label_regiao = QLabel('Região: (top, left, width, height)')
        self.label_regiao.setStyleSheet('color: #b48ead; margin-top: 4px; font-size: 14px;')
        
        regiao_layout.addWidget(self.btn_selecionar_regiao)
        regiao_layout.addWidget(self.label_regiao)
        col_esq.addWidget(regiao_card)

        # 4. Imagens de Referência
        ref_card = QGroupBox('Imagens de Referência')
        ref_card.setProperty('glass', True)
        ref_layout = QVBoxLayout(ref_card)
        
        self.btn_add_ref = QPushButton('Adicionar imagem de referência')
        self.btn_add_ref.setMinimumHeight(24)
        self.btn_add_ref.clicked.connect(self.adicionar_imagem_referencia)
        self.btn_add_ref.setIcon(QIcon(resource_path('ui/icons/add_image.png')))
        
        self.lista_referencias = QListWidget()
        self.lista_referencias.setViewMode(QListWidget.ListMode)
        self.lista_referencias.setMaximumHeight(100)
        self.lista_referencias.setStyleSheet('background: transparent; border: none;')
        self.lista_referencias.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista_referencias.customContextMenuRequested.connect(self.menu_referencia)
        
        ref_layout.addWidget(self.btn_add_ref)
        ref_layout.addWidget(self.lista_referencias)
        col_esq.addWidget(ref_card)

        # 5. Monitoramento
        monitor_card = QGroupBox('Monitoramento')
        monitor_card.setProperty('glass', True)
        monitor_layout = QVBoxLayout(monitor_card)
        
        # Botões de controle
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        self.btn_iniciar = QPushButton('Iniciar')
        self.btn_iniciar.setMinimumWidth(110)
        self.btn_iniciar.setMinimumHeight(28)
        self.btn_iniciar.clicked.connect(self.iniciar_monitoramento)
        self.btn_iniciar.setProperty('monitor', True)
        self.btn_iniciar.setIcon(QIcon(resource_path('ui/icons/start.png')))
        self.btn_iniciar.setObjectName("btnIniciar")
        
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setMinimumWidth(110)
        self.btn_parar.setMinimumHeight(28)
        self.btn_parar.setEnabled(False)
        self.btn_parar.clicked.connect(self.parar_monitoramento)
        self.btn_parar.setProperty('monitor', True)
        self.btn_parar.setObjectName('btnParar')
        self.btn_parar.setIcon(QIcon(resource_path('ui/icons/stop.png')))
        
        btn_layout.addWidget(self.btn_iniciar)
        btn_layout.addWidget(self.btn_parar)
        monitor_layout.addLayout(btn_layout)
        
        # Intervalo
        tempo_layout = QHBoxLayout()
        tempo_label = QLabel('Intervalo (s):')
        tempo_label.setStyleSheet('font-size: 14px; color: #b48ead;')
        
        self.spin_tempo = QDoubleSpinBox()
        self.spin_tempo.setDecimals(2)
        self.spin_tempo.setMinimum(0.1)
        self.spin_tempo.setMaximum(10.0)
        self.spin_tempo.setSingleStep(0.1)
        self.spin_tempo.setValue(0.5)
        self.spin_tempo.setStyleSheet('font-size: 14px; background: #23272f; color: #eceff4; border-radius: 8px; padding: 2px 8px;')
        
        tempo_layout.addWidget(tempo_label)
        tempo_layout.addWidget(self.spin_tempo)
        monitor_layout.addLayout(tempo_layout)
        
        col_esq.addWidget(monitor_card)

        # COLUNA DIREITA
        col_dir = QVBoxLayout()
        col_dir.setSpacing(18)

        # Log e Configuração
        log_card = QGroupBox('Log e Configuração')
        log_card.setProperty('glass', True)
        log_layout = QVBoxLayout(log_card)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(70)
        self.log.setStyleSheet('font-size: 13px; background: #23272f; color: #eceff4; border-radius: 12px; border: none; padding: 6px; font-family: "Fira Mono", monospace;')
        
        btn_layout = QHBoxLayout()
        
        self.btn_exportar_log = QPushButton('Exportar log')
        self.btn_exportar_log.setMinimumWidth(130)
        self.btn_exportar_log.clicked.connect(self.exportar_log)
        self.btn_exportar_log.setIcon(QIcon(resource_path('ui/icons/save.png')))
        
        self.btn_exportar_cfg = QPushButton('Exportar cfg')
        self.btn_exportar_cfg.setMinimumWidth(130)
        self.btn_exportar_cfg.clicked.connect(self.exportar_config)
        self.btn_exportar_cfg.setIcon(QIcon(resource_path('ui/icons/save.png')))
        
        self.btn_importar_cfg = QPushButton('Importar cfg')
        self.btn_importar_cfg.setMinimumWidth(130)
        self.btn_importar_cfg.clicked.connect(self.importar_config)
        self.btn_importar_cfg.setIcon(QIcon(resource_path('ui/icons/open.png')))
        
        btn_layout.addWidget(self.btn_exportar_log)
        btn_layout.addWidget(self.btn_exportar_cfg)
        btn_layout.addWidget(self.btn_importar_cfg)
        
        log_layout.addWidget(self.log)
        log_layout.addLayout(btn_layout)
        
        col_dir.addWidget(log_card)

        # Adicionar colunas ao layout principal
        main_hbox.addLayout(col_esq, 2)
        main_hbox.addLayout(col_dir, 1)
        main_layout.addLayout(main_hbox)

        # RODAPÉ
        rodape = QLabel('v1.0.0  |  © 2024 SeuNome  |  Suporte: suporte@seudominio.com')
        rodape.setAlignment(Qt.AlignCenter)
        rodape.setProperty('footer', True)
        rodape.setStyleSheet('margin-top: 4px;')
        main_layout.addWidget(rodape)

        # Configurações finais
        self.setMinimumSize(900, 750)
        
        # Preencher automaticamente a lista de monitores ou janelas
        if self.combo_fonte.currentText() == 'Monitor':
            self.atualizar_lista_monitores_janelas(filtrar='monitor')
        elif self.combo_fonte.currentText() == 'Janela':
            self.atualizar_lista_monitores_janelas(filtrar='janela')

    def on_fonte_changed(self):
        """Atualiza a interface conforme a fonte de captura selecionada."""
        fonte = self.combo_fonte.currentText()
        if fonte == 'Monitor':
            self.combo_monitor.show()
            self.btn_atualizar_entradas_vmix.show()
            self.atualizar_lista_monitores_janelas(filtrar='monitor')
        elif fonte == 'Janela':
            self.combo_monitor.show()
            self.btn_atualizar_entradas_vmix.show()
            self.atualizar_lista_monitores_janelas(filtrar='janela')

    def atualizar_lista_monitores_janelas(self, filtrar=None):
        """Atualiza a lista de monitores e janelas disponíveis para captura."""
        import mss
        import pyautogui
        self.combo_monitor.clear()
        encontrou_janela = False
        if filtrar in (None, 'monitor'):
            with mss.mss() as sct:
                for i, m in enumerate(sct.monitors[1:], 1):
                    self.combo_monitor.addItem(f"Monitor {i}", f"monitor_{i}")
        if filtrar in (None, 'janela'):
            try:
                janelas = pyautogui.getAllWindows()
                for w in janelas:
                    if w.title and w.visible:
                        self.combo_monitor.addItem(f"Janela: {w.title}", f"janela_{w._hWnd}")
                        encontrou_janela = True
                if not encontrou_janela:
                    if hasattr(self, 'log'):
                        self.log.append('Nenhuma janela de aplicativo encontrada para captura.')
            except Exception:
                if hasattr(self, 'log'):
                    self.log.append('Erro ao tentar listar janelas de aplicativos.')

    def selecionar_regiao(self):
        """Permite ao usuário selecionar visualmente a região do PGM."""
        import mss
        import pyautogui
        escolha = self.combo_monitor.currentData()
        if escolha and escolha.startswith('monitor_'):
            idx = int(escolha.split('_')[1])
            with mss.mss() as sct:
                monitor = sct.monitors[idx]
                img = np.array(sct.grab(monitor))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            r = cv2.selectROI(f"Selecione a região do PGM no Monitor {idx} e pressione ENTER", img, False, False)
            cv2.destroyAllWindows()
            if r and r[2] > 0 and r[3] > 0:
                left, top, width, height = int(r[0]), int(r[1]), int(r[2]), int(r[3])
                self.regiao = (top, left, width, height, idx, None)
                self.label_regiao.setText(f'Região: top={top}, left={left}, width={width}, height={height}, monitor={idx}')
                self.log.append(f'Região selecionada: top={top}, left={left}, width={width}, height={height}, monitor={idx}')
                # Captura a referência diretamente do recorte da imagem já capturada
                ref_crop = img[top:top+height, left:left+width]
                idx_ref = 1
                while True:
                    nome_arquivo = f'referencia_{idx_ref}.png'
                    if not os.path.exists(nome_arquivo):
                        break
                    idx_ref += 1
                cv2.imwrite(nome_arquivo, ref_crop)
                self.referencias.append({'path': nome_arquivo, 'acoes': []})
                self.atualizar_lista_referencias()
                self.log.append(f'Imagem de referência capturada e salva como {nome_arquivo}.')
                QMessageBox.information(self, 'Captura realizada', f'Imagem de referência capturada e salva como {nome_arquivo}!')
            else:
                QMessageBox.warning(self, 'Seleção de região', 'Seleção não realizada.')
        elif escolha and escolha.startswith('janela_'):
            hwnd = int(escolha.split('_')[1])
            janela = None
            for w in pyautogui.getAllWindows():
                if w._hWnd == hwnd:
                    janela = w
                    break
            if janela:
                bbox = janela.box
                img = pyautogui.screenshot(region=bbox)
                img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                r = cv2.selectROI(f"Selecione a região do PGM na janela '{janela.title}' e pressione ENTER", img, False, False)
                cv2.destroyAllWindows()
                if r and r[2] > 0 and r[3] > 0:
                    left, top, width, height = int(r[0]), int(r[1]), int(r[2]), int(r[3])
                    self.regiao = (top, left, width, height, None, hwnd)
                    self.label_regiao.setText(f'Região: top={top}, left={left}, width={width}, height={height}, janela={janela.title}')
                    self.log.append(f'Região selecionada: top={top}, left={left}, width={width}, height={height}, janela={janela.title}')
                    # Captura a referência diretamente do recorte da imagem já capturada
                    ref_crop = img[top:top+height, left:left+width]
                    idx_ref = 1
                    while True:
                        nome_arquivo = f'referencia_{idx_ref}.png'
                        if not os.path.exists(nome_arquivo):
                            break
                        idx_ref += 1
                    cv2.imwrite(nome_arquivo, ref_crop)
                    self.referencias.append({'path': nome_arquivo, 'acoes': []})
                    self.atualizar_lista_referencias()
                    self.log.append(f'Imagem de referência capturada e salva como {nome_arquivo}.')
                    QMessageBox.information(self, 'Captura realizada', f'Imagem de referência capturada e salva como {nome_arquivo}!')
                else:
                    QMessageBox.warning(self, 'Seleção de região', 'Seleção não realizada.')
            else:
                QMessageBox.warning(self, 'Seleção de região', 'Janela não encontrada.')
        else:
            QMessageBox.warning(self, 'Seleção de região', 'Selecione um monitor ou janela para capturar.')

    def capturar_referencia(self):
        """Captura uma imagem de referência da região selecionada."""
        import mss
        import pyautogui
        if not self.regiao:
            QMessageBox.warning(self, 'Capturar referência', 'Selecione a região do PGM primeiro!')
            return
        top, left, width, height, monitor_idx, hwnd = self.regiao
        if monitor_idx:
            with mss.mss() as sct:
                monitor = sct.monitors[monitor_idx]
                img = np.array(sct.grab(monitor))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            ref_crop = img[top:top+height, left:left+width]
        elif hwnd:
            for w in pyautogui.getAllWindows():
                if w._hWnd == hwnd:
                    bbox = w.box
                    img = pyautogui.screenshot(region=bbox)
                    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    ref_crop = img[top:top+height, left:left+width]
                    break
            else:
                QMessageBox.warning(self, 'Capturar referência', 'Janela não encontrada!')
                return
        else:
            QMessageBox.warning(self, 'Capturar referência', 'Selecione um monitor ou janela!')
            return
        # Gerar nome único para a nova referência
        idx = 1
        while True:
            nome_arquivo = f'referencia_{idx}.png'
            if not os.path.exists(nome_arquivo):
                break
            idx += 1
        cv2.imwrite(nome_arquivo, ref_crop)
        self.referencias.append({'path': nome_arquivo, 'acoes': []})
        self.atualizar_lista_referencias()
        self.log.append(f'Imagem de referência capturada e salva como {nome_arquivo}.')
        QMessageBox.information(self, 'Captura realizada', f'Imagem de referência capturada e salva como {nome_arquivo}!')

    def buscar_entradas_vmix(self):
        """Busca as entradas do vMix e retorna uma lista de títulos."""
        try:
            resp = requests.get('http://localhost:8088/api', timeout=2)
            root = ET.fromstring(resp.content)
            entradas = [input_elem.attrib['title'] for input_elem in root.findall('.//inputs/input')]
            return entradas
        except Exception:
            self.log.append('Não foi possível conectar ao vMix. Verifique se o vMix está aberto e a API ativada.')
            return []

    def iniciar_monitoramento(self):
        """Inicia o monitoramento da região selecionada."""
        if not self.regiao:
            QMessageBox.warning(self, 'Monitoramento', 'Selecione a região do PGM primeiro!')
            return
        # Verifica se há pelo menos uma ação vMix nas referências
        exige_vmix = False
        for ref in self.referencias:
            acoes = ref.get('acoes', [])
            for acao in acoes:
                if acao['tipo'] in ['cut', 'overlay', 'transition', 'shortcut']:
                    exige_vmix = True
        # Só exige entrada do vMix se houver ação vMix
        self.log.append('Monitoramento iniciado.')
        intervalo = self.spin_tempo.value()
        # Passar host e porta do OBS
        host_obs = self.input_obs_host.text().strip()
        port_obs = self.input_obs_port.text().strip()
        self.monitor_thread = MonitorThread(
            regiao=self.regiao,
            referencias=self.referencias,
            entrada_vmix_nome=None,
            entrada_vmix_numero=None,
            intervalo=intervalo,
            host_obs=host_obs,
            port_obs=port_obs
        )
        self.monitor_thread.log_signal.connect(self.log.append)
        self.monitor_thread.start()
        self.btn_iniciar.setEnabled(False)
        self.btn_parar.setEnabled(True)

    def parar_monitoramento(self):
        """Para o monitoramento em andamento."""
        if hasattr(self, 'monitor_thread') and self.monitor_thread is not None:
            self.monitor_thread.stop()
            self.log.append('Monitoramento parado pelo usuário.')
        self.btn_iniciar.setEnabled(True)
        self.btn_parar.setEnabled(False)

    def abrir_sobre(self):
        """Exibe a janela 'Sobre' com informações do projeto."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Sobre o SwitchPilot')
        dialog.setMinimumWidth(400)
        vbox = QVBoxLayout(dialog)
        titulo = QLabel('<b>SwitchPilot</b>')
        titulo.setAlignment(Qt.AlignCenter)
        vbox.addWidget(titulo)
        autores = QLabel('Desenvolvido por: <br><b>Ana Silva</b> e <b>João Souza</b>')
        autores.setAlignment(Qt.AlignCenter)
        vbox.addWidget(autores)
        mensagem = QLabel('<i>Se este programa te ajudou, considere apoiar o projeto!</i>')
        mensagem.setAlignment(Qt.AlignCenter)
        vbox.addWidget(mensagem)
        vbox.addSpacing(8)
        pix = QLabel('Doação via Pix:<br><b>pix@switchpilot.com</b>')
        pix.setAlignment(Qt.AlignCenter)
        vbox.addWidget(pix)
        paypal = QLabel('PayPal:<br><b>paypal.me/switchpilot</b>')
        paypal.setAlignment(Qt.AlignCenter)
        vbox.addWidget(paypal)
        vbox.addSpacing(8)
        fechar = QPushButton('Fechar')
        fechar.clicked.connect(dialog.accept)
        vbox.addWidget(fechar)
        dialog.exec_()

    def atualizar_status_vmix(self, online):
        """Atualiza o status visual do vMix (online/offline)."""
        # Protege contra QLabel deletado ou widget destruído
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                if online:
                    self.status_label.setText('● Online')
        except Exception:
            pass

    def closeEvent(self, event):
        """Evento de fechamento da janela principal."""
        from PyQt5.QtCore import QSettings
        settings = QSettings('SwitchPilot', 'PainelVmix')
        mostrar_doacao = settings.value('mostrar_doacao', 'sim')
        if mostrar_doacao == 'sim':
            dialog = QDialog(self)
            dialog.setWindowTitle('Apoie o SwitchPilot!')
            dialog.setMinimumWidth(420)
            vbox = QVBoxLayout(dialog)
            label = QLabel('<b>Se este programa te ajudou, considere apoiar o projeto!</b>')
            label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)
            vbox.addSpacing(8)
            pix = QLabel('Doação via Pix:<br><b>pix@switchpilot.com</b>')
            pix.setAlignment(Qt.AlignCenter)
            vbox.addWidget(pix)
            paypal = QLabel('PayPal:<br><b>paypal.me/switchpilot</b>')
            paypal.setAlignment(Qt.AlignCenter)
            vbox.addWidget(paypal)
            vbox.addSpacing(8)
            chk = QCheckBox('Não mostrar novamente')
            vbox.addWidget(chk, alignment=Qt.AlignCenter)
            hbox = QHBoxLayout()
            btn_ok = QPushButton('Fechar')
            btn_ok.clicked.connect(dialog.accept)
            hbox.addWidget(btn_ok)
            vbox.addLayout(hbox)
            dialog.exec_()
            if chk.isChecked():
                settings.setValue('mostrar_doacao', 'nao')
        if hasattr(self, 'status_thread'):
            try:
                self.status_thread.status_signal.disconnect(self.atualizar_status_vmix)
            except Exception:
                pass
            if hasattr(self.status_thread, 'stop'):
                self.status_thread.stop()
            self.status_thread.wait()
        super().closeEvent(event)

    def mostrar_erro_vmix(self, erro):
        """Exibe mensagem de erro ao não conectar ao vMix."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Não foi possível conectar ao vMix')
        dialog.setMinimumWidth(420)
        vbox = QVBoxLayout(dialog)
        label = QLabel('Não foi possível conectar ao vMix nesta máquina.\n')
        label.setWordWrap(True)
        vbox.addWidget(label)
        self.diagnostico_itens = [
            {'nome': 'vMix está aberto e rodando', 'status': None},
            {'nome': 'API do vMix está ativada (porta 8088)', 'status': None},
            {'nome': 'Firewall/antivírus está permitindo a conexão', 'status': None},
        ]
        self.diagnostico_labels = []
        for item in self.diagnostico_itens:
            l = QLabel(f'- {item["nome"]}')
            l.setWordWrap(True)
            vbox.addWidget(l)
            self.diagnostico_labels.append(l)
        vbox.addSpacing(8)
        hbox = QHBoxLayout()
        btn_diag = QPushButton('Diagnóstico')
        btn_diag.clicked.connect(lambda: self.fazer_diagnostico(btn_diag))
        hbox.addWidget(btn_diag)
        btn_ok = QPushButton('OK')
        btn_ok.clicked.connect(dialog.accept)
        hbox.addWidget(btn_ok)
        vbox.addLayout(hbox)
        dialog.exec_()

    def fazer_diagnostico(self, btn_diag):
        """Executa diagnóstico de conexão com o vMix."""
        status_vm = False
        if psutil:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'vmix' in proc.info['name'].lower():
                    status_vm = True
                    break
        else:
            status_vm = None
        status_api = False
        try:
            s = socket.create_connection(('localhost', 8088), timeout=1)
            s.close()
            status_api = True
        except Exception:
            status_api = False
        status_fw = None
        if status_vm and not status_api:
            status_fw = False
        elif status_vm and status_api:
            status_fw = True
        checks = {True: '✅', False: '❌', None: '❓'}
        self.diagnostico_labels[0].setText(f'- vMix está aberto e rodando {checks[status_vm]}')
        self.diagnostico_labels[1].setText(f'- API do vMix está ativada (porta 8088) {checks[status_api]}')
        self.diagnostico_labels[2].setText(f'- Firewall/antivírus está permitindo a conexão {checks[status_fw]}')
        btn_diag.setEnabled(False)

    def adicionar_imagem_referencia(self):
        """Adiciona imagens ou vídeos de referência à lista."""
        files, _ = QFileDialog.getOpenFileNames(self, 'Selecionar imagens ou vídeos de referência', '', 'Imagens/Vídeos (*.png *.jpg *.jpeg *.gif *.mp4 *.avi *.mov)')
        for f in files:
            if f.lower().endswith(('.gif', '.mp4', '.avi', '.mov')):
                self.adicionar_referencia_video_ou_gif(f)
            else:
                if not any(ref['path'] == f for ref in self.referencias):
                    self.referencias.append({'path': f, 'acoes': []})
        self.atualizar_lista_referencias()

    def adicionar_referencia_video_ou_gif(self, filepath):
        """Extrai quadros de vídeos ou GIFs para referência."""
        import cv2
        import os
        cap = cv2.VideoCapture(filepath)
        idx = 1
        frame_count = 0
        quadros_seq = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % 10 == 0:
                nome_arquivo = f'refvideo_{os.path.basename(filepath)}_{idx}.png'
                cv2.imwrite(nome_arquivo, frame)
                quadros_seq.append(nome_arquivo)
                idx += 1
            frame_count += 1
        cap.release()
        if quadros_seq:
            self.referencias.append({'sequencia': quadros_seq, 'acoes': []})
            self.log.append(f'Sequência de {len(quadros_seq)} quadros extraída de {os.path.basename(filepath)}.')

    def atualizar_lista_referencias(self):
        """Atualiza a lista de referências exibidas na interface, com layout para ListMode."""
        self.lista_referencias.clear()
        for ref in self.referencias:
            path = ''
            nome_completo = ''
            if 'path' in ref:
                path = ref['path']
                nome_completo = os.path.basename(path)
            elif 'sequencia' in ref:
                path = ref['sequencia'][0] if ref['sequencia'] else ''
                nome_completo = f"Seq ({len(ref['sequencia'])}q): {os.path.basename(path) if path else ''}"
            else:
                continue
            
            acoes = ref.get('acoes', [])
            badge = None
            if acoes:
                badge = QLabel(str(len(acoes)))
                # Estilo do badge pode ser ajustado no QSS ou aqui
                badge.setStyleSheet('background-color: #007bff; color: white; border-radius: 9px; padding: 1px 5px; font-size: 9pt; font-weight: bold;')
                badge.setAlignment(Qt.AlignCenter)

            # 1. Criar o item da lista
            item = QListWidgetItem(self.lista_referencias) # Adiciona à lista implicitamente
            
            # 2. Criar o widget customizado para o item
            widget = QWidget()
            hbox = QHBoxLayout(widget)
            hbox.setContentsMargins(5, 3, 5, 3) # Margens verticais menores
            hbox.setSpacing(8) 

            # 2a. Thumbnail à esquerda
            thumb_label = QLabel()
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                thumb_label.setPixmap(pixmap.scaled(40, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                thumb_label.setText("Err") # Indicar erro ao carregar
                thumb_label.setStyleSheet("color: red;")
            thumb_label.setFixedSize(40, 30) 
            hbox.addWidget(thumb_label)

            # 2b. Texto (nome) no meio
            label_nome = QLabel(nome_completo) 
            label_nome.setWordWrap(True) 
            label_nome.setStyleSheet('font-size: 10pt; color: #eceff4;') 
            hbox.addWidget(label_nome, 1) # Stretch factor 1 para ocupar espaço

            # 2c. Badge à direita (se houver)
            if badge:
                badge_layout = QVBoxLayout() # Layout para controlar alinhamento vertical
                badge_layout.addWidget(badge, alignment=Qt.AlignTop | Qt.AlignRight)
                hbox.addLayout(badge_layout)
            else:
                # Adicionar um pequeno espaço se não houver badge para manter alinhamento
                spacer = QSpacerItem(18, 18, QSizePolicy.Minimum, QSizePolicy.Minimum)
                hbox.addItem(spacer)

            widget.setLayout(hbox)
            
            # 3. Definir o tamanho do item e o widget customizado
            item.setSizeHint(widget.sizeHint()) 
            self.lista_referencias.setItemWidget(item, widget)

            # 4. Definir o Tooltip (como antes)
            if acoes:
                item.setToolTip(nome_completo + '\n' + '\n'.join([descrever_acao(a) for a in acoes]))
            else:
                item.setToolTip(nome_completo)

    def menu_referencia(self, pos):
        """Exibe menu de contexto para adicionar/remover ações ou referências."""
        item = self.lista_referencias.itemAt(pos)
        if item:
            menu = QMenu()
            action_add = menu.addAction('Adicionar ação')
            action_list = menu.addAction('Listar/remover ações')
            action_remove = menu.addAction('Remover imagem')
            escolha = menu.exec_(self.lista_referencias.mapToGlobal(pos))
            idx = self.lista_referencias.row(item)
            if escolha == action_add:
                self.adicionar_acao_referencia(idx)
            elif escolha == action_list:
                self.listar_remover_acoes(idx)
            elif escolha == action_remove:
                if len(self.referencias) > 1:
                    self.referencias.pop(idx)
                    self.atualizar_lista_referencias()
                else:
                    QMessageBox.warning(self, 'Referência', 'Deixe pelo menos uma imagem de referência.')

    def adicionar_acao_referencia(self, idx):
        """Abre diálogo para associar uma nova ação à referência selecionada."""
        dialog = QDialog(self)
        dialog.setWindowTitle('⚡ Nova ação para referência')
        dialog.setMinimumWidth(340)
        vbox = QVBoxLayout(dialog)
        vbox.setContentsMargins(24, 18, 24, 18)
        vbox.setSpacing(16)
        label = QLabel(f"<b>Imagem:</b> {os.path.basename(self.referencias[idx]['path'])}")
        label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(label)
        vbox.addSpacing(8)
        label2 = QLabel('Tipo de ação:')
        vbox.addWidget(label2)
        combo_tipo = QComboBox()
        combo_tipo.setMinimumWidth(180)
        combo_tipo.addItem('Cortar para entrada', 'cut')
        combo_tipo.addItem('Exibir overlay', 'overlay')
        combo_tipo.addItem('Ativar transição', 'transition')
        combo_tipo.addItem('Executar shortcut', 'shortcut')
        combo_tipo.addItem('Mudar cena do OBS', 'obs_scene')
        combo_tipo.addItem('Ativar fonte do OBS', 'obs_source_on')
        combo_tipo.addItem('Desativar fonte do OBS', 'obs_source_off')
        combo_tipo.addItem('Iniciar gravação OBS', 'obs_start_record')
        combo_tipo.addItem('Parar gravação OBS', 'obs_stop_record')
        combo_tipo.addItem('Iniciar transmissão OBS', 'obs_start_stream')
        combo_tipo.addItem('Parar transmissão OBS', 'obs_stop_stream')
        combo_tipo.setCurrentIndex(0)
        combo_tipo.show()
        vbox.addWidget(combo_tipo)
        label3 = QLabel('Selecione a entrada do vMix:')
        vbox.addWidget(label3)
        combo_entrada = QComboBox()
        combo_entrada.setMinimumWidth(180)
        combo_entrada.setEnabled(False)
        combo_entrada.addItem('Carregando entradas...')
        vbox.addWidget(combo_entrada)
        # Busca automática das entradas do vMix
        def preencher_entradas():
            combo_entrada.clear()
            combo_entrada.setEnabled(False)
            combo_entrada.addItem('Carregando entradas...')
            QApplication.processEvents()
            entradas = self.buscar_entradas_vmix()
            combo_entrada.clear()
            if entradas:
                combo_entrada.addItems(entradas)
                combo_entrada.setEnabled(True)
            else:
                combo_entrada.addItem('Nenhuma entrada encontrada')
                combo_entrada.setEnabled(False)
        preencher_entradas()
        label_overlay = QLabel('Selecione o número do overlay (1 a 4):')
        combo_overlay = QComboBox()
        combo_overlay.setMinimumWidth(120)
        combo_overlay.addItems(['1', '2', '3', '4'])
        vbox.addWidget(label_overlay)
        vbox.addWidget(combo_overlay)
        label_trans = QLabel('Selecione o tipo de transição:')
        combo_trans = QComboBox()
        combo_trans.setMinimumWidth(140)
        combo_trans.addItems(['Fade', 'Cut', 'Wipe', 'Cube', 'Fly', 'Zoom', 'Slide', 'Merge'])
        vbox.addWidget(label_trans)
        vbox.addWidget(combo_trans)
        label_shortcut = QLabel('Nome do shortcut do vMix:')
        input_shortcut = QLineEdit()
        input_shortcut.setPlaceholderText('Ex: MEU_SHORTCUT')
        input_shortcut.setMinimumWidth(160)
        vbox.addWidget(label_shortcut)
        vbox.addWidget(input_shortcut)
        label_obs_scene = QLabel('Nome da cena do OBS:')
        combo_obs_scene = QComboBox()
        combo_obs_scene.setMinimumWidth(140)
        combo_obs_scene.setEditable(True)
        vbox.addWidget(label_obs_scene)
        vbox.addWidget(combo_obs_scene)
        label_obs_source = QLabel('Nome da fonte do OBS:')
        combo_obs_source = QComboBox()
        combo_obs_source.setMinimumWidth(140)
        combo_obs_source.setEditable(True)
        vbox.addWidget(label_obs_source)
        vbox.addWidget(combo_obs_source)
        # Preencher cenas e fontes do OBS
        def preencher_obs():
            host = self.input_obs_host.text().strip()
            port = self.input_obs_port.text().strip()
            cenas = self.buscar_cenas_obs(host, port)
            fontes = self.buscar_fontes_obs(host, port)
            combo_obs_scene.clear()
            combo_obs_source.clear()
            if cenas:
                combo_obs_scene.addItems(cenas)
            if fontes:
                combo_obs_source.addItems(fontes)
        preencher_obs()
        # Esconde todos inicialmente
        label3.hide()
        combo_entrada.hide()
        label_overlay.hide()
        combo_overlay.hide()
        label_trans.hide()
        combo_trans.hide()
        label_shortcut.hide()
        input_shortcut.hide()
        label_obs_scene.hide()
        combo_obs_scene.hide()
        label_obs_source.hide()
        combo_obs_source.hide()
        def on_tipo_changed():
            tipo = combo_tipo.currentData()
            # Esconde todos inicialmente
            label3.hide()
            combo_entrada.hide()
            label_overlay.hide()
            combo_overlay.hide()
            label_trans.hide()
            combo_trans.hide()
            label_shortcut.hide()
            input_shortcut.hide()
            label_obs_scene.hide()
            combo_obs_scene.hide()
            label_obs_source.hide()
            combo_obs_source.hide()
            # Exibe apenas os campos relevantes
            if tipo == 'cut':
                label3.show()
                combo_entrada.show()
            elif tipo == 'overlay':
                label_overlay.show()
                combo_overlay.show()
            elif tipo == 'transition':
                label_trans.show()
                combo_trans.show()
            elif tipo == 'shortcut':
                label_shortcut.show()
                input_shortcut.show()
            elif tipo == 'obs_scene':
                label_obs_scene.show()
                combo_obs_scene.show()
            elif tipo in ['obs_source_on', 'obs_source_off']:
                label_obs_source.show()
                combo_obs_source.show()
            # Para os tipos obs_start_record, obs_stop_record, obs_start_stream, obs_stop_stream, nada extra aparece
        combo_tipo.currentIndexChanged.connect(on_tipo_changed)
        on_tipo_changed()
        vbox.addSpacing(10)
        btn_ok = QPushButton('OK')
        btn_ok.setStyleSheet('background: #5e81ac; color: #fff; font-weight: bold; border-radius: 8px; padding: 6px 18px; font-size: 15px; min-width: 90px;')
        btn_ok.setMinimumHeight(32)
        btn_ok.clicked.connect(dialog.accept)
        vbox.addWidget(btn_ok, alignment=Qt.AlignCenter)
        vbox.addSpacing(8)
        if dialog.exec_() == QDialog.Accepted:
            tipo = combo_tipo.currentData()
            entrada = combo_entrada.currentText()
            if tipo == 'cut':
                acao = {'tipo': 'cut', 'parametros': {'entrada': entrada}}
            elif tipo == 'overlay':
                acao = {'tipo': 'overlay', 'parametros': {'overlay': combo_overlay.currentText()}}
            elif tipo == 'transition':
                acao = {'tipo': 'transition', 'parametros': {'transicao': combo_trans.currentText()}}
            elif tipo == 'shortcut':
                acao = {'tipo': 'shortcut', 'parametros': {'nome': input_shortcut.text().strip()}}
            elif tipo == 'obs_scene':
                acao = {'tipo': 'obs_scene', 'parametros': {'scene': combo_obs_scene.currentText().strip()}}
            elif tipo == 'obs_source_on':
                acao = {'tipo': 'obs_source_on', 'parametros': {'source': combo_obs_source.currentText().strip()}}
            elif tipo == 'obs_source_off':
                acao = {'tipo': 'obs_source_off', 'parametros': {'source': combo_obs_source.currentText().strip()}}
            elif tipo == 'obs_start_record':
                acao = {'tipo': 'obs_start_record', 'parametros': {}}
            elif tipo == 'obs_stop_record':
                acao = {'tipo': 'obs_stop_record', 'parametros': {}}
            elif tipo == 'obs_start_stream':
                acao = {'tipo': 'obs_start_stream', 'parametros': {}}
            elif tipo == 'obs_stop_stream':
                acao = {'tipo': 'obs_stop_stream', 'parametros': {}}
            self.referencias[idx].setdefault('acoes', []).append(acao)
            self.atualizar_lista_referencias()
            QMessageBox.information(self, 'Ação adicionada', 'Ação salva com sucesso!')

    def listar_remover_acoes(self, idx):
        """Lista e permite remover ações associadas a uma referência."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Ações associadas à imagem')
        vbox = QVBoxLayout(dialog)
        label = QLabel(f"Imagem: {os.path.basename(self.referencias[idx]['path'])}")
        vbox.addWidget(label)
        acoes = self.referencias[idx].get('acoes', [])
        for i, acao in enumerate(acoes):
            hbox = QHBoxLayout()
            lbl = QLabel(descrever_acao(acao))
            hbox.addWidget(lbl)
            btn_rem = QPushButton('Remover')
            btn_rem.clicked.connect(lambda _, i=i: self.remover_acao(idx, i, dialog))
            hbox.addWidget(btn_rem)
            vbox.addLayout(hbox)
        btn_ok = QPushButton('Fechar')
        btn_ok.clicked.connect(dialog.accept)
        vbox.addWidget(btn_ok)
        dialog.exec_()

    def remover_acao(self, idx, acao_idx, dialog):
        """Remove uma ação específica de uma referência."""
        self.referencias[idx]['acoes'].pop(acao_idx)
        self.atualizar_lista_referencias()
        dialog.accept()

    def exportar_log(self):
        """Exporta o log atual para um arquivo de texto."""
        from PyQt5.QtWidgets import QFileDialog
        texto = self.log.toPlainText()
        if not texto.strip():
            QMessageBox.information(self, 'Exportar log', 'O log está vazio.')
            return
        caminho, _ = QFileDialog.getSaveFileName(self, 'Salvar log como', 'log_switchpilot.txt', 'Arquivos de texto (*.txt)')
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(texto)
            QMessageBox.information(self, 'Exportar log', f'Log exportado para:\n{caminho}')

    def exportar_config(self):
        """Exporta as configurações e referências para um arquivo JSON."""
        import json
        from PyQt5.QtWidgets import QFileDialog
        cfg = {'referencias': self.referencias}
        caminho, _ = QFileDialog.getSaveFileName(self, 'Exportar configurações', 'switchpilot_config.json', 'Configuração JSON (*.json)')
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, 'Exportar configurações', f'Configurações exportadas para:\n{caminho}')

    def importar_config(self):
        """Importa configurações e referências de um arquivo JSON."""
        import json
        from PyQt5.QtWidgets import QFileDialog
        caminho, _ = QFileDialog.getOpenFileName(self, 'Importar configurações', '', 'Configuração JSON (*.json)')
        if caminho:
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                if 'referencias' in cfg:
                    self.referencias = cfg['referencias']
                    self.atualizar_lista_referencias()
                    QMessageBox.information(self, 'Importar configurações', 'Configurações importadas com sucesso!')
                else:
                    QMessageBox.warning(self, 'Importar configurações', 'Arquivo inválido ou corrompido.')
            except Exception as e:
                QMessageBox.warning(self, 'Importar configurações', f'Erro ao importar: {e}')

    def salvar_config_obs(self):
        """Salva as configurações do OBS."""
        settings = QSettings()
        config = self.obs_config.get_config()
        settings.setValue('obs/config', config)
        
    def carregar_config_obs(self):
        """Carrega as configurações do OBS."""
        settings = QSettings()
        config = settings.value('obs/config', {
            'host': 'localhost',
            'port': '4455',
            'password': ''
        })
        self.obs_config.set_config(config)
        
    def testar_conexao_obs(self):
        """Testa a conexão com o OBS."""
        config = self.obs_config.get_config()
        host = config['host']
        port = config['port']
        password = config['password']
        
        try:
            # Tentar conectar ao OBS
            ws = websocket.WebSocket()
            ws.connect(f"ws://{host}:{port}")
            
            if password:
                self.autenticar_obs(ws, password)
            
            # Se chegou aqui, a conexão foi bem sucedida
            QMessageBox.information(self, 'Sucesso',
                                  'Conexão com OBS estabelecida com sucesso!')
            ws.close()
            
        except Exception as e:
            QMessageBox.warning(self, 'Erro',
                              f'Erro ao conectar com OBS:\n{str(e)}')

    def autenticar_obs(self, ws, senha):
        """Autentica no OBS WebSocket 5.x usando Identify, challenge e salt. Trata resposta vazia/conexão fechada."""
        import json, base64, hashlib
        import websocket
        resp = ws.recv()
        data = json.loads(resp)
        identify = {
            "op": 1,
            "d": {
                "rpcVersion": 1
            }
        }
        if 'authentication' in data.get('d', {}):
            challenge = data['d']['authentication']['challenge']
            salt = data['d']['authentication']['salt']
            if not senha:
                raise Exception('O OBS exige senha, mas nenhum valor foi informado.')
            senha = senha.strip()
            secret = base64.b64encode(hashlib.sha256((senha + salt).encode('utf-8')).digest()).decode('utf-8')
            auth = base64.b64encode(hashlib.sha256((secret + challenge).encode('utf-8')).digest()).decode('utf-8')
            identify["d"]["authentication"] = auth
        json_identify = json.dumps(identify)
        ws.send(json_identify)
        try:
            resp2 = ws.recv()
        except websocket._exceptions.WebSocketConnectionClosedException:
            resp2 = ''
        if not resp2:
            raise Exception('A conexão com o OBS foi fechada após tentar autenticar. Verifique se a senha está correta e se o OBS está configurado para aceitar conexões.')
        data2 = json.loads(resp2)
        if data2.get('op') == 2 and data2.get('d', {}).get('negotiatedRpcVersion') == 1:
            return True
        if data2.get('op') == 5 and data2.get('d', {}).get('eventType') == 'Exit':
            raise Exception('Autenticação OBS falhou: senha incorreta.')
        raise Exception('Falha na autenticação OBS.')

    def buscar_cenas_obs(self, host, port):
        """Retorna uma lista de nomes de cenas do OBS via WebSocket. Loga a resposta bruta."""
        try:
            import websocket, json
            ws = websocket.create_connection(f"ws://{host}:{port}", timeout=2)
            senha = self.input_obs_senha.text().strip()
            if not self.autenticar_obs(ws, senha):
                QMessageBox.warning(self, 'OBS', 'Falha na autenticação com o OBS.')
                ws.close()
                return []
            req_id = str(uuid.uuid4())
            msg = {"op": 6, "d": {"requestType": "GetSceneList", "requestId": req_id}}
            ws.send(json.dumps(msg))
            resp = ws.recv()
            ws.close()
            data = json.loads(resp)
            cenas = data.get('d', {}).get('responseData', {}).get('scenes', [])
            if not cenas:
                QMessageBox.warning(self, 'OBS', 'Não foi possível obter a lista de cenas do OBS. Verifique autenticação, versão do WebSocket e permissões.')
            else:
                self.log.append('Cenas do OBS carregadas.')
            return [c['sceneName'] for c in cenas]
        except Exception:
            self.log.append('Erro ao buscar cenas do OBS.')
            QMessageBox.warning(self, 'OBS', 'Erro ao buscar cenas do OBS.')
            return []

    def buscar_fontes_obs(self, host, port):
        """Retorna uma lista de nomes de fontes do OBS via WebSocket. Loga a resposta bruta."""
        try:
            import websocket, json
            ws = websocket.create_connection(f"ws://{host}:{port}", timeout=2)
            senha = self.input_obs_senha.text().strip()
            if not self.autenticar_obs(ws, senha):
                QMessageBox.warning(self, 'OBS', 'Falha na autenticação com o OBS.')
                ws.close()
                return []
            req_id = str(uuid.uuid4())
            msg = {"op": 6, "d": {"requestType": "GetInputList", "requestId": req_id}}
            ws.send(json.dumps(msg))
            resp = ws.recv()
            ws.close()
            data = json.loads(resp)
            fontes = data.get('d', {}).get('responseData', {}).get('inputs', [])
            if not fontes:
                QMessageBox.warning(self, 'OBS', 'Não foi possível obter a lista de fontes do OBS. Verifique autenticação, versão do WebSocket e permissões.')
            else:
                self.log.append('Fontes do OBS carregadas.')
            return [f['inputName'] for f in fontes]
        except Exception:
            self.log.append('Erro ao buscar fontes do OBS.')
            QMessageBox.warning(self, 'OBS', 'Erro ao buscar fontes do OBS.')
            return []

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    painel = PainelVmix()
    painel.show()
    sys.exit(app.exec_()) 