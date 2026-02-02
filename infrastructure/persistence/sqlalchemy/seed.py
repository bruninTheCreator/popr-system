from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.purchase_order import PurchaseOrder, POItem, POStatus
from .models import POModel
from .po_repository_impl import SQLAlchemyPORepository


async def seed_demo_pos(session: AsyncSession, data_path: Path) -> None:
    result = await session.execute(select(func.count(POModel.id)))
    if int(result.scalar_one()) > 0:
        return

    repo = SQLAlchemyPORepository(session)
    demo_pos = _load_demo_pos(data_path)
    for po in demo_pos:
        await repo.save(po)


def _load_demo_pos(data_path: Path) -> list[PurchaseOrder]:
    if not data_path.exists():
        return _fallback_demo_pos()

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    pos = []
    now = datetime.utcnow()
    for entry in data.get("pos", []):
        items = [
            POItem(
                item_number=str(item["item_number"]),
                description=item["description"],
                quantity=Decimal(str(item["quantity"])),
                unit_price=Decimal(str(item["unit_price"])),
                total_price=Decimal(str(item["total_price"])),
                material_code=item.get("material_code")
            )
            for item in entry.get("items", [])
        ]

        status_value = entry.get("status", "pending")
        status = POStatus(status_value) if status_value in POStatus._value2member_map_ else POStatus.PENDING

        po = PurchaseOrder(
            id=str(uuid4()),
            po_number=entry["po_number"],
            vendor_code=entry["vendor_code"],
            vendor_name=entry["vendor_name"],
            total_amount=Decimal(str(entry["total_amount"])),
            currency=entry.get("currency", "BRL"),
            items=items,
            status=status
        )
        po.created_by = entry.get("created_by", "system")
        po.created_at = now
        po.updated_at = now
        po.sap_doc_number = entry.get("sap_doc_number")
        po.sap_fiscal_year = entry.get("sap_fiscal_year")
        pos.append(po)

    return pos


def _fallback_demo_pos() -> list[PurchaseOrder]:
    now = datetime.utcnow()
    pos = []
    samples = [
        {
            "po_number": "PO-1001",
            "vendor_code": "V001",
            "vendor_name": "Fornecedor Alpha",
            "total_amount": "12500.50",
            "currency": "BRL",
            "status": "awaiting_approval",
            "items": [
                {
                    "item_number": "10",
                    "description": "Cabo optico",
                    "quantity": "10",
                    "unit_price": "450.05",
                    "total_price": "4500.50"
                },
                {
                    "item_number": "20",
                    "description": "Conector SC",
                    "quantity": "50",
                    "unit_price": "160.00",
                    "total_price": "8000.00"
                }
            ]
        },
        {
            "po_number": "PO-1002",
            "vendor_code": "V014",
            "vendor_name": "Fornecedor Beta",
            "total_amount": "3200.00",
            "currency": "BRL",
            "status": "pending",
            "items": [
                {
                    "item_number": "10",
                    "description": "Roteador",
                    "quantity": "2",
                    "unit_price": "1600.00",
                    "total_price": "3200.00"
                }
            ]
        },
        {
            "po_number": "PO-1003",
            "vendor_code": "V007",
            "vendor_name": "Fornecedor Gama",
            "total_amount": "7800.00",
            "currency": "BRL",
            "status": "processing",
            "items": [
                {
                    "item_number": "10",
                    "description": "Switch 48 portas",
                    "quantity": "1",
                    "unit_price": "7800.00",
                    "total_price": "7800.00"
                }
            ]
        }
    ]

    for sample in samples:
        items = [
            POItem(
                item_number=item["item_number"],
                description=item["description"],
                quantity=Decimal(item["quantity"]),
                unit_price=Decimal(item["unit_price"]),
                total_price=Decimal(item["total_price"])
            )
            for item in sample["items"]
        ]
        status = POStatus(sample["status"])
        po = PurchaseOrder(
            id=str(uuid4()),
            po_number=sample["po_number"],
            vendor_code=sample["vendor_code"],
            vendor_name=sample["vendor_name"],
            total_amount=Decimal(sample["total_amount"]),
            currency=sample["currency"],
            items=items,
            status=status
        )
        po.created_at = now
        po.updated_at = now
        pos.append(po)

    return pos
