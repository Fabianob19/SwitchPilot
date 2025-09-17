#!/usr/bin/env python3
"""
TESTE NDI ISOLADO - Sem interferências
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2

def test_isolated():
    """Teste isolado sem interferências"""
    
    print("⚠️  INSTRUÇÕES IMPORTANTES:")
    print("=" * 40)
    print("1. FECHE Studio Monitor COMPLETAMENTE")
    print("2. FECHE qualquer software NDI ativo")
    print("3. AGUARDE 10 segundos")
    print("4. Pressione ENTER para continuar...")
    print("=" * 40)
    
    input("👆 Pressione ENTER quando pronto...")
    
    print("\n🎯 Iniciando teste isolado...")
    
    if not NDI.initialize():
        print("❌ Falha na inicialização")
        return False
    
    print("✅ NDI inicializado em ambiente isolado")
    
    ndi_find = NDI.find_create_v2()
    time.sleep(3)
    sources = NDI.find_get_current_sources(ndi_find)
    
    if not sources:
        print("❌ Nenhuma fonte (esperado se tudo fechado)")
        NDI.find_destroy(ndi_find)
        NDI.destroy()
        return False
    
    print(f"📡 {len(sources)} fontes encontradas:")
    for i, s in enumerate(sources):
        print(f"   {i}: {s.ndi_name}")
    
    # Testar a fonte que funcionou antes
    nvidia_source = None
    for source in sources:
        if "NVIDIA GeForce GTX 1660 SUPER 1" in source.ndi_name:
            nvidia_source = source
            break
    
    if not nvidia_source:
        print("⚠️ Fonte NVIDIA GTX 1660 SUPER 1 não encontrada")
        print("🔄 Usando primeira fonte disponível...")
        nvidia_source = sources[0]
    
    NDI.find_destroy(ndi_find)
    
    print(f"🎯 Testando: {nvidia_source.ndi_name}")
    
    recv_create = NDI.RecvCreateV3()
    recv_create.source_to_connect_to = nvidia_source
    recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
    recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
    
    ndi_recv = NDI.recv_create_v3(recv_create)
    if not ndi_recv:
        print("❌ Falha ao criar receiver")
        NDI.destroy()
        return False
    
    print("✅ Receiver criado")
    print("⏰ Aguardando estabilização (3s)...")
    time.sleep(3)
    
    print("🎯 Iniciando captura (50 tentativas)...")
    
    for attempt in range(50):
        try:
            result = NDI.recv_capture_v2(ndi_recv, 1000)  # 1s timeout
            frame_type, video_frame, audio_frame, metadata_frame = result
            
            if frame_type == NDI.FRAME_TYPE_VIDEO:
                print(f"🎉 SUCESSO na tentativa {attempt + 1}!")
                print(f"📺 Resolução: {video_frame.xres}x{video_frame.yres}")
                
                if video_frame.data:
                    # Salvar frame como prova
                    frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                    expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                    
                    if len(frame_data) >= expected_size:
                        frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                        frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                        
                        cv2.imwrite('ndi_isolated_success.png', frame_bgr)
                        print(f"💾 Frame salvo: ndi_isolated_success.png")
                
                NDI.recv_free_video_v2(ndi_recv, video_frame)
                NDI.recv_destroy(ndi_recv)
                NDI.destroy()
                return True
            
            # Cleanup
            if frame_type == NDI.FRAME_TYPE_AUDIO:
                NDI.recv_free_audio_v2(ndi_recv, audio_frame)
            elif frame_type == NDI.FRAME_TYPE_METADATA:
                NDI.recv_free_metadata(ndi_recv, metadata_frame)
            
            if (attempt + 1) % 10 == 0:
                print(f"   🔄 Tentativa {attempt + 1}/50")
                
        except Exception as e:
            if attempt == 0:  # Só mostrar primeiro erro
                print(f"⚠️ Primeiro erro: {e}")
    
    print("❌ Nenhum frame capturado em 50 tentativas")
    NDI.recv_destroy(ndi_recv)
    NDI.destroy()
    return False

def main():
    print("🧪 TESTE NDI ISOLADO")
    print("=" * 50)
    print("🎯 Objetivo: Testar sem interferências")
    print("💡 Fechando outras aplicações NDI")
    print("=" * 50)
    
    success = test_isolated()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCESSO NO TESTE ISOLADO!")
        print("✅ NDI funciona quando sem conflitos")
        print("💡 Solução: Usar SwitchPilot SEM Studio Monitor")
    else:
        print("❌ Ainda com problemas")
        print("💭 Possíveis causas:")
        print("   1. Drivers NDI desatualizados")
        print("   2. Configuração de rede")
        print("   3. Firewall bloqueando")
        print("   4. Fonte NDI não ativa")
    print("=" * 50)

if __name__ == "__main__":
    main() 