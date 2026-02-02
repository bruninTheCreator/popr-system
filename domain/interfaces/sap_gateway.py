"""
Interface do Gateway SAP
Contrato para integrações com SAP (GUI, RFC, REST, etc)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class SAPGateway(ABC):
    """Interface para integração com SAP."""

    @abstractmethod
    async def connect(self) -> bool:
        """Conecta ao SAP."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Desconecta do SAP."""
        pass

    @abstractmethod
    async def get_po_data(self, po_number: str) -> Dict[str, Any]:
        """Busca dados completos de uma PO no SAP."""
        pass

    @abstractmethod
    async def get_po_header(self, po_number: str) -> Dict[str, Any]:
        """Busca apenas o cabeçalho da PO."""
        pass

    @abstractmethod
    async def get_po_items(self, po_number: str) -> List[Dict[str, Any]]:
        """Busca itens da PO."""
        pass

    @abstractmethod
    async def post_invoice(self, po_number: str, invoice_data: Dict[str, Any]) -> str:
        """Posta uma invoice no SAP."""
        pass

    @abstractmethod
    async def lock_document(self, doc_number: str) -> bool:
        """Bloqueia um documento no SAP."""
        pass

    @abstractmethod
    async def unlock_document(self, doc_number: str) -> bool:
        """Desbloqueia um documento no SAP."""
        pass

    @abstractmethod
    async def check_document_status(self, doc_number: str) -> str:
        """Verifica status de um documento no SAP."""
        pass

    @abstractmethod
    async def search_pos_by_vendor(
        self,
        vendor_code: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[str]:
        """Busca POs por fornecedor."""
        pass
