# =============================================================================
# popr/domain/interfaces/__init__.py
"""
Exports das interfaces do domínio
"""
from .po_repository import PORepository
from .sap_gateway import SAPGateway
from .notification_service import NotificationService

__all__ = [
    "PORepository",
    "SAPGateway",
    "NotificationService"
]