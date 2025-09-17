#!/usr/bin/env python3
"""
TESTE SIMPLES NDI - Replica exatamente o que funcionou
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2

def simple_ndi_test():
    """Teste simples que replica exatamente o que funcionou"""
    print("🎯 TESTE SIMPLES NDI")
    print("=" * 40)
    print("📺 Replicando condições que funcionaram...")
    
    # Aguardar 10 segundos primeiro (para garantir recursos livres)
    print("⏰ Aguardando 10 segundos para liberar recursos...")
    time.sleep(10)
    
    try:
        print("🔧 Inicializando NDI...")
        if not NDI.initialize():
            print("❌ Falha na inicialização")
            return False
        
        print("✅ NDI inicializado")
        
        # Aguardar mais tempo para descoberta
        print("⏰ Aguardando descoberta (3s)...")
        time.sleep(3)
        
        # Criar finder
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Falha ao criar finder")
            NDI.destroy()
            return False
        
        print("✅ Finder criado")
        
        # Aguardar descoberta
        print("⏰ Descobrindo fontes (2s)...")
        time.sleep(2)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources:
            print("❌ Nenhuma fonte encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False
        
        print(f"📡 {len(sources)} fontes encontradas:")
        for i, source in enumerate(sources):
            print(f"   {i}: {source.ndi_name}")
        
        # Usar a fonte que funcionou: NVIDIA GeForce GTX 1660 SUPER 1
        target_source = None
        for source in sources:
            if "NVIDIA GeForce GTX 1660 SUPER 1" in source.ndi_name:
                target_source = source
                print(f"✅ Fonte alvo encontrada: {source.ndi_name}")
                break
        
        NDI.find_destroy(ndi_find)
        
        if not target_source:
            print("❌ Fonte NVIDIA GTX 1660 SUPER 1 não encontrada")
            NDI.destroy()
            return False
        
        # Usar EXATAMENTE a mesma configuração que funcionou
        print("🔧 Criando receiver com configuração que funcionou...")
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = target_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        if not ndi_recv:
            print("❌ Falha ao criar receiver")
            NDI.destroy()
            return False
        
        print("✅ Receiver criado")
        
        # Aguardar conexão (mais tempo)
        print("⏰ Aguardando conexão estabilizar (5s)...")
        time.sleep(5)
        
        # Tentar capturar com paciência
        print("🎯 Iniciando captura com paciência...")
        max_attempts = 100
        timeout_ms = 1000  # 1 segundo por tentativa
        
        for attempt in range(max_attempts):
            try:
                result = NDI.recv_capture_v2(ndi_recv, timeout_ms)
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    print(f"🎉 FRAME ENCONTRADO na tentativa {attempt + 1}!")
                    print(f"📺 Resolução: {video_frame.xres}x{video_frame.yres}")
                    
                    if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                        frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                        expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                        
                        if len(frame_data) >= expected_size:
                            frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                            frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                            
                            if frame_bgr.size > 0:
                                print(f"✅ SUCESSO! Frame: {frame_bgr.shape}")
                                
                                # Salvar frame
                                cv2.imwrite('ndi_simple_success.png', frame_bgr)
                                print(f"💾 Frame salvo: ndi_simple_success.png")
                                
                                NDI.recv_free_video_v2(ndi_recv, video_frame)
                                NDI.recv_destroy(ndi_recv)
                                NDI.destroy()
                                
                                return True
                    
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
                # Progress a cada 10 tentativas
                if (attempt + 1) % 10 == 0:
                    print(f"   🔄 Tentativa {attempt + 1}/{max_attempts}")
                
            except Exception as e:
                print(f"❌ Erro na tentativa {attempt + 1}: {e}")
                continue
        
        print(f"⏰ Todas as {max_attempts} tentativas esgotadas")
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        return False
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        try:
            NDI.destroy()
        except:
            pass
        return False

def main():
    print("🎯 TESTE SIMPLES NDI - REPLICANDO SUCESSO")
    print("=" * 50)
    print("📋 Baseado na captura que funcionou antes")
    print("🎮 Fonte: NVIDIA GeForce GTX 1660 SUPER 1")
    print("=" * 50)
    
    success = simple_ndi_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCESSO! NDI funcionou!")
        print("✅ Frame capturado e salvo")
        print("💡 Agora podemos usar no SwitchPilot!")
    else:
        print("❌ Ainda não funcionou")
        print("💡 Sugestões:")
        print("   1. Aguardar mais 30 segundos")
        print("   2. Fechar Studio Monitor")
        print("   3. Tentar novamente")
    print("=" * 50)

if __name__ == "__main__":
    main() 