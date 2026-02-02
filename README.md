# POPR System — documentação detalhada (arquivo por arquivo)

Este README descreve **todos os arquivos relevantes** do projeto e o fluxo de chamada **arquivo → arquivo**.

## Visão geral do fluxo

1) **UI** (`ui/src/components/POPRDashboard.jsx`) chama a **API** via `/api/v1/...`.
2) **API** (`api/routes/*.py`) cria comandos e chama **Use Cases** (`application/use_cases/*.py`).
3) **Use Cases** orquestram **Domain** (`domain/*`) e **Infrastructure** (`infrastructure/*`).
4) **Infrastructure** persiste no SQLite e conversa com SAP (demo ou GUI).

---

## API

### `api/__init__.py`
- Marca `api` como pacote Python.

### `api/main.py`
- Cria o `FastAPI` app.
- Registra rotas: `po_routes` e `material_routes`.
- No startup: inicializa o banco e roda o seed (`seed_demo_pos`).

### `api/dependencies.py`
- **Dependency Injection** do FastAPI.
- Cria `Database` (SQLite async).
- Injeta:
  - `PORepository` (SQLAlchemy)
  - `SAPGateway` (demo ou SAP GUI)
  - `NotificationService` (simple ou email)
- Usa envs:
  - `POPR_SAP_PROVIDER` (demo|sap)
  - `POPR_NOTIFY_PROVIDER` (simple|email)

### `api/routes/__init__.py`
- Marca `routes` como pacote Python.

### `api/routes/po_routes.py`
- Endpoints `/api/v1/pos/*`.
- Cria comandos e chama:
  - `ProcessPOUseCase`
  - `ApprovePOUseCase`
  - `RejectPOUseCase`
- Mapeia entidades de domínio para DTOs de resposta.

### `api/routes/material_routes.py`
- Endpoints:
  - `POST /process-material`
  - `GET /history/{material_id}`
- Chama `ProcessMaterialUseCase`.

---

## Application (casos de uso e portas)

### `application/__init__.py`
- Marca `application` como pacote.

### `application/use_cases/__init__.py`
- Marca `use_cases` como pacote.

### `application/use_cases/process_po.py`
- **Fluxo principal**:
  1. Buscar PO
  2. Validar
  3. Lock
  4. SAP data
  5. Reconciliar
  6. Aprovar
  7. Postar invoice
  8. Finalizar
  9. Notificar
- Usa:
  - `PORepository`
  - `SAPGateway`
  - `NotificationService`
  - Entidade `PurchaseOrder`

### `application/use_cases/approve_po.py`
- Fluxo de **aprovação/rejeição manual**.
- Posta invoice se `post_invoice = True`.

### `application/use_cases/process_material.py`
- Fluxo de materiais (estoque + POs abertas).
- Usa `ERPProviderPort`, `RepositoryPort`, `NotificationPort`.

### `application/ports/__init__.py`
- Exporta interfaces de portas.

### `application/ports/erp_provider_port.py`
- Contrato para consulta de estoque/POs em ERP.

### `application/ports/repository_port.py`
- Contrato para armazenar histórico de materiais.

### `application/ports/notification_port.py`
- Contrato simples de envio de email (fluxo de materiais).

---

## Domain

### `domain/__init__.py`
- Marca `domain` como pacote.

### `domain/entities/__init__.py`
- Marca `entities` como pacote.

### `domain/entities/purchase_order.py`
- Entidade central `PurchaseOrder`.
- Regras de transição de status.
- Lock / unlock.
- Validações de consistência.

### `domain/entities/material_status.py`
- Entidade e estados do fluxo de materiais.

### `domain/interfaces/__init__.py`
- Exporta as interfaces do domínio.

### `domain/interfaces/po_repository.py`
- Contrato do repositório de POs.

### `domain/interfaces/sap_gateway.py`
- Contrato do gateway SAP (async).

### `domain/interfaces/notification_service.py`
- Contrato de notificações (async).

### `domain/exceptions/__init__.py`
- Marca `exceptions` como pacote.

### `domain/exceptions/domain_exceptions.py`
- Exceções específicas de negócio.

### `domain/events/__init__.py`
- Marca `events` como pacote.

### `domain/events/po_events.py`
- Eventos de domínio (registrados pelo fluxo).

---

## Infrastructure

### Pacotes
- `infrastructure/__init__.py`
- `infrastructure/persistence/__init__.py`
- `infrastructure/persistence/sqlalchemy/__init__.py`
- `infrastructure/erp/__init__.py`
- `infrastructure/sap/__init__.py`
- `infrastructure/messaging/__init__.py`
- `infrastructure/repository/__init__.py`

### Persistência (SQLite + SQLAlchemy)
- `infrastructure/persistence/sqlalchemy/models.py`
  - Modelos `POModel` e `POItemModel`.
- `infrastructure/persistence/sqlalchemy/database.py`
  - Engine async e `sessionmaker`.
- `infrastructure/persistence/sqlalchemy/po_repository_impl.py`
  - Implementa `PORepository` usando SQLAlchemy.
- `infrastructure/persistence/sqlalchemy/seed.py`
  - Seed inicial do banco.

### SAP / ERP
- `infrastructure/sap/demo_sap_gateway.py`
  - SAP demo: lê `demo_po_data.json` e simula SAP.
- `infrastructure/sap/sap_gui_adapter.py`
  - Adapter real via SAP GUI Scripting.
- `infrastructure/erp/demo_provider.py`
  - Provider demo para fluxo de materiais.
- `infrastructure/erp/sap_gui_provider.py`
  - Provider stub (não implementado).

### Mensageria / Notificação
- `infrastructure/messaging/simple_notification_service.py`
  - Notificação simples (log).
- `infrastructure/messaging/email_adapter.py`
  - Envio SMTP (notificações formais).
- `infrastructure/messaging/slack_adapter.py`
  - Envio via webhook do Slack.
- `infrastructure/messaging/simple_email_notification.py`
  - Implementa `NotificationPort` do fluxo de materiais.

### Repositório de materiais
- `infrastructure/repository/json_status_repository.py`
  - Persistência do histórico de materiais em JSON.
- `infrastructure/repository/material_history.json`
  - Dados persistidos do histórico.

---

## UI

### `ui/index.html`
- Ponto de entrada do Vite.

### `ui/vite.config.js`
- Proxy `/api` → `http://localhost:5174` (backend).

### `ui/package.json` / `ui/package-lock.json`
- Dependências e scripts do frontend.

### `ui/src/main.jsx`
- Bootstrap React (`createRoot`).

### `ui/src/App.jsx`
- Renderiza `POPRDashboard`.

### `ui/src/components/POPRDashboard.jsx`
- Tela principal.
- Busca POs na API.
- Aciona Processar/Aprovar/Rejeitar.

### `ui/src/index.css`
- Estilos globais do dashboard.

---

## Dados e arquivos gerados

### `infrastructure/erp/demo_po_data.json`
- Dados demo de POs (seed do banco e SAP demo).

### `infrastructure/erp/demo_data.json`
- Dados demo do fluxo de materiais.

### `popr.db`
- SQLite gerado automaticamente.

### `uvicorn.out.log` / `uvicorn.err.log`
- Logs do backend (gerados no ambiente local).

---

## Execução local

Backend (porta 5174):
```bash
python -m uvicorn api.main:app --port 5174
```

Frontend (porta 5173):
```bash
cd ui
npm run dev
```

---

## Observações

- Arquivos `__pycache__/*.pyc` são artefatos do Python e podem ser ignorados.
- A integração SAP real exige SAP GUI e `pywin32` instalado.
