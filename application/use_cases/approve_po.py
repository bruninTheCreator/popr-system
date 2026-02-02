# popr/application/use_cases/approve_po.py
"""
Use Case: Approve or Reject Purchase Order

Para aprovações manuais de POs que precisam de autorização
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import logging

# Domain imports
from domain.entities.purchase_order import PurchaseOrder, POStatus
from domain.interfaces.po_repository import PORepository
from domain.interfaces.sap_gateway import SAPGateway
from domain.interfaces.notification_service import NotificationService
from domain.exceptions.domain_exceptions import (
    PONotFoundException,
    InvalidApprovalException,
    InvalidRejectionException
)


# =============================================================================
# COMANDOS
# =============================================================================

@dataclass
class ApprovePOCommand:
    """Comando para aprovar uma PO"""
    po_number: str
    approved_by: str
    notes: Optional[str] = None
    post_invoice: bool = True  # Se deve postar invoice automaticamente
    notify: bool = True


@dataclass
class RejectPOCommand:
    """Comando para rejeitar uma PO"""
    po_number: str
    rejected_by: str
    reason: str  # Obrigatório!
    can_retry: bool = True  # Se pode ser reprocessada depois
    notify: bool = True


@dataclass
class ApprovalResult:
    """Resultado da aprovação/rejeição"""
    success: bool
    po: Optional[PurchaseOrder]
    message: str
    action: str  # "approved", "rejected"
    invoice_posted: bool = False
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


# =============================================================================
# USE CASE: APPROVE PO
# =============================================================================

class ApprovePOUseCase:
    """
    Use Case: Aprova uma Purchase Order manualmente
    
    QUANDO USAR:
    - PO acima do threshold (> R$ 10.000)
    - Aprovação forçada pelo usuário
    - Casos especiais que precisam de análise manual
    
    FLUXO:
    1. Busca a PO
    2. Valida se pode ser aprovada
    3. Aprova
    4. Posta invoice (opcional)
    5. Finaliza
    6. Notifica
    """
    
    def __init__(
        self,
        po_repository: PORepository,
        sap_gateway: SAPGateway,
        notification_service: NotificationService,
        logger: Optional[logging.Logger] = None
    ):
        self.po_repo = po_repository
        self.sap = sap_gateway
        self.notifier = notification_service
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self, command: ApprovePOCommand) -> ApprovalResult:
        """
        Executa a aprovação da PO
        """
        try:
            # ================================================================
            # PASSO 1: BUSCAR A PO
            # ================================================================
            self.logger.info(f"Approving PO {command.po_number} by {command.approved_by}")
            
            po = await self.po_repo.get_by_po_number(command.po_number)
            
            if not po:
                raise PONotFoundException(command.po_number)
            
            # ================================================================
            # PASSO 2: VALIDAR SE PODE APROVAR
            # ================================================================
            if po.status != POStatus.AWAITING_APPROVAL:
                raise InvalidApprovalException(
                    po.po_number,
                    po.status.value,
                    f"PO must be in AWAITING_APPROVAL status, but is in {po.status.value}"
                )
            
            # ================================================================
            # PASSO 3: APROVAR
            # ================================================================
            po.approve(
                user=command.approved_by,
                notes=command.notes
            )
            
            await self.po_repo.save(po)
            
            self.logger.info(f"✅ PO {command.po_number} approved by {command.approved_by}")
            
            # ================================================================
            # PASSO 4: POSTAR INVOICE (se solicitado)
            # ================================================================
            invoice_posted = False
            
            if command.post_invoice:
                try:
                    invoice_posted = await self._post_invoice(po)
                    
                    if invoice_posted:
                        # Finaliza a PO
                        po.transition_to(
                            POStatus.COMPLETED,
                            "Completed after approval",
                            command.approved_by
                        )
                        await self.po_repo.save(po)
                        
                except Exception as e:
                    self.logger.error(f"Failed to post invoice: {str(e)}")
                    # Não falha a aprovação por causa disso
            
            # ================================================================
            # PASSO 5: NOTIFICAR
            # ================================================================
            if command.notify:
                try:
                    await self.notifier.notify_approved(
                        po,
                        recipients=[po.created_by, command.approved_by]
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to send notification: {str(e)}")
            
            # ================================================================
            # SUCESSO! ✅
            # ================================================================
            return ApprovalResult(
                success=True,
                po=po,
                message=f"PO {command.po_number} approved successfully",
                action="approved",
                invoice_posted=invoice_posted
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error approving PO {command.po_number}: {str(e)}")
            
            return ApprovalResult(
                success=False,
                po=po if 'po' in locals() else None,
                message=f"Failed to approve PO: {str(e)}",
                action="approved",
                errors=[str(e)]
            )
    
    async def _post_invoice(self, po: PurchaseOrder) -> bool:
        """Posta invoice no SAP"""
        try:
            invoice_data = {
                "po_number": po.po_number,
                "vendor_code": po.vendor_code,
                "total_amount": float(po.total_amount),
                "currency": po.currency,
                "items": [
                    {
                        "item_number": item.item_number,
                        "quantity": float(item.quantity),
                        "unit_price": float(item.unit_price)
                    }
                    for item in po.items
                ]
            }
            
            invoice_number = await self.sap.post_invoice(po.po_number, invoice_data)
            
            self.logger.info(f"Invoice {invoice_number} posted for PO {po.po_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to post invoice: {str(e)}")
            return False


# =============================================================================
# USE CASE: REJECT PO
# =============================================================================

class RejectPOUseCase:
    """
    Use Case: Rejeita uma Purchase Order
    
    QUANDO USAR:
    - Dados incorretos
    - Valor não autorizado
    - Vendor não aprovado
    - Qualquer motivo que impeça o processamento
    
    FLUXO:
    1. Busca a PO
    2. Valida se pode ser rejeitada
    3. Rejeita
    4. Libera locks
    5. Notifica
    """
    
    def __init__(
        self,
        po_repository: PORepository,
        notification_service: NotificationService,
        logger: Optional[logging.Logger] = None
    ):
        self.po_repo = po_repository
        self.notifier = notification_service
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self, command: RejectPOCommand) -> ApprovalResult:
        """
        Executa a rejeição da PO
        """
        try:
            # ================================================================
            # PASSO 1: BUSCAR A PO
            # ================================================================
            self.logger.info(f"Rejecting PO {command.po_number} by {command.rejected_by}")
            
            po = await self.po_repo.get_by_po_number(command.po_number)
            
            if not po:
                raise PONotFoundException(command.po_number)
            
            # ================================================================
            # PASSO 2: VALIDAR SE PODE REJEITAR
            # ================================================================
            if po.status != POStatus.AWAITING_APPROVAL:
                raise InvalidRejectionException(
                    po.po_number,
                    po.status.value,
                    f"PO must be in AWAITING_APPROVAL status, but is in {po.status.value}"
                )
            
            # ================================================================
            # PASSO 3: REJEITAR
            # ================================================================
            po.reject(
                user=command.rejected_by,
                reason=command.reason
            )
            
            await self.po_repo.save(po)
            
            self.logger.info(f"❌ PO {command.po_number} rejected by {command.rejected_by}")
            
            # ================================================================
            # PASSO 4: LIBERAR LOCKS (se houver)
            # ================================================================
            if po.is_locked():
                try:
                    po.release_lock(command.rejected_by)
                    await self.po_repo.save(po)
                except Exception as e:
                    self.logger.warning(f"Failed to release lock: {str(e)}")
            
            # ================================================================
            # PASSO 5: NOTIFICAR
            # ================================================================
            if command.notify:
                try:
                    await self.notifier.notify_rejected(
                        po,
                        recipients=[po.created_by, command.rejected_by],
                        reason=command.reason
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to send notification: {str(e)}")
            
            # ================================================================
            # SUCESSO! ✅
            # ================================================================
            return ApprovalResult(
                success=True,
                po=po,
                message=f"PO {command.po_number} rejected: {command.reason}",
                action="rejected"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error rejecting PO {command.po_number}: {str(e)}")
            
            return ApprovalResult(
                success=False,
                po=po if 'po' in locals() else None,
                message=f"Failed to reject PO: {str(e)}",
                action="rejected",
                errors=[str(e)]
            )


# =============================================================================
# USE CASE: BULK APPROVE (Bônus!)
# =============================================================================

@dataclass
class BulkApproveCommand:
    """Comando para aprovar múltiplas POs de uma vez"""
    po_numbers: List[str]
    approved_by: str
    notes: Optional[str] = None
    post_invoices: bool = True
    notify: bool = True


@dataclass
class BulkApprovalResult:
    """Resultado da aprovação em lote"""
    total: int
    approved: int
    failed: int
    results: List[ApprovalResult]
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso em %"""
        return (self.approved / self.total * 100) if self.total > 0 else 0.0


class BulkApprovePOUseCase:
    """
    Use Case: Aprova múltiplas POs de uma vez
    
    Útil para:
    - Aprovar várias POs de um mesmo fornecedor
    - Aprovação em lote de POs similares
    - Processamento batch
    """
    
    def __init__(
        self,
        approve_use_case: ApprovePOUseCase,
        logger: Optional[logging.Logger] = None
    ):
        self.approve_use_case = approve_use_case
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self, command: BulkApproveCommand) -> BulkApprovalResult:
        """
        Aprova múltiplas POs
        """
        results = []
        approved_count = 0
        failed_count = 0
        
        self.logger.info(
            f"Bulk approving {len(command.po_numbers)} POs by {command.approved_by}"
        )
        
        for po_number in command.po_numbers:
            try:
                # Aprova cada uma individualmente
                result = await self.approve_use_case.execute(
                    ApprovePOCommand(
                        po_number=po_number,
                        approved_by=command.approved_by,
                        notes=command.notes,
                        post_invoice=command.post_invoices,
                        notify=False  # Notifica no final
                    )
                )
                
                results.append(result)
                
                if result.success:
                    approved_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to approve PO {po_number}: {str(e)}")
                
                results.append(ApprovalResult(
                    success=False,
                    po=None,
                    message=f"Error: {str(e)}",
                    action="approved",
                    errors=[str(e)]
                ))
                failed_count += 1
        
        # Resultado final
        bulk_result = BulkApprovalResult(
            total=len(command.po_numbers),
            approved=approved_count,
            failed=failed_count,
            results=results
        )
        
        self.logger.info(
            f"✅ Bulk approval completed: "
            f"{approved_count}/{len(command.po_numbers)} approved "
            f"({bulk_result.success_rate:.1f}% success rate)"
        )
        
        return bulk_result


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

"""
# Aprovar uma PO
approve_use_case = ApprovePOUseCase(repo, sap, notifier)

result = await approve_use_case.execute(
    ApprovePOCommand(
        po_number="PO-12345",
        approved_by="maria.silva",
        notes="Aprovado após verificação manual",
        post_invoice=True
    )
)

if result.success:
    print(f"✅ {result.message}")
    if result.invoice_posted:
        print("📄 Invoice postada com sucesso!")
else:
    print(f"❌ {result.message}")


# Rejeitar uma PO
reject_use_case = RejectPOUseCase(repo, notifier)

result = await reject_use_case.execute(
    RejectPOCommand(
        po_number="PO-67890",
        rejected_by="maria.silva",
        reason="Vendor não autorizado para este tipo de compra",
        can_retry=False
    )
)


# Aprovar múltiplas POs
bulk_use_case = BulkApprovePOUseCase(approve_use_case)

result = await bulk_use_case.execute(
    BulkApproveCommand(
        po_numbers=["PO-001", "PO-002", "PO-003"],
        approved_by="maria.silva",
        notes="Aprovação em lote - vendor ABC"
    )
)

print(f"Aprovadas: {result.approved}/{result.total}")
print(f"Taxa de sucesso: {result.success_rate:.1f}%")
"""
