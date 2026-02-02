"""
Slack Adapter - Notificações via Slack

Para notificações rápidas e informais
"""
import aiohttp
from typing import List, Optional
import logging

from domain.entities.purchase_order import PurchaseOrder
from domain.interfaces.notification_service import NotificationService


class SlackNotificationService(NotificationService):
    """
    Implementação usando Slack Webhooks
    
    QUANDO USAR:
    - Notificações rápidas
    - Alertas em tempo real
    - Comunicação informal da equipe
    
    SETUP:
    1. Criar Incoming Webhook no Slack
    2. Obter webhook URL
    3. Configurar este adapter
    """
    
    def __init__(
        self,
        webhook_url: str,
        channel: str = "#popr-notifications",
        username: str = "POPR Bot",
        logger: Optional[logging.Logger] = None
    ):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.logger = logger or logging.getLogger(__name__)
    
    async def notify_approval_required(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """Notifica aprovação requerida via Slack"""
        
        message = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":clipboard:",
            "attachments": [
                {
                    "color": "#ff9800",
                    "title": f"⚠️ Aprovação Requerida - PO {po.po_number}",
                    "fields": [
                        {"title": "Fornecedor", "value": po.vendor_name, "short": True},
                        {"title": "Valor", "value": f"{po.currency} {po.total_amount:,.2f}", "short": True},
                        {"title": "Status", "value": po.status.value, "short": True},
                        {"title": "Criada por", "value": po.created_by, "short": True}
                    ],
                    "footer": "POPR System",
                    "ts": int(po.created_at.timestamp())
                }
            ]
        }
        
        return await self._send_slack_message(message)
    
    async def notify_approved(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """Notifica aprovação via Slack"""
        
        message = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":white_check_mark:",
            "attachments": [
                {
                    "color": "#4caf50",
                    "title": f"✅ PO Aprovada - {po.po_number}",
                    "fields": [
                        {"title": "Fornecedor", "value": po.vendor_name, "short": True},
                        {"title": "Valor", "value": f"{po.currency} {po.total_amount:,.2f}", "short": True},
                        {"title": "Aprovada por", "value": po.approved_by or "Sistema", "short": True}
                    ],
                    "footer": "POPR System"
                }
            ]
        }
        
        return await self._send_slack_message(message)
    
    async def notify_rejected(
        self,
        po: PurchaseOrder,
        recipients: List[str],
        reason: str
    ) -> bool:
        """Notifica rejeição via Slack"""
        
        message = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":x:",
            "attachments": [
                {
                    "color": "#f44336",
                    "title": f"❌ PO Rejeitada - {po.po_number}",
                    "fields": [
                        {"title": "Fornecedor", "value": po.vendor_name, "short": True},
                        {"title": "Motivo", "value": reason, "short": False}
                    ],
                    "footer": "POPR System"
                }
            ]
        }
        
        return await self._send_slack_message(message)
    
    async def notify_error(
        self,
        po: PurchaseOrder,
        error_message: str,
        recipients: List[str]
    ) -> bool:
        """Notifica erro via Slack"""
        
        message = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":rotating_light:",
            "attachments": [
                {
                    "color": "#dc3545",
                    "title": f"💥 Erro - PO {po.po_number}",
                    "fields": [
                        {"title": "Erro", "value": error_message, "short": False}
                    ],
                    "footer": "POPR System - Erro crítico!"
                }
            ]
        }
        
        return await self._send_slack_message(message)
    
    async def notify_completed(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """Notifica conclusão via Slack"""
        
        processing_time = po.get_processing_time()
        time_str = f"{processing_time.total_seconds():.2f}s" if processing_time else "N/A"
        
        message = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":tada:",
            "attachments": [
                {
                    "color": "#2196f3",
                    "title": f"🎉 Processamento Concluído - {po.po_number}",
                    "fields": [
                        {"title": "Fornecedor", "value": po.vendor_name, "short": True},
                        {"title": "Valor", "value": f"{po.currency} {po.total_amount:,.2f}", "short": True},
                        {"title": "Tempo", "value": time_str, "short": True},
                        {"title": "SAP Doc", "value": po.sap_doc_number or "N/A", "short": True}
                    ],
                    "footer": "POPR System - Sucesso!"
                }
            ]
        }
        
        return await self._send_slack_message(message)
    
    async def _send_slack_message(self, message: dict) -> bool:
        """Envia mensagem para Slack"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    if response.status == 200:
                        self.logger.info("✅ Slack notification sent")
                        return True
                    else:
                        self.logger.error(f"❌ Slack error: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Failed to send Slack message: {str(e)}")
            return False

    # Compatibilidade com interfaces antigas
    def send_email(self, to: List[str], subject: str, body: str) -> bool:
        self.logger.info("send_email called for %s (not supported)", to)
        return False

    def send_slack_message(self, channel: str, message: str) -> bool:
        self.logger.info("send_slack_message called for %s (sync fallback)", channel)
        return False

    def notify_po_status_change(self, po_number: str, new_status: str, recipients: List[str]) -> None:
        self.logger.info("PO %s status -> %s (%s)", po_number, new_status, recipients)
