# popr/domain/interfaces/notification_service.py
"""
Interface - Notification Service
Contrato para serviços de notificação
"""

from abc import ABC, abstractmethod
from typing import List


class NotificationService(ABC):
    """Interface para serviço de notificações"""
    
    @abstractmethod
    def send_email(self, to: List[str], subject: str, body: str) -> bool:
        """Envia email"""
        pass
    
    @abstractmethod
    def send_slack_message(self, channel: str, message: str) -> bool:
        """Envia mensagem Slack"""
        pass
    
    @abstractmethod
    def notify_po_status_change(self, po_number: str, new_status: str, recipients: List[str]) -> None:
        """Notifica mudança de status da PO"""
        pass