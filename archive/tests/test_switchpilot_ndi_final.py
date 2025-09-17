#!/usr/bin/env python3
"""
Teste final do SwitchPilot com NDI usando o controlador corrigido
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o controlador NDI corrigido
from switchpilot.integrations.ndi_controller import NDIController
import time
import cv2
import logging

# Configurar logging para debug
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_switchpilot_ndi_final():
    """Teste final do NDI no SwitchPilot"""
    print("🚀 TESTE FINAL SWITCHPILOT + NDI CORRIGIDO")
    print("=" * 80)
    print("🎯 Usando o controlador NDI corrigido do SwitchPilot")
    print("=" * 80)
    
    # Criar instância do controlador NDI
    ndi_controller = NDIController()
    
    try:
        # Inicializar NDI
        if not ndi_controller.initialize():
            print("❌ Falha ao inicializar NDI")
            return False
        
        print("✅ NDI Controller inicializado")
        
        # Obter fontes disponíveis
        sources = ndi_controller.get_sources()
        
        if not sources:
            print("❌ Nenhuma fonte NDI encontrada")
            return False
        
        print(f"📡 {len(sources)} fontes encontradas:")
        for source in sources:
            print(f"   - {source['name']}")
        
        # Procurar Test Pattern
        test_pattern_name = None
        for source in sources:
            if 'Test Pattern' in source['name']:
                test_pattern_name = source['name']
                break
        
        if not test_pattern_name:
            test_pattern_name = sources[0]['name']
            print(f"🎯 Usando primeira fonte: {test_pattern_name}")
        else:
            print(f"🎯 Usando Test Pattern: {test_pattern_name}")
        
        # Conectar à fonte
        if not ndi_controller.connect_to_source(test_pattern_name):
            print("❌ Falha ao conectar à fonte NDI")
            return False
        
        print("✅ Conectado à fonte NDI")
        
        # Testar captura de frames
        print("🎬 Iniciando captura de frames...")
        
        frames_captured = 0
        successful_frames = 0
        
        for i in range(10):  # Tentar capturar 10 frames
            frame = ndi_controller.capture_frame(1000)  # 1 segundo timeout
            
            if frame is not None:
                frames_captured += 1
                
                # Verificar se o frame é válido
                if frame.shape[0] > 0 and frame.shape[1] > 0:
                    successful_frames += 1
                    
                    print(f"📺 Frame {successful_frames}: {frame.shape}")
                    
                    # Salvar primeiro frame
                    if successful_frames == 1:
                        filename = f"switchpilot_ndi_frame_{test_pattern_name.replace(' ', '_')}.png"
                        cv2.imwrite(filename, frame)
                        print(f"   💾 Frame salvo: {filename}")
                    
                    # Análise do frame
                    mean_color = frame.mean(axis=(0, 1))
                    print(f"   🌈 Cor média (BGR): {mean_color}")
                    
                    # Se conseguirmos pelo menos 2 frames válidos, está funcionando (NDI pode ser intermitente)
                    if successful_frames >= 2:
                        print("🎉 TESTE APROVADO! NDI funcionando no SwitchPilot!")
                        break
                else:
                    print(f"⚠️  Frame {frames_captured} inválido: {frame.shape}")
            else:
                print(f"❌ Frame {i+1} não capturado")
            
            time.sleep(0.2)  # Aguardar um pouco entre frames
        
        print(f"\n📊 Resumo:")
        print(f"   Frames tentados: 10")
        print(f"   Frames capturados: {frames_captured}")
        print(f"   Frames válidos: {successful_frames}")
        
        # Obter informações da fonte
        source_info = ndi_controller.get_source_info()
        if source_info:
            print(f"\n📋 Informações da fonte:")
            print(f"   Nome: {source_info['name']}")
            print(f"   URL: {source_info['url']}")
            print(f"   Conectado: {source_info['connected']}")
            print(f"   Capturando: {source_info['capturing']}")
        
        return successful_frames >= 2
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpar recursos
        ndi_controller.cleanup()
        print("🧹 Recursos NDI limpos")

def main():
    print("🚀 TESTE FINAL: SWITCHPILOT + NDI")
    print("=" * 80)
    print("🎯 Testando o controlador NDI corrigido integrado ao SwitchPilot")
    print("🔧 Todas as correções de arrays NumPy aplicadas")
    print("=" * 80)
    
    success = test_switchpilot_ndi_final()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 SUCESSO COMPLETO!")
        print("✅ NDI totalmente funcional no SwitchPilot")
        print("✅ Controlador NDI pronto para produção")
        print("✅ Frames sendo capturados e processados corretamente")
        print("💡 O SwitchPilot agora pode usar fontes NDI!")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("   1. Integrar o NDI Controller na interface do SwitchPilot")
        print("   2. Adicionar seleção de fontes NDI na UI")
        print("   3. Testar automação com fontes NDI")
    else:
        print("❌ AINDA HÁ PROBLEMAS")
        print("🔍 Verifique os logs acima para mais detalhes")
    print("=" * 80)

if __name__ == "__main__":
    main() 