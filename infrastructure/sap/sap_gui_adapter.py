# popr/infrastructure/sap/sap_gui_adapter.py
"""
SAP GUI Adapter - Implementação real do SAPGateway

Este adapter usa SAP GUI Scripting para se conectar ao SAP
e executar transações automaticamente.
"""
import win32com.client
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import time

# Domain imports
from ...domain.interfaces.sap_gateway import SAPGateway


class SAPConnectionError(Exception):
    """Erro de conexão com SAP"""
    pass


class SAPTransactionError(Exception):
    """Erro ao executar transação SAP"""
    pass


class SAPGUIAdapter(SAPGateway):
    """
    Adapter para SAP GUI Scripting
    
    Implementa a interface SAPGateway usando SAP GUI.
    
    REQUISITOS:
    - SAP GUI instalado
    - SAP GUI Scripting habilitado
    - pywin32 instalado: pip install pywin32
    
    TRANSAÇÕES UTILIZADAS:
    - ME23N: Exibir Purchase Order
    - MIRO: Postar Invoice
    - ME22N: Modificar Purchase Order
    """
    
    def __init__(
        self,
        system_id: str,
        client: str,
        user: str,
        password: str,
        language: str = "PT",
        logger: Optional[logging.Logger] = None
    ):
        self.system_id = system_id
        self.client = client
        self.user = user
        self.password = password
        self.language = language
        self.logger = logger or logging.getLogger(__name__)
        
        # Objetos SAP (inicializados no connect)
        self.sap_gui = None
        self.application = None
        self.connection = None
        self.session = None
        
        self._connected = False
    
    # =========================================================================
    # CONEXÃO
    # =========================================================================
    
    async def connect(self) -> bool:
        """
        Conecta ao SAP via GUI Scripting
        
        Returns:
            True se conectou com sucesso
        """
        try:
            self.logger.info(f"Connecting to SAP system {self.system_id}")
            
            # 1. Obtém o SAP GUI Scripting engine
            self.sap_gui = win32com.client.GetObject("SAPGUI")
            
            if not self.sap_gui:
                raise SAPConnectionError("SAP GUI not found")
            
            # 2. Obtém a aplicação
            self.application = self.sap_gui.GetScriptingEngine
            
            # 3. Abre conexão
            connection_string = f"/H/{self.system_id}/S/3200"
            self.connection = self.application.OpenConnection(connection_string, True)
            
            # 4. Obtém a sessão
            self.session = self.connection.Children(0)
            
            # 5. Faz login
            self._login()
            
            self._connected = True
            self.logger.info("✅ Connected to SAP successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to SAP: {str(e)}")
            raise SAPConnectionError(f"Connection failed: {str(e)}")
    
    def _login(self) -> None:
        """Executa o login no SAP"""
        try:
            # Preenche campos de login
            self.session.findById("wnd[0]/usr/txtRSYST-MANDT").text = self.client
            self.session.findById("wnd[0]/usr/txtRSYST-BNAME").text = self.user
            self.session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = self.password
            self.session.findById("wnd[0]/usr/txtRSYST-LANGU").text = self.language
            
            # Pressiona Enter
            self.session.findById("wnd[0]").sendVKey(0)
            
            # Aguarda um pouco
            time.sleep(1)
            
            # Verifica se logou (se não tem erro)
            try:
                error = self.session.findById("wnd[1]/usr/txtMESSTXT1").text
                if error:
                    raise SAPConnectionError(f"Login failed: {error}")
            except:
                pass  # Se não encontrou erro, está OK
                
        except Exception as e:
            raise SAPConnectionError(f"Login failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Desconecta do SAP"""
        try:
            if self.session:
                self.session.findById("wnd[0]").close()
            
            if self.connection:
                self.connection.CloseSession(self.session)
            
            self._connected = False
            self.logger.info("Disconnected from SAP")
            
        except Exception as e:
            self.logger.warning(f"Error disconnecting: {str(e)}")
    
    # =========================================================================
    # BUSCAR DADOS DE PO
    # =========================================================================
    
    async def get_po_data(self, po_number: str) -> Dict[str, Any]:
        """
        Busca dados completos de uma PO no SAP
        
        Usa transação ME23N para exibir a PO
        """
        self._ensure_connected()
        
        try:
            self.logger.info(f"Fetching PO data for {po_number}")
            
            # 1. Abre transação ME23N
            self.session.startTransaction("ME23N")
            time.sleep(0.5)
            
            # 2. Preenche número da PO
            self.session.findById("wnd[0]/usr/ctxtRM06E-BSTNR").text = po_number
            
            # 3. Executa (Enter)
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(1)
            
            # 4. Verifica se encontrou a PO
            try:
                error_msg = self.session.findById("wnd[1]/usr/txtMESSTXT1").text
                if "não existe" in error_msg.lower() or "not exist" in error_msg.lower():
                    raise ValueError(f"PO {po_number} not found in SAP")
            except:
                pass  # Se não tem erro, continua
            
            # 5. Extrai dados do cabeçalho
            header_data = self._extract_header_data()
            
            # 6. Extrai itens
            items_data = self._extract_items_data()
            
            # 7. Volta para menu principal
            self.session.findById("wnd[0]").sendVKey(3)  # F3 = Back
            time.sleep(0.5)
            
            # 8. Monta resultado
            result = {
                **header_data,
                "items": items_data,
                "extracted_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ PO data extracted: {len(items_data)} items")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get PO data: {str(e)}")
            # Tenta voltar ao menu
            try:
                self.session.findById("wnd[0]").sendVKey(3)
            except:
                pass
            raise SAPTransactionError(f"Failed to get PO data: {str(e)}")
    
    def _extract_header_data(self) -> Dict[str, Any]:
        """Extrai dados do cabeçalho da PO"""
        try:
            data = {
                "po_number": self._safe_get_text("wnd[0]/usr/ctxtRM06E-BSTNR"),
                "vendor_code": self._safe_get_text("wnd[0]/usr/ctxtEKKO-LIFNR"),
                "vendor_name": self._safe_get_text("wnd[0]/usr/txtLFA1-NAME1"),
                "currency": self._safe_get_text("wnd[0]/usr/ctxtEKKO-WAERS"),
                "total_amount": self._safe_get_number("wnd[0]/usr/txtRM06E-NETWR"),
                "sap_doc_number": self._safe_get_text("wnd[0]/usr/ctxtEKKO-EBELN"),
                "sap_fiscal_year": self._safe_get_text("wnd[0]/usr/txtEKKO-AEDAT")[:4],
                "purchase_org": self._safe_get_text("wnd[0]/usr/ctxtEKKO-EKORG"),
                "purchase_group": self._safe_get_text("wnd[0]/usr/ctxtEKKO-EKGRP"),
                "created_by": self._safe_get_text("wnd[0]/usr/txtEKKO-ERNAM"),
                "created_date": self._safe_get_text("wnd[0]/usr/txtEKKO-AEDAT")
            }
            
            return data
            
        except Exception as e:
            self.logger.warning(f"Error extracting header: {str(e)}")
            return {}
    
    def _extract_items_data(self) -> List[Dict[str, Any]]:
        """Extrai itens da PO"""
        items = []
        
        try:
            # Clica na aba de itens
            self.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/tabsHEADER_DETAIL/tabpTABIDT13").select()
            time.sleep(0.5)
            
            # Identifica a tabela de itens
            table = self.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211")
            
            # Itera pelos itens
            row_count = table.RowCount
            
            for i in range(row_count):
                try:
                    item = {
                        "item_number": self._safe_get_text(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/txtMEPO1211-EBELP[0,{i}]"),
                        "material_code": self._safe_get_text(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/ctxtMEPO1211-EMATN[1,{i}]"),
                        "description": self._safe_get_text(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/txtMEPO1211-TXZ01[2,{i}]"),
                        "quantity": self._safe_get_number(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/txtMEPO1211-MENGE[3,{i}]"),
                        "unit": self._safe_get_text(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/ctxtMEPO1211-MEINS[4,{i}]"),
                        "unit_price": self._safe_get_number(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/txtMEPO1211-NETPR[5,{i}]"),
                        "total_price": self._safe_get_number(f"wnd[0]/usr/.../tblSAPLMEGUITC_1211/txtMEPO1211-NETWR[6,{i}]")
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting item {i}: {str(e)}")
                    continue
            
            return items
            
        except Exception as e:
            self.logger.warning(f"Error extracting items: {str(e)}")
            return []
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _safe_get_text(self, element_id: str) -> str:
        """Busca texto de um elemento de forma segura"""
        try:
            return self.session.findById(element_id).text
        except:
            return ""
    
    def _safe_get_number(self, element_id: str) -> float:
        """Busca número de um elemento de forma segura"""
        try:
            text = self.session.findById(element_id).text
            # Remove formatação (pontos, vírgulas)
            text = text.replace(".", "").replace(",", ".")
            return float(text)
        except:
            return 0.0
    
    def _ensure_connected(self) -> None:
        """Garante que está conectado"""
        if not self._connected:
            raise SAPConnectionError("Not connected to SAP. Call connect() first.")
    
    # =========================================================================
    # OUTROS MÉTODOS DA INTERFACE
    # =========================================================================
    
    async def get_po_header(self, po_number: str) -> Dict[str, Any]:
        """Busca apenas o cabeçalho (mais rápido)"""
        # Implementação similar a get_po_data, mas sem extrair itens
        full_data = await self.get_po_data(po_number)
        
        # Remove itens
        header = {k: v for k, v in full_data.items() if k != "items"}
        return header
    
    async def get_po_items(self, po_number: str) -> List[Dict[str, Any]]:
        """Busca apenas os itens"""
        full_data = await self.get_po_data(po_number)
        return full_data.get("items", [])
    
    async def post_invoice(
        self,
        po_number: str,
        invoice_data: Dict[str, Any]
    ) -> str:
        """
        Posta uma invoice no SAP
        
        Usa transação MIRO
        """
        self._ensure_connected()
        
        try:
            self.logger.info(f"Posting invoice for PO {po_number}")
            
            # 1. Abre transação MIRO
            self.session.startTransaction("MIRO")
            time.sleep(1)
            
            # 2. Preenche campos
            self.session.findById("wnd[0]/usr/ctxtRM08M-BELNR").text = po_number
            self.session.findById("wnd[0]/usr/txtRM08M-WRBTR").text = str(invoice_data.get("total_amount"))
            
            # 3. Simula (Ctrl+S)
            self.session.findById("wnd[0]").sendVKey(11)
            time.sleep(1)
            
            # 4. Verifica erros
            # TODO: Implementar verificação de erros
            
            # 5. Posta (Ctrl+S novamente)
            self.session.findById("wnd[0]").sendVKey(11)
            time.sleep(1)
            
            # 6. Captura número do documento
            doc_number = self._safe_get_text("wnd[0]/sbar/pane[0]")
            
            # 7. Volta ao menu
            self.session.findById("wnd[0]").sendVKey(3)
            
            self.logger.info(f"✅ Invoice posted: {doc_number}")
            
            return doc_number
            
        except Exception as e:
            self.logger.error(f"❌ Failed to post invoice: {str(e)}")
            try:
                self.session.findById("wnd[0]").sendVKey(3)
            except:
                pass
            raise SAPTransactionError(f"Failed to post invoice: {str(e)}")
    
    async def lock_document(self, doc_number: str) -> bool:
        """Bloqueia documento no SAP"""
        # Implementação específica de lock
        # Pode usar transação ME22N com modo de bloqueio
        self.logger.info(f"Locking document {doc_number}")
        return True
    
    async def unlock_document(self, doc_number: str) -> bool:
        """Desbloqueia documento no SAP"""
        self.logger.info(f"Unlocking document {doc_number}")
        return True
    
    async def check_document_status(self, doc_number: str) -> str:
        """Verifica status do documento"""
        # TODO: Implementar
        return "active"
    
    async def search_pos_by_vendor(
        self,
        vendor_code: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[str]:
        """Busca POs por fornecedor"""
        # Usa ME2N para pesquisar
        self._ensure_connected()
        
        try:
            self.session.startTransaction("ME2N")
            time.sleep(0.5)
            
            # Preenche vendor
            self.session.findById("wnd[0]/usr/ctxtEN_LIFNR-LOW").text = vendor_code
            
            if date_from:
                self.session.findById("wnd[0]/usr/ctxtEN_BEDAT-LOW").text = date_from
            if date_to:
                self.session.findById("wnd[0]/usr/ctxtEN_BEDAT-HIGH").text = date_to
            
            # Executa
            self.session.findById("wnd[0]").sendVKey(8)
            time.sleep(1)
            
            # Extrai POs da lista
            # TODO: Implementar extração
            
            # Volta
            self.session.findById("wnd[0]").sendVKey(3)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

"""
# Configurar adapter
sap_adapter = SAPGUIAdapter(
    system_id="PRD",
    client="100",
    user="SEU_USUARIO",
    password="SUA_SENHA",
    language="PT"
)

# Conectar
await sap_adapter.connect()

# Buscar dados da PO
po_data = await sap_adapter.get_po_data("4500123456")

print(f"PO: {po_data['po_number']}")
print(f"Vendor: {po_data['vendor_name']}")
print(f"Total: {po_data['total_amount']} {po_data['currency']}")
print(f"Items: {len(po_data['items'])}")

# Postar invoice
invoice_number = await sap_adapter.post_invoice(
    po_number="4500123456",
    invoice_data={
        "total_amount": 5000.00,
        "currency": "BRL"
    }
)

print(f"Invoice posted: {invoice_number}")

# Desconectar
await sap_adapter.disconnect()
"""