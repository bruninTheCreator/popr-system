from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.purchase_order import PurchaseOrder, POItem, POStatus
from domain.interfaces.po_repository import PORepository

from .models import PurchaseOrderModel


def _serialize_decimal(value: Decimal | float | int | str) -> str:
    return str(value)


def _deserialize_decimal(value: str | float | int | Decimal) -> Decimal:
    return Decimal(str(value))


def _serialize_item(item: POItem) -> dict:
    return {
        "item_number": item.item_number,
        "description": item.description,
        "quantity": _serialize_decimal(item.quantity),
        "unit_price": _serialize_decimal(item.unit_price),
        "total_price": _serialize_decimal(item.total_price),
        "material_code": item.material_code,
    }


def _deserialize_item(data: dict) -> POItem:
    return POItem(
        item_number=data["item_number"],
        description=data["description"],
        quantity=_deserialize_decimal(data["quantity"]),
        unit_price=_deserialize_decimal(data["unit_price"]),
        total_price=_deserialize_decimal(data["total_price"]),
        material_code=data.get("material_code"),
    )


def _model_to_entity(model: PurchaseOrderModel) -> PurchaseOrder:
    return PurchaseOrder(
        id=model.id,
        po_number=model.po_number,
        vendor_code=model.vendor_code,
        vendor_name=model.vendor_name,
        total_amount=_deserialize_decimal(model.total_amount),
        currency=model.currency,
        items=[_deserialize_item(item) for item in model.items],
        status=POStatus(model.status),
        version=model.version,
        locked_by=model.locked_by,
        locked_at=model.locked_at,
        lock_expires_at=model.lock_expires_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
        sap_doc_number=model.sap_doc_number,
        sap_fiscal_year=model.sap_fiscal_year,
        sap_data=model.sap_data or {},
        reconciliation_status=model.reconciliation_status,
        reconciliation_notes=model.reconciliation_notes,
        discrepancies=list(model.discrepancies or []),
        created_by=model.created_by,
        approved_by=model.approved_by,
        approved_at=model.approved_at,
        rejection_reason=model.rejection_reason,
        events=list(model.events or []),
    )


def _update_model_from_entity(model: PurchaseOrderModel, po: PurchaseOrder) -> None:
    model.po_number = po.po_number
    model.vendor_code = po.vendor_code
    model.vendor_name = po.vendor_name
    model.total_amount = po.total_amount
    model.currency = po.currency
    model.status = po.status.value
    model.version = po.version
    model.locked_by = po.locked_by
    model.locked_at = po.locked_at
    model.lock_expires_at = po.lock_expires_at
    model.created_at = po.created_at
    model.updated_at = po.updated_at
    model.sap_doc_number = po.sap_doc_number
    model.sap_fiscal_year = po.sap_fiscal_year
    model.sap_data = po.sap_data or {}
    model.reconciliation_status = po.reconciliation_status
    model.reconciliation_notes = po.reconciliation_notes
    model.discrepancies = po.discrepancies or []
    model.created_by = po.created_by
    model.approved_by = po.approved_by
    model.approved_at = po.approved_at
    model.rejection_reason = po.rejection_reason
    model.events = po.events or []
    model.items = [_serialize_item(item) for item in po.items]


class SQLAlchemyPORepository(PORepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, po: PurchaseOrder) -> PurchaseOrder:
        existing = await self.session.get(PurchaseOrderModel, po.id)
        if existing is None:
            existing = PurchaseOrderModel(
                id=po.id,
                created_at=po.created_at,
                updated_at=po.updated_at,
                status=po.status.value,
                version=po.version,
                vendor_code=po.vendor_code,
                vendor_name=po.vendor_name,
                po_number=po.po_number,
                total_amount=po.total_amount,
                currency=po.currency,
                created_by=po.created_by,
                items=[_serialize_item(item) for item in po.items],
                events=po.events or [],
                sap_data=po.sap_data or {},
                discrepancies=po.discrepancies or [],
            )
            _update_model_from_entity(existing, po)
            self.session.add(existing)
        else:
            _update_model_from_entity(existing, po)

        await self.session.commit()
        await self.session.refresh(existing)
        return _model_to_entity(existing)

    async def get_by_id(self, po_id: str) -> Optional[PurchaseOrder]:
        model = await self.session.get(PurchaseOrderModel, po_id)
        if model is None:
            return None
        return _model_to_entity(model)

    async def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        result = await self.session.execute(
            select(PurchaseOrderModel).where(PurchaseOrderModel.po_number == po_number)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _model_to_entity(model)

    async def list_by_status(
        self,
        status: POStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PurchaseOrder]:
        result = await self.session.execute(
            select(PurchaseOrderModel)
            .where(PurchaseOrderModel.status == status.value)
            .offset(offset)
            .limit(limit)
        )
        return [_model_to_entity(model) for model in result.scalars().all()]

    async def list_locked_by_user(self, user: str) -> List[PurchaseOrder]:
        result = await self.session.execute(
            select(PurchaseOrderModel).where(PurchaseOrderModel.locked_by == user)
        )
        return [_model_to_entity(model) for model in result.scalars().all()]

    async def list_pending_approval(self) -> List[PurchaseOrder]:
        result = await self.session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.status == POStatus.AWAITING_APPROVAL.value
            )
        )
        return [_model_to_entity(model) for model in result.scalars().all()]

    async def list_with_expired_locks(self) -> List[PurchaseOrder]:
        now = datetime.now()
        result = await self.session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.lock_expires_at.is_not(None),
                PurchaseOrderModel.lock_expires_at < now,
            )
        )
        return [_model_to_entity(model) for model in result.scalars().all()]

    async def delete(self, po_id: str) -> bool:
        result = await self.session.execute(
            delete(PurchaseOrderModel).where(PurchaseOrderModel.id == po_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, po_number: str) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(PurchaseOrderModel)
            .where(PurchaseOrderModel.po_number == po_number)
        )
        return result.scalar_one() > 0

    async def count_by_status(self, status: POStatus) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(PurchaseOrderModel)
            .where(PurchaseOrderModel.status == status.value)
        )
        return result.scalar_one()
