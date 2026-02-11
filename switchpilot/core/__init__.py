"""
Core - Núcleo do SwitchPilot

Contém os controladores principais:
- MainController: Orquestra UI, referências e integrações
- MonitorThread: Thread de monitoramento e detecção
"""

from .main_controller import MainController
from .monitor_thread import MonitorThread

__all__ = ['MainController', 'MonitorThread']
