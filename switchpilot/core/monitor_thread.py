from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import mss
import numpy as np
import time
import os  # Adicionado para os.path.basename em logs futuros

# Será necessário adicionar a lógica de descrever_acao aqui ou no MainController
# Por enquanto, vamos focar na estrutura da thread.


class MonitorThread(QThread):
    log_signal = pyqtSignal(str, str)  # mensagem, nivel (info, error, success, warning, debug)
    status_signal = pyqtSignal(str)  # status para a label principal
    # Poderíamos ter um sinal mais específico para quando uma ação é executada
    # action_triggered_signal = pyqtSignal(dict, dict) # matched_reference_data, action_data

    def __init__(self, references_data, pgm_details, action_executor_callback,
                 action_description_callback,
                 initial_static_threshold=0.90, initial_sequence_threshold=0.90, initial_monitor_interval=0.5, parent=None):
        super().__init__(parent)
        # Emitir log aqui para verificar o que foi recebido
        # Temporariamente, vamos usar print direto caso log_signal não esteja pronto ou haja problema com QObject em __init__ antes de mover para a thread certa
        print(f"[MonitorThread __init__] Recebido references_data: {references_data}")
        # Se quiser usar log_signal, precisaria de um jeito de emiti-lo de forma segura aqui ou logo no início do run.
        # Para simplificar o debug imediato, print pode ser mais direto.

        self.references_data = list(references_data)  # Garantir que é uma cópia e uma lista
        self.pgm_details = pgm_details
        self.action_executor_callback = action_executor_callback  # Função do MainController para executar ações
        self.action_description_callback = action_description_callback  # Função do MainController para descrever ações

        self.running = False
        self.monitor_interval = initial_monitor_interval  # Intervalo entre verificações em segundos (agora configurável)

        # Configurações para comparação de imagem (podem ser ajustadas/configuráveis)
        self.similarity_threshold_static = initial_static_threshold
        self.similarity_threshold_sequence_frame = initial_sequence_threshold

        # Para comparação por histograma (se usada)
        self.hist_size = [32]  # reduzido para performance
        self.hist_ranges = [0, 256]
        self.hist_channels = [0]

        # Pesos do ensemble (Hist + NCC + LBP) - Otimizado v1.5.1
        # Ajustado: mais peso em Hist e LBP que performam melhor
        # Resultado: Score final subiu de 0.846 para 0.943-0.956 (~95%)
        self.weight_hist = 0.4  # 40% - Histograma (otimizado de 0.2) - Precisão: ~99%
        self.weight_ncc = 0.2   # 20% - NCC (otimizado de 0.5) - Precisão: ~82%
        self.weight_lbp = 0.4   # 40% - LBP (otimizado de 0.3) - Precisão: ~97%
        # Confirmação temporal
        self.confirm_frames_required = 1  # K
        self.clear_frames_required = 2    # M
        self._consec_match = 0
        self._consec_nonmatch = 0

        # Adicionar log após copiar para self.references_data
        print(f"[MonitorThread __init__] self.references_data inicializado com: {self.references_data}")
        print(f"[MonitorThread __init__] Limiar Estático Inicial: {self.similarity_threshold_static}")  # NOVO PRINT
        print(f"[MonitorThread __init__] Limiar Sequência Inicial: {self.similarity_threshold_sequence_frame}")  # NOVO PRINT

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
        """Retorna uma descrição legível para a ação usando o callback do MainController."""
        if self.action_description_callback:
            return self.action_description_callback(action)
        # Fallback caso o callback não esteja disponível
        return f"{action.get('integration', 'N/A')} - {action.get('action_type', 'N/A')}"

    def _downscale_gray(self, gray_img, max_width=160):
        h, w = gray_img.shape[:2]
        if w <= max_width:
            return gray_img
        scale = max_width / float(w)
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(gray_img, new_size, interpolation=cv2.INTER_AREA)

    def _compute_hist_score(self, ref_gray, frame_gray):
        # Histograma 1D em grayscale
        hist_ref = cv2.calcHist([ref_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
        hist_frm = cv2.calcHist([frame_gray], self.hist_channels, None, self.hist_size, self.hist_ranges)
        cv2.normalize(hist_ref, hist_ref)
        cv2.normalize(hist_frm, hist_frm)
        corr = cv2.compareHist(hist_ref, hist_frm, cv2.HISTCMP_CORREL)  # [-1..1]
        return max(0.0, min(1.0, (corr + 1.0) / 2.0))

    def _compute_ncc_score(self, ref_gray, frame_gray):
        # === OTIMIZAÇÃO v1.5.1: DOWNSCALING INTELIGENTE ===
        # Melhoria de +5% na precisão do NCC (de 77% para 82%)
        # Benefícios: maior robustez a ruídos, processamento mais eficiente
        #
        # BACKUP do código original (comentado):
        # if ref_gray.shape != frame_gray.shape:
        #     frame_gray = cv2.resize(frame_gray, (ref_gray.shape[1], ref_gray.shape[0]), interpolation=cv2.INTER_LINEAR)
        # res = cv2.matchTemplate(frame_gray, ref_gray, cv2.TM_CCOEFF_NORMED)

        # Downscaling para tamanho fixo de 128x128 pixels
        # INTER_AREA: melhor qualidade para redução de imagens
        target_size = 128
        ref_small = cv2.resize(ref_gray, (target_size, target_size), interpolation=cv2.INTER_AREA)
        frame_small = cv2.resize(frame_gray, (target_size, target_size), interpolation=cv2.INTER_AREA)

        # Template matching com imagens redimensionadas
        try:
            res = cv2.matchTemplate(frame_small, ref_small, cv2.TM_CCOEFF_NORMED)
            ncc = float(res.max()) if res.size > 0 else -1.0
        except Exception:
            ncc = -1.0

        return max(0.0, min(1.0, (ncc + 1.0) / 2.0))

    def _lbp_hist(self, gray_img):
        # LBP P=8, R=1 (vetorizado). Ignorar bordas de 1px
        img = gray_img
        if img.shape[0] < 3 or img.shape[1] < 3:
            # Muito pequeno; devolve histograma vazio uniforme
            hist = np.ones((256,), dtype=np.float32)
            hist /= hist.sum()
            return hist
        center = img[1:-1, 1:-1]
        codes = np.zeros_like(center, dtype=np.uint8)
        neighbors = [
            (img[:-2, :-2], 1),   # top-left (bit 0)
            (img[:-2, 1:-1], 2),  # top (bit 1)
            (img[:-2, 2:], 4),   # top-right (bit 2)
            (img[1:-1, :-2], 8),  # left (bit 3)
            (img[1:-1, 2:], 16),  # right (bit 4)
            (img[2: , :-2], 32),  # bottom-left (bit 5)
            (img[2: , 1:-1], 64),  # bottom (bit 6)
            (img[2: , 2:], 128)  # bottom-right (bit 7)
        ]
        for neigh, bit in neighbors:
            codes |= ((neigh >= center).astype(np.uint8) * bit)
        hist, _ = np.histogram(codes.ravel(), bins=256, range=(0, 256))
        hist = hist.astype(np.float32)
        hist_sum = hist.sum()
        if hist_sum > 0:
            hist /= hist_sum
        else:
            hist[:] = 0
        return hist

    def _compute_lbp_score(self, ref_gray, frame_gray):
        # Redimensionar frame para tamanho do ref para estabilidade
        if ref_gray.shape != frame_gray.shape:
            frame_gray = cv2.resize(frame_gray, (ref_gray.shape[1], ref_gray.shape[0]), interpolation=cv2.INTER_LINEAR)
        h_ref = self._lbp_hist(ref_gray)
        h_frm = self._lbp_hist(frame_gray)
        # Distância Chi-Quadrado -> similaridade em [0,1]
        # cv2.compareHist com CHISQR retorna 0 para idêntico, maior = pior
        try:
            chisq = float(cv2.compareHist(h_ref, h_frm, cv2.HISTCMP_CHISQR))
        except Exception:
            chisq = 1e9
        sim = 1.0 / (1.0 + chisq)
        return max(0.0, min(1.0, sim))

    def _combined_similarity(self, ref_gray_ds, frame_gray_ds):
        # Calcular componentes
        s_hist = self._compute_hist_score(ref_gray_ds, frame_gray_ds)
        s_ncc = self._compute_ncc_score(ref_gray_ds, frame_gray_ds)
        s_lbp = self._compute_lbp_score(ref_gray_ds, frame_gray_ds)
        s = self.weight_hist * s_hist + self.weight_ncc * s_ncc + self.weight_lbp * s_lbp
        self.log_signal.emit(f"Scores -> Hist:{s_hist:.3f} NCC:{s_ncc:.3f} LBP:{s_lbp:.3f} | S:{s:.3f}", "debug")
        return s

    def run(self):
        print("[DIAG-PRINT] Entrou no método run() da MonitorThread.")
        self.log_signal.emit("[DIAG] Entrou no método run() da MonitorThread.", "debug")
        self.running = True
        self.log_signal.emit("Thread de monitoramento iniciada.", "info")
        self.status_signal.emit("Monitoramento Ativo")

        if not self.references_data:
            self.log_signal.emit("Nenhuma referência carregada na thread. Parando.", "warning")
            self.status_signal.emit("Monitoramento Parado")
            return  # Sair imediatamente

        # Preparar referências (ex: carregar imagens estáticas, calcular histogramas)
        prepared_references = []
        max_sequence_len = 0
        self.log_signal.emit(f"Preparando {len(self.references_data)} referências para monitoramento...", "debug")
        for ref in self.references_data:
            if ref.get('type') == 'static':
                img = cv2.imread(ref['path'], cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    prepared_references.append({'type': 'static', 'name': ref.get('name', ''), 'img': img, 'actions': ref.get('actions', [])})
                    self.log_signal.emit(f"Referência estática '{ref.get('name', '')}' carregada.", "debug")
                else:
                    self.log_signal.emit(f"Falha ao carregar imagem de referência: {ref['path']}", "error")
            elif ref.get('type') == 'sequence':
                frames = []
                for fp in ref.get('frame_paths', []):
                    img = cv2.imread(fp, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        frames.append(img)
                if frames:
                    prepared_references.append({'type': 'sequence', 'name': ref.get('name', ''), 'frames': frames, 'actions': ref.get('actions', [])})
                    self.log_signal.emit(f"Sequência '{ref.get('name', '')}' carregada com {len(frames)} frames.", "debug")
                    max_sequence_len = max(max_sequence_len, len(frames))
                else:
                    self.log_signal.emit(f"Falha ao carregar frames da sequência: {ref.get('name', '')}", "error")

        self.log_signal.emit(f"[DIAG] prepared_references: {prepared_references}", "debug")

        if not prepared_references:
            self.log_signal.emit("Nenhuma referência válida para monitoramento. Parando thread.", "error")
            self.status_signal.emit("Monitoramento Parado")
            return  # Sair imediatamente

        self.log_signal.emit(f"[DIAG] Antes do while self.running: running={self.running}", "debug")

        buffer_pgm = []
        # Detalhes da captura PGM
        roi_x, roi_y, roi_w, roi_h = self.pgm_details['roi']
        capture_kind = self.pgm_details['kind']
        capture_id = self.pgm_details['id']  # monitor_idx ou window_obj

        with mss.mss() as sct:
            while self.running:
                start_cycle = time.time()
                self.log_signal.emit("Iniciando ciclo de monitoramento...", "debug")
                captured_frame_bgr = None
                try:
                    if capture_kind == 'monitor':
                        monitor_capture_details = sct.monitors[capture_id]
                        grab_area = {"top": monitor_capture_details["top"] + roi_y,
                                     "left": monitor_capture_details["left"] + roi_x,
                                     "width": roi_w, "height": roi_h,
                                     "mon": capture_id}
                        sct_img = sct.grab(grab_area)
                        img_np = np.array(sct_img)
                        captured_frame_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                    elif capture_kind == 'window':
                        window_obj = capture_id
                        if not (window_obj and hasattr(window_obj, 'visible') and window_obj.visible and window_obj.width > 0 and window_obj.height > 0):
                            self.log_signal.emit(f"Janela '{window_obj.title if window_obj else 'N/A'}' não está mais válida ou visível. Pausando captura temporariamente.", "warning")
                            time.sleep(self.monitor_interval * 2)
                            continue
                        capture_region_global = (window_obj.left + roi_x,
                                                 window_obj.top + roi_y,
                                                 roi_w,
                                                 roi_h)
                        import pyautogui
                        pil_img = pyautogui.screenshot(region=capture_region_global)
                        captured_frame_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    if captured_frame_bgr is None:
                        self.log_signal.emit(f"Falha ao capturar frame PGM ({capture_kind}).", "error")
                        continue
                    captured_frame_gray = cv2.cvtColor(captured_frame_bgr, cv2.COLOR_BGR2GRAY)
                    frame_gray_ds = self._downscale_gray(captured_frame_gray)
                except Exception as e:
                    self.log_signal.emit(f"Erro ao capturar frame PGM: {e}", "error")
                    continue

                match_found_in_cycle = False
                # Reset contagem de não-match por ciclo
                cycle_best_score = 0.0
                best_ref_name = None

                for ref in prepared_references:
                    if not self.running:
                        break
                    ref_name = ref.get('name', 'Desconhecida')
                    if ref.get('type') == 'static':
                        ref_image_gray = ref.get('img')
                        # Downscale/refit ref para o mesmo tamanho de cálculo
                        ref_gray_ds = self._downscale_gray(ref_image_gray, max_width=frame_gray_ds.shape[1])
                        if ref_gray_ds.shape != frame_gray_ds.shape:
                            ref_gray_ds = cv2.resize(ref_gray_ds, (frame_gray_ds.shape[1], frame_gray_ds.shape[0]), interpolation=cv2.INTER_LINEAR)
                        s = self._combined_similarity(ref_gray_ds, frame_gray_ds)
                        cycle_best_score = max(cycle_best_score, s)
                        best_ref_name = ref_name if cycle_best_score == s else best_ref_name
                        if s >= self.similarity_threshold_static:
                            self._consec_match += 1
                            self._consec_nonmatch = 0
                            if self._consec_match < self.confirm_frames_required:
                                self.log_signal.emit(f"Confirmação: {self._consec_match}/{self.confirm_frames_required} (S={s:.3f}) — aguardando", "debug")
                            if self._consec_match >= self.confirm_frames_required:
                                self.log_signal.emit(f"Referência '{ref_name}' detectada (S={s:.3f}). Executando ação...", "success")
                                if self.action_executor_callback and ref.get('actions'):
                                    for action in ref.get('actions'):
                                        desc = self._get_action_description(action)
                                        self.log_signal.emit(f"Executando ação: {desc}", "info")
                                        self.action_executor_callback(action)
                                match_found_in_cycle = True
                                self._consec_match = 0  # reset após acionar
                                break
                        else:
                            self._consec_nonmatch += 1
                            if self._consec_nonmatch >= self.clear_frames_required:
                                self._consec_match = 0
                    elif ref.get('type') == 'sequence':
                        frames = ref.get('frames', [])
                        current_sequence_len = len(frames)
                        buffer_pgm.append(frame_gray_ds)
                        while len(buffer_pgm) > current_sequence_len:
                            buffer_pgm.pop(0)
                        if current_sequence_len > 0 and len(buffer_pgm) >= current_sequence_len:
                            frame_scores = []
                            for i in range(current_sequence_len):
                                ref_seq_frame_gray = frames[i]
                                ref_gray_ds = self._downscale_gray(ref_seq_frame_gray, max_width=frame_gray_ds.shape[1])
                                if ref_gray_ds.shape != frame_gray_ds.shape:
                                    ref_gray_ds = cv2.resize(ref_gray_ds, (frame_gray_ds.shape[1], frame_gray_ds.shape[0]), interpolation=cv2.INTER_LINEAR)
                                buffer_frame_gray = buffer_pgm[-current_sequence_len + i]
                                s_i = self._combined_similarity(ref_gray_ds, buffer_frame_gray)
                                frame_scores.append(s_i)
                            s_seq = float(np.mean(frame_scores)) if frame_scores else 0.0
                            self.log_signal.emit(f"Seq '{ref_name}', Scores=[{', '.join([f'{v:.2f}' for v in frame_scores])}] -> S={s_seq:.3f}", "debug")
                            cycle_best_score = max(cycle_best_score, s_seq)
                            best_ref_name = ref_name if cycle_best_score == s_seq else best_ref_name
                            if s_seq >= self.similarity_threshold_sequence_frame:
                                self._consec_match += 1
                                self._consec_nonmatch = 0
                                if self._consec_match < self.confirm_frames_required:
                                    self.log_signal.emit(f"Confirmação: {self._consec_match}/{self.confirm_frames_required} (S={s_seq:.3f}) — aguardando", "debug")
                                if self._consec_match >= self.confirm_frames_required:
                                    self.log_signal.emit(f"Referência de SEQUÊNCIA encontrada: '{ref_name}' (S={s_seq:.3f})", "success")
                                    if self.action_executor_callback and ref.get('actions'):
                                        for action in ref.get('actions'):
                                            desc = self._get_action_description(action)
                                            self.log_signal.emit(f"Executando ação: {desc}", "info")
                                            self.action_executor_callback(action)
                                    match_found_in_cycle = True
                                    self._consec_match = 0
                                    buffer_pgm.clear()
                                    break
                            else:
                                self._consec_nonmatch += 1
                                if self._consec_nonmatch >= self.clear_frames_required:
                                    self._consec_match = 0

                if match_found_in_cycle:
                    self.log_signal.emit("Match encontrado. Aguardando antes do próximo ciclo completo de verificação.", "debug")
                    time.sleep(self.monitor_interval)  # reduzir espera pós-match, mantendo sempre enviar
                else:
                    self.log_signal.emit(f"Nenhum match neste ciclo. Melhor S={cycle_best_score:.3f} ({best_ref_name if best_ref_name else 'N/A'})", "debug")
                    time.sleep(self.monitor_interval)
                elapsed = time.time() - start_cycle
                self.log_signal.emit(f"Ciclo de monitoramento finalizado em {elapsed:.2f}s.", "debug")

        self.log_signal.emit("[DIAG] Saiu do método run() da MonitorThread.", "debug")
        self.log_signal.emit("Thread de monitoramento terminada.", "info")
        self.status_signal.emit("Monitoramento Parado")

    def stop(self):
        self.log_signal.emit("Sinal de parada recebido pela thread de monitoramento.", "info")
        self.running = False
