"""
NSFWDetector v11 — Engine ONNX Custom Limpa (YOLOv8 Medium 640m)
[MULTI-PROCESS ARCHITECTURE]

Arquitetura:
  detect_fast()      → Fase 1 síncrona (1 inferência GPU via IPC)
  detect_deep_async()→ Fase 2 background (quadrantes via IPC)

Princípios v11 (Worker-based):
  - Isola o onnxruntime-directml em um processo dedicado para evitar
    conflitos letais (DLL Hell) de MSVC com PyQt5 e numpy do processo principal.
  - Thresholds alinhados ao NudeNet original (YOLO ≥ 0.20, NMS 0.25)
  - Zero falso positivo > recall perfeito
"""
import cv2
import numpy as np
import threading
import os
import sys
import subprocess
import json
import base64
import atexit


class NSFWDetector:

    LABELS = [
        "FEMALE_GENITALIA_COVERED", "FACE_FEMALE", "BUTTOCKS_EXPOSED",
        "FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED", "MALE_BREAST_EXPOSED",
        "ANUS_EXPOSED", "FEET_EXPOSED", "BELLY_COVERED", "FEET_COVERED",
        "ARMPITS_COVERED", "ARMPITS_EXPOSED", "FACE_MALE", "BELLY_EXPOSED",
        "MALE_GENITALIA_EXPOSED", "ANUS_COVERED", "FEMALE_BREAST_COVERED",
        "BUTTOCKS_COVERED"
    ]

    # Somente partes VERDADEIRAMENTE explícitas. Nada de "covered" ou "buttocks".
    EXPLICIT_PARTS = {
        'MALE_GENITALIA_EXPOSED',
        'FEMALE_GENITALIA_EXPOSED',
        'FEMALE_BREAST_EXPOSED',
        'ANUS_EXPOSED',
    }

    # Confiança mínima por categoria (defaults)
    DEFAULT_MIN_CONFIDENCE = {
        'FEMALE_BREAST_EXPOSED': 0.60,
        'ANUS_EXPOSED': 0.40,
    }

    DEFAULT_GENERAL_THRESHOLD = 0.55

    def __init__(self, log_callback=None):
        self.enabled = False
        self._deep_lock = threading.Lock()
        self.log_callback = log_callback

        # Configurable thresholds (can be changed at runtime)
        self.general_threshold = self.DEFAULT_GENERAL_THRESHOLD
        self.category_min_confidence = dict(self.DEFAULT_MIN_CONFIDENCE)

        # Multi-process handling
        self.worker_process = None

        # Ensure cleanup on main process exit
        atexit.register(self.cleanup)

    def set_thresholds(self, general_threshold: float, min_confidence: dict):
        """Atualiza os limiares de detecção em runtime."""
        self.general_threshold = general_threshold
        self.category_min_confidence = dict(min_confidence)

    def initialize(self):
        try:
            # Buscar modelo em múltiplos locais (dev vs PyInstaller)
            model_path = None
            search_paths = []

            # 1. PyInstaller: sys._MEIPASS aponta para _internal/
            if hasattr(sys, '_MEIPASS'):
                search_paths.append(os.path.join(sys._MEIPASS, 'nudenet', '640m.onnx'))

            # 2. Caminho Local do Desenvolvimento Relativo à Raiz
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            search_paths.append(os.path.join(project_root, 'nudenet', '640m.onnx'))

            # 3. Fallbacks globais da VENV ou outras instalações
            try:
                import importlib.util
                spec = importlib.util.find_spec('nudenet')
                if spec and spec.submodule_search_locations:
                    _nn_dir = spec.submodule_search_locations[0]
                    search_paths.append(os.path.join(_nn_dir, '640m.onnx'))
            except Exception:
                pass

            for p in search_paths:
                if os.path.exists(p):
                    model_path = p
                    break

            if not model_path:
                if self.log_callback:
                    self.log_callback(f"[NSFWDetector v11] ERRO: 640m.onnx não encontrado! Buscou em: {search_paths}", "error")
                return False

            # Launch Isolated Subprocess Worker
            try:
                # Handle noconsole mode in PyInstaller
                startupinfo = None
                creationflags = 0
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    creationflags = subprocess.CREATE_NO_WINDOW

                if getattr(sys, 'frozen', False):
                    worker_cmd = [sys.executable, "--nsfw-worker"]
                else:
                    worker_cmd = [sys.executable, "main.py", "--nsfw-worker"]

                self.worker_process = subprocess.Popen(
                    worker_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout so it's read
                    text=True,
                    bufsize=1,  # Line buffered
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
                
                # Command: load
                self._send_command({"cmd": "load", "model_path": model_path})
                resp = self._recv_response()
                
                if not resp or not resp.get("ok"):
                    err = resp.get("error", "Unknown error") if resp else "Empty response"
                    if self.log_callback:
                        trace = resp.get("trace", "") if resp else ""
                        self.log_callback(f"[NSFWDetector v11] ERRO fatal ao carregar sessão ONNX no Worker:\n{err}\n{trace}", "error")
                    self.cleanup()
                    self.worker_process = None
                    self.enabled = False
                    return False
                
                self.enabled = True
                active = resp.get("providers", [])[0] if resp.get("providers") else "Unknown"
                hw = "GPU (CUDA)" if "CUDA" in active else ("GPU (DirectML)" if "Dml" in active else f"CPU ({active})")
                if self.log_callback:
                    self.log_callback(f"[NSFWDetector v11] 640m Medium | {hw} | {model_path} [Subprocess Mode]", "success")
                return True

            except Exception:
                self.enabled = False
                if self.log_callback:
                    import traceback
                    err_trace = traceback.format_exc()
                    self.log_callback(f"[NSFWDetector v11] ERRO fatal ao iniciar processo worker:\n{err_trace}", "error")
                return False

        except Exception as e:
            if self.log_callback:
                self.log_callback(f"[NSFWDetector v11] Falha crassa na inicialização: {e}", "error")
            return False

    def _send_command(self, obj: dict):
        if self.worker_process and self.worker_process.poll() is None:
            self.worker_process.stdin.write(json.dumps(obj) + "\n")
            self.worker_process.stdin.flush()
        else:
            raise RuntimeError("Worker process is dead.")

    def _recv_response(self, timeout=5.0) -> dict:
        if not self.worker_process or self.worker_process.poll() is not None:
            return {}

        result = [None]

        def _read():
            try:
                for line in iter(self.worker_process.stdout.readline, ""):
                    line = line.strip()
                    if not line:
                        continue
                    # Intercept debug prints from the worker
                    if line.startswith("[Worker]"):
                        if self.log_callback:
                            self.log_callback(line, "debug")
                        continue
                    # Ignorar outros logs de warning (como do ONNX) que não são JSON
                    if line.startswith('{') and line.endswith('}'):
                        result[0] = line
                        break
                    # Any other line is an unhandled log, just print it for now
                    elif line:
                        print(f"[NSFW Worker LOG] {line}")
            except Exception:
                pass

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout)

        if t.is_alive():
            if self.log_callback:
                self.log_callback(f"[NSFWDetector IPC] TRÁGICO: Worker demorou mais de {timeout}s para responder (Timeout/Lock).", "error")
            return {}

        line = result[0]
        if not line:
            return {}
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            if self.log_callback:
                self.log_callback(f"[NSFWDetector IPC] Erro de JSONDecode no Worker. Resposta: {line}", "error")
            return {}

    def cleanup(self):
        if hasattr(self, 'worker_process') and self.worker_process:
            try:
                self.worker_process.terminate()
            except Exception:
                pass

    # ================================================================
    # IPC Infer
    # ================================================================

    def _infer_raw(self, img_bgr, resolution=640):
        with self._deep_lock:
            # Compress to JPG to send fast over pipes
            success, encoded_img = cv2.imencode('.jpg', img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            if not success:
                return []

            img_b64 = base64.b64encode(encoded_img.tobytes()).decode('utf-8')

            try:
                self._send_command({"cmd": "infer", "image_b64": img_b64, "resolution": resolution})
                resp = self._recv_response()
                if resp and resp.get("ok"):
                    return resp.get("detections", [])
                else:
                    err = resp.get("error", "Unknown error") if resp else "Empty response"
                    if self.log_callback:
                        self.log_callback(f"[NSFWDetector IPC] Worker infer failed: {err}", "error")
                    return []
            except Exception:
                if self.log_callback:
                    self.log_callback("[NSFWDetector IPC] Communication error.", "error")
                return []

    # ================================================================
    # Scoring
    # ================================================================

    def _score(self, detections):
        best = 0.0
        parts = {}
        for det in detections:
            label = det.get('class')
            conf = det.get('score', 0)
            if label in self.EXPLICIT_PARTS:
                min_conf = self.category_min_confidence.get(label, 0.0)
                if conf >= min_conf:
                    best = max(best, conf)
                    parts[label] = round(conf, 3)
        return best, parts

    def _auto_crop(self, img_bgr):
        """Remove bordas pretas (letterbox) do PGM."""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
        coords = cv2.findNonZero(mask)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            total = img_bgr.shape[0] * img_bgr.shape[1]
            region = w * h
            if 0.15 * total < region < 0.95 * total:
                return img_bgr[y:y + h, x:x + w]
        return img_bgr

    def _quadrants(self, img):
        h, w = img.shape[:2]
        qh, qw = int(h * 0.6), int(w * 0.6)
        if qh < 50 or qw < 50:
            return []
        ch, cw = h // 2, w // 2
        return [
            img[ch - qh // 2:ch + qh // 2, cw - qw // 2:cw + qw // 2],
            img[h - qh:h, 0:qw],
            img[h - qh:h, w - qw:w],
            img[0:qh, 0:qw],
            img[0:qh, w - qw:w],
        ]

    # ================================================================
    # Fase 1: Rápida (síncrona, ~30ms na GPU)
    # ================================================================

    def detect_fast(self, img_bgr, threshold=None):
        if threshold is None:
            threshold = self.general_threshold
        if not self.enabled or self.worker_process is None:
            return {'is_nsfw': False, 'score': 0.0, 'details': {}}

        if not np.any(img_bgr) or img_bgr.sum() == 0:
            if getattr(self, 'log_callback', None):
                self.log_callback(
                    "[NSFWDetector v11] AVISO: A imagem capturada está TODA PRETA!",
                    "warning"
                )
            return {'is_nsfw': False, 'score': 0.0, 'details': {}}

        try:
            # Uma única inferência no frame completo via IPC
            preds = self._infer_raw(img_bgr, resolution=416)  # [OPT-2] Fast scan at 416
            score, parts = self._score(preds)

            return {
                'is_nsfw': score >= threshold,
                'score': round(score, 3),
                'details': {'parts': parts, 'phase': 1},
            }
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            if getattr(self, 'log_callback', None):
                self.log_callback(f"[NSFWDetector v11] Erro na inferência rápida via IPC: {e}\n{err_msg}", "error")
            return {'is_nsfw': False, 'score': 0.0, 'details': {}}

    # ================================================================
    # Fase 2: Profunda (assíncrona, background thread)
    # ================================================================

    def detect_deep_async(self, img_bgr, callback, threshold=None):
        if threshold is None:
            threshold = self.general_threshold
        if not self.enabled or self.worker_process is None:
            return

        if hasattr(self, '_deep_thread') and self._deep_thread is not None and self._deep_thread.is_alive():
            return

        frame_copy = img_bgr.copy()

        def _deep_scan():
            try:
                cropped = self._auto_crop(frame_copy)
                best_score, best_parts = 0.0, {}

                # Quadrantes (zoom em partes do frame)
                for quad in self._quadrants(cropped):
                    preds = self._infer_raw(quad)
                    s, p = self._score(preds)
                    if s > best_score:
                        best_score, best_parts = s, p

                    if best_score >= threshold:
                        callback({
                            'is_nsfw': True,
                            'score': round(best_score, 3),
                            'details': {'parts': best_parts, 'phase': 2}
                        })
                        return

            except Exception:
                pass

        self._deep_thread = threading.Thread(target=_deep_scan, daemon=True)
        self._deep_thread.start()

    # ================================================================
    # Detecção completa (síncrona, para testes)
    # ================================================================

    def detect(self, img_bgr, threshold=None):
        if threshold is None:
            threshold = self.general_threshold
        r1 = self.detect_fast(img_bgr, threshold)
        if r1['is_nsfw']:
            return r1

        score = r1['score']
        parts = r1['details'].get('parts', {})
        cropped = self._auto_crop(img_bgr)

        # Quadrantes
        for quad in self._quadrants(cropped):
            preds = self._infer_raw(quad)
            s, p = self._score(preds)
            if s > score:
                score, parts = s, p
            if score >= threshold:
                break

        return {
            'is_nsfw': score >= threshold,
            'score': round(score, 3),
            'details': {'parts': parts, 'phase': 2}
        }
