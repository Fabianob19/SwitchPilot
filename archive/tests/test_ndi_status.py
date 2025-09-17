#!/usr/bin/env python3
"""
Teste de Status NDI - Verificar estado atual das fontes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import time

def check_ndi_status():
    """Verifica status atual do NDI e fontes"""
    print("🔍 DIAGNÓSTICO DE STATUS NDI")
    print("=" * 60)
    
    try:
        if not NDI.initialize():
            print("❌ NDI não pode ser inicializado")
            return
        
        print("✅ NDI inicializado com sucesso")
        
        # Criar finder
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Não foi possível criar NDI finder")
            NDI.destroy()
            return
        
        print("✅ NDI finder criado")
        
        # Aguardar descoberta
        print("⏳ Descobrindo fontes NDI (5 segundos)...")
        time.sleep(5)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources:
            print("❌ NENHUMA fonte NDI encontrada")
            print("\n💡 POSSÍVEIS CAUSAS:")
            print("   1. Nenhum software NDI está rodando")
            print("   2. NDI Studio Monitor não está aberto")
            print("   3. Firewall bloqueando NDI")
            print("   4. Serviço NDI não está ativo")
            
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return
        
        print(f"📡 {len(sources)} fontes NDI encontradas:")
        print("-" * 60)
        
        for i, source in enumerate(sources):
            source_name = getattr(source, 'ndi_name', f'Fonte {i+1}')
            source_url = getattr(source, 'url_address', 'N/A')
            
            print(f"\n🎯 FONTE {i+1}: {source_name}")
            print(f"   📡 URL: {source_url}")
            print(f"   🔍 Testando conectividade...")
            
            # Testar conexão rápida
            recv_create = NDI.RecvCreateV3()
            recv_create.source_to_connect_to = source
            recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
            recv_create.allow_video_fields = True
            
            ndi_recv = NDI.recv_create_v3(recv_create)
            
            if not ndi_recv:
                print("   ❌ Não foi possível criar receiver")
                continue
            
            print("   ✅ Receiver criado")
            
            # Testar por 3 segundos
            start_time = time.time()
            frames_video = 0
            frames_audio = 0
            frames_none = 0
            
            while (time.time() - start_time) < 3:
                try:
                    result = NDI.recv_capture_v2(ndi_recv, 100)
                    frame_type, video_frame, audio_frame, metadata_frame = result
                    
                    if frame_type == NDI.FRAME_TYPE_VIDEO:
                        frames_video += 1
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                    elif frame_type == NDI.FRAME_TYPE_AUDIO:
                        frames_audio += 1
                        NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                    elif frame_type == NDI.FRAME_TYPE_METADATA:
                        NDI.recv_free_metadata(ndi_recv, metadata_frame)
                    else:
                        frames_none += 1
                    
                except Exception as e:
                    print(f"   ⚠️ Erro na captura: {e}")
                    break
            
            # Relatório da fonte
            print(f"   📊 RESULTADOS (3s de teste):")
            print(f"      📺 Frames de vídeo: {frames_video}")
            print(f"      🔊 Frames de áudio: {frames_audio}")
            print(f"      ⚪ Frames vazios: {frames_none}")
            
            if frames_video > 0:
                print(f"   🎉 FONTE ATIVA - Transmitindo vídeo!")
            elif frames_audio > 0:
                print(f"   🔊 FONTE ATIVA - Apenas áudio")
            else:
                print(f"   💤 FONTE INATIVA - Não está transmitindo")
            
            NDI.recv_destroy(ndi_recv)
            print("   🧹 Receiver limpo")
        
        NDI.find_destroy(ndi_find)
        NDI.destroy()
        
        print(f"\n" + "=" * 60)
        print("📋 RESUMO DO DIAGNÓSTICO:")
        print(f"   📡 Total de fontes encontradas: {len(sources)}")
        print("\n💡 RECOMENDAÇÕES:")
        print("   1. Para ativar fontes NDI:")
        print("      - Abra NDI Studio Monitor")
        print("      - Ou abra OBS com fonte NDI")
        print("      - Ou use NDI Test Pattern Generator")
        print("   2. Para Test Pattern:")
        print("      - Baixe NDI Tools")
        print("      - Execute NDI Test Pattern Generator")
        print("   3. Para fontes de tela:")
        print("      - Use NDI Screen Capture")
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        try:
            NDI.destroy()
        except:
            pass

def main():
    print("🔍 DIAGNÓSTICO DE STATUS NDI")
    print("=" * 60)
    print("🎯 Objetivo: Verificar por que as fontes não estão transmitindo")
    print("🔬 Método: Testar conectividade e atividade de cada fonte")
    print("=" * 60)
    
    check_ndi_status()

if __name__ == "__main__":
    main() 