from typing import Optional
import logging

from ...application.ports.notification_port import NotificationPort


class SimpleEmailNotification(NotificationPort):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def send_email(self, to: str, subject: str, body: str) -> bool:
        self.logger.info(
            "Sending email to=%s subject=%s body=%s",
            to,
            subject,
            body,
        )
        return True
