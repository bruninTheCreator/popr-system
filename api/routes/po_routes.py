"""
Endpoints REST para Purchase Orders
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

from ...domain.entities.purchase_order import POStatus
from ...domain.interfaces.po_repository import PORepository
from ...application.use_cases.process_po import ProcessPOCommand, ProcessPOUseCase
from ...application.use_cases.approve_po import ApprovePOCommand, RejectPOCommand
from ..dependencies import (
    get_po_repository,
    get_process_po_use_case,
    get_approve_po_use_case,
    get_reject_po_use_case
)

router = APIRouter(prefix="/api/v1/pos", tags=["Purchase Orders"])


# =============================================================================
# REQUEST/RESPONSE MODELS (DTOs)
# =============================================================================

class POItemResponse(BaseModel):
    """Resposta de um item da PO"""
    item_number: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    material_code: Optional[str] = None


class POResponse(BaseModel):
    """Resposta de uma PO completa"""
    id: str
    po_number: str
    vendor_code: str
    vendor_name: str
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[POItemResponse]
    
    # Campos opcionais
    locked_by: Optional[str] = None
    sap_doc_number: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class ProcessPORequest(BaseModel):
    """Request para processar uma PO"""
    po_number: str = Field(..., description="Número da PO")
    user: str = Field(..., description="Usuário que está processando")
    force_approval: bool = Field(False, description="Forçar aprovação manual")
    skip_sap_lock: bool = Field(False, description="Pular lock do SAP (para testes)")
    notify_on_complete: bool = Field(True, description="Notificar ao completar")


class ApprovePORequest(BaseModel):
    """Request para aprovar uma PO"""
    po_number: str
    approved_by: str
    notes: Optional[str] = None
    post_invoice: bool = True
    notify: bool = True


class RejectPORequest(BaseModel):
    """Request para rejeitar uma PO"""
    po_number: str
    rejected_by: str
    reason: str = Field(..., description="Motivo da rejeição (obrigatório)")
    can_retry: bool = True
    notify: bool = True


class POListResponse(BaseModel):
    """Resposta de lista de POs"""
    total: int
    items: List[POResponse]
    page: int
    page_size: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/process", response_model=POResponse, status_code=status.HTTP_200_OK)
async def process_po(
    request: ProcessPORequest,
    use_case: ProcessPOUseCase = Depends(get_process_po_use_case)
):
    """
    🎯 Processa uma Purchase Order do início ao fim
    
    Este é o endpoint PRINCIPAL do POPR!
    
    Fluxo:
    1. Valida dados
    2. Bloqueia no SAP
    3. Busca dados do SAP
    4. Reconcilia
    5. Aprova (auto ou manual)
    6. Posta invoice
    7. Finaliza
    
    Returns:
        PO processada com todos os dados
    """
    try:
        # Cria comando
        command = ProcessPOCommand(
            po_number=request.po_number,
            user=request.user,
            force_approval=request.force_approval,
            skip_sap_lock=request.skip_sap_lock,
            notify_on_complete=request.notify_on_complete
        )
        
        # Executa use case
        result = await use_case.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": result.message,
                    "errors": result.errors
                }
            )
        
        # Converte para response
        po = result.po
        return POResponse(
            id=po.id,
            po_number=po.po_number,
            vendor_code=po.vendor_code,
            vendor_name=po.vendor_name,
            total_amount=po.total_amount,
            currency=po.currency,
            status=po.status.value,
            created_at=po.created_at,
            updated_at=po.updated_at,
            items=[
                POItemResponse(
                    item_number=item.item_number,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    material_code=item.material_code
                )
                for item in po.items
            ],
            locked_by=po.locked_by,
            sap_doc_number=po.sap_doc_number,
            approved_by=po.approved_by,
            approved_at=po.approved_at,
            rejection_reason=po.rejection_reason
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PO: {str(e)}"
        )


@router.post("/approve", response_model=POResponse)
async def approve_po(
    request: ApprovePORequest,
    use_case = Depends(get_approve_po_use_case)
):
    """
    ✅ Aprova uma Purchase Order manualmente
    
    Usado para POs que requerem aprovação manual
    (valores acima do threshold ou casos especiais)
    """
    try:
        command = ApprovePOCommand(
            po_number=request.po_number,
            approved_by=request.approved_by,
            notes=request.notes,
            post_invoice=request.post_invoice,
            notify=request.notify
        )
        
        result = await use_case.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": result.message,
                    "errors": result.errors
                }
            )
        
        # Converte para response (similar ao process_po)
        po = result.po
        return POResponse(
            id=po.id,
            po_number=po.po_number,
            vendor_code=po.vendor_code,
            vendor_name=po.vendor_name,
            total_amount=po.total_amount,
            currency=po.currency,
            status=po.status.value,
            created_at=po.created_at,
            updated_at=po.updated_at,
            items=[
                POItemResponse(**item.__dict__)
                for item in po.items
            ],
            approved_by=po.approved_by,
            approved_at=po.approved_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reject", response_model=POResponse)
async def reject_po(
    request: RejectPORequest,
    use_case = Depends(get_reject_po_use_case)
):
    """
    ❌ Rejeita uma Purchase Order
    
    Usado quando:
    - Dados incorretos
    - Vendor não autorizado
    - Valor não aprovado
    """
    try:
        command = RejectPOCommand(
            po_number=request.po_number,
            rejected_by=request.rejected_by,
            reason=request.reason,
            can_retry=request.can_retry,
            notify=request.notify
        )
        
        result = await use_case.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        po = result.po
        return POResponse(
            id=po.id,
            po_number=po.po_number,
            vendor_code=po.vendor_code,
            vendor_name=po.vendor_name,
            total_amount=po.total_amount,
            currency=po.currency,
            status=po.status.value,
            created_at=po.created_at,
            updated_at=po.updated_at,
            items=[POItemResponse(**item.__dict__) for item in po.items],
            rejection_reason=po.rejection_reason
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{po_number}", response_model=POResponse)
async def get_po(
    po_number: str,
    repo: PORepository = Depends(get_po_repository)
):
    """
    📋 Busca uma PO por número
    """
    po = await repo.get_by_po_number(po_number)
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PO {po_number} not found"
        )
    
    return POResponse(
        id=po.id,
        po_number=po.po_number,
        vendor_code=po.vendor_code,
        vendor_name=po.vendor_name,
        total_amount=po.total_amount,
        currency=po.currency,
        status=po.status.value,
        created_at=po.created_at,
        updated_at=po.updated_at,
        items=[POItemResponse(**item.__dict__) for item in po.items],
        locked_by=po.locked_by,
        sap_doc_number=po.sap_doc_number,
        approved_by=po.approved_by,
        approved_at=po.approved_at
    )


@router.get("/", response_model=POListResponse)
async def list_pos(
    status_filter: Optional[str] = Query(None, description="Filtrar por status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    repo: PORepository = Depends(get_po_repository)
):
    """
    📝 Lista Purchase Orders
    
    Query params:
    - status: Filtrar por status (pending, approved, etc)
    - page: Página (default: 1)
    - page_size: Itens por página (default: 50, max: 100)
    """
    if status_filter:
        # Valida status
        try:
            po_status = POStatus[status_filter.upper()]
            pos = await repo.list_by_status(
                po_status,
                limit=page_size,
                offset=(page - 1) * page_size
            )
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    else:
        # TODO: Implementar list_all no repositório
        pos = []
    
    return POListResponse(
        total=len(pos),
        items=[
            POResponse(
                id=po.id,
                po_number=po.po_number,
                vendor_code=po.vendor_code,
                vendor_name=po.vendor_name,
                total_amount=po.total_amount,
                currency=po.currency,
                status=po.status.value,
                created_at=po.created_at,
                updated_at=po.updated_at,
                items=[POItemResponse(**item.__dict__) for item in po.items]
            )
            for po in pos
        ],
        page=page,
        page_size=page_size
    )


@router.get("/pending-approval/", response_model=POListResponse)
async def list_pending_approval(
    repo: PORepository = Depends(get_po_repository)
):
    """
    ⏳ Lista POs aguardando aprovação
    """
    pos = await repo.list_pending_approval()
    
    return POListResponse(
        total=len(pos),
        items=[
            POResponse(
                id=po.id,
                po_number=po.po_number,
                vendor_code=po.vendor_code,
                vendor_name=po.vendor_name,
                total_amount=po.total_amount,
                currency=po.currency,
                status=po.status.value,
                created_at=po.created_at,
                updated_at=po.updated_at,
                items=[POItemResponse(**item.__dict__) for item in po.items]
            )
            for po in pos
        ],
        page=1,
        page_size=len(pos)
    )