"""
SwitchPilot - Automação de corte de cenas para lives

Módulo principal do SwitchPilot, contendo:
- core: Controladores principais e thread de monitoramento
- integrations: Integrações OBS, vMix e NDI
- ui: Interface gráfica PyQt5
"""

from switchpilot.utils.paths import get_resource_path


def _get_version():
    """Lê a versão do arquivo VERSION na raiz do projeto"""
    try:
        # Caminho para o arquivo VERSION na raiz do projeto
        version_file = get_resource_path('VERSION')
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except (FileNotFoundError, IOError):
        # Fallback se o arquivo não existir
        return "1.5.2"


__version__ = _get_version()
__author__ = "Fabianob19"
__license__ = "MIT"
