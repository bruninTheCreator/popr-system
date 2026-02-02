# popr/application/use_cases/process_po.py
"""
Use Case: Process Purchase Order

Este é o MAESTRO do sistema! 
Orquestra todo o fluxo POPR do início ao fim.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import logging
from decimal import Decimal

# Domain imports
from domain.entities.purchase_order import PurchaseOrder, POStatus
from domain.interfaces.po_repository import PORepository
from domain.interfaces.sap_gateway import SAPGateway
from domain.interfaces.notification_service import NotificationService
from domain.exceptions.domain_exceptions import (
    PONotFoundException,
    POValidationException,
    POAlreadyLockedException,
    ReconciliationException
)
from domain.events.po_events import (
    POProcessingStarted,
    POValidated,
    SAPDataFetched,
    SAPDocumentLocked,
    POReconciliationStarted,
    POReconciliationCompleted,
    POReconciliationFailed,
    POApprovalRequired,
    POAutoApproved,
    POApproved,
    SAPInvoicePosted,
    POCompleted,
    POErrorOccurred,
    NotificationSent
)


# =============================================================================
# COMMANDO - O que queremos fazer
# =============================================================================

@dataclass
class ProcessPOCommand:
    """
    Commando para processar uma PO
    
    Este é o INPUT do use case
    """
    po_number: str
    user: str  # Quem está processando
    force_approval: bool = False  # Força aprovação manual mesmo < threshold
    skip_sap_lock: bool = False  # Para testes
    notify_on_complete: bool = True


@dataclass
class ProcessPOResult:
    """
    Resultado do processamento
    
    Este é o OUTPUT do use case
    """
    success: bool
    po: Optional[PurchaseOrder]
    message: str
    errors: List[str]
    processing_time_seconds: float
    events_published: int
    
    # Detalhes do processamento
    validation_passed: bool = False
    sap_sync_completed: bool = False
    reconciliation_passed: bool = False
    approval_status: str = "pending"  # "auto", "manual", "rejected"
    invoice_posted: bool = False


# =============================================================================
# USE CASE - A lógica de orquestração
# =============================================================================

class ProcessPOUseCase:
    """
    Use Case: Processa uma Purchase Order do início ao fim
    
    RESPONSABILIDADES:
    1. Buscar a PO
    2. Validar dados
    3. Bloquear no SAP
    4. Buscar dados do SAP
    5. Reconciliar
    6. Aprovar (automático ou manual)
    7. Postar invoice
    8. Finalizar
    9. Notificar
    
    IMPORTANT: Este use case NÃO tem lógica de negócio!
    Ele apenas ORQUESTRA chamadas ao domain e aos adapters.
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
        
    async def execute(self, command: ProcessPOCommand) -> ProcessPOResult:
        """
        Executa o processamento completo da PO
        
        Este é o FLUXO PRINCIPAL do POPR! 🎯
        """
        start_time = datetime.now()
        po = None
        errors = []
        events_count = 0
        
        try:
            # ================================================================
            # PASSO 1: BUSCAR A PO
            # ================================================================
            self.logger.info(f"[STEP 1] Fetching PO {command.po_number}")
            
            po = await self._fetch_po(command.po_number)

            if po.status == POStatus.ERROR:
                po.transition_to(POStatus.PENDING, "Requeue after error", command.user)
                await self.po_repo.save(po)
            
            # Publica evento
            events_count += 1
            
            # ================================================================
            # PASSO 2: VALIDAR DADOS
            # ================================================================
            self.logger.info(f"[STEP 2] Validating PO {command.po_number}")
            
            validation_passed, validation_errors = await self._validate_po(po)
            
            if not validation_passed:
                return self._build_error_result(
                    po, validation_errors, start_time, events_count
                )
            
            events_count += 1
            
            # ================================================================
            # PASSO 3: BLOQUEAR A PO (para processamento)
            # ================================================================
            self.logger.info(f"[STEP 3] Acquiring lock on PO {command.po_number}")
            
            await self._acquire_lock(po, command.user)
            events_count += 1
            
            # Marca que começou o processamento
            po.transition_to(POStatus.PROCESSING, "Starting processing", command.user)
            await self.po_repo.save(po)
            events_count += 1
            
            # ================================================================
            # PASSO 4: BLOQUEAR NO SAP (se necessário)
            # ================================================================
            if not command.skip_sap_lock and po.sap_doc_number:
                self.logger.info(f"[STEP 4] Locking SAP document {po.sap_doc_number}")
                
                sap_locked = await self._lock_sap_document(po)
                if sap_locked:
                    events_count += 1
            
            # ================================================================
            # PASSO 5: BUSCAR DADOS DO SAP
            # ================================================================
            self.logger.info(f"[STEP 5] Fetching SAP data for PO {command.po_number}")
            
            sap_data = await self._fetch_sap_data(po)
            po.sap_data = sap_data
            await self.po_repo.save(po)
            events_count += 1
            
            # ================================================================
            # PASSO 6: RECONCILIAR DADOS
            # ================================================================
            self.logger.info(f"[STEP 6] Reconciling PO data")
            
            po.transition_to(POStatus.RECONCILING, "Starting reconciliation", command.user)
            await self.po_repo.save(po)
            events_count += 1
            
            reconciliation_passed = await self._reconcile_data(po, sap_data)
            events_count += 1
            
            if not reconciliation_passed:
                return self._build_reconciliation_error_result(
                    po, start_time, events_count
                )
            
            # ================================================================
            # PASSO 7: APROVAR (automático ou manual)
            # ================================================================
            self.logger.info(f"[STEP 7] Processing approval")
            
            approval_result = await self._process_approval(po, command)
            events_count += approval_result["events_count"]
            
            # Se precisa de aprovação manual, para aqui
            if approval_result["requires_manual_approval"]:
                return self._build_pending_approval_result(
                    po, start_time, events_count
                )
            
            # ================================================================
            # PASSO 8: POSTAR INVOICE NO SAP
            # ================================================================
            if po.status == POStatus.APPROVED:
                self.logger.info(f"[STEP 8] Posting invoice to SAP")
                
                invoice_posted = await self._post_invoice(po)
                if invoice_posted:
                    events_count += 1
            
            # ================================================================
            # PASSO 9: FINALIZAR
            # ================================================================
            self.logger.info(f"[STEP 9] Completing PO")
            
            po.transition_to(POStatus.COMPLETED, "Processing completed", command.user)
            await self.po_repo.save(po)
            events_count += 1
            
            # ================================================================
            # PASSO 10: LIBERAR LOCK
            # ================================================================
            self.logger.info(f"[STEP 10] Releasing locks")
            
            po.release_lock(command.user)
            await self.po_repo.save(po)
            events_count += 1
            
            # Desbloqueia no SAP também
            if po.sap_doc_number:
                await self.sap.unlock_document(po.sap_doc_number)
            
            # ================================================================
            # PASSO 11: NOTIFICAR
            # ================================================================
            if command.notify_on_complete:
                self.logger.info(f"[STEP 11] Sending notifications")
                
                await self._send_completion_notification(po)
                events_count += 1
            
            # ================================================================
            # SUCESSO! 🎉
            # ================================================================
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"✅ PO {command.po_number} processed successfully in "
                f"{processing_time:.2f}s"
            )
            
            return ProcessPOResult(
                success=True,
                po=po,
                message=f"PO {command.po_number} processed successfully",
                errors=[],
                processing_time_seconds=processing_time,
                events_published=events_count,
                validation_passed=True,
                sap_sync_completed=True,
                reconciliation_passed=True,
                approval_status="auto" if not command.force_approval else "manual",
                invoice_posted=True
            )
            
        except Exception as e:
            # ================================================================
            # ERROR! Registra e faz cleanup
            # ================================================================
            self.logger.error(f"❌ Error processing PO {command.po_number}: {str(e)}")
            
            if po:
                try:
                    po.transition_to(POStatus.ERROR, str(e), command.user)
                    po.release_lock(command.user)
                    await self.po_repo.save(po)
                    
                    # Notifica error
                    await self.notifier.notify_error(
                        po,
                        str(e),
                        [command.user]
                    )
                except:
                    pass  # Não falha se o cleanup falhar
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessPOResult(
                success=False,
                po=po,
                message=f"Error processing PO: {str(e)}",
                errors=[str(e)],
                processing_time_seconds=processing_time,
                events_published=events_count
            )
    
    # =========================================================================
    # MÉTODOS AUXILIARES (cada um faz UMA coisa)
    # =========================================================================
    
    async def _fetch_po(self, po_number: str) -> PurchaseOrder:
        """Busca a PO do banco"""
        po = await self.po_repo.get_by_po_number(po_number)
        
        if not po:
            raise PONotFoundException(po_number)
        
        return po
    
    async def _validate_po(self, po: PurchaseOrder) -> tuple[bool, List[str]]:
        """Valida a PO"""
        is_valid, errors = po.validate()
        
        if not is_valid:
            po.transition_to(POStatus.ERROR, f"Validation failed: {errors}")
            await self.po_repo.save(po)
            raise POValidationException(po.po_number, errors)
        
        return True, []
    
    async def _acquire_lock(self, po: PurchaseOrder, user: str) -> None:
        """Bloqueia a PO para processamento"""
        try:
            po.acquire_lock(user, duration_minutes=30)
            await self.po_repo.save(po)
        except ValueError as e:
            raise POAlreadyLockedException(
                po.po_number,
                po.locked_by or "unknown",
                po.lock_expires_at.isoformat() if po.lock_expires_at else "unknown"
            )
    
    async def _lock_sap_document(self, po: PurchaseOrder) -> bool:
        """Bloqueia documento no SAP"""
        try:
            return await self.sap.lock_document(po.sap_doc_number)
        except Exception as e:
            self.logger.warning(f"Failed to lock SAP document: {str(e)}")
            return False
    
    async def _fetch_sap_data(self, po: PurchaseOrder) -> dict:
        """Busca dados do SAP"""
        sap_data = await self.sap.get_po_data(po.po_number)
        
        # Atualiza dados da PO se necessário
        if "sap_doc_number" in sap_data:
            po.sap_doc_number = sap_data["sap_doc_number"]
        if "sap_fiscal_year" in sap_data:
            po.sap_fiscal_year = sap_data["sap_fiscal_year"]
        
        return sap_data
    
    async def _reconcile_data(self, po: PurchaseOrder, sap_data: dict) -> bool:
        """
        Reconcilia dados da PO com SAP
        
        Verifica se:
        - Valores batem
        - Items são os mesmos
        - Vendor está correto
        """
        discrepancies = []
        
        # Compara vendor
        if po.vendor_code != sap_data.get("vendor_code"):
            discrepancies.append(
                f"Vendor mismatch: PO={po.vendor_code}, SAP={sap_data.get('vendor_code')}"
            )
        
        # Compara valor total
        sap_amount = Decimal(str(sap_data.get("total_amount", 0)))
        if abs(po.total_amount - sap_amount) > Decimal("0.01"):
            discrepancies.append(
                f"Amount mismatch: PO={po.total_amount}, SAP={sap_amount}"
            )
        
        # Compara quantidade de itens
        sap_items_count = len(sap_data.get("items", []))
        if len(po.items) != sap_items_count:
            discrepancies.append(
                f"Items count mismatch: PO={len(po.items)}, SAP={sap_items_count}"
            )
        
        # Se tem discrepâncias, falha
        if discrepancies:
            po.discrepancies = discrepancies
            po.reconciliation_status = "failed"
            po.reconciliation_notes = "; ".join(discrepancies)
            await self.po_repo.save(po)
            return False
        
        # Sucesso!
        po.reconciliation_status = "success"
        po.reconciliation_notes = "All data reconciled successfully"
        await self.po_repo.save(po)
        return True
    
    async def _process_approval(self, po: PurchaseOrder, command: ProcessPOCommand) -> dict:
        """
        Processa aprovação (automática ou manual)
        """
        events_count = 0
        
        # Verifica se precisa aprovação manual
        requires_manual = po.requires_approval() or command.force_approval
        
        if requires_manual:
            # Muda para aguardando aprovação
            po.transition_to(
                POStatus.AWAITING_APPROVAL,
                f"Amount {po.total_amount} requires approval",
                command.user
            )
            await self.po_repo.save(po)
            events_count += 1
            
            # Notifica aprovadores
            await self.notifier.notify_approval_required(
                po,
                recipients=["approver@company.com"]  # TODO: buscar da config
            )
            events_count += 1
            
            return {
                "requires_manual_approval": True,
                "events_count": events_count
            }
        
        else:
            # Aprovação automática
            po.approve(user="system", notes="Auto-approved (below threshold)")
            await self.po_repo.save(po)
            events_count += 1
            
            return {
                "requires_manual_approval": False,
                "events_count": events_count
            }
    
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
    
    async def _send_completion_notification(self, po: PurchaseOrder) -> None:
        """Envia notificação de conclusão"""
        try:
            await self.notifier.notify_completed(
                po,
                recipients=[po.created_by]
            )
        except Exception as e:
            self.logger.warning(f"Failed to send notification: {str(e)}")
    
    # =========================================================================
    # MÉTODOS PARA CONSTRUIR RESULTADOS
    # =========================================================================
    
    def _build_error_result(
        self,
        po: Optional[PurchaseOrder],
        errors: List[str],
        start_time: datetime,
        events_count: int
    ) -> ProcessPOResult:
        """Constrói resultado de erro"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessPOResult(
            success=False,
            po=po,
            message="Validation failed",
            errors=errors,
            processing_time_seconds=processing_time,
            events_published=events_count,
            validation_passed=False
        )
    
    def _build_reconciliation_error_result(
        self,
        po: PurchaseOrder,
        start_time: datetime,
        events_count: int
    ) -> ProcessPOResult:
        """Constrói resultado de erro de reconciliação"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessPOResult(
            success=False,
            po=po,
            message="Reconciliation failed",
            errors=po.discrepancies,
            processing_time_seconds=processing_time,
            events_published=events_count,
            validation_passed=True,
            sap_sync_completed=True,
            reconciliation_passed=False
        )
    
    def _build_pending_approval_result(
        self,
        po: PurchaseOrder,
        start_time: datetime,
        events_count: int
    ) -> ProcessPOResult:
        """Constrói resultado de aprovação pendente"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessPOResult(
            success=True,
            po=po,
            message="PO awaiting manual approval",
            errors=[],
            processing_time_seconds=processing_time,
            events_published=events_count,
            validation_passed=True,
            sap_sync_completed=True,
            reconciliation_passed=True,
            approval_status="pending"
        )
