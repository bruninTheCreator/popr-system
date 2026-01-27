# popr/domain/entities/purchase_order.py
"""
Entidade de Domínio - Purchase Order
Esta é a RAINHA do sistema
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any


class POStatus(Enum):
    """Estados possíveis de uma Purchase Order"""
    DRAFT = "draft"                      # Rascunho
    PENDING = "pending"                  # Aguardando processamento
    LOCKED = "locked"                    # Bloqueada para processamento
    PROCESSING = "processing"            # Em processamento
    RECONCILING = "reconciling"          # Reconciliando dados
    AWAITING_APPROVAL = "awaiting_approval"  # Aguardando aprovação manual
    APPROVED = "approved"                # Aprovada
    REJECTED = "rejected"                # Rejeitada
    CANCELLED = "cancelled"              # Cancelada
    ERROR = "error"                      # Erro no processamento
    COMPLETED = "completed"              # Finalizada com sucesso


@dataclass
class POItem:
    """Item de uma Purchase Order"""
    item_number: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    material_code: Optional[str] = None
    
    def validate(self) -> bool:
        """Valida se o total está correto"""
        expected_total = self.quantity * self.unit_price
        return abs(expected_total - self.total_price) < Decimal("0.01")


@dataclass
class PurchaseOrder:
    """
    Entidade Principal - Purchase Order
    
    Representa uma ordem de compra com todas suas regras de negócio.
    Esta classe é INDEPENDENTE de infraestrutura (banco, SAP, etc).
    """
    
    # ========== IDENTIFICADORES ==========
    id: str
    po_number: str
    
    # ========== DADOS DO PEDIDO ==========
    vendor_code: str
    vendor_name: str
    total_amount: Decimal
    currency: str = "BRL"
    items: List[POItem] = field(default_factory=list)
    
    # ========== ESTADO E CONTROLE ==========
    status: POStatus = POStatus.DRAFT
    version: int = 1  # Para controle de concorrência otimista
    
    # ========== LOCK MANAGEMENT ==========
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None
    lock_expires_at: Optional[datetime] = None
    
    # ========== TIMESTAMPS ==========
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # ========== SAP INTEGRATION ==========
    sap_doc_number: Optional[str] = None
    sap_fiscal_year: Optional[str] = None
    sap_data: Dict[str, Any] = field(default_factory=dict)
    
    # ========== RECONCILIATION ==========
    reconciliation_status: Optional[str] = None
    reconciliation_notes: Optional[str] = None
    discrepancies: List[str] = field(default_factory=list)
    
    # ========== APROVAÇÃO ==========
    created_by: str = "system"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # ========== AUDITORIA ==========
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # ========================================================================
    # MÉTODOS DE NEGÓCIO
    # ========================================================================
    
    def can_transition_to(self, new_status: POStatus) -> bool:
        """
        Verifica se pode transitar para um novo status.
        
        Regra: Nem toda transição é válida!
        Exemplo: Não pode ir direto de PENDING pra COMPLETED
        """
        VALID_TRANSITIONS = {
            POStatus.DRAFT: [POStatus.PENDING, POStatus.CANCELLED],
            POStatus.PENDING: [POStatus.LOCKED, POStatus.CANCELLED],
            POStatus.LOCKED: [POStatus.PROCESSING, POStatus.PENDING, POStatus.ERROR],
            POStatus.PROCESSING: [POStatus.RECONCILING, POStatus.ERROR],
            POStatus.RECONCILING: [
                POStatus.AWAITING_APPROVAL,
                POStatus.APPROVED,
                POStatus.ERROR
            ],
            POStatus.AWAITING_APPROVAL: [POStatus.APPROVED, POStatus.REJECTED],
            POStatus.APPROVED: [POStatus.COMPLETED],
            POStatus.REJECTED: [POStatus.PENDING, POStatus.CANCELLED],
            POStatus.ERROR: [POStatus.PENDING, POStatus.CANCELLED],
            POStatus.CANCELLED: [],
            POStatus.COMPLETED: []
        }
        
        return new_status in VALID_TRANSITIONS.get(self.status, [])
    
    def transition_to(
        self,
        new_status: POStatus,
        reason: str = "",
        user: str = "system"
    ) -> None:
        """
        Muda o status da PO (com validação!)
        
        Args:
            new_status: Novo status
            reason: Motivo da mudança
            user: Quem fez a mudança
            
        Raises:
            ValueError: Se a transição for inválida
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Invalid transition: {self.status.value} -> {new_status.value}"
            )
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        self.version += 1
        
        self.add_event("status_changed", {
            "from": old_status.value,
            "to": new_status.value,
            "reason": reason,
            "user": user
        })
    
    def acquire_lock(self, user: str, duration_minutes: int = 30) -> None:
        """
        Bloqueia a PO para processamento.
        
        Regra: Só uma pessoa pode processar a PO por vez!
        
        Args:
            user: Usuário que vai processar
            duration_minutes: Tempo do lock em minutos
            
        Raises:
            ValueError: Se já estiver bloqueada
        """
        if self.is_locked():
            raise ValueError(
                f"PO already locked by {self.locked_by} until {self.lock_expires_at}"
            )
        
        self.locked_by = user
        self.locked_at = datetime.now()
        self.lock_expires_at = datetime.now() + timedelta(minutes=duration_minutes)
        
        self.transition_to(POStatus.LOCKED, f"Locked by {user}", user)
        
        self.add_event("lock_acquired", {
            "user": user,
            "expires_at": self.lock_expires_at.isoformat()
        })
    
    def release_lock(self, user: str) -> None:
        """
        Libera o lock da PO.
        
        Args:
            user: Usuário que vai liberar
            
        Raises:
            ValueError: Se não estiver bloqueada ou se não for o dono do lock
        """
        if not self.is_locked():
            return
        
        if self.locked_by != user:
            raise ValueError(
                f"Cannot release lock. Locked by {self.locked_by}, "
                f"trying to release by {user}"
            )
        
        self.locked_by = None
        self.locked_at = None
        self.lock_expires_at = None
        
        self.add_event("lock_released", {"user": user})
    
    def is_locked(self) -> bool:
        """
        Verifica se a PO está bloqueada.
        
        Regra: Se o lock expirou, libera automaticamente!
        """
        if not self.locked_by:
            return False
        
        # Verifica se o lock expirou
        if self.lock_expires_at and datetime.now() > self.lock_expires_at:
            self.locked_by = None
            self.locked_at = None
            self.lock_expires_at = None
            self.add_event("lock_expired", {})
            return False
        
        return True
    
    def requires_approval(self) -> bool:
        """
        Verifica se a PO precisa de aprovação manual.
        
        Regra de Negócio: POs acima de R$ 10.000 precisam de aprovação!
        """
        APPROVAL_THRESHOLD = Decimal("10000.00")
        return self.total_amount > APPROVAL_THRESHOLD
    
    def validate(self) -> tuple[bool, List[str]]:
        errors = []
        
        # Valida valor
        if self.total_amount <= 0:
            errors.append("Total amount must be positive")
        
        # Valida vendor
        if not self.vendor_code or len(self.vendor_code) < 3:
            errors.append("Invalid vendor code")
        
        if not self.vendor_name:
            errors.append("Vendor name is required")
        
        # Valida moeda
        VALID_CURRENCIES = ["BRL", "USD", "EUR"]
        if self.currency not in VALID_CURRENCIES:
            errors.append(f"Invalid currency: {self.currency}. Must be one of {VALID_CURRENCIES}")
        
        # Valida itens
        if not self.items:
            errors.append("PO must have at least one item")
        
        # Valida total dos itens
        if self.items:
            items_total = sum(item.total_price for item in self.items)
            if abs(items_total - self.total_amount) > Decimal("0.01"):
                errors.append(
                    f"Items total ({items_total}) doesn't match PO total ({self.total_amount})"
                )
        
        # Valida cada item
        for idx, item in enumerate(self.items):
            if not item.validate():
                errors.append(f"Item {idx + 1} has invalid calculations")
        
        return len(errors) == 0, errors
    
    def approve(self, user: str, notes: Optional[str] = None) -> None:
        if self.status not in [POStatus.AWAITING_APPROVAL, POStatus.RECONCILING]:
            raise ValueError(f"Cannot approve PO in status {self.status.value}")
        
        self.approved_by = user
        self.approved_at = datetime.now()
        
        self.transition_to(POStatus.APPROVED, notes or "Approved", user)
        
        self.add_event("approved", {
            "user": user,
            "notes": notes
        })
    
    def reject(self, user: str, reason: str) -> None:
        if self.status != POStatus.AWAITING_APPROVAL:
            raise ValueError(f"Cannot reject PO in status {self.status.value}")
        
        self.rejection_reason = reason
        
        self.transition_to(POStatus.REJECTED, reason, user)
        
        self.add_event("rejected", {
            "user": user,
            "reason": reason
        })
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "status": self.status.value,
            "version": self.version,
            "data": data
        }
        self.events.append(event)
    
    def get_processing_time(self) -> Optional[timedelta]:
        """Calcula quanto tempo levou para processar"""
        if self.status == POStatus.COMPLETED and self.approved_at:
            return self.approved_at - self.created_at
        return None
    
    def __str__(self) -> str:
        return (
            f"PO({self.po_number}, "
            f"status={self.status.value}, "
            f"amount={self.total_amount} {self.currency})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()