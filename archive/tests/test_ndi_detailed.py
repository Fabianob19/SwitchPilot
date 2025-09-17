#!/usr/bin/env python3
"""
Teste detalhado específico para NDI
Investiga mais profundamente as fontes NDI e tenta diferentes configurações
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import traceback

def test_ndi_source_detailed(source, source_index):
    """Testa uma fonte NDI específica com diferentes configurações"""
    source_name = getattr(source, 'ndi_name', f'Fonte {source_index}')
    source_url = getattr(source, 'url_address', 'N/A')
    
    print(f"\n{'='*60}")
    print(f"🔍 TESTE DETALHADO DA FONTE {source_index}: {source_name}")
    print(f"📡 URL: {source_url}")
    print(f"{'='*60}")
    
    ndi_recv = None
    
    # Configurações diferentes para testar
    configs = [
        {
            'name': 'Configuração Padrão',
            'color_format': NDI.RECV_COLOR_FORMAT_BGRX_BGRA,
            'bandwidth': NDI.RECV_BANDWIDTH_HIGHEST
        },
        {
            'name': 'Configuração Baixa Largura de Banda',
            'color_format': NDI.RECV_COLOR_FORMAT_BGRX_BGRA,
            'bandwidth': NDI.RECV_BANDWIDTH_LOWEST
        },
        {
            'name': 'Configuração Áudio/Vídeo',
            'color_format': NDI.RECV_COLOR_FORMAT_BGRX_BGRA,
            'bandwidth': NDI.RECV_BANDWIDTH_AUDIO_ONLY
        }
    ]
    
    for config in configs:
        print(f"\n🔧 Testando {config['name']}...")
        
        try:
            # Criar receiver com configuração específica
            recv_create = NDI.RecvCreateV3()
            recv_create.source_to_connect_to = source
            recv_create.color_format = config['color_format']
            recv_create.bandwidth = config['bandwidth']
            recv_create.allow_video_fields = True
            
            ndi_recv = NDI.recv_create_v3(recv_create)
            if not ndi_recv:
                print(f"   ❌ Não foi possível criar receiver")
                continue
            
            print(f"   ✅ Receiver criado")
            
            # Verificar conexão
            print(f"   ⏳ Aguardando conexão...")
            time.sleep(2)
            
            # Tentar capturar por 10 segundos
            timeout = 10
            start_time = time.time()
            frames_video = 0
            frames_audio = 0
            frames_metadata = 0
            frames_none = 0
            
            while (time.time() - start_time) < timeout:
                try:
                    result = NDI.recv_capture_v2(ndi_recv, 100)
                    frame_type, video_frame, audio_frame, metadata_frame = result
                    
                    if frame_type == NDI.FRAME_TYPE_VIDEO:
                        frames_video += 1
                        print(f"   📺 Frame de vídeo #{frames_video} - {video_frame.xres}x{video_frame.yres}")
                        
                        if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                            print(f"      ✅ Dados válidos: {len(video_frame.data)} bytes")
                            
                            # Tentar converter frame
                            try:
                                frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                                expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                                
                                if len(frame_data) >= expected_size:
                                    frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                                    frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                                    
                                    if frame_bgr.size > 0:
                                        print(f"      🎉 SUCESSO! Frame convertido: {frame_bgr.shape}")
                                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                                        NDI.recv_destroy(ndi_recv)
                                        return True, {
                                            'config': config['name'],
                                            'frames_video': frames_video,
                                            'resolution': f"{video_frame.xres}x{video_frame.yres}",
                                            'data_size': len(video_frame.data)
                                        }
                                    else:
                                        print(f"      ⚠️  Frame vazio após conversão")
                                else:
                                    print(f"      ⚠️  Dados insuficientes: {len(frame_data)} < {expected_size}")
                            except Exception as conv_e:
                                print(f"      ❌ Erro na conversão: {conv_e}")
                        else:
                            print(f"      ⚠️  Frame sem dados")
                        
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        
                        if frames_video >= 3:  # Se conseguiu 3 frames, já é sucesso
                            break
                            
                    elif frame_type == NDI.FRAME_TYPE_AUDIO:
                        frames_audio += 1
                        NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                        if frames_audio == 1:
                            print(f"   🔊 Frame de áudio recebido")
                            
                    elif frame_type == NDI.FRAME_TYPE_METADATA:
                        frames_metadata += 1
                        NDI.recv_free_metadata(ndi_recv, metadata_frame)
                        if frames_metadata == 1:
                            print(f"   📝 Metadata recebida")
                    else:
                        frames_none += 1
                        if frames_none == 1:
                            print(f"   ⚪ Nenhum frame (waiting...)")
                    
                    time.sleep(0.01)
                    
                except Exception as inner_e:
                    print(f"   ❌ Erro interno: {inner_e}")
                    break
            
            print(f"   📊 Resumo após {timeout}s:")
            print(f"      📺 Frames de vídeo: {frames_video}")
            print(f"      🔊 Frames de áudio: {frames_audio}")
            print(f"      📝 Frames de metadata: {frames_metadata}")
            print(f"      ⚪ Frames vazios: {frames_none}")
            
            if ndi_recv:
                NDI.recv_destroy(ndi_recv)
                ndi_recv = None
                
        except Exception as config_e:
            print(f"   ❌ Erro na configuração: {config_e}")
            if ndi_recv:
                try:
                    NDI.recv_destroy(ndi_recv)
                except:
                    pass
                ndi_recv = None
    
    return False, {'error': 'Nenhuma configuração funcionou'}

def main():
    print("🔍 TESTE DETALHADO NDI - DIAGNÓSTICO AVANÇADO")
    print("=" * 80)
    
    try:
        if not NDI.initialize():
            print("❌ NDI não pode ser inicializado")
            return
        
        print("✅ NDI inicializado")
        
        # Criar finder
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Não foi possível criar NDI finder")
            NDI.destroy()
            return
        
        print("✅ NDI finder criado")
        print("⏳ Descobrindo fontes NDI...")
        
        # Aguardar mais tempo para descoberta
        time.sleep(5)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources or len(sources) == 0:
            print("❌ Nenhuma fonte NDI encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return
        
        print(f"📡 {len(sources)} fontes NDI encontradas")
        
        # Listar todas as fontes
        for i, source in enumerate(sources):
            source_name = getattr(source, 'ndi_name', f'Fonte {i+1}')
            source_url = getattr(source, 'url_address', 'N/A')
            print(f"  {i+1}. {source_name} - {source_url}")
        
        NDI.find_destroy(ndi_find)
        
        # Testar cada fonte individualmente
        results = {}
        for i, source in enumerate(sources):
            source_name = getattr(source, 'ndi_name', f'Fonte {i+1}')
            success, details = test_ndi_source_detailed(source, i+1)
            results[source_name] = {
                'success': success,
                'details': details
            }
        
        # Relatório final
        print(f"\n{'='*80}")
        print("📊 RELATÓRIO FINAL DO TESTE NDI DETALHADO")
        print(f"{'='*80}")
        
        working_sources = []
        failing_sources = []
        
        for source_name, result in results.items():
            if result['success']:
                working_sources.append(source_name)
                print(f"✅ {source_name}")
                if 'config' in result['details']:
                    print(f"   🔧 Configuração: {result['details']['config']}")
                if 'resolution' in result['details']:
                    print(f"   📺 Resolução: {result['details']['resolution']}")
            else:
                failing_sources.append(source_name)
                print(f"❌ {source_name}")
                if 'error' in result['details']:
                    print(f"   🔍 Erro: {result['details']['error']}")
        
        print(f"\n📈 RESUMO:")
        print(f"✅ Fontes funcionando: {len(working_sources)}")
        print(f"❌ Fontes com problema: {len(failing_sources)}")
        
        if working_sources:
            print(f"🎉 Fontes NDI funcionais encontradas: {', '.join(working_sources)}")
        else:
            print("🚨 NENHUMA fonte NDI está funcionando corretamente")
            print("💡 Possíveis causas:")
            print("   - Fontes não estão transmitindo ativamente")
            print("   - Problema de rede/firewall")
            print("   - Fontes configuradas apenas para áudio")
            print("   - Incompatibilidade de codec/formato")
        
        NDI.destroy()
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        traceback.print_exc()
        try:
            NDI.destroy()
        except:
            pass

if __name__ == "__main__":
    main() 