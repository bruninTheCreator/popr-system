"""
Email Adapter - Implementação de NotificationService via Email

Envia notificações por email usando SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from datetime import datetime

# Domain imports
from ...domain.entities.purchase_order import PurchaseOrder
from ...domain.interfaces.notification_service import NotificationService


class EmailConfig:
    """Configuração do servidor SMTP"""
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: str = "POPR System"
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name


class EmailNotificationService(NotificationService):
    """
    Implementação de NotificationService usando Email
    
    QUANDO USAR:
    - Notificações formais
    - Aprovações que precisam de registro
    - Relatórios detalhados
    
    TEMPLATES:
    - Aprovação requerida
    - PO aprovada
    - PO rejeitada
    - Erro no processamento
    - Processamento concluído
    """
    
    def __init__(
        self,
        config: EmailConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
    
    # =========================================================================
    # IMPLEMENTAÇÃO DA INTERFACE
    # =========================================================================
    
    async def notify_approval_required(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que uma PO precisa de aprovação
        """
        subject = f"[POPR] Aprovação Requerida - PO {po.po_number}"
        
        body = f"""
        <h2>Aprovação Requerida</h2>
        
        <p>A Purchase Order abaixo requer sua aprovação:</p>
        
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr>
                <td><strong>PO Number:</strong></td>
                <td>{po.po_number}</td>
            </tr>
            <tr>
                <td><strong>Fornecedor:</strong></td>
                <td>{po.vendor_name} ({po.vendor_code})</td>
            </tr>
            <tr>
                <td><strong>Valor Total:</strong></td>
                <td>{po.currency} {po.total_amount:,.2f}</td>
            </tr>
            <tr>
                <td><strong>Status:</strong></td>
                <td>{po.status.value}</td>
            </tr>
            <tr>
                <td><strong>Criada em:</strong></td>
                <td>{po.created_at.strftime('%d/%m/%Y %H:%M')}</td>
            </tr>
            <tr>
                <td><strong>Criada por:</strong></td>
                <td>{po.created_by}</td>
            </tr>
        </table>
        
        <h3>Itens da PO:</h3>
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr>
                <th>Item</th>
                <th>Descrição</th>
                <th>Quantidade</th>
                <th>Preço Unitário</th>
                <th>Total</th>
            </tr>
            {"".join([f'''
            <tr>
                <td>{item.item_number}</td>
                <td>{item.description}</td>
                <td>{item.quantity}</td>
                <td>{po.currency} {item.unit_price:,.2f}</td>
                <td>{po.currency} {item.total_price:,.2f}</td>
            </tr>
            ''' for item in po.items])}
        </table>
        
        <p>
            <strong>⚠️ Esta PO requer aprovação manual pois o valor excede o limite de aprovação automática.</strong>
        </p>
        
        <p>
            Para aprovar ou rejeitar, acesse o sistema POPR.
        </p>
        
        <hr>
        <small>Este é um email automático do sistema POPR - Purchase Order Processing and Reconciliation</small>
        """
        
        return await self._send_email(recipients, subject, body)
    
    async def notify_approved(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que uma PO foi aprovada
        """
        subject = f"[POPR] ✅ PO Aprovada - {po.po_number}"
        
        approval_type = "automática" if po.approved_by == "system" else "manual"
        
        body = f"""
        <h2>✅ Purchase Order Aprovada</h2>
        
        <p>A Purchase Order foi aprovada com sucesso!</p>
        
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr>
                <td><strong>PO Number:</strong></td>
                <td>{po.po_number}</td>
            </tr>
            <tr>
                <td><strong>Fornecedor:</strong></td>
                <td>{po.vendor_name}</td>
            </tr>
            <tr>
                <td><strong>Valor Total:</strong></td>
                <td>{po.currency} {po.total_amount:,.2f}</td>
            </tr>
            <tr>
                <td><strong>Tipo de Aprovação:</strong></td>
                <td>{approval_type.capitalize()}</td>
            </tr>
            <tr>
                <td><strong>Aprovada por:</strong></td>
                <td>{po.approved_by}</td>
            </tr>
            <tr>
                <td><strong>Aprovada em:</strong></td>
                <td>{po.approved_at.strftime('%d/%m/%Y %H:%M') if po.approved_at else 'N/A'}</td>
            </tr>
        </table>
        
        <p><strong>Status:</strong> {po.status.value}</p>
        
        <hr>
        <small>POPR System - Automated Notification</small>
        """
        
        return await self._send_email(recipients, subject, body)
    
    async def notify_rejected(
        self,
        po: PurchaseOrder,
        recipients: List[str],
        reason: str
    ) -> bool:
        """
        Notifica que uma PO foi rejeitada
        """
        subject = f"[POPR] ❌ PO Rejeitada - {po.po_number}"
        
        body = f"""
        <h2>❌ Purchase Order Rejeitada</h2>
        
        <p>A Purchase Order foi rejeitada.</p>
        
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr>
                <td><strong>PO Number:</strong></td>
                <td>{po.po_number}</td>
            </tr>
            <tr>
                <td><strong>Fornecedor:</strong></td>
                <td>{po.vendor_name}</td>
            </tr>
            <tr>
                <td><strong>Valor Total:</strong></td>
                <td>{po.currency} {po.total_amount:,.2f}</td>
            </tr>
            <tr>
                <td><strong>Rejeitada por:</strong></td>
                <td>{po.approved_by or 'N/A'}</td>
            </tr>
        </table>
        
        <h3>⚠️ Motivo da Rejeição:</h3>
        <p style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107;">
            {reason or po.rejection_reason or 'Não especificado'}
        </p>
        
        <p>A PO pode ser corrigida e reenviada para processamento.</p>
        
        <hr>
        <small>POPR System - Automated Notification</small>
        """
        
        return await self._send_email(recipients, subject, body)
    
    async def notify_error(
        self,
        po: PurchaseOrder,
        error_message: str,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que houve erro no processamento
        """
        subject = f"[POPR] 💥 Erro no Processamento - PO {po.po_number}"
        
        body = f"""
        <h2>💥 Erro no Processamento</h2>
        
        <p>Ocorreu um erro durante o processamento da Purchase Order:</p>
        
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr>
                <td><strong>PO Number:</strong></td>
                <td>{po.po_number}</td>
            </tr>
            <tr>
                <td><strong>Fornecedor:</strong></td>
                <td>{po.vendor_name}</td>
            </tr>
            <tr>
                <td><strong>Status:</strong></td>
                <td>{po.status.value}</td>
            </tr>
        </table>
        
        <h3>❌ Mensagem de Erro:</h3>
        <p style="background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; color: #721c24;">
            {error_message}
        </p>
        
        <p>O sistema tentará reprocessar automaticamente ou você pode tentar manualmente.</p>
        
        <hr>
        <small>POPR System - Error Notification</small>
        """
        
        return await self._send_email(recipients, subject, body)
    
    async def notify_completed(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que o processamento foi concluído
        """
        subject = f"[POPR] 🎉 Processamento Concluído - PO {po.po_number}"
        
        processing_time = po.get_processing_time()
        time_str = f"{processing_time.total_seconds():.2f} segundos" if processing_time else "N/A"
        
        body = f"""
        <h2>🎉 Processamento Concluído com Sucesso!</h2>
        
        <p>A Purchase Order foi processada e finalizada com sucesso:</p>
        
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr>
                <td><strong>PO Number:</strong></td>
                <td>{po.po_number}</td>
            </tr>
            <tr>
                <td><strong>Fornecedor:</strong></td>
                <td>{po.vendor_name}</td>
            </tr>
            <tr>
                <td><strong>Valor Total:</strong></td>
                <td>{po.currency} {po.total_amount:,.2f}</td>
            </tr>
            <tr>
                <td><strong>SAP Doc Number:</strong></td>
                <td>{po.sap_doc_number or 'N/A'}</td>
            </tr>
            <tr>
                <td><strong>Tempo de Processamento:</strong></td>
                <td>{time_str}</td>
            </tr>
            <tr>
                <td><strong>Status Final:</strong></td>
                <td style="color: green; font-weight: bold;">{po.status.value}</td>
            </tr>
        </table>
        
        <h3>✅ Próximos Passos:</h3>
        <ul>
            <li>Invoice postada no SAP</li>
            <li>Dados reconciliados com sucesso</li>
            <li>Processamento finalizado</li>
        </ul>
        
        <hr>
        <small>POPR System - Success Notification</small>
        """
        
        return await self._send_email(recipients, subject, body)
    
    # =========================================================================
    # MÉTODO PRIVADO PARA ENVIO
    # =========================================================================
    
    async def _send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> bool:
        """
        Envia email via SMTP
        """
        try:
            # Cria mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ", ".join(recipients)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Adiciona corpo HTML
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Conecta ao servidor SMTP
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                
                # Envia
                server.send_message(msg)
            
            self.logger.info(f"✅ Email sent to {recipients}: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send email: {str(e)}")
            return False