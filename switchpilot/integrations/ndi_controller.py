#!/usr/bin/env python3
"""
NDI Controller para SwitchPilot
Controlador para captura de fontes NDI com tratamento correto de arrays NumPy
"""

import sys
import os
import time
import numpy as np
import cv2
import logging
from typing import Optional, Tuple, List, Dict, Any

try:
    import NDIlib as NDI
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    NDI = None


class NDIController:
    """Controlador para captura de fontes NDI"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ndi_initialized = False
        self.ndi_find = None
        self.ndi_recv = None
        self.current_source = None
        self.is_capturing = False

        # Configurações padrão
        self.default_timeout = 1000  # ms
        self.connection_timeout = 5.0  # segundos

    def initialize(self) -> bool:
        """Inicializa o NDI"""
        if not NDI_AVAILABLE:
            self.logger.error("NDI não está disponível. Instale o NDI SDK e python-ndi")
            return False

        try:
            if not NDI.initialize():
                self.logger.error("Falha ao inicializar NDI")
                return False

            self.ndi_initialized = True
            self.logger.info("NDI inicializado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao inicializar NDI: {e}")
            return False

    def get_sources(self) -> List[Dict[str, str]]:
        """Obtém lista de fontes NDI disponíveis"""
        if not self.ndi_initialized:
            if not self.initialize():
                return []

        try:
            # Criar finder se não existir
            if not self.ndi_find:
                self.ndi_find = NDI.find_create_v2()
                if not self.ndi_find:
                    self.logger.error("Não foi possível criar NDI finder")
                    return []

                # Aguardar descoberta
                time.sleep(2)

            sources = NDI.find_get_current_sources(self.ndi_find)

            if not sources:
                self.logger.warning("Nenhuma fonte NDI encontrada")
                return []

            # Converter para formato mais amigável
            source_list = []
            for i, source in enumerate(sources):
                source_info = {
                    'id': i,
                    'name': getattr(source, 'ndi_name', f'Fonte NDI {i+1}'),
                    'url': getattr(source, 'url_address', ''),
                    'source_obj': source
                }
                source_list.append(source_info)

            self.logger.info(f"Encontradas {len(source_list)} fontes NDI")
            return source_list

        except Exception as e:
            self.logger.error(f"Erro ao obter fontes NDI: {e}")
            return []

    def connect_to_source(self, source_name: str) -> bool:
        """Conecta a uma fonte NDI específica"""
        try:
            sources = self.get_sources()

            # Procurar fonte por nome
            target_source = None
            for source in sources:
                if source['name'] == source_name:
                    target_source = source['source_obj']
                    self.current_source = source
                    break

            if not target_source:
                self.logger.error(f"Fonte NDI '{source_name}' não encontrada")
                return False

            # Fechar receiver anterior se existir
            if self.ndi_recv:
                self.disconnect()

            # Configurar receiver
            recv_create = NDI.RecvCreateV3()
            recv_create.source_to_connect_to = target_source
            recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
            recv_create.allow_video_fields = True

            self.ndi_recv = NDI.recv_create_v3(recv_create)

            if not self.ndi_recv:
                self.logger.error(f"Não foi possível criar receiver para '{source_name}'")
                return False

            # Aguardar conexão estabilizar
            time.sleep(self.connection_timeout)

            self.logger.info(f"Conectado à fonte NDI: {source_name}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao conectar à fonte NDI '{source_name}': {e}")
            return False

    def capture_frame(self, timeout_ms: int = None) -> Optional[np.ndarray]:
        """Captura um frame da fonte NDI atual"""
        if not self.ndi_recv:
            self.logger.error("Nenhuma fonte NDI conectada")
            return None

        if timeout_ms is None:
            timeout_ms = self.default_timeout

        # Tentar várias vezes para garantir captura
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                result = NDI.recv_capture_v2(self.ndi_recv, timeout_ms)
                frame_type, video_frame, audio_frame, metadata_frame = result

                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    try:
                        # Converter frame NDI para numpy array
                        frame_bgr = self._convert_ndi_frame_to_bgr(video_frame)

                        # Liberar frame NDI
                        NDI.recv_free_video_v2(self.ndi_recv, video_frame)

                        if frame_bgr is not None:
                            return frame_bgr

                    except Exception as conv_e:
                        self.logger.error(f"Erro na conversão do frame NDI: {conv_e}")
                        NDI.recv_free_video_v2(self.ndi_recv, video_frame)

                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(self.ndi_recv, audio_frame)

                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(self.ndi_recv, metadata_frame)

                # Se não conseguiu frame de vídeo, tentar novamente
                if attempt < max_attempts - 1:
                    time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Erro na captura NDI (tentativa {attempt+1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(0.1)

        # Não conseguiu capturar frame válido
        return None

    def _convert_ndi_frame_to_bgr(self, video_frame) -> Optional[np.ndarray]:
        """Converte frame NDI para formato BGR (OpenCV)"""
        try:
            # CORREÇÃO: Verificar se há dados sem usar 'and' com arrays NumPy
            if not hasattr(video_frame, 'data') or video_frame.data is None:
                self.logger.warning("Frame NDI sem dados")
                return None

            # Verificar tamanho separadamente
            if len(video_frame.data) == 0:
                self.logger.warning("Frame NDI com dados vazios")
                return None

            # Converter dados para numpy array
            frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
            expected_size = video_frame.yres * video_frame.line_stride_in_bytes

            if len(frame_data) < expected_size:
                self.logger.warning(f"Dados insuficientes: {len(frame_data)} < {expected_size}")
                return None

            # Reshape para imagem
            # NDI usa BGRA (4 canais) com line stride
            bytes_per_pixel = 4
            pixels_per_line = video_frame.line_stride_in_bytes // bytes_per_pixel

            frame_data = frame_data.reshape((video_frame.yres, pixels_per_line, bytes_per_pixel))

            # Extrair apenas a região válida da imagem (remover padding)
            frame_bgra = frame_data[:, :video_frame.xres, :]

            # Converter BGRA para BGR (remover canal alpha)
            frame_bgr = frame_bgra[:, :, :3].copy()

            # Verificar se o frame não está vazio (correção do bug de comparação)
            if frame_bgr.size == 0:
                self.logger.warning("Frame convertido está vazio")
                return None

            # Verificar se não é um frame completamente preto (usar any() corretamente)
            mean_values = np.mean(frame_bgr, axis=(0, 1))
            if not np.any(mean_values > 5):  # Correção: usar np.any() em vez de comparação direta
                self.logger.debug("Frame parece estar muito escuro")

            return frame_bgr

        except Exception as e:
            self.logger.error(f"Erro na conversão do frame: {e}")
            return None

    def start_capture(self) -> bool:
        """Inicia captura contínua"""
        if not self.ndi_recv:
            self.logger.error("Nenhuma fonte NDI conectada")
            return False

        self.is_capturing = True
        self.logger.info("Captura NDI iniciada")
        return True

    def stop_capture(self):
        """Para captura contínua"""
        self.is_capturing = False
        self.logger.info("Captura NDI parada")

    def disconnect(self):
        """Desconecta da fonte NDI atual"""
        try:
            if self.ndi_recv:
                NDI.recv_destroy(self.ndi_recv)
                self.ndi_recv = None
                self.logger.info("Desconectado da fonte NDI")

            self.current_source = None
            self.is_capturing = False

        except Exception as e:
            self.logger.error(f"Erro ao desconectar NDI: {e}")

    def cleanup(self):
        """Limpa recursos NDI"""
        try:
            self.disconnect()

            if self.ndi_find:
                NDI.find_destroy(self.ndi_find)
                self.ndi_find = None

            if self.ndi_initialized:
                NDI.destroy()
                self.ndi_initialized = False
                self.logger.info("NDI finalizado")

        except Exception as e:
            self.logger.error(f"Erro na limpeza NDI: {e}")

    def __del__(self):
        """Destrutor - garante limpeza dos recursos"""
        self.cleanup()

    def get_source_info(self) -> Optional[Dict[str, Any]]:
        """Retorna informações da fonte atual"""
        if not self.current_source:
            return None

        return {
            'name': self.current_source['name'],
            'url': self.current_source['url'],
            'connected': self.ndi_recv is not None,
            'capturing': self.is_capturing
        }

    def is_available(self) -> bool:
        """Verifica se NDI está disponível"""
        return NDI_AVAILABLE and self.ndi_initialized

    def test_connection(self, source_name: str, timeout_seconds: int = 10) -> bool:
        """Testa conexão com uma fonte NDI"""
        try:
            if not self.connect_to_source(source_name):
                return False

            # Tentar capturar alguns frames
            start_time = time.time()
            frames_captured = 0

            while (time.time() - start_time) < timeout_seconds:
                frame = self.capture_frame(500)  # 500ms timeout
                if frame is not None:
                    frames_captured += 1
                    if frames_captured >= 3:  # 3 frames é suficiente para teste
                        self.logger.info(f"Teste de conexão NDI bem-sucedido: {frames_captured} frames")
                        return True

                time.sleep(0.1)

            self.logger.warning(f"Teste de conexão NDI falhou: apenas {frames_captured} frames em {timeout_seconds}s")
            return False

        except Exception as e:
            self.logger.error(f"Erro no teste de conexão NDI: {e}")
            return False
        finally:
            self.disconnect()
