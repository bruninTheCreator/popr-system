from typing import List, Optional
import logging

from domain.entities.purchase_order import PurchaseOrder
from domain.interfaces.notification_service import NotificationService


class SimpleNotificationService(NotificationService):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    async def notify_approval_required(self, po: PurchaseOrder, recipients: List[str]) -> bool:
        self.logger.info("Approval required for PO %s -> %s", po.po_number, recipients)
        return True

    async def notify_approved(self, po: PurchaseOrder, recipients: List[str]) -> bool:
        self.logger.info("PO approved %s -> %s", po.po_number, recipients)
        return True

    async def notify_rejected(self, po: PurchaseOrder, recipients: List[str], reason: str) -> bool:
        self.logger.info("PO rejected %s reason=%s -> %s", po.po_number, reason, recipients)
        return True

    async def notify_error(self, po: PurchaseOrder, error_message: str, recipients: List[str]) -> bool:
        self.logger.info("PO error %s error=%s -> %s", po.po_number, error_message, recipients)
        return True

    async def notify_completed(self, po: PurchaseOrder, recipients: List[str]) -> bool:
        self.logger.info("PO completed %s -> %s", po.po_number, recipients)
        return True

    def send_email(self, to: List[str], subject: str, body: str) -> bool:
        self.logger.info("Email to=%s subject=%s body=%s", to, subject, body)
        return True

    def send_slack_message(self, channel: str, message: str) -> bool:
        self.logger.info("Slack channel=%s message=%s", channel, message)
        return True

    def notify_po_status_change(self, po_number: str, new_status: str, recipients: List[str]) -> None:
        self.logger.info("PO status change %s -> %s (%s)", po_number, new_status, recipients)
