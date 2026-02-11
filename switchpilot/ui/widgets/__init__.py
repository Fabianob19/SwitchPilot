"""
Widgets - Componentes da Interface

Widgets principais:
- ReferenceManagerWidget: Gerenciamento de referências e ROI
- MonitoringControlWidget: Controle de monitoramento e logs
- OBSConfigWidget: Configuração OBS
- VMixConfigWidget: Configuração vMix
- CustomTitleBar: Barra de título customizada
- ActionConfigDialog: Diálogo de configuração de ações
- ThresholdConfigDialog: Diálogo de configuração de limiares
"""

from .reference_manager import ReferenceManagerWidget
from .monitoring_control_widget import MonitoringControlWidget
from .obs_config import OBSConfigWidget
from .vmix_config import VMixConfigWidget
from .custom_title_bar import CustomTitleBar
from .action_config_dialog import ActionConfigDialog
from .threshold_config_dialog import ThresholdConfigDialog

__all__ = [
    'ReferenceManagerWidget',
    'MonitoringControlWidget',
    'OBSConfigWidget',
    'VMixConfigWidget',
    'CustomTitleBar',
    'ActionConfigDialog',
    'ThresholdConfigDialog',
]
