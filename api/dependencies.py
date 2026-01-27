"""
Dependency Injection para FastAPI

Aqui configuramos todas as dependências que serão injetadas nos endpoints
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from fastapi import Depends

from ..infrastructure.persistence.sqlalchemy.database import Database
from ..infrastructure.persistence.sqlalchemy.po_repository_impl import SQLAlchemyPORepository
from ..infrastructure.sap.sap_gui_adapter import SAPGUIAdapter
from ..infrastructure.messaging.email_adapter import EmailNotificationService, EmailConfig
from ..infrastructure.messaging.slack_adapter import SlackNotificationService
from ..application.use_cases.process_po import ProcessPOUseCase
from ..application.use_cases.approve_po import ApprovePOUseCase, RejectPOUseCase
from ..domain.interfaces.notification_service import NotificationService

# Configuração global (isso viria de um arquivo de config)
DATABASE_URL = "sqlite+aiosqlite:///./popr.db"
db = Database(DATABASE_URL)

# Logger
logger = logging.getLogger(__name__)


# =============================================================================
# DEPENDÊNCIAS DE INFRAESTRUTURA
# =============================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Retorna uma sessão do banco de dados
    
    Uso:
        @app.get("/pos")
        async def list_pos(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    session = db.get_session()
    try:
        yield session
    finally:
        await session.close()


async def get_po_repository(
    session: AsyncSession = Depends(get_db_session)
) -> SQLAlchemyPORepository:
    """Retorna o repositório de POs"""
    return SQLAlchemyPORepository(session)


async def get_sap_gateway() -> AsyncGenerator[SAPGUIAdapter, None]:
    """
    Retorna o gateway SAP
    
    TODO: Configurar com variáveis de ambiente
    """
    sap = SAPGUIAdapter(
        system_id="PRD",
        client="100",
        user="SAP_USER",
        password="SAP_PASS",
        language="PT"
    )
    
    # Conecta
    await sap.connect()
    
    try:
        yield sap
    finally:
        await sap.disconnect()


async def get_notification_service() -> NotificationService:
    """
    Retorna o serviço de notificações
    
    Pode ser Email, Slack, ou Composite
    """
    # Email config
    email_config = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="popr@company.com",
        smtp_password="app_password",
        from_email="popr@company.com",
        from_name="POPR System"
    )
    
    return EmailNotificationService(email_config)


# =============================================================================
# DEPENDÊNCIAS DE USE CASES
# =============================================================================

async def get_process_po_use_case(
    repo = Depends(get_po_repository),
    sap = Depends(get_sap_gateway),
    notifier = Depends(get_notification_service)
) -> ProcessPOUseCase:
    """Retorna o use case de processar PO"""
    return ProcessPOUseCase(repo, sap, notifier, logger)


async def get_approve_po_use_case(
    repo = Depends(get_po_repository),
    sap = Depends(get_sap_gateway),
    notifier = Depends(get_notification_service)
) -> ApprovePOUseCase:
    """Retorna o use case de aprovar PO"""
    return ApprovePOUseCase(repo, sap, notifier, logger)


async def get_reject_po_use_case(
    repo = Depends(get_po_repository),
    notifier = Depends(get_notification_service)
) -> RejectPOUseCase:
    """Retorna o use case de rejeitar PO"""
    return RejectPOUseCase(repo, notifier, logger)