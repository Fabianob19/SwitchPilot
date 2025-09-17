#!/usr/bin/env python3
"""
Teste completo de todos os tipos de captura do SwitchPilot
Executa testes individuais para cada método de captura disponível
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import pyautogui
import mss
import NDIlib as NDI
import time
import traceback

def test_monitor_capture():
    """Testa captura de monitores usando mss"""
    print("=" * 60)
    print("🖥️  TESTE CAPTURA MONITOR (MSS)")
    print("=" * 60)
    
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"✅ MSS inicializado com sucesso")
            print(f"📺 Monitores disponíveis: {len(monitors)-1}")
            
            # Listar todos os monitores
            for i in range(1, len(monitors)):
                monitor = monitors[i]
                print(f"  Monitor {i}: {monitor['width']}x{monitor['height']} - Top:{monitor['top']}, Left:{monitor['left']}")
            
            if len(monitors) > 1:
                # Testar captura do primeiro monitor
                monitor = monitors[1]
                print(f"\n🔍 Testando captura do Monitor 1...")
                
                start_time = time.time()
                screenshot = sct.grab(monitor)
                capture_time = (time.time() - start_time) * 1000
                
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                print(f"✅ Screenshot capturado: {img_bgr.shape}")
                print(f"⏱️  Tempo de captura: {capture_time:.2f}ms")
                print(f"💾 Tamanho dos dados: {img_bgr.nbytes} bytes")
                
                # Testar ROI (região de interesse)
                roi_x, roi_y, roi_w, roi_h = 100, 100, 300, 200
                roi_area = {"top": monitor["top"] + roi_y, 
                           "left": monitor["left"] + roi_x, 
                           "width": roi_w, "height": roi_h, 
                           "mon": 1}
                
                roi_screenshot = sct.grab(roi_area)
                roi_img = np.array(roi_screenshot)
                roi_img_bgr = cv2.cvtColor(roi_img, cv2.COLOR_BGRA2BGR)
                
                print(f"✅ ROI capturada: {roi_img_bgr.shape}")
                print(f"🎯 ROI configurada para: x={roi_x}, y={roi_y}, w={roi_w}, h={roi_h}")
                
                return True, {
                    'monitors_found': len(monitors)-1,
                    'capture_time_ms': capture_time,
                    'image_shape': img_bgr.shape,
                    'roi_shape': roi_img_bgr.shape
                }
            else:
                print("❌ Nenhum monitor encontrado")
                return False, {'error': 'Nenhum monitor encontrado'}
                
    except Exception as e:
        print(f"❌ Erro na captura de monitor: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False, {'error': str(e)}

def test_window_capture():
    """Testa captura de janelas usando pyautogui"""
    print("\n" + "=" * 60)
    print("🪟 TESTE CAPTURA JANELA (PYAUTOGUI)")
    print("=" * 60)
    
    try:
        print("🔍 Buscando janelas disponíveis...")
        all_windows = pyautogui.getAllWindows()
        valid_windows = [w for w in all_windows if w.title and w.visible and w.width > 0 and w.height > 0]
        
        print(f"✅ PyAutoGUI inicializado com sucesso")
        print(f"🪟 Janelas totais encontradas: {len(all_windows)}")
        print(f"🎯 Janelas válidas para captura: {len(valid_windows)}")
        
        # Listar algumas janelas válidas
        print("\n📋 Primeiras 5 janelas válidas:")
        for i, window in enumerate(valid_windows[:5]):
            print(f"  {i+1}. '{window.title}' - {window.width}x{window.height} @ ({window.left},{window.top})")
        
        if valid_windows:
            # Testar captura da primeira janela válida
            test_window = valid_windows[0]
            print(f"\n🔍 Testando captura da janela: '{test_window.title}'")
            print(f"📏 Coordenadas: {test_window.left}, {test_window.top}, {test_window.width}, {test_window.height}")
            
            if test_window.left is not None and test_window.top is not None:
                region = (test_window.left, test_window.top, test_window.width, test_window.height)
                
                start_time = time.time()
                pil_img = pyautogui.screenshot(region=region)
                capture_time = (time.time() - start_time) * 1000
                
                img = np.array(pil_img)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                print(f"✅ Screenshot da janela capturado: {img_bgr.shape}")
                print(f"⏱️  Tempo de captura: {capture_time:.2f}ms")
                print(f"💾 Tamanho dos dados: {img_bgr.nbytes} bytes")
                
                # Testar ROI na janela
                roi_x, roi_y, roi_w, roi_h = 50, 50, 200, 150
                roi_region = (test_window.left + roi_x, test_window.top + roi_y, roi_w, roi_h)
                roi_pil = pyautogui.screenshot(region=roi_region)
                roi_img = np.array(roi_pil)
                roi_img_bgr = cv2.cvtColor(roi_img, cv2.COLOR_RGB2BGR)
                
                print(f"✅ ROI da janela capturada: {roi_img_bgr.shape}")
                print(f"🎯 ROI configurada para: x={roi_x}, y={roi_y}, w={roi_w}, h={roi_h}")
                
                return True, {
                    'windows_found': len(valid_windows),
                    'test_window': test_window.title,
                    'capture_time_ms': capture_time,
                    'image_shape': img_bgr.shape,
                    'roi_shape': roi_img_bgr.shape
                }
            else:
                print("❌ Coordenadas da janela inválidas")
                return False, {'error': 'Coordenadas da janela inválidas'}
        else:
            print("❌ Nenhuma janela válida encontrada")
            return False, {'error': 'Nenhuma janela válida encontrada'}
            
    except Exception as e:
        print(f"❌ Erro na captura de janela: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False, {'error': str(e)}

def test_ndi_capture():
    """Testa captura NDI usando NDIlib"""
    print("\n" + "=" * 60)
    print("📡 TESTE CAPTURA NDI (NDILIB)")
    print("=" * 60)
    
    ndi_recv = None
    ndi_find = None
    
    try:
        print("🔍 Inicializando NDI...")
        if not NDI.initialize():
            print("❌ NDI não pode ser inicializado")
            return False, {'error': 'NDI não pode ser inicializado'}
        
        print("✅ NDI inicializado com sucesso")
        
        print("🔍 Criando NDI finder...")
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            print("❌ Não foi possível criar NDI finder")
            NDI.destroy()
            return False, {'error': 'Não foi possível criar NDI finder'}
        
        print("✅ NDI finder criado")
        print("⏳ Aguardando descoberta de fontes NDI (3 segundos)...")
        time.sleep(3)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        print(f"📡 Fontes NDI descobertas: {len(sources) if sources else 0}")
        
        if not sources or len(sources) == 0:
            print("❌ Nenhuma fonte NDI encontrada")
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False, {'error': 'Nenhuma fonte NDI encontrada'}
        
        # Listar todas as fontes NDI
        print("\n📋 Fontes NDI disponíveis:")
        for i, source in enumerate(sources):
            source_name = getattr(source, 'ndi_name', f'Fonte {i+1}')
            source_url = getattr(source, 'url_address', 'N/A')
            print(f"  {i+1}. {source_name}")
            print(f"     URL: {source_url}")
        
        # Testar primeira fonte
        test_source = sources[0]
        source_name = getattr(test_source, 'ndi_name', 'Fonte Desconhecida')
        print(f"\n🔍 Testando captura da fonte: {source_name}")
        
        NDI.find_destroy(ndi_find)
        ndi_find = None
        
        # Criar receiver
        print("🔧 Configurando NDI receiver...")
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = test_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        ndi_recv = NDI.recv_create_v3(recv_create)
        if not ndi_recv:
            print("❌ Não foi possível criar NDI receiver")
            NDI.destroy()
            return False, {'error': 'Não foi possível criar NDI receiver'}
        
        print("✅ NDI receiver criado")
        print("⏳ Aguardando frames de vídeo...")
        
        # Tentar capturar frame
        timeout_seconds = 15
        start_time = time.time()
        frames_received = 0
        frames_valid = 0
        
        while (time.time() - start_time) < timeout_seconds:
            try:
                result = NDI.recv_capture_v2(ndi_recv, 100)
                frame_type, video_frame, audio_frame, metadata_frame = result
                
                if frame_type == NDI.FRAME_TYPE_VIDEO:
                    frames_received += 1
                    
                    # Verificar se os dados do frame são válidos
                    if video_frame.data is None or len(video_frame.data) == 0:
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        continue
                    
                    # Converter frame NDI para numpy array
                    frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                    expected_size = video_frame.yres * video_frame.line_stride_in_bytes
                    
                    if len(frame_data) < expected_size:
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        continue
                    
                    frame_data = frame_data.reshape((video_frame.yres, video_frame.line_stride_in_bytes // 4, 4))
                    frame_bgr = frame_data[:, :video_frame.xres, :3].copy()
                    
                    if frame_bgr.size == 0:
                        NDI.recv_free_video_v2(ndi_recv, video_frame)
                        continue
                    
                    frames_valid += 1
                    
                    if frames_valid == 1:  # Primeiro frame válido
                        capture_time = (time.time() - start_time) * 1000
                        print(f"✅ Primeiro frame NDI capturado: {frame_bgr.shape}")
                        print(f"⏱️  Tempo para primeiro frame: {capture_time:.2f}ms")
                        print(f"💾 Tamanho dos dados: {frame_bgr.nbytes} bytes")
                        print(f"📺 Resolução: {video_frame.xres}x{video_frame.yres}")
                        print(f"🎨 Formato de cor: BGRX -> BGR")
                    
                    NDI.recv_free_video_v2(ndi_recv, video_frame)
                    
                    # Capturar alguns frames para teste de performance
                    if frames_valid >= 5:
                        total_time = time.time() - start_time
                        fps = frames_valid / total_time
                        print(f"✅ Capturados {frames_valid} frames válidos em {total_time:.2f}s")
                        print(f"📊 FPS médio: {fps:.2f}")
                        
                        NDI.recv_destroy(ndi_recv)
                        NDI.destroy()
                        
                        return True, {
                            'sources_found': len(sources),
                            'test_source': source_name,
                            'frames_received': frames_received,
                            'frames_valid': frames_valid,
                            'capture_time_ms': capture_time,
                            'fps': fps,
                            'resolution': f"{video_frame.xres}x{video_frame.yres}",
                            'image_shape': frame_bgr.shape
                        }
                
                elif frame_type == NDI.FRAME_TYPE_AUDIO:
                    NDI.recv_free_audio_v2(ndi_recv, audio_frame)
                elif frame_type == NDI.FRAME_TYPE_METADATA:
                    NDI.recv_free_metadata(ndi_recv, metadata_frame)
                
                time.sleep(0.01)
                
            except Exception as inner_e:
                print(f"⚠️  Erro interno na captura: {inner_e}")
                break
        
        print(f"⏰ Timeout após {timeout_seconds}s")
        print(f"📊 Frames recebidos: {frames_received}, Frames válidos: {frames_valid}")
        
        if ndi_recv:
            NDI.recv_destroy(ndi_recv)
        NDI.destroy()
        
        return False, {
            'error': 'Timeout na captura NDI',
            'sources_found': len(sources),
            'frames_received': frames_received,
            'frames_valid': frames_valid
        }
        
    except Exception as e:
        print(f"❌ Erro na captura NDI: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        
        # Cleanup em caso de erro
        try:
            if ndi_recv:
                NDI.recv_destroy(ndi_recv)
            if ndi_find:
                NDI.find_destroy(ndi_find)
            NDI.destroy()
        except:
            pass
        
        return False, {'error': str(e)}

def main():
    """Executa todos os testes de captura"""
    print("🚀 INICIANDO TESTES DE CAPTURA DO SWITCHPILOT")
    print("=" * 80)
    print(f"⏰ Horário de início: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"💻 Sistema: {sys.platform}")
    print("=" * 80)
    
    # Executar todos os testes
    results = {}
    details = {}
    
    # Teste 1: Monitor
    success, detail = test_monitor_capture()
    results['Monitor'] = success
    details['Monitor'] = detail
    
    # Teste 2: Janela
    success, detail = test_window_capture()
    results['Janela'] = success
    details['Janela'] = detail
    
    # Teste 3: NDI
    success, detail = test_ndi_capture()
    results['NDI'] = success
    details['NDI'] = detail
    
    # Relatório final
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 80)
    
    for capture_type, success in results.items():
        status = "✅ FUNCIONANDO" if success else "❌ COM PROBLEMAS"
        print(f"{capture_type:<12}: {status}")
        
        if success and capture_type in details:
            detail = details[capture_type]
            if 'capture_time_ms' in detail:
                print(f"             ⏱️  Tempo: {detail['capture_time_ms']:.2f}ms")
            if 'image_shape' in detail:
                print(f"             📏 Formato: {detail['image_shape']}")
        elif not success and capture_type in details:
            detail = details[capture_type]
            if 'error' in detail:
                print(f"             ❌ Erro: {detail['error']}")
    
    print("\n" + "-" * 80)
    
    # Status geral
    all_success = all(results.values())
    any_success = any(results.values())
    
    if all_success:
        print("🎉 TODOS OS TIPOS DE CAPTURA ESTÃO FUNCIONANDO PERFEITAMENTE!")
    elif any_success:
        print("⚠️  ALGUNS TIPOS DE CAPTURA ESTÃO FUNCIONANDO")
        working = [k for k, v in results.items() if v]
        failing = [k for k, v in results.items() if not v]
        print(f"✅ Funcionando: {', '.join(working)}")
        print(f"❌ Com problemas: {', '.join(failing)}")
    else:
        print("🚨 NENHUM TIPO DE CAPTURA ESTÁ FUNCIONANDO - VERIFICAR DEPENDÊNCIAS!")
    
    print(f"\n⏰ Testes concluídos em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return results, details

if __name__ == "__main__":
    try:
        results, details = main()
        
        # Salvar log detalhado
        log_file = f"test_captures_log_{int(time.time())}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Log dos Testes de Captura - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for capture_type, success in results.items():
                f.write(f"{capture_type}: {'SUCESSO' if success else 'FALHA'}\n")
                if capture_type in details:
                    f.write(f"Detalhes: {details[capture_type]}\n")
                f.write("\n")
        
        print(f"📄 Log detalhado salvo em: {log_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n🚨 Erro crítico nos testes: {e}")
        traceback.print_exc() 