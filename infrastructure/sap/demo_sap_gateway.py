import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from domain.interfaces.sap_gateway import SAPGateway


class DemoSAPGateway(SAPGateway):
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self._connected = False
        self._cache: Dict[str, Any] = {}

    async def connect(self) -> bool:
        self._connected = True
        self._cache = self._load_data()
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def get_po_data(self, po_number: str) -> Dict[str, Any]:
        self._ensure_connected()
        po = self._find_po(po_number)
        if po is None:
            raise ValueError(f"PO {po_number} not found in demo SAP")
        return {
            **po,
            "extracted_at": datetime.utcnow().isoformat()
        }

    async def get_po_header(self, po_number: str) -> Dict[str, Any]:
        data = await self.get_po_data(po_number)
        return {k: v for k, v in data.items() if k != "items"}

    async def get_po_items(self, po_number: str) -> List[Dict[str, Any]]:
        data = await self.get_po_data(po_number)
        return list(data.get("items", []))

    async def post_invoice(self, po_number: str, invoice_data: Dict[str, Any]) -> str:
        self._ensure_connected()
        return f"INV-{po_number}-{int(datetime.utcnow().timestamp())}"

    async def lock_document(self, doc_number: str) -> bool:
        self._ensure_connected()
        return True

    async def unlock_document(self, doc_number: str) -> bool:
        self._ensure_connected()
        return True

    async def check_document_status(self, doc_number: str) -> str:
        self._ensure_connected()
        return "active"

    async def search_pos_by_vendor(
        self,
        vendor_code: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[str]:
        self._ensure_connected()
        pos = self._cache.get("pos", [])
        return [po["po_number"] for po in pos if po.get("vendor_code") == vendor_code]

    async def create_po(self, po_data: Dict[str, Any]) -> Optional[str]:
        self._ensure_connected()
        return po_data.get("po_number")

    async def update_po(self, po_number: str, updates: Dict[str, Any]) -> bool:
        self._ensure_connected()
        return True

    async def get_po_status(self, po_number: str) -> Optional[str]:
        self._ensure_connected()
        po = self._find_po(po_number)
        return po.get("status") if po else None

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("DemoSAPGateway not connected. Call connect() first.")

    def _load_data(self) -> Dict[str, Any]:
        if not self.data_path.exists():
            return {"pos": []}
        with self.data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _find_po(self, po_number: str) -> Optional[Dict[str, Any]]:
        for po in self._cache.get("pos", []):
            if po.get("po_number") == po_number:
                return po
        return None
