#!/usr/bin/env python3
"""
Teste específico da captura NDI como implementada no SwitchPilot
Simula exatamente o processo que está falhando
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2

def test_switchpilot_ndi_capture():
    """Testa a captura NDI exatamente como o SwitchPilot faz"""
    print("🔍 TESTE CAPTURA NDI SWITCHPILOT")
    print("=" * 50)
    
    # Simular os dados que o SwitchPilot está usando
    ndi_source_data = {
        'ndi_name': 'DESKTOP-F9GHF2T (Test Pattern)',
        'url_address': '172.20.80.1:5963'
    }
    
    try:
        source_name = ndi_source_data.get('ndi_name', 'Fonte Desconhecida')
        print(f"[DEBUG] Tentando capturar fonte: {source_name}")
        
        # Inicializar NDI
        if not NDI.initialize():
            print("Erro: NDI não pode ser inicializado")
            return None
        
        print("[DEBUG] NDI inicializado")
        
        # Descobrir fontes NDI novamente para obter o objeto correto
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("Erro: Não foi possível criar NDI finder")
            NDI.destroy()
            return None
        
        print("[DEBUG] NDI finder criado")
        
        # Aguardar descoberta
        print("[DEBUG] Aguardando descoberta de fontes...")
        time.sleep(2)  # Aumentei para 2 segundos
        
        # Obter fontes
        sources = NDI.find_get_current_sources(ndi_find)
        print(f"[DEBUG] Fontes encontradas: {len(sources) if sources else 0}")
        
        if sources:
            for i, source in enumerate(sources):
                print(f"[DEBUG] Fonte {i}: {getattr(source, 'ndi_name', 'Sem nome')}")
        
        target_source = None
        
        for source in sources:
            if source.ndi_name == source_name:
                target_source = source
                print(f"[DEBUG] Fonte alvo encontrada: {source.ndi_name}")
                break
        
        NDI.find_destroy(ndi_find)
        
        if not target_source:
            print(f"[DEBUG] Fonte {source_name} não encontrada")
            NDI.destroy()
            return None
        
        print("[DEBUG] Criando configuração do receiver...")
        
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
        
        print("[DEBUG] NDI receiver criado")
        
        # Aguardar e capturar frame
        timeout_seconds = 20  # Aumentei o timeout
        start_time = time.time()
        print(f"[DEBUG] Iniciando captura NDI, timeout: {timeout_seconds}s")
        
        frames_attempted = 0
        
        while (time.time() - start_time) < timeout_seconds:
            try:
                # A função recv_capture_v2 retorna uma tupla
                result = NDI.recv_capture_v2(ndi_recv, 200)  # Aumentei o timeout da captura
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                frames_attempted += 1
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    print(f"[DEBUG] Frame de vídeo recebido: {video_frame.xres}x{video_frame.yres}")
                    
                    # Verificar se os dados do frame são válidos
                    if video_frame.data is None or len(video_frame.data) == 0:
                        print(f"[DEBUG] Frame sem dados, continuando...")
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        continue
                    
                    print(f"[DEBUG] Frame tem dados: {len(video_frame.data)} bytes")
                    
                    # Converter frame NDI para numpy array
                    frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                    
                    # Verificar se o tamanho dos dados é consistente
                    expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                    print(f"[DEBUG] Dados esperados: {expected_size}, recebidos: {len(frame_data)}")
                    
                    if len(frame_data) < expected_size:
                        print(f"[DEBUG] Dados insuficientes, continuando...")
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        continue
                    
                    print(f"[DEBUG] Convertendo frame...")
                    frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                    
                    # Converter BGRX para BGR (remover canal alpha)
                    frame_bgr = frame_data[:, :video_frame.xres, :3].copy()  # Fazer cópia para garantir continuidade
                    
                    # Verificar se o frame resultante é válido
                    if frame_bgr.size == 0:
                        print(f"[DEBUG] Frame convertido está vazio, continuando...")
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        continue
                    
                    print(f"[DEBUG] Frame NDI capturado com sucesso: {frame_bgr.shape}")
                    
                    # Salvar frame para verificação
                    cv2.imwrite('switchpilot_ndi_test.png', frame_bgr)
                    print(f"[DEBUG] Frame salvo como switchpilot_ndi_test.png")
                    
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
                else:
                    print(f"[DEBUG] Frame tipo desconhecido: {frame_type}")
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.01)
                
            except Exception as inner_e:
                print(f"[DEBUG] Erro interno na captura NDI: {inner_e}")
                import traceback
                traceback.print_exc()
                break
        
        # Timeout - não conseguiu capturar frame
        print(f"[DEBUG] Timeout de {timeout_seconds}s atingido sem capturar frame válido")
        print(f"[DEBUG] Tentativas de frame: {frames_attempted}")
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        return None
        
    except Exception as e:
        print(f"Erro ao capturar frame NDI: {e}")
        import traceback
        traceback.print_exc()
        try:
            NDI.destroy()
        except:
            pass
        return None

def main():
    print("🎯 TESTE ESPECÍFICO DA CAPTURA NDI DO SWITCHPILOT")
    print("=" * 60)
    
    result = test_switchpilot_ndi_capture()
    
    print("\n" + "=" * 60)
    if result is not None:
        print("✅ SUCESSO! NDI captura está funcionando no SwitchPilot")
        print(f"📺 Frame capturado: {result.shape}")
        print("💾 Frame salvo como: switchpilot_ndi_test.png")
    else:
        print("❌ FALHA! NDI captura não está funcionando no SwitchPilot")
        print("🔍 Verificar logs acima para identificar o problema")
    print("=" * 60)

if __name__ == "__main__":
    main() 