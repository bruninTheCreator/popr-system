"""
Eventos de Domínio - Purchase Order
Cada evento representa algo que ACONTECEU no sistema (passado!)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal


@dataclass
class DomainEvent:
    """Classe base para eventos de domínio"""
    event_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    aggregate_id: str = ""  # ID da PO
    aggregate_type: str = "PurchaseOrder"
    event_version: int = 1


# =============================================================================
# EVENTOS DO CICLO DE VIDA DA PO
# =============================================================================

@dataclass
class POCreated(DomainEvent):
    """
    Evento: PO foi criada
    
    Disparado quando uma nova PO entra no sistema
    """
    po_number: str = ""
    vendor_code: str = ""
    vendor_name: str = ""
    total_amount: Decimal = Decimal("0")
    currency: str = "BRL"
    created_by: str = "system"
    
    def __post_init__(self):
        self.event_type = "po.created"


@dataclass
class POLocked(DomainEvent):
    """
    Evento: PO foi bloqueada para processamento
    
    Disparado quando alguém bloqueia a PO
    """
    po_number: str = ""
    locked_by: str = ""
    locked_at: datetime = field(default_factory=datetime.now)
    lock_duration_minutes: int = 30
    
    def __post_init__(self):
        self.event_type = "po.locked"


@dataclass
class POUnlocked(DomainEvent):
    """
    Evento: PO foi desbloqueada
    
    Disparado quando o lock é liberado (manual ou expiração)
    """
    po_number: str = ""
    unlocked_by: str = ""
    reason: str = ""  # "manual_release", "expired", "error"
    
    def __post_init__(self):
        self.event_type = "po.unlocked"


@dataclass
class POStatusChanged(DomainEvent):
    """
    Evento: Status da PO mudou
    
    Disparado em TODA mudança de status
    """
    po_number: str = ""
    from_status: str = ""
    to_status: str = ""
    changed_by: str = "system"
    reason: str = ""
    
    def __post_init__(self):
        self.event_type = "po.status_changed"


# =============================================================================
# EVENTOS DE PROCESSAMENTO (FLUXO POPR!)
# =============================================================================

@dataclass
class POProcessingStarted(DomainEvent):
    """
    Evento: Processamento da PO iniciado
    
    INÍCIO DO FLUXO POPR!
    """
    po_number: str = ""
    processor: str = ""
    
    def __post_init__(self):
        self.event_type = "po.processing_started"


@dataclass
class POValidated(DomainEvent):
    """
    Evento: PO foi validada
    
    Disparado após validação bem-sucedida
    """
    po_number: str = ""
    validation_result: bool = True
    errors: List[str] = field(default_factory=list)
    validated_by: str = "system"
    
    def __post_init__(self):
        self.event_type = "po.validated"


@dataclass
class SAPDataFetched(DomainEvent):
    """
    Evento: Dados foram buscados do SAP
    
    Disparado após buscar com sucesso no SAP
    """
    po_number: str = ""
    sap_doc_number: str = ""
    sap_fiscal_year: str = ""
    items_count: int = 0
    fetch_duration_seconds: float = 0.0
    
    def __post_init__(self):
        self.event_type = "po.sap_data_fetched"


@dataclass
class POReconciliationStarted(DomainEvent):
    """
    Evento: Reconciliação iniciada
    
    Início da comparação entre dados da PO e SAP
    """
    po_number: str = ""
    reconciliation_id: str = ""
    
    def __post_init__(self):
        self.event_type = "po.reconciliation_started"


@dataclass
class POReconciliationCompleted(DomainEvent):
    """
    Evento: Reconciliação completada
    
    Disparado após reconciliar dados
    """
    po_number: str = ""
    reconciliation_id: str = ""
    success: bool = True
    discrepancies: List[str] = field(default_factory=list)
    matched_items: int = 0
    total_items: int = 0
    
    def __post_init__(self):
        self.event_type = "po.reconciliation_completed"


@dataclass
class POReconciliationFailed(DomainEvent):
    """
    Evento: Reconciliação falhou
    
    Disparado quando reconciliação encontra erros críticos
    """
    po_number: str = ""
    reconciliation_id: str = ""
    errors: List[str] = field(default_factory=list)
    discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        self.event_type = "po.reconciliation_failed"


# =============================================================================
# EVENTOS DE APROVAÇÃO
# =============================================================================

@dataclass
class POApprovalRequired(DomainEvent):
    """
    Evento: PO requer aprovação manual
    
    Disparado quando PO > threshold e precisa aprovação
    """
    po_number: str = ""
    total_amount: Decimal = Decimal("0")
    threshold: Decimal = Decimal("10000")
    approvers: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.event_type = "po.approval_required"


@dataclass
class POApproved(DomainEvent):
    """
    Evento: PO foi aprovada
    
    Disparado quando alguém aprova a PO
    """
    po_number: str = ""
    approved_by: str = ""
    approved_at: datetime = field(default_factory=datetime.now)
    approval_notes: Optional[str] = None
    approval_type: str = "manual"  # "manual" ou "automatic"
    
    def __post_init__(self):
        self.event_type = "po.approved"


@dataclass
class POAutoApproved(DomainEvent):
    """
    Evento: PO foi aprovada automaticamente
    
    Disparado quando PO < threshold
    """
    po_number: str = ""
    total_amount: Decimal = Decimal("0")
    threshold: Decimal = Decimal("10000")
    reason: str = "Below approval threshold"
    
    def __post_init__(self):
        self.event_type = "po.auto_approved"


@dataclass
class PORejected(DomainEvent):
    """
    Evento: PO foi rejeitada
    
    Disparado quando alguém rejeita a PO
    """
    po_number: str = ""
    rejected_by: str = ""
    rejected_at: datetime = field(default_factory=datetime.now)
    rejection_reason: str = ""
    can_retry: bool = True
    
    def __post_init__(self):
        self.event_type = "po.rejected"


# =============================================================================
# EVENTOS DE INTEGRAÇÃO SAP
# =============================================================================

@dataclass
class SAPDocumentLocked(DomainEvent):
    """
    Evento: Documento bloqueado no SAP
    
    Disparado após bloquear com sucesso no SAP
    """
    po_number: str = ""
    sap_doc_number: str = ""
    locked_by: str = ""
    
    def __post_init__(self):
        self.event_type = "sap.document_locked"


@dataclass
class SAPDocumentUnlocked(DomainEvent):
    """
    Evento: Documento desbloqueado no SAP
    """
    po_number: str = ""
    sap_doc_number: str = ""
    unlocked_by: str = ""
    
    def __post_init__(self):
        self.event_type = "sap.document_unlocked"


@dataclass
class SAPInvoicePosted(DomainEvent):
    """
    Evento: Invoice postada no SAP
    
    Disparado após postar invoice com sucesso
    """
    po_number: str = ""
    invoice_number: str = ""
    sap_doc_number: str = ""
    posted_by: str = ""
    posted_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.event_type = "sap.invoice_posted"


# =============================================================================
# EVENTOS DE FINALIZAÇÃO
# =============================================================================

@dataclass
class POCompleted(DomainEvent):
    """
    Evento: PO finalizada com sucesso
    
    FIM DO FLUXO POPR! 🎉
    """
    po_number: str = ""
    completed_at: datetime = field(default_factory=datetime.now)
    processing_duration_seconds: float = 0.0
    total_amount: Decimal = Decimal("0")
    sap_doc_number: str = ""
    
    def __post_init__(self):
        self.event_type = "po.completed"


@dataclass
class POCancelled(DomainEvent):
    """
    Evento: PO foi cancelada
    """
    po_number: str = ""
    cancelled_by: str = ""
    cancellation_reason: str = ""
    
    def __post_init__(self):
        self.event_type = "po.cancelled"


# =============================================================================
# EVENTOS DE ERRO
# =============================================================================

@dataclass
class POErrorOccurred(DomainEvent):
    """
    Evento: Erro ocorreu durante processamento
    
    Disparado quando algo dá errado
    """
    po_number: str = ""
    error_type: str = ""  # "validation", "sap", "reconciliation", "system"
    error_message: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)
    can_retry: bool = True
    retry_count: int = 0
    
    def __post_init__(self):
        self.event_type = "po.error_occurred"


@dataclass
class PORetryScheduled(DomainEvent):
    """
    Evento: Retry agendado para PO com erro
    """
    po_number: str = ""
    retry_count: int = 0
    max_retries: int = 3
    retry_at: datetime = field(default_factory=datetime.now)
    original_error: str = ""
    
    def __post_init__(self):
        self.event_type = "po.retry_scheduled"


# =============================================================================
# EVENTOS DE NOTIFICAÇÃO
# =============================================================================

@dataclass
class NotificationSent(DomainEvent):
    """
    Evento: Notificação enviada
    
    Disparado após enviar email/slack/teams
    """
    po_number: str = ""
    notification_type: str = ""  # "email", "slack", "teams"
    recipients: List[str] = field(default_factory=list)
    subject: str = ""
    sent_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    
    def __post_init__(self):
        self.event_type = "notification.sent"


# =============================================================================
# EVENT PUBLISHER (Interface)
# =============================================================================

from abc import ABC, abstractmethod

class EventPublisher(ABC):
    """
    Interface para publicar eventos
    
    Pode ser implementado por:
    - InMemoryEventBus (simples)
    - RabbitMQPublisher (produção)
    - KafkaPublisher (alta escala)
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publica um evento"""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publica múltiplos eventos"""
        pass