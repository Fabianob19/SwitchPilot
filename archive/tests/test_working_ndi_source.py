#!/usr/bin/env python3
"""
Teste da fonte NDI que está funcionando
NVIDIA GeForce GTX 1660 SUPER 1
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2

def test_working_ndi_source():
    """Testa especificamente a fonte que está funcionando"""
    print("🎯 TESTE DA FONTE NDI FUNCIONANDO")
    print("=" * 50)
    
    # Fonte que está funcionando conforme os logs
    working_source_name = 'DESKTOP-F9GHF2T (NVIDIA GeForce GTX 1660 SUPER 1)'
    
    try:
        print(f"[DEBUG] Testando fonte funcionando: {working_source_name}")
        
        if not NDI.initialize():
            print("❌ NDI não pode ser inicializado")
            return False
        
        print("✅ NDI inicializado")
        
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Não foi possível criar NDI finder")
            NDI.destroy()
            return False
        
        print("✅ NDI finder criado")
        time.sleep(2)
        
        sources = NDI.find_get_current_sources(ndi_find)
        print(f"📡 Fontes encontradas: {len(sources) if sources else 0}")
        
        working_source = None
        for source in sources:
            source_name = getattr(source, 'ndi_name', '')
            print(f"   - {source_name}")
            if source_name == working_source_name:
                working_source = source
                print(f"✅ Fonte funcionando encontrada!")
                break
        
        NDI.find_destroy(ndi_find)
        
        if not working_source:
            print(f"❌ Fonte {working_source_name} não encontrada")
            NDI.destroy()
            return False
        
        print("🔧 Configurando receiver...")
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = working_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        if not ndi_recv:
            print("❌ Não foi possível criar receiver")
            NDI.destroy()
            return False
        
        print("✅ Receiver criado")
        print("⏳ Aguardando frames...")
        
        timeout = 10
        start_time = time.time()
        frames_received = 0
        
        while (time.time() - start_time) < timeout:
            try:
                result = NDI.recv_capture_v2(ndi_recv, 200)
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    frames_received += 1
                    print(f"📺 Frame {frames_received}: {video_frame.xres}x{video_frame.yres}")
                    
                    if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                        frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                        expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                        
                        if len(frame_data) >= expected_size:
                            frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                            frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                            
                            if frame_bgr.size > 0:
                                print(f"✅ Frame convertido: {frame_bgr.shape}")
                                
                                # Salvar primeiro frame
                                if frames_received == 1:
                                    cv2.imwrite('working_ndi_source.png', frame_bgr)
                                    print(f"💾 Frame salvo: working_ndi_source.png")
                                
                                NDI.recv_free_video_v2(ndi_recv, video_frame)
                                
                                # Se conseguiu 3 frames, é sucesso
                                if frames_received >= 3:
                                    break
                        
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Erro: {e}")
                break
        
        print(f"📊 Total de frames capturados: {frames_received}")
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        return frames_received > 0
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        try:
            NDI.destroy()
        except:
            pass
        return False

def main():
    print("🎯 TESTE DA FONTE NDI QUE ESTÁ FUNCIONANDO")
    print("=" * 60)
    print("📺 NVIDIA GeForce GTX 1660 SUPER 1")
    print("=" * 60)
    
    success = test_working_ndi_source()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCESSO! A fonte NDI está funcionando consistentemente!")
        print("💡 Recomendação: Use esta fonte para seus testes")
        print("📋 Configuração recomendada:")
        print("   - Fonte: NVIDIA GeForce GTX 1660 SUPER 1")
        print("   - Aguarde 2-3 segundos entre tentativas")
        print("   - Evite testar múltiplas fontes rapidamente")
    else:
        print("❌ A fonte não está funcionando no momento")
        print("💡 Tente novamente em alguns segundos")
    print("=" * 60)

if __name__ == "__main__":
    main() 