#!/usr/bin/env python3
"""
TESTE AGRESSIVO NDI - VAI TENTAR ATÉ FUNCIONAR!
Implementa múltiplas estratégias para forçar o NDI a funcionar
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2
import subprocess
import psutil

def kill_python_processes():
    """Mata todos os processos Python para liberar recursos NDI"""
    print("🔪 Eliminando processos Python conflitantes...")
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any('main.py' in cmd for cmd in cmdline):
                    print(f"   🎯 Matando PID: {proc.info['pid']}")
                    proc.kill()
        time.sleep(2)
        print("✅ Processos Python eliminados")
    except Exception as e:
        print(f"⚠️  Erro ao matar processos: {e}")

def force_ndi_cleanup():
    """Força limpeza completa dos recursos NDI"""
    print("🧹 Forçando limpeza completa NDI...")
    try:
        # Tentar inicializar e destruir múltiplas vezes
        for i in range(3):
            if NDI.initialize():
                NDI.destroy()
                print(f"   ✅ Limpeza NDI #{i+1}")
            time.sleep(1)
        
        # Aguardar mais tempo para garantir limpeza
        print("⏰ Aguardando limpeza completa...")
        time.sleep(5)
        print("✅ Limpeza NDI concluída")
    except Exception as e:
        print(f"⚠️  Erro na limpeza: {e}")

def test_ndi_with_strategy(strategy_name, source_name, timeout_ms=500, max_attempts=50):
    """Testa NDI com uma estratégia específica"""
    print(f"\n🎯 ESTRATÉGIA: {strategy_name}")
    print(f"📡 Fonte: {source_name}")
    print(f"⏰ Timeout: {timeout_ms}ms, Max tentativas: {max_attempts}")
    
    try:
        if not NDI.initialize():
            print("❌ NDI não pode ser inicializado")
            return None
        
        print("✅ NDI inicializado")
        
        # Aguardar descoberta baseado na estratégia
        if "rápido" in strategy_name.lower():
            time.sleep(1)
        elif "médio" in strategy_name.lower():
            time.sleep(3)
        else:
            time.sleep(5)
        
        # Criar finder
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Não foi possível criar finder")
            NDI.destroy()
            return None
        
        print("✅ Finder criado")
        
        # Aguardar descoberta adicional
        time.sleep(2)
        
        sources = NDI.find_get_current_sources(ndi_find)
        if not sources:
            print("❌ Nenhuma fonte encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return None
        
        print(f"📡 {len(sources)} fontes encontradas")
        
        # Procurar fonte alvo
        target_source = None
        for source in sources:
            if source.ndi_name == source_name:
                target_source = source
                print(f"✅ Fonte encontrada: {source.ndi_name}")
                break
        
        NDI.find_destroy(ndi_find)
        
        if not target_source:
            print(f"❌ Fonte {source_name} não encontrada")
            NDI.destroy()
            return None
        
        # Criar receiver com configuração da estratégia
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = target_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        
        # Ajustar largura de banda baseado na estratégia
        if "baixa" in strategy_name.lower():
            recv_create.bandwidth = NDI.RECV_BANDWIDTH_LOWEST
        elif "alta" in strategy_name.lower():
            recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        else:
            recv_create.bandwidth = NDI.RECV_BANDWIDTH_METADATA_ONLY
        
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        if not ndi_recv:
            print("❌ Não foi possível criar receiver")
            NDI.destroy()
            return None
        
        print("✅ Receiver criado")
        
        # Aguardar conexão
        print("⏳ Aguardando conexão...")
        time.sleep(3)
        
        # Tentar capturar frames
        attempts = 0
        frames_received = 0
        
        while attempts < max_attempts and frames_received == 0:
            try:
                result = NDI.recv_capture_v2(ndi_recv, timeout_ms)
                frame_type, video_frame, audio_frame, metadata_frame = result
                attempts += 1
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    print(f"🎉 FRAME ENCONTRADO! Tentativa #{attempts}")
                    print(f"📺 Resolução: {video_frame.xres}x{video_frame.yres}")
                    
                    if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                        frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                        expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                        
                        if len(frame_data) >= expected_size:
                            frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                            frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                            
                            if frame_bgr.size > 0:
                                print(f"✅ SUCESSO! Frame convertido: {frame_bgr.shape}")
                                
                                # Salvar frame
                                filename = f"ndi_success_{strategy_name.replace(' ', '_').lower()}.png"
                                cv2.imwrite(filename, frame_bgr)
                                print(f"💾 Frame salvo: {filename}")
                                
                                frames_received += 1
                                
                                NDI.recv_free_video_v2(ndi_recv, video_frame)
                                NDI.recv_destroy(ndi_recv)
                                NDI.destroy()
                                
                                return frame_bgr
                    
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
                # Progress indicator
                if attempts % 10 == 0:
                    print(f"   🔄 Tentativa {attempts}/{max_attempts}")
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Erro na tentativa {attempts}: {e}")
                break
        
        print(f"⏰ Estratégia finalizada. Tentativas: {attempts}, Frames: {frames_received}")
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        time.sleep(2)  # Aguardar limpeza
        
        return None
        
    except Exception as e:
        print(f"❌ Erro crítico na estratégia: {e}")
        try:
            NDI.destroy()
        except:
            pass
        time.sleep(2)
        return None

def main():
    print("🚀 TESTE AGRESSIVO NDI - VAI FUNCIONAR!")
    print("=" * 80)
    
    # Matar processos conflitantes
    kill_python_processes()
    
    # Limpeza inicial
    force_ndi_cleanup()
    
    # Fontes para testar (a que funcionou primeiro)
    sources_to_test = [
        'DESKTOP-F9GHF2T (NVIDIA GeForce GTX 1660 SUPER 1)',
        'DESKTOP-F9GHF2T (Test Pattern)',
        'DESKTOP-F9GHF2T (NVIDIA GeForce GTX 1660 SUPER 2)'
    ]
    
    # Estratégias para tentar
    strategies = [
        ("Rápido + Alta Largura", 200, 30),
        ("Médio + Largura Baixa", 500, 50),
        ("Lento + Largura Máxima", 1000, 100),
        ("Super Lento + Metadata", 2000, 150),
        ("Ultra Agressivo", 100, 200)
    ]
    
    for source_name in sources_to_test:
        print(f"\n{'='*60}")
        print(f"🎯 TESTANDO FONTE: {source_name}")
        print(f"{'='*60}")
        
        for strategy_name, timeout_ms, max_attempts in strategies:
            print(f"\n⚡ Tentando estratégia: {strategy_name}")
            
            result = test_ndi_with_strategy(strategy_name, source_name, timeout_ms, max_attempts)
            
            if result is not None:
                print(f"\n🎉🎉🎉 SUCESSO TOTAL! 🎉🎉🎉")
                print(f"✅ Fonte funcionando: {source_name}")
                print(f"🏆 Estratégia vencedora: {strategy_name}")
                print(f"📺 Frame capturado: {result.shape}")
                print(f"💡 Use esta configuração no SwitchPilot!")
                print("=" * 80)
                return True
            
            print(f"❌ Estratégia {strategy_name} falhou")
            
            # Limpeza entre estratégias
            print("🧹 Limpeza entre estratégias...")
            force_ndi_cleanup()
        
        print(f"❌ Todas as estratégias falharam para {source_name}")
    
    print("\n💥 NENHUMA ESTRATÉGIA FUNCIONOU!")
    print("🔍 Possíveis soluções:")
    print("   1. Reiniciar o computador")
    print("   2. Reinstalar NDI Runtime")
    print("   3. Verificar configurações de firewall")
    print("   4. Tentar em outro momento")
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n💀 TESTE FALHOU EM TODAS AS TENTATIVAS") 