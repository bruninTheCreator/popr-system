import unittest
from decimal import Decimal
from datetime import datetime, timedelta

from application.use_cases.approve_po import (
    ApprovePOCommand,
    ApprovePOUseCase,
    RejectPOCommand,
    RejectPOUseCase,
)
from application.use_cases.process_po import ProcessPOCommand, ProcessPOUseCase
from domain.entities.purchase_order import POItem, PurchaseOrder, POStatus


class FakePORepository:
    def __init__(self) -> None:
        self._by_id = {}
        self._by_number = {}

    async def save(self, po: PurchaseOrder) -> PurchaseOrder:
        self._by_id[po.id] = po
        self._by_number[po.po_number] = po
        return po

    async def get_by_id(self, po_id: str):
        return self._by_id.get(po_id)

    async def get_by_po_number(self, po_number: str):
        return self._by_number.get(po_number)

    async def list_by_status(self, status: POStatus, limit: int = 100, offset: int = 0):
        items = [po for po in self._by_id.values() if po.status == status]
        return items[offset : offset + limit]

    async def list_locked_by_user(self, user: str):
        return [po for po in self._by_id.values() if po.locked_by == user]

    async def list_pending_approval(self):
        return [
            po for po in self._by_id.values() if po.status == POStatus.AWAITING_APPROVAL
        ]

    async def list_with_expired_locks(self):
        now = datetime.now()
        return [
            po
            for po in self._by_id.values()
            if po.lock_expires_at and po.lock_expires_at < now
        ]

    async def delete(self, po_id: str) -> bool:
        po = self._by_id.pop(po_id, None)
        if po:
            self._by_number.pop(po.po_number, None)
            return True
        return False

    async def exists(self, po_number: str) -> bool:
        return po_number in self._by_number

    async def count_by_status(self, status: POStatus) -> int:
        return len([po for po in self._by_id.values() if po.status == status])


class FakeSAPGateway:
    def __init__(self, sap_data: dict) -> None:
        self.sap_data = sap_data
        self.locked_documents = []
        self.unlocked_documents = []
        self.posted_invoices = []

    async def lock_document(self, doc_number: str) -> bool:
        self.locked_documents.append(doc_number)
        return True

    async def unlock_document(self, doc_number: str) -> bool:
        self.unlocked_documents.append(doc_number)
        return True

    async def get_po_data(self, po_number: str) -> dict:
        return dict(self.sap_data)

    async def post_invoice(self, po_number: str, invoice_data: dict) -> str:
        self.posted_invoices.append((po_number, invoice_data))
        return "INV-123"


class FakeNotificationService:
    def __init__(self) -> None:
        self.approval_required = []
        self.completed = []
        self.approved = []
        self.rejected = []
        self.errors = []

    async def notify_approval_required(self, po, recipients):
        self.approval_required.append((po, recipients))
        return True

    async def notify_completed(self, po, recipients):
        self.completed.append((po, recipients))
        return True

    async def notify_approved(self, po, recipients):
        self.approved.append((po, recipients))
        return True

    async def notify_rejected(self, po, recipients, reason):
        self.rejected.append((po, recipients, reason))
        return True

    async def notify_error(self, po, message, recipients):
        self.errors.append((po, message, recipients))
        return True


def build_po(
    po_number: str,
    total_amount: Decimal,
    status: POStatus = POStatus.PENDING,
) -> PurchaseOrder:
    items = [
        POItem(
            item_number="10",
            description="Item",
            quantity=Decimal("1"),
            unit_price=total_amount,
            total_price=total_amount,
        )
    ]
    return PurchaseOrder(
        id=f"po-{po_number}",
        po_number=po_number,
        vendor_code="V-001",
        vendor_name="Fornecedor",
        total_amount=total_amount,
        currency="BRL",
        items=items,
        status=status,
        created_by="user",
        created_at=datetime.now() - timedelta(days=1),
        updated_at=datetime.now() - timedelta(days=1),
    )


class ProcessPOUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_po_auto_approves_and_completes(self):
        repo = FakePORepository()
        po = build_po("PO-100", Decimal("1000.00"))
        await repo.save(po)
        sap = FakeSAPGateway(
            {
                "vendor_code": po.vendor_code,
                "total_amount": po.total_amount,
                "items": [{"item_number": "10"}],
            }
        )
        notifier = FakeNotificationService()
        use_case = ProcessPOUseCase(repo, sap, notifier)

        result = await use_case.execute(
            ProcessPOCommand(po_number=po.po_number, user="ana")
        )

        self.assertTrue(result.success)
        self.assertEqual(result.po.status, POStatus.COMPLETED)
        self.assertEqual(len(sap.posted_invoices), 1)
        self.assertEqual(len(notifier.completed), 1)

    async def test_process_po_requires_manual_approval(self):
        repo = FakePORepository()
        po = build_po("PO-200", Decimal("20000.00"))
        await repo.save(po)
        sap = FakeSAPGateway(
            {
                "vendor_code": po.vendor_code,
                "total_amount": po.total_amount,
                "items": [{"item_number": "10"}],
            }
        )
        notifier = FakeNotificationService()
        use_case = ProcessPOUseCase(repo, sap, notifier)

        result = await use_case.execute(
            ProcessPOCommand(po_number=po.po_number, user="ana")
        )

        self.assertTrue(result.success)
        self.assertEqual(result.po.status, POStatus.AWAITING_APPROVAL)
        self.assertEqual(len(notifier.approval_required), 1)
        self.assertEqual(len(sap.posted_invoices), 0)


class ApprovalUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_approve_po_posts_invoice_and_completes(self):
        repo = FakePORepository()
        po = build_po("PO-300", Decimal("500.00"), status=POStatus.AWAITING_APPROVAL)
        await repo.save(po)
        sap = FakeSAPGateway({})
        notifier = FakeNotificationService()
        use_case = ApprovePOUseCase(repo, sap, notifier)

        result = await use_case.execute(
            ApprovePOCommand(
                po_number=po.po_number,
                approved_by="maria",
                notes="ok",
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.po.status, POStatus.COMPLETED)
        self.assertEqual(len(sap.posted_invoices), 1)
        self.assertEqual(len(notifier.approved), 1)

    async def test_reject_po_releases_lock(self):
        repo = FakePORepository()
        po = build_po("PO-400", Decimal("500.00"), status=POStatus.AWAITING_APPROVAL)
        po.locked_by = "maria"
        po.locked_at = datetime.now()
        po.lock_expires_at = datetime.now() + timedelta(minutes=15)
        await repo.save(po)
        notifier = FakeNotificationService()
        use_case = RejectPOUseCase(repo, notifier)

        result = await use_case.execute(
            RejectPOCommand(
                po_number=po.po_number,
                rejected_by="maria",
                reason="invalid",
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.po.status, POStatus.REJECTED)
        self.assertFalse(result.po.is_locked())
        self.assertEqual(len(notifier.rejected), 1)


if __name__ == "__main__":
    unittest.main()
