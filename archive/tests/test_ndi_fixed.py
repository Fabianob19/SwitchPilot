#!/usr/bin/env python3
"""
Teste NDI Corrigido - Sem erros de comparação de arrays
Teste completo com todas as correções aplicadas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2

def test_ndi_fixed():
    """Teste NDI com todas as correções aplicadas"""
    print("🔧 TESTE NDI CORRIGIDO")
    print("=" * 60)
    print("✅ Correções aplicadas:")
    print("   - Tratamento correto de arrays NumPy")
    print("   - Uso adequado de np.any() e np.all()")
    print("   - Conversão segura de frames NDI")
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
        print("⏳ Descobrindo fontes...")
        
        # Aguardar descoberta
        time.sleep(3)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources:
            print("❌ Nenhuma fonte NDI encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False
        
        print(f"📡 {len(sources)} fontes encontradas:")
        for i, source in enumerate(sources):
            source_name = getattr(source, 'ndi_name', f'Fonte {i+1}')
            print(f"   {i+1}. {source_name}")
        
        # Tentar Test Pattern primeiro (mais estável)
        target_source = None
        target_name = ""
        
        for source in sources:
            source_name = getattr(source, 'ndi_name', '')
            if 'Test Pattern' in source_name:
                target_source = source
                target_name = source_name
                print(f"🎯 Selecionado: {source_name} (Test Pattern)")
                break
        
        # Se não encontrar Test Pattern, usar a primeira fonte
        if not target_source and sources:
            target_source = sources[0]
            target_name = getattr(target_source, 'ndi_name', 'Primeira fonte')
            print(f"🎯 Selecionado: {target_name} (primeira disponível)")
        
        if not target_source:
            print("❌ Nenhuma fonte válida encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False
        
        NDI.find_destroy(ndi_find)
        
        print(f"🔧 Configurando receiver...")
        
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
        print("⏳ Aguardando frames...")
        
        timeout = 15
        start_time = time.time()
        frames_received = 0
        successful_conversions = 0
        
        while (time.time() - start_time) < timeout:
            try:
                result = NDI.recv_capture_v2(ndi_recv, 500)
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    frames_received += 1
                    
                    print(f"📺 Frame #{frames_received}")
                    print(f"   📏 Resolução: {video_frame.xres}x{video_frame.yres}")
                    print(f"   📊 Line stride: {video_frame.line_stride_in_bytes}")
                    print(f"   🎨 Formato: {video_frame.FourCC}")
                    
                    if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                        try:
                            # CONVERSÃO CORRIGIDA
                            frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                            expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                            
                            if len(frame_data) >= expected_size:
                                # Reshape para imagem
                                bytes_per_pixel = 4  # BGRA
                                pixels_per_line = video_frame.line_stride_in_bytes // bytes_per_pixel
                                
                                frame_data = frame_data.reshape((video_frame.yres, pixels_per_line, bytes_per_pixel))
                                
                                # Extrair região válida
                                frame_bgra = frame_data[:, :video_frame.xres, :]
                                
                                # Converter BGRA para BGR
                                frame_bgr = frame_bgra[:, :, :3].copy()
                                
                                # VERIFICAÇÕES CORRIGIDAS
                                if frame_bgr.size > 0:
                                    successful_conversions += 1
                                    
                                    # Análise estatística do frame
                                    mean_values = np.mean(frame_bgr, axis=(0, 1))
                                    std_values = np.std(frame_bgr, axis=(0, 1))
                                    
                                    print(f"   ✅ Conversão bem-sucedida!")
                                    print(f"   🌈 Cor média (BGR): {mean_values}")
                                    print(f"   📊 Desvio padrão: {std_values}")
                                    
                                    # CORREÇÃO: Usar np.any() adequadamente
                                    is_not_black = np.any(mean_values > 10)
                                    has_variation = np.any(std_values > 5)
                                    
                                    if is_not_black:
                                        print(f"   ✅ Frame não é preto")
                                    else:
                                        print(f"   ⚠️  Frame muito escuro")
                                    
                                    if has_variation:
                                        print(f"   ✅ Frame tem variação de cor")
                                    else:
                                        print(f"   ⚠️  Frame muito uniforme")
                                    
                                    # Salvar primeiro frame válido
                                    if successful_conversions == 1:
                                        filename = f"ndi_frame_corrigido_{target_name.replace(' ', '_')}.png"
                                        cv2.imwrite(filename, frame_bgr)
                                        print(f"   💾 Frame salvo: {filename}")
                                    
                                    # Se conseguirmos 3 conversões bem-sucedidas, está funcionando
                                    if successful_conversions >= 3:
                                        print(f"   🎉 TESTE APROVADO! {successful_conversions} conversões bem-sucedidas")
                                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                                        NDI.recv_destroy(ndi_recv)
                                        NDI.destroy()
                                        return True
                                else:
                                    print(f"   ❌ Frame vazio após conversão")
                            else:
                                print(f"   ❌ Dados insuficientes: {len(frame_data)} < {expected_size}")
                                
                        except Exception as conv_e:
                            print(f"   ❌ Erro na conversão: {conv_e}")
                    else:
                        print(f"   ❌ Frame sem dados")
                    
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                    
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Erro na captura: {e}")
                break
        
        print(f"⏰ Tempo esgotado após {timeout}s")
        print(f"📊 Total de frames: {frames_received}")
        print(f"📊 Conversões bem-sucedidas: {successful_conversions}")
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        return successful_conversions > 0
        
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
    print("🔧 TESTE NDI COM TODAS AS CORREÇÕES")
    print("=" * 80)
    print("🎯 Objetivo: Verificar se todas as correções funcionam")
    print("🔧 Correções aplicadas:")
    print("   - np.any() usado corretamente")
    print("   - Comparações de arrays NumPy seguras")
    print("   - Conversão robusta de frames NDI")
    print("   - Tratamento de erros melhorado")
    print("=" * 80)
    
    success = test_ndi_fixed()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 SUCESSO TOTAL! NDI ESTÁ FUNCIONANDO!")
        print("✅ Todas as correções foram aplicadas com sucesso")
        print("✅ Frames NDI sendo capturados e convertidos corretamente")
        print("✅ Tratamento de arrays NumPy funcionando")
        print("💡 O NDI agora está pronto para usar no SwitchPilot!")
    else:
        print("❌ AINDA HÁ PROBLEMAS")
        print("🔍 Possíveis causas:")
        print("   - Fontes NDI não estão transmitindo vídeo")
        print("   - Problema de compatibilidade de drivers")
        print("   - Configuração de rede")
    print("=" * 80)

if __name__ == "__main__":
    main() 