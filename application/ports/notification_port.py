from typing import Protocol


class NotificationPort(Protocol):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Envia um email e retorna True se enviado com sucesso."""
        ...
