#!/usr/bin/env python3
"""
TESTE ULTRA SIMPLES NDI - Versão mínima
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time

def ultra_simple_test():
    """Teste mais simples possível"""
    print("⚡ TESTE ULTRA SIMPLES")
    
    # Sem timeouts complexos - só o básico
    if not NDI.initialize():
        print("❌ Falha NDI.initialize()")
        return False
    
    print("✅ NDI inicializado")
    
    # Buscar fontes (básico)
    ndi_find = NDI.find_create_v2()
    time.sleep(2)  # Só 2 segundos
    sources = NDI.find_get_current_sources(ndi_find)
    
    if not sources:
        print("❌ Sem fontes")
        NDI.find_destroy(ndi_find)
        NDI.destroy()
        return False
    
    print(f"📡 {len(sources)} fontes:")
    for i, s in enumerate(sources):
        print(f"   {i}: {s.ndi_name}")
    
    # Pegar primeira fonte (NVIDIA GTX 1660 SUPER 1)
    source = sources[0]
    print(f"🎯 Testando: {source.ndi_name}")
    
    NDI.find_destroy(ndi_find)
    
    # Receiver SUPER SIMPLES
    recv_create = NDI.RecvCreateV3()
    recv_create.source_to_connect_to = source
    # SEM configurações especiais - usar padrões
    
    ndi_recv = NDI.recv_create_v3(recv_create)
    if not ndi_recv:
        print("❌ Falha receiver")
        NDI.destroy()
        return False
    
    print("✅ Receiver OK")
    
    # Tentar apenas 20 vezes rapidamente
    print("🎯 Tentando 20x...")
    for i in range(20):
        try:
            # Timeout de apenas 500ms
            result = NDI.recv_capture_v2(ndi_recv, 500)
            frame_type, video_frame, audio_frame, metadata_frame = result
            
            if frame_type == NDI.FRAME_TYPE_VIDEO:
                print(f"🎉 FRAME! Tentativa {i+1}")
                print(f"📺 {video_frame.xres}x{video_frame.yres}")
                
                NDI.recv_free_video_v2(ndi_recv, video_frame)
                NDI.recv_destroy(ndi_recv)
                NDI.destroy()
                return True
            
            # Cleanup outros tipos
            if frame_type == NDI.FRAME_TYPE_AUDIO:
                NDI.recv_free_audio_v2(ndi_recv, audio_frame)
            elif frame_type == NDI.FRAME_TYPE_METADATA:
                NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
        except Exception as e:
            print(f"⚠️ Erro {i+1}: {e}")
    
    print("❌ Nenhum frame em 20 tentativas")
    NDI.recv_destroy(ndi_recv)
    NDI.destroy()
    return False

def main():
    print("⚡ TESTE ULTRA SIMPLES NDI")
    print("=" * 30)
    print("🚀 Configuração mínima")
    print("📊 20 tentativas rápidas")
    print("=" * 30)
    
    success = ultra_simple_test()
    
    if success:
        print("\n🎉 FUNCIONOU!")
    else:
        print("\n❌ Não funcionou")
        print("\n💡 DIAGNÓSTICO:")
        print("   📺 Studio Monitor: ✅ Funciona")
        print("   🐍 Python NDI: ❌ Não funciona")
        print("   🔧 Possível causa: Conflito recursos")
        print("\n🛠️ SOLUÇÕES:")
        print("   1. Reiniciar máquina")
        print("   2. Fechar TUDO relacionado NDI")
        print("   3. Executar Python PRIMEIRO")

if __name__ == "__main__":
    main() 