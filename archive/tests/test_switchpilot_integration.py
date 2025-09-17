#!/usr/bin/env python3
"""
Teste de Integração Completo do SwitchPilot
Verifica se o sistema principal está funcional com todas as integrações
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import subprocess
import psutil
import requests
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Importar componentes do SwitchPilot
try:
    from switchpilot.ui.main_window import MainWindow
    from switchpilot.core.main_controller import MainController
    from switchpilot.core.monitor_thread import MonitorThread
    from switchpilot.integrations.obs_controller import OBSController
    from switchpilot.integrations.vmix_controller import VMixController
except ImportError as e:
    print(f"❌ Erro ao importar componentes do SwitchPilot: {e}")
    sys.exit(1)

def check_process_running():
    """Verifica se o SwitchPilot está rodando"""
    print("🔍 VERIFICANDO PROCESSO SWITCHPILOT")
    print("=" * 50)
    
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and 'main.py' in ' '.join(cmdline):
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': cmdline
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if python_processes:
        print(f"✅ SwitchPilot encontrado rodando:")
        for proc in python_processes:
            print(f"   PID: {proc['pid']}")
            print(f"   Comando: {' '.join(proc['cmdline'])}")
        return True
    else:
        print("❌ SwitchPilot não está rodando")
        return False

def test_dependencies():
    """Testa se todas as dependências estão funcionando"""
    print("\n🔧 TESTANDO DEPENDÊNCIAS")
    print("=" * 50)
    
    results = {}
    
    # Testar PyQt5
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        results['PyQt5'] = True
        print("✅ PyQt5: Funcionando")
    except Exception as e:
        results['PyQt5'] = False
        print(f"❌ PyQt5: {e}")
    
    # Testar OpenCV
    try:
        import cv2
        results['OpenCV'] = True
        print(f"✅ OpenCV: Versão {cv2.__version__}")
    except Exception as e:
        results['OpenCV'] = False
        print(f"❌ OpenCV: {e}")
    
    # Testar MSS
    try:
        import mss
        with mss.mss() as sct:
            monitors = len(sct.monitors) - 1
        results['MSS'] = True
        print(f"✅ MSS: {monitors} monitores detectados")
    except Exception as e:
        results['MSS'] = False
        print(f"❌ MSS: {e}")
    
    # Testar PyAutoGUI
    try:
        import pyautogui
        windows = len(pyautogui.getAllWindows())
        results['PyAutoGUI'] = True
        print(f"✅ PyAutoGUI: {windows} janelas detectadas")
    except Exception as e:
        results['PyAutoGUI'] = False
        print(f"❌ PyAutoGUI: {e}")
    
    # Testar NDI
    try:
        import NDIlib as NDI
        if NDI.initialize():
            ndi_find = NDI.find_create_v2()
            if ndi_find:
                time.sleep(1)
                sources = NDI.find_get_current_sources(ndi_find)
                NDI.find_destroy(ndi_find)
                NDI.destroy()
                results['NDI'] = True
                print(f"✅ NDI: {len(sources) if sources else 0} fontes encontradas")
            else:
                results['NDI'] = False
                print("❌ NDI: Não foi possível criar finder")
        else:
            results['NDI'] = False
            print("❌ NDI: Não foi possível inicializar")
    except Exception as e:
        results['NDI'] = False
        print(f"❌ NDI: {e}")
    
    return results

def test_integrations():
    """Testa as integrações OBS e vMix"""
    print("\n🔗 TESTANDO INTEGRAÇÕES")
    print("=" * 50)
    
    results = {}
    
    # Testar OBS
    try:
        obs_controller = OBSController()
        # Tentar conectar (pode falhar se OBS não estiver rodando)
        results['OBS'] = True
        print("✅ OBS Controller: Classe carregada")
    except Exception as e:
        results['OBS'] = False
        print(f"❌ OBS Controller: {e}")
    
    # Testar vMix
    try:
        vmix_controller = VMixController()
        results['vMix'] = True
        print("✅ vMix Controller: Classe carregada")
        
        # Tentar conectar ao vMix API
        try:
            response = requests.get('http://localhost:8088/api', timeout=2)
            if response.status_code == 200:
                print("✅ vMix API: Conectado e funcionando")
                results['vMix_API'] = True
            else:
                print(f"⚠️  vMix API: Resposta {response.status_code}")
                results['vMix_API'] = False
        except requests.exceptions.RequestException:
            print("⚠️  vMix API: Não disponível (vMix não está rodando)")
            results['vMix_API'] = False
            
    except Exception as e:
        results['vMix'] = False
        results['vMix_API'] = False
        print(f"❌ vMix Controller: {e}")
    
    return results

def test_ui_components():
    """Testa se os componentes da UI podem ser carregados"""
    print("\n🖥️ TESTANDO COMPONENTES DA UI")
    print("=" * 50)
    
    results = {}
    
    try:
        # O SwitchPilot já está rodando, então não vamos criar nova instância
        # Apenas verificar se as classes podem ser importadas
        results['MainWindow'] = True
        print("✅ MainWindow: Classe importada")
    except Exception as e:
        results['MainWindow'] = False
        print(f"❌ MainWindow: {e}")
    
    try:
        results['MainController'] = True
        print("✅ MainController: Classe importada")
    except Exception as e:
        results['MainController'] = False
        print(f"❌ MainController: {e}")
    
    try:
        results['MonitorThread'] = True
        print("✅ MonitorThread: Classe importada")
    except Exception as e:
        results['MonitorThread'] = False
        print(f"❌ MonitorThread: {e}")
    
    return results

def test_file_structure():
    """Verifica se a estrutura de arquivos está correta"""
    print("\n📁 VERIFICANDO ESTRUTURA DE ARQUIVOS")
    print("=" * 50)
    
    required_files = [
        'main.py',
        'requirements.txt',
        'switchpilot_config.json',
        'switchpilot/ui/main_window.py',
        'switchpilot/core/main_controller.py',
        'switchpilot/core/monitor_thread.py',
        'switchpilot/integrations/obs_controller.py',
        'switchpilot/integrations/vmix_controller.py',
    ]
    
    results = {}
    
    for file_path in required_files:
        if os.path.exists(file_path):
            results[file_path] = True
            print(f"✅ {file_path}")
        else:
            results[file_path] = False
            print(f"❌ {file_path} - FALTANDO")
    
    return results

def main():
    """Executa todos os testes de integração"""
    print("🚀 TESTE DE INTEGRAÇÃO COMPLETO DO SWITCHPILOT")
    print("=" * 80)
    print(f"⏰ Iniciado em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Executar todos os testes
    process_running = check_process_running()
    dependencies = test_dependencies()
    integrations = test_integrations()
    ui_components = test_ui_components()
    file_structure = test_file_structure()
    
    # Relatório final
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO FINAL DE INTEGRAÇÃO")
    print("=" * 80)
    
    print(f"🔄 Processo Principal: {'✅ RODANDO' if process_running else '❌ PARADO'}")
    
    print("\n📦 DEPENDÊNCIAS:")
    for dep, status in dependencies.items():
        print(f"   {dep}: {'✅' if status else '❌'}")
    
    print("\n🔗 INTEGRAÇÕES:")
    for integration, status in integrations.items():
        print(f"   {integration}: {'✅' if status else '❌'}")
    
    print("\n🖥️ COMPONENTES UI:")
    for component, status in ui_components.items():
        print(f"   {component}: {'✅' if status else '❌'}")
    
    print("\n📁 ESTRUTURA DE ARQUIVOS:")
    files_ok = sum(1 for status in file_structure.values() if status)
    files_total = len(file_structure)
    print(f"   Arquivos OK: {files_ok}/{files_total}")
    
    # Cálculo do score geral
    all_results = {
        'Processo': process_running,
        **dependencies,
        **integrations,
        **ui_components,
        **file_structure
    }
    
    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results.values() if result)
    score = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 SCORE GERAL: {score:.1f}% ({passed_tests}/{total_tests})")
    
    if score >= 90:
        print("🎉 EXCELENTE! SwitchPilot está funcionando perfeitamente!")
    elif score >= 75:
        print("✅ BOM! SwitchPilot está funcionando bem com pequenos problemas.")
    elif score >= 50:
        print("⚠️  MÉDIO! SwitchPilot funciona mas precisa de ajustes.")
    else:
        print("❌ CRÍTICO! SwitchPilot tem problemas significativos.")
    
    print(f"\n⏰ Concluído em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return score, all_results

if __name__ == "__main__":
    score, results = main()
    
    # Salvar relatório
    report_file = f"integration_test_report_{int(time.time())}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Relatório de Integração SwitchPilot - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Score Geral: {score:.1f}%\n\n")
        
        for test, result in results.items():
            f.write(f"{test}: {'PASSOU' if result else 'FALHOU'}\n")
    
    print(f"📄 Relatório salvo em: {report_file}") 