"""
Interface do Serviço de Notificações
"""
from abc import ABC, abstractmethod
from typing import List

from domain.entities.purchase_order import PurchaseOrder


class NotificationService(ABC):
    """Interface para envio de notificações."""

    @abstractmethod
    async def notify_approval_required(self, po: PurchaseOrder, recipients: List[str]) -> bool:
        pass

    @abstractmethod
    async def notify_approved(self, po: PurchaseOrder, recipients: List[str]) -> bool:
        pass

    @abstractmethod
    async def notify_rejected(self, po: PurchaseOrder, recipients: List[str], reason: str) -> bool:
        pass

    @abstractmethod
    async def notify_error(self, po: PurchaseOrder, error_message: str, recipients: List[str]) -> bool:
        pass

    @abstractmethod
    async def notify_completed(self, po: PurchaseOrder, recipients: List[str]) -> bool:
        pass
