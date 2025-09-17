#!/usr/bin/env python3
"""
Teste específico para a fonte NDI Test Pattern
Baseado nos dados do arquivo src_teste.pkl
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import pickle

def load_test_data():
    """Carrega os dados de teste do arquivo pkl"""
    try:
        with open('src_teste.pkl', 'rb') as f:
            data = pickle.load(f)
        print(f"📄 Dados carregados do arquivo: {data}")
        return data
    except Exception as e:
        print(f"❌ Erro ao carregar src_teste.pkl: {e}")
        return None

def test_ndi_testpattern():
    """Testa especificamente a fonte NDI Test Pattern"""
    print("🎯 TESTE ESPECÍFICO: NDI TEST PATTERN")
    print("=" * 60)
    
    # Carregar dados de teste
    test_data = load_test_data()
    if test_data:
        target_ndi_name = test_data.get('ndi_name', 'DESKTOP-F9GHF2T (Test Pattern)')
        print(f"🎯 Nome da fonte alvo: {target_ndi_name}")
    else:
        target_ndi_name = 'DESKTOP-F9GHF2T (Test Pattern)'
        print(f"🎯 Usando nome padrão: {target_ndi_name}")
    
    try:
        if not NDI.initialize():
            print("❌ NDI não pode ser inicializado")
            return False
        
        print("✅ NDI inicializado")
        
        # Criar finder
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Não foi possível criar NDI finder")
            NDI.destroy()
            return False
        
        print("✅ NDI finder criado")
        print("⏳ Procurando fonte Test Pattern...")
        
        # Aguardar descoberta
        time.sleep(3)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources:
            print("❌ Nenhuma fonte NDI encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False
        
        # Procurar pela fonte Test Pattern
        test_pattern_source = None
        for source in sources:
            source_name = getattr(source, 'ndi_name', '')
            if 'Test Pattern' in source_name or source_name == target_ndi_name:
                test_pattern_source = source
                print(f"✅ Fonte Test Pattern encontrada: {source_name}")
                break
        
        if not test_pattern_source:
            print(f"❌ Fonte Test Pattern não encontrada")
            print("📋 Fontes disponíveis:")
            for i, source in enumerate(sources):
                print(f"  {i+1}. {getattr(source, 'ndi_name', f'Fonte {i+1}')}")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False
        
        NDI.find_destroy(ndi_find)
        
        print(f"🔧 Configurando receiver para Test Pattern...")
        
        # Configurar receiver otimizado para Test Pattern
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = test_pattern_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        if not ndi_recv:
            print("❌ Não foi possível criar receiver para Test Pattern")
            NDI.destroy()
            return False
        
        print("✅ Receiver Test Pattern criado")
        print("⏳ Aguardando frames de Test Pattern...")
        
        # Test Pattern deve gerar frames consistentemente
        timeout = 20  # Mais tempo para Test Pattern
        start_time = time.time()
        frames_received = 0
        
        while (time.time() - start_time) < timeout:
            try:
                result = NDI.recv_capture_v2(ndi_recv, 500)  # Timeout maior
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    frames_received += 1
                    
                    print(f"📺 Frame Test Pattern #{frames_received}")
                    print(f"   📏 Resolução: {video_frame.xres}x{video_frame.yres}")
                    print(f"   📊 Line stride: {video_frame.line_stride_in_bytes}")
                    print(f"   🎨 Formato: {video_frame.FourCC}")
                    
                    if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                        print(f"   ✅ Dados: {len(video_frame.data)} bytes")
                        
                        try:
                            # Converter Test Pattern frame
                            frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                            expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                            
                            print(f"   🔍 Dados recebidos: {len(frame_data)} bytes")
                            print(f"   🔍 Dados esperados: {expected_size} bytes")
                            
                            if len(frame_data) >= expected_size:
                                # Reshape para imagem
                                frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                                frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                                
                                if frame_bgr.size > 0:
                                    print(f"   🎉 SUCESSO! Test Pattern convertido: {frame_bgr.shape}")
                                    
                                    # Analisar conteúdo do Test Pattern
                                    mean_color = np.mean(frame_bgr, axis=(0, 1))
                                    print(f"   🌈 Cor média (BGR): {mean_color}")
                                    
                                    # CORREÇÃO: Verificar se é realmente um test pattern (não deve ser todo preto)
                                    # Usar np.any() corretamente para comparação de arrays
                                    is_valid_pattern = np.any(mean_color > 10)
                                    if is_valid_pattern:
                                        print(f"   ✅ Test Pattern válido (não é preto)")
                                        
                                        # Salvar um frame de exemplo
                                        import cv2
                                        cv2.imwrite('test_pattern_frame.png', frame_bgr)
                                        print(f"   💾 Frame salvo em: test_pattern_frame.png")
                                        
                                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                                        NDI.recv_destroy(ndi_recv)
                                        NDI.destroy()
                                        
                                        return True
                                    else:
                                        print(f"   ⚠️  Test Pattern parece estar preto")
                                else:
                                    print(f"   ❌ Frame vazio após conversão")
                            else:
                                print(f"   ❌ Dados insuficientes")
                        except Exception as conv_e:
                            print(f"   ❌ Erro na conversão: {conv_e}")
                    else:
                        print(f"   ❌ Frame sem dados")
                    
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
                # Test Pattern deve ser rápido
                if frames_received >= 5:
                    break
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Erro na captura: {e}")
                break
        
        print(f"⏰ Tempo esgotado após {timeout}s")
        print(f"📊 Total de frames Test Pattern: {frames_received}")
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        return frames_received > 0
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        try:
            NDI.destroy()
        except:
            pass
        return False

def main():
    print("🎯 TESTE ESPECÍFICO NDI TEST PATTERN")
    print("=" * 80)
    print("📄 Baseado nos dados do arquivo src_teste.pkl")
    print("=" * 80)
    
    success = test_ndi_testpattern()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 SUCESSO! Test Pattern NDI está funcionando!")
        print("✅ Frames de Test Pattern capturados com sucesso")
        print("✅ Dados convertidos corretamente")
        print("💡 A fonte NDI Test Pattern é funcional para o SwitchPilot")
    else:
        print("❌ FALHA! Test Pattern NDI não está funcionando")
        print("🔍 Possíveis causas:")
        print("   - Test Pattern não está ativo/transmitindo")
        print("   - Problema na configuração do NDI")
        print("   - Fonte configurada apenas para áudio")
        print("   - Problema de compatibilidade")
    print("=" * 80)

if __name__ == "__main__":
    main() 