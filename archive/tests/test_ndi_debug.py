#!/usr/bin/env python3
"""
Debug específico para encontrar o erro de comparação de arrays NumPy
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import traceback

def debug_ndi_conversion():
    """Debug específico da conversão NDI"""
    print("🐛 DEBUG NDI - ENCONTRANDO O ERRO")
    print("=" * 60)
    
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
        time.sleep(3)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources:
            print("❌ Nenhuma fonte NDI encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False
        
        # Usar Test Pattern
        target_source = None
        for source in sources:
            source_name = getattr(source, 'ndi_name', '')
            if 'Test Pattern' in source_name:
                target_source = source
                print(f"🎯 Usando: {source_name}")
                break
        
        if not target_source:
            target_source = sources[0]
            print(f"🎯 Usando primeira fonte: {getattr(target_source, 'ndi_name', 'Desconhecida')}")
        
        NDI.find_destroy(ndi_find)
        
        # Configurar receiver
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = target_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        if not ndi_recv:
            print("❌ Não foi possível criar receiver")
            NDI.destroy()
            return False
        
        print("✅ Receiver criado")
        print("🐛 Iniciando debug da captura...")
        
        timeout = 10
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                print("🔍 Chamando NDI.recv_capture_v2...")
                result = NDI.recv_capture_v2(ndi_recv, 500)
                print("✅ recv_capture_v2 executado")
                
                frame_type, video_frame, audio_frame, metadata_frame = result
                print(f"🔍 Frame type: {frame_type}")
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    print("📺 Frame de vídeo recebido")
                    print(f"   📏 Resolução: {video_frame.xres}x{video_frame.yres}")
                    print(f"   📊 Line stride: {video_frame.line_stride_in_bytes}")
                    print(f"   🎨 Formato: {video_frame.FourCC}")
                    
                    print("🔍 Verificando video_frame.data...")
                    if hasattr(video_frame, 'data'):
                        print(f"✅ video_frame.data existe")
                        print(f"🔍 Tipo de data: {type(video_frame.data)}")
                        
                        # AQUI PODE ESTAR O PROBLEMA
                        print("🔍 Testando len(video_frame.data)...")
                        try:
                            data_len = len(video_frame.data)
                            print(f"✅ len(data): {data_len}")
                        except Exception as len_e:
                            print(f"❌ Erro em len(data): {len_e}")
                            traceback.print_exc()
                        
                        print("🔍 Testando video_frame.data and len(video_frame.data) > 0...")
                        try:
                            # ESTA LINHA PODE ESTAR CAUSANDO O ERRO
                            has_data = video_frame.data and len(video_frame.data) > 0  # PROBLEMA AQUI?
                            print(f"✅ has_data: {has_data}")
                        except Exception as check_e:
                            print(f"❌ ERRO ENCONTRADO! video_frame.data and len(video_frame.data) > 0")
                            print(f"❌ Erro: {check_e}")
                            traceback.print_exc()
                        
                        print("🔍 Testando np.frombuffer...")
                        try:
                            frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                            print(f"✅ np.frombuffer executado: {len(frame_data)} bytes")
                        except Exception as buf_e:
                            print(f"❌ Erro em np.frombuffer: {buf_e}")
                            traceback.print_exc()
                        
                        print("🔍 Testando comparação de tamanhos...")
                        try:
                            expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                            print(f"✅ expected_size: {expected_size}")
                            
                            # ESTA COMPARAÇÃO PODE SER O PROBLEMA
                            size_check = len(frame_data) >= expected_size
                            print(f"✅ size_check: {size_check}")
                        except Exception as size_e:
                            print(f"❌ Erro na comparação de tamanhos: {size_e}")
                            traceback.print_exc()
                        
                        print("🔍 Testando reshape...")
                        try:
                            bytes_per_pixel = 4
                            pixels_per_line = video_frame.line_stride_in_bytes // bytes_per_pixel
                            
                            frame_data_reshaped = frame_data.reshape((video_frame.yres, pixels_per_line, bytes_per_pixel))
                            print(f"✅ reshape executado: {frame_data_reshaped.shape}")
                            
                            frame_bgra = frame_data_reshaped[:, :video_frame.xres, :]
                            print(f"✅ slice executado: {frame_bgra.shape}")
                            
                            frame_bgr = frame_bgra[:, :, :3].copy()
                            print(f"✅ conversão BGR executada: {frame_bgr.shape}")
                            
                            print("🔍 Testando verificações de array...")
                            
                            # ESTAS PODEM SER AS LINHAS PROBLEMÁTICAS
                            print("🔍 Testando frame_bgr.size > 0...")
                            size_check = frame_bgr.size > 0
                            print(f"✅ size check: {size_check}")
                            
                            print("🔍 Testando np.mean...")
                            mean_values = np.mean(frame_bgr, axis=(0, 1))
                            print(f"✅ mean_values: {mean_values}")
                            print(f"✅ mean_values type: {type(mean_values)}")
                            
                            print("🔍 Testando np.any(mean_values > 10)...")
                            # ESTA LINHA PODE SER O PROBLEMA
                            is_not_black = np.any(mean_values > 10)
                            print(f"✅ is_not_black: {is_not_black}")
                            
                            print("🎉 CONVERSÃO COMPLETA SEM ERROS!")
                            
                        except Exception as conv_e:
                            print(f"❌ ERRO ENCONTRADO NA CONVERSÃO!")
                            print(f"❌ Erro: {conv_e}")
                            traceback.print_exc()
                    else:
                        print("❌ video_frame.data não existe")
                    
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    print("✅ Frame liberado")
                    
                    # Se chegamos até aqui sem erro, podemos parar
                    print("🎉 DEBUG COMPLETO - NENHUM ERRO ENCONTRADO!")
                    break
                    
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    print("🔊 Frame de áudio recebido")
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    print("📄 Frame de metadata recebido")
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                else:
                    print(f"❓ Frame tipo desconhecido: {frame_type}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ ERRO CAPTURADO NO DEBUG!")
                print(f"❌ Erro: {e}")
                traceback.print_exc()
                break
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro crítico no debug: {e}")
        traceback.print_exc()
        try:
            NDI.destroy()
        except:
            pass
        return False

def main():
    print("🐛 DEBUG NDI - IDENTIFICAÇÃO DE ERRO")
    print("=" * 80)
    print("🎯 Objetivo: Encontrar exatamente onde está o erro de arrays")
    print("=" * 80)
    
    debug_ndi_conversion()

if __name__ == "__main__":
    main() 