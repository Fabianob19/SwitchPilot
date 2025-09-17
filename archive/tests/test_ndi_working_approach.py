#!/usr/bin/env python3
"""
Teste NDI usando a abordagem que funcionou no diagnóstico
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import NDIlib as NDI
import numpy as np
import time
import cv2
from collections import deque

class WorkingApproachNDI:
    """Usando exatamente a abordagem que funcionou no diagnóstico"""
    
    def __init__(self):
        self.ndi_recv = None
        self.frame_buffer = deque(maxlen=3)
        self.stats = {'attempts': 0, 'direct_success': 0, 'buffer_uses': 0}
    
    def connect_working_approach(self):
        """Conexão usando a mesma abordagem do diagnóstico que funcionou"""
        print("🚀 CONEXÃO - ABORDAGEM QUE FUNCIONOU")
        print("=" * 50)
        
        if not NDI.initialize():
            return False, None
        
        print("✅ NDI inicializado")
        
        # EXATAMENTE como no diagnóstico
        ndi_find = NDI.find_create_v2()
        if not ndi_find:
            NDI.destroy()
            return False, None
        
        print("✅ NDI finder criado")
        
        # AGUARDAR como no diagnóstico
        print("⏳ Descobrindo fontes NDI (5 segundos)...")
        time.sleep(5)
        
        sources = NDI.find_get_current_sources(ndi_find)
        
        if not sources:
            NDI.find_destroy(ndi_find)
            NDI.destroy()
            return False, None
        
        print(f"📡 {len(sources)} fontes NDI encontradas")
        
        # Escolher NVIDIA GTX 1660 SUPER 1 (melhor performance)
        target_source = None
        source_name = ""
        
        for source in sources:
            name = getattr(source, 'ndi_name', '')
            if 'NVIDIA GeForce GTX 1660 SUPER 1' in name:
                target_source = source
                source_name = name
                print(f"🎯 Usando melhor fonte: {name}")
                break
        
        if not target_source:
            target_source = sources[0]
            source_name = getattr(target_source, 'ndi_name', 'Primeira fonte')
            print(f"🎯 Usando primeira fonte: {source_name}")
        
        NDI.find_destroy(ndi_find)
        
        # CONFIGURAÇÃO EXATA como no diagnóstico
        recv_create = NDI.RecvCreateV3()
        recv_create.source_to_connect_to = target_source
        recv_create.color_format = NDI.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = NDI.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = True
        
        self.ndi_recv = NDI.recv_create_v3(recv_create)
        
        if not self.ndi_recv:
            NDI.destroy()
            return False, None
        
        print("✅ Receiver criado")
        
        return True, source_name
    
    def capture_working_approach(self):
        """Captura usando a mesma abordagem do diagnóstico"""
        self.stats['attempts'] += 1
        
        try:
            # TIMEOUT EXATO como no diagnóstico
            result = NDI.recv_capture_v2(self.ndi_recv, 100)  # 100ms como no diagnóstico
            frame_type, video_frame, audio_frame, metadata_frame = result
            
            if frame_type == NDI.FRAME_TYPE_VIDEO:
                frame_bgr = self._convert_safe(video_frame)
                NDI.recv_free_video_v2(self.ndi_recv, video_frame)
                
                if frame_bgr is not None:
                    self.stats['direct_success'] += 1
                    self.frame_buffer.append(frame_bgr)
                    return frame_bgr
            
            elif frame_type == NDI.FRAME_TYPE_AUDIO:
                NDI.recv_free_audio_v2(self.ndi_recv, audio_frame)
            elif frame_type == NDI.FRAME_TYPE_METADATA:
                NDI.recv_free_metadata(self.ndi_recv, metadata_frame)
            
        except Exception as e:
            pass
        
        # Fallback para buffer
        if self.frame_buffer:
            self.stats['buffer_uses'] += 1
            return self.frame_buffer[-1].copy()
        
        return None
    
    def _convert_safe(self, video_frame):
        """Conversão segura com correções aplicadas"""
        try:
            if not hasattr(video_frame, 'data') or video_frame.data is None:
                return None
            
            if len(video_frame.data) == 0:
                return None
            
            frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
            expected_size = video_frame.yres * video_frame.line_stride_in_bytes
            
            if len(frame_data) < expected_size:
                return None
            
            bytes_per_pixel = 4
            pixels_per_line = video_frame.line_stride_in_bytes // bytes_per_pixel
            
            frame_data = frame_data.reshape((video_frame.yres, pixels_per_line, bytes_per_pixel))
            frame_bgra = frame_data[:, :video_frame.xres, :]
            frame_bgr = frame_bgra[:, :, :3].copy()
            
            if frame_bgr.size == 0:
                return None
            
            return frame_bgr
            
        except Exception:
            return None
    
    def test_working_approach(self, num_tests=50):
        """Teste usando a abordagem que funcionou"""
        print(f"\n🧪 TESTE COM ABORDAGEM QUE FUNCIONOU ({num_tests} tentativas)")
        print("=" * 60)
        
        successful = 0
        start_time = time.time()
        consecutive_successes = 0
        max_consecutive = 0
        
        for i in range(num_tests):
            print(f"📊 {i+1:2d}/{num_tests}: ", end="", flush=True)
            
            frame = self.capture_working_approach()
            
            if frame is not None:
                successful += 1
                consecutive_successes += 1
                max_consecutive = max(max_consecutive, consecutive_successes)
                
                if successful == 1:
                    print("✅ (primeiro frame)")
                    cv2.imwrite("working_approach_frame.png", frame)
                    print(f"    💾 Frame salvo: working_approach_frame.png")
                elif successful % 10 == 0:
                    print(f"✅ ({successful}º sucesso)")
                else:
                    print("✅")
            else:
                print("❌")
                consecutive_successes = 0
            
            # Pausa como no diagnóstico
            time.sleep(0.01)
        
        total_time = time.time() - start_time
        success_rate = (successful / num_tests) * 100
        fps = num_tests / total_time
        
        print(f"\n🎯 RESULTADOS:")
        print(f"   ✅ Sucessos: {successful}/{num_tests}")
        print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"   ⏱️  Tempo total: {total_time:.1f}s")
        print(f"   🔄 FPS médio: {fps:.1f}")
        print(f"   🔥 Máx. consecutivos: {max_consecutive}")
        
        print(f"\n🔍 ESTATÍSTICAS:")
        print(f"   🎯 Sucessos diretos: {self.stats['direct_success']}")
        print(f"   🔄 Usos do buffer: {self.stats['buffer_uses']}")
        print(f"   📊 Total de tentativas: {self.stats['attempts']}")
        
        direct_rate = (self.stats['direct_success'] / num_tests) * 100 if num_tests > 0 else 0
        buffer_rate = (self.stats['buffer_uses'] / num_tests) * 100 if num_tests > 0 else 0
        
        print(f"\n📈 ANÁLISE:")
        print(f"   🎯 Taxa de captura direta: {direct_rate:.1f}%")
        print(f"   🔄 Taxa de uso do buffer: {buffer_rate:.1f}%")
        print(f"   ❌ Taxa de falha total: {100 - success_rate:.1f}%")
        
        return success_rate, direct_rate, max_consecutive
    
    def cleanup(self):
        """Limpeza"""
        if self.ndi_recv:
            NDI.recv_destroy(self.ndi_recv)
        NDI.destroy()

def main():
    print("🚀 TESTE NDI - ABORDAGEM QUE FUNCIONOU")
    print("=" * 70)
    print("🎯 OBJETIVO: Usar exatamente a mesma abordagem do diagnóstico")
    print("📊 DIAGNÓSTICO MOSTROU: 205 frames da NVIDIA GTX 1660 SUPER 1")
    print("🔬 MÉTODO: Replicar exatamente o código que funcionou")
    print("=" * 70)
    
    ndi = WorkingApproachNDI()
    
    try:
        success, source_name = ndi.connect_working_approach()
        if not success:
            print("❌ Falha na conexão")
            return
        
        print(f"✅ Conectado: {source_name}")
        
        success_rate, direct_rate, max_consecutive = ndi.test_working_approach(50)
        
        print(f"\n🏆 AVALIAÇÃO:")
        if success_rate >= 95:
            print(f"🎉 EXCELENTE! {success_rate:.1f}% - Abordagem funcionou!")
        elif success_rate >= 80:
            print(f"✅ MUITO BOM! {success_rate:.1f}% - Boa performance")
        elif success_rate >= 50:
            print(f"✅ BOM: {success_rate:.1f}% - Melhor que antes")
        else:
            print(f"⚠️ AINDA COM PROBLEMAS: {success_rate:.1f}%")
        
        print(f"\n💡 CONCLUSÃO:")
        if success_rate >= 80:
            print("✅ A abordagem do diagnóstico funciona!")
            print("✅ Agora sabemos como fazer funcionar")
            print("✅ Podemos otimizar a partir desta base")
        elif success_rate >= 50:
            print("🔧 Abordagem parcialmente funcional")
            print("🔧 Precisa de pequenos ajustes")
        else:
            print("🔧 Necessário investigar mais")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ndi.cleanup()

if __name__ == "__main__":
    main() 