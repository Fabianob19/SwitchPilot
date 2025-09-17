#!/usr/bin/env python3
"""
Teste NDI replicando EXATAMENTE o loop do diagnóstico
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2

def test_exact_diagnosis_loop():
    """Replica EXATAMENTE o loop do diagnóstico que funcionou"""
    print("🔍 REPLICANDO EXATAMENTE O DIAGNÓSTICO")
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
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return
        
        print(f"📡 {len(sources)} fontes NDI encontradas")
        
        # Escolher NVIDIA GTX 1660 SUPER 1
        target_source = None
        source_name = ""
        
        for source in sources:
            name = getattr(source, 'ndi_name', '')
            if 'NVIDIA GeForce GTX 1660 SUPER 1' in name:
                target_source = source
                source_name = name
                break
        
        if not target_source:
            target_source = sources[0]
            source_name = getattr(target_source, 'ndi_name', 'Primeira fonte')
        
        print(f"🎯 FONTE ESCOLHIDA: {source_name}")
        
        NDI.find_destroy(ndi_find)
        
        # Configuração
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = target_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        
        if not ndi_recv:
            print("❌ Não foi possível criar receiver")
            NDI.destroy()
            return
        
        print("✅ Receiver criado")
        
        # LOOP EXATO DO DIAGNÓSTICO
        print("🔍 Testando por 3 segundos (EXATO como diagnóstico)...")
        start_time = time.time()
        frames_video = 0
        frames_audio = 0
        frames_none = 0
        saved_frames = 0
        
        while (time.time() - start_time) < 3:
            try:
                # EXATAMENTE como no diagnóstico
                result = NDI.recv_capture_v2(ndi_recv, 100)
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    frames_video += 1
                    
                    # Tentar converter e salvar frame
                    if saved_frames < 5:  # Salvar apenas os primeiros 5
                        try:
                            if hasattr(video_frame, 'data') and video_frame.data is not None and len(video_frame.data) > 0:
                                frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                                expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                                
                                if len(frame_data) >= expected_size:
                                    bytes_per_pixel = 4
                                    pixels_per_line = video_frame.line_stride_in_bytes // bytes_per_pixel
                                    
                                    frame_data = frame_data.reshape((video_frame.yres, pixels_per_line, bytes_per_pixel))
                                    frame_bgra = frame_data[:, :video_frame.xres, :]
                                    frame_bgr = frame_bgra[:, :, :3].copy()
                                    
                                    if frame_bgr.size > 0:
                                        saved_frames += 1
                                        filename = f"exact_diagnosis_frame_{saved_frames}.png"
                                        cv2.imwrite(filename, frame_bgr)
                                        print(f"    💾 Frame {saved_frames} salvo: {filename}")
                        except Exception as e:
                            print(f"    ⚠️ Erro ao converter frame {frames_video}: {e}")
                    
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
        
        # Relatório EXATO como diagnóstico
        print(f"   📊 RESULTADOS (3s de teste):")
        print(f"      📺 Frames de vídeo: {frames_video}")
        print(f"      🔊 Frames de áudio: {frames_audio}")
        print(f"      ⚪ Frames vazios: {frames_none}")
        print(f"      💾 Frames salvos: {saved_frames}")
        
        if frames_video > 0:
            print(f"   🎉 FONTE ATIVA - Transmitindo vídeo!")
            fps = frames_video / 3.0
            print(f"   📈 FPS calculado: {fps:.1f}")
            
            # Teste adicional de captura contínua
            print(f"\n🧪 TESTE ADICIONAL: Captura contínua (30 tentativas)")
            successful_captures = 0
            
            for i in range(30):
                try:
                    result = NDI.recv_capture_v2(ndi_recv, 100)
                    frame_type, video_frame, audio_frame, metadata_frame = result
                    
                    if frame_type == NDI.FRAME_TYPE_VIDEO:
                        successful_captures += 1
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        print(f"📊 {i+1:2d}/30: ✅")
                    elif frame_type == NDI.FRAME_TYPE_AUDIO:
                        NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                        print(f"📊 {i+1:2d}/30: 🔊")
                    elif frame_type == NDI.FRAME_TYPE_METADATA:
                        NDI.recv_free_metadata(ndi_recv, metadata_frame)
                        print(f"📊 {i+1:2d}/30: 📄")
                    else:
                        print(f"📊 {i+1:2d}/30: ❌")
                    
                except Exception as e:
                    print(f"📊 {i+1:2d}/30: ⚠️ {e}")
                
                time.sleep(0.1)  # 100ms como no diagnóstico
            
            capture_rate = (successful_captures / 30) * 100
            print(f"\n📈 TAXA DE CAPTURA CONTÍNUA: {capture_rate:.1f}% ({successful_captures}/30)")
            
            if capture_rate >= 80:
                print("🎉 EXCELENTE! Taxa de captura muito boa!")
            elif capture_rate >= 50:
                print("✅ BOM! Taxa de captura aceitável")
            else:
                print("⚠️ Taxa de captura baixa, mas funcional")
                
        else:
            print(f"   💤 FONTE INATIVA - Não está transmitindo")
        
        NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        print(f"\n" + "=" * 60)
        print("📋 RESUMO FINAL:")
        print(f"   📺 Frames de vídeo no diagnóstico: {frames_video}")
        print(f"   💾 Frames convertidos com sucesso: {saved_frames}")
        
        if frames_video > 0 and saved_frames > 0:
            print("🎉 SUCESSO! Conseguimos replicar o diagnóstico!")
            print("✅ Agora sabemos que a conversão funciona")
            print("✅ O problema deve estar na lógica dos outros testes")
        elif frames_video > 0:
            print("🔧 Frames detectados mas conversão falhou")
            print("🔧 Problema na conversão de dados")
        else:
            print("❌ Nenhum frame detectado - problema na captura")
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        try:
            NDI.destroy()
        except:
            pass

def main():
    print("🔍 TESTE EXATO DO DIAGNÓSTICO NDI")
    print("=" * 60)
    print("🎯 Objetivo: Replicar EXATAMENTE o loop que capturou 205 frames")
    print("🔬 Método: Copiar linha por linha o código do diagnóstico")
    print("=" * 60)
    
    test_exact_diagnosis_loop()

if __name__ == "__main__":
    main() 