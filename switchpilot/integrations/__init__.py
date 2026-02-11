"""
Integrations - Integrações com softwares de streaming

Contém controladores para:
- OBSController: Integração com OBS Studio (WebSocket 5.x)
- VMixController: Integração com vMix (API HTTP)
- NDIController: Integração NDI (opcional)
"""

from .obs_controller import OBSController
from .vmix_controller import VMixController
from .ndi_controller import NDIController

__all__ = ['OBSController', 'VMixController', 'NDIController']
