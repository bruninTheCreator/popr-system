# popr/domain/interfaces/po_repository.py
"""
Interface do Repositório de Purchase Orders
Este é um PORT (contrato) que será implementado na camada de infraestrutura
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

# Imports do domain (não tem dependência de infraestrutura!)
from ..entities.purchase_order import PurchaseOrder, POStatus


class PORepository(ABC):
    """
    Interface para persistência de Purchase Orders.
    
    Esta interface define O QUE o repositório deve fazer,
    mas NÃO define COMO ele faz (isso fica pro adapter).
    """
    
    @abstractmethod
    async def save(self, po: PurchaseOrder) -> PurchaseOrder:
        """
        Salva ou atualiza uma PO no banco.
        
        Args:
            po: Purchase Order a ser salva
            
        Returns:
            PO salva (com ID gerado se necessário)
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, po_id: str) -> Optional[PurchaseOrder]:
        """
        Busca uma PO por ID.
        
        Args:
            po_id: ID da PO
            
        Returns:
            PO encontrada ou None
        """
        pass
    
    @abstractmethod
    async def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """
        Busca uma PO pelo número.
        
        Args:
            po_number: Número da PO (ex: "PO-12345")
            
        Returns:
            PO encontrada ou None
        """
        pass
    
    @abstractmethod
    async def list_by_status(
        self,
        status: POStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[PurchaseOrder]:
        """
        Lista POs por status.
        
        Args:
            status: Status das POs
            limit: Máximo de resultados
            offset: Paginação
            
        Returns:
            Lista de POs
        """
        pass
    
    @abstractmethod
    async def list_locked_by_user(self, user: str) -> List[PurchaseOrder]:
        """
        Lista todas as POs bloqueadas por um usuário.
        
        Args:
            user: Nome do usuário
            
        Returns:
            Lista de POs bloqueadas pelo usuário
        """
        pass
    
    @abstractmethod
    async def list_pending_approval(self) -> List[PurchaseOrder]:
        """
        Lista POs aguardando aprovação.
        
        Returns:
            Lista de POs em AWAITING_APPROVAL
        """
        pass
    
    @abstractmethod
    async def list_with_expired_locks(self) -> List[PurchaseOrder]:
        """
        Lista POs com locks expirados.
        
        Returns:
            Lista de POs com locks expirados
        """
        pass
    
    @abstractmethod
    async def delete(self, po_id: str) -> bool:
        """
        Deleta uma PO (soft delete recomendado).
        
        Args:
            po_id: ID da PO
            
        Returns:
            True se deletou, False se não encontrou
        """
        pass
    
    @abstractmethod
    async def exists(self, po_number: str) -> bool:
        """
        Verifica se uma PO existe.
        
        Args:
            po_number: Número da PO
            
        Returns:
            True se existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: POStatus) -> int:
        """
        Conta quantas POs existem em um status.
        
        Args:
            status: Status para contar
            
        Returns:
            Quantidade de POs
        """
        pass


# =============================================================================
# popr/domain/interfaces/sap_gateway.py
"""
Interface do Gateway SAP
Este é um PORT que será implementado por adapters (GUI, RFC, REST, etc)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class SAPGateway(ABC):
    """
    Interface para integração com SAP.
    
    Define os métodos necessários para:
    - Buscar dados de POs
    - Postar invoices
    - Gerenciar locks de documentos
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Conecta ao SAP.
        
        Returns:
            True se conectou com sucesso
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Desconecta do SAP"""
        pass
    
    @abstractmethod
    async def get_po_data(self, po_number: str) -> Dict[str, Any]:
        """
        Busca dados completos de uma PO no SAP.
        
        Args:
            po_number: Número da PO
            
        Returns:
            Dicionário com dados da PO:
            {
                "po_number": "PO-12345",
                "vendor_code": "V001",
                "vendor_name": "Fornecedor ABC",
                "total_amount": 5000.00,
                "currency": "BRL",
                "items": [...],
                "sap_doc_number": "4500123456",
                "fiscal_year": "2025"
            }
        """
        pass
    
    @abstractmethod
    async def get_po_header(self, po_number: str) -> Dict[str, Any]:
        """
        Busca apenas o cabeçalho da PO (mais rápido).
        
        Args:
            po_number: Número da PO
            
        Returns:
            Dados do cabeçalho
        """
        pass
    
    @abstractmethod
    async def get_po_items(self, po_number: str) -> List[Dict[str, Any]]:
        """
        Busca itens da PO.
        
        Args:
            po_number: Número da PO
            
        Returns:
            Lista de itens
        """
        pass
    
    @abstractmethod
    async def post_invoice(
        self,
        po_number: str,
        invoice_data: Dict[str, Any]
    ) -> str:
        """
        Posta uma invoice no SAP.
        
        Args:
            po_number: Número da PO
            invoice_data: Dados da invoice
            
        Returns:
            Número do documento criado no SAP
        """
        pass
    
    @abstractmethod
    async def lock_document(self, doc_number: str) -> bool:
        """
        Bloqueia um documento no SAP.
        
        Args:
            doc_number: Número do documento SAP
            
        Returns:
            True se bloqueou com sucesso
        """
        pass
    
    @abstractmethod
    async def unlock_document(self, doc_number: str) -> bool:
        """
        Desbloqueia um documento no SAP.
        
        Args:
            doc_number: Número do documento SAP
            
        Returns:
            True se desbloqueou com sucesso
        """
        pass
    
    @abstractmethod
    async def check_document_status(self, doc_number: str) -> str:
        """
        Verifica o status de um documento no SAP.
        
        Args:
            doc_number: Número do documento
            
        Returns:
            Status do documento
        """
        pass
    
    @abstractmethod
    async def search_pos_by_vendor(
        self,
        vendor_code: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[str]:
        """
        Busca POs por fornecedor.
        
        Args:
            vendor_code: Código do fornecedor
            date_from: Data inicial (YYYY-MM-DD)
            date_to: Data final (YYYY-MM-DD)
            
        Returns:
            Lista de números de PO
        """
        pass


# =============================================================================
# popr/domain/interfaces/notification_service.py
"""
Interface do Serviço de Notificações
"""
from abc import ABC, abstractmethod
from typing import List
from ..entities.purchase_order import PurchaseOrder


class NotificationService(ABC):
    """
    Interface para envio de notificações.
    
    Pode ser implementado por:
    - EmailAdapter
    - SlackAdapter
    - TeamsAdapter
    - SMSAdapter
    """
    
    @abstractmethod
    async def notify_approval_required(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que uma PO precisa de aprovação.
        
        Args:
            po: Purchase Order
            recipients: Lista de destinatários
            
        Returns:
            True se enviou com sucesso
        """
        pass
    
    @abstractmethod
    async def notify_approved(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que uma PO foi aprovada.
        """
        pass
    
    @abstractmethod
    async def notify_rejected(
        self,
        po: PurchaseOrder,
        recipients: List[str],
        reason: str
    ) -> bool:
        """
        Notifica que uma PO foi rejeitada.
        """
        pass
    
    @abstractmethod
    async def notify_error(
        self,
        po: PurchaseOrder,
        error_message: str,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que houve erro no processamento.
        """
        pass
    
    @abstractmethod
    async def notify_completed(
        self,
        po: PurchaseOrder,
        recipients: List[str]
    ) -> bool:
        """
        Notifica que o processamento foi concluído.
        """
        pass
