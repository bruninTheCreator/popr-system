# popr/domain/interfaces/sap_gateway.py
"""
Interface - SAP Gateway
Contrato para integração com SAP
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SAPGateway(ABC):
    """Interface para gateway SAP"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Conecta ao SAP"""
        pass
    
    @abstractmethod
    def create_po(self, po_data: Dict[str, Any]) -> Optional[str]:
        """Cria PO no SAP"""
        pass
    
    @abstractmethod
    def update_po(self, po_number: str, updates: Dict[str, Any]) -> bool:
        """Atualiza PO no SAP"""
        pass
    
    @abstractmethod
    def get_po_status(self, po_number: str) -> Optional[str]:
        """Obtém status da PO no SAP"""
        pass