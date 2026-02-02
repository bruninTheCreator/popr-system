from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities.purchase_order import PurchaseOrder, POItem, POStatus
from domain.interfaces.po_repository import PORepository
from .models import POModel, POItemModel


class SQLAlchemyPORepository(PORepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, po: PurchaseOrder) -> PurchaseOrder:
        model = await self._get_model_by_po_number(po.po_number)
        if model is None:
            model = POModel(
                id=po.id or str(uuid4()),
                po_number=po.po_number,
                vendor_code=po.vendor_code,
                vendor_name=po.vendor_name,
                total_amount=po.total_amount,
                currency=po.currency,
                status=po.status.value,
                version=po.version,
                locked_by=po.locked_by,
                locked_at=po.locked_at,
                lock_expires_at=po.lock_expires_at,
                created_at=po.created_at,
                updated_at=po.updated_at,
                sap_doc_number=po.sap_doc_number,
                sap_fiscal_year=po.sap_fiscal_year,
                sap_data=po.sap_data,
                reconciliation_status=po.reconciliation_status,
                reconciliation_notes=po.reconciliation_notes,
                discrepancies=po.discrepancies,
                created_by=po.created_by,
                approved_by=po.approved_by,
                approved_at=po.approved_at,
                rejection_reason=po.rejection_reason,
                events=po.events
            )
            self.session.add(model)
        else:
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
            model.sap_data = po.sap_data
            model.reconciliation_status = po.reconciliation_status
            model.reconciliation_notes = po.reconciliation_notes
            model.discrepancies = po.discrepancies
            model.created_by = po.created_by
            model.approved_by = po.approved_by
            model.approved_at = po.approved_at
            model.rejection_reason = po.rejection_reason
            model.events = po.events

            model.items.clear()

        for item in po.items:
            model.items.append(
                POItemModel(
                    id=str(uuid4()),
                    item_number=item.item_number,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    material_code=item.material_code
                )
            )

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, po_id: str) -> Optional[PurchaseOrder]:
        result = await self.session.execute(
            select(POModel)
            .options(selectinload(POModel.items))
            .where(POModel.id == po_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        model = await self._get_model_by_po_number(po_number)
        return self._to_domain(model) if model else None

    async def list_by_status(
        self,
        status: POStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[PurchaseOrder]:
        result = await self.session.execute(
            select(POModel)
            .options(selectinload(POModel.items))
            .where(POModel.status == status.value)
            .order_by(POModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list_locked_by_user(self, user: str) -> List[PurchaseOrder]:
        result = await self.session.execute(
            select(POModel)
            .options(selectinload(POModel.items))
            .where(POModel.locked_by == user)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list_pending_approval(self) -> List[PurchaseOrder]:
        return await self.list_by_status(POStatus.AWAITING_APPROVAL)

    async def list_with_expired_locks(self) -> List[PurchaseOrder]:
        now = datetime.utcnow()
        result = await self.session.execute(
            select(POModel)
            .options(selectinload(POModel.items))
            .where(POModel.lock_expires_at.isnot(None))
            .where(POModel.lock_expires_at < now)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def delete(self, po_id: str) -> bool:
        result = await self.session.execute(
            delete(POModel).where(POModel.id == po_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, po_number: str) -> bool:
        result = await self.session.execute(
            select(func.count(POModel.id)).where(POModel.po_number == po_number)
        )
        return result.scalar_one() > 0

    async def count_by_status(self, status: POStatus) -> int:
        result = await self.session.execute(
            select(func.count(POModel.id)).where(POModel.status == status.value)
        )
        return int(result.scalar_one())

    async def _get_model_by_po_number(self, po_number: str) -> Optional[POModel]:
        result = await self.session.execute(
            select(POModel)
            .options(selectinload(POModel.items))
            .where(POModel.po_number == po_number)
        )
        return result.scalar_one_or_none()

    def _to_domain(self, model: POModel) -> PurchaseOrder:
        status = POStatus(model.status) if model.status in POStatus._value2member_map_ else POStatus.DRAFT
        items = [
            POItem(
                item_number=item.item_number,
                description=item.description,
                quantity=Decimal(str(item.quantity)),
                unit_price=Decimal(str(item.unit_price)),
                total_price=Decimal(str(item.total_price)),
                material_code=item.material_code
            )
            for item in model.items
        ]

        po = PurchaseOrder(
            id=model.id,
            po_number=model.po_number,
            vendor_code=model.vendor_code,
            vendor_name=model.vendor_name,
            total_amount=Decimal(str(model.total_amount)),
            currency=model.currency,
            items=items,
            status=status
        )

        po.version = model.version
        po.locked_by = model.locked_by
        po.locked_at = model.locked_at
        po.lock_expires_at = model.lock_expires_at
        po.created_at = model.created_at
        po.updated_at = model.updated_at
        po.sap_doc_number = model.sap_doc_number
        po.sap_fiscal_year = model.sap_fiscal_year
        po.sap_data = model.sap_data or {}
        po.reconciliation_status = model.reconciliation_status
        po.reconciliation_notes = model.reconciliation_notes
        po.discrepancies = model.discrepancies or []
        po.created_by = model.created_by
        po.approved_by = model.approved_by
        po.approved_at = model.approved_at
        po.rejection_reason = model.rejection_reason
        po.events = model.events or []
        return po
