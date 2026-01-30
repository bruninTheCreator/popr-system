# POPR System

Purchase Order Processing & Reconciliation (POPR) e um sistema para orquestrar o ciclo completo de uma Purchase Order: validacao, reconciliacao com SAP, aprovacao (automatica ou manual), postagem de invoice e notificacoes.

## Visao geral

O fluxo principal esta no use case `ProcessPOUseCase` e executa:

1. Buscar a PO
2. Validar dados
3. Bloquear a PO e (opcionalmente) o documento no SAP
4. Buscar dados no SAP
5. Reconciliar dados
6. Aprovar (automatica ou manual)
7. Postar invoice no SAP
8. Finalizar e notificar

Existe tambem um fluxo de aprovacao/rejeicao manual (`ApprovePOUseCase` e `RejectPOUseCase`) e um dashboard React para acompanhamento.

## Arquitetura

O projeto segue um estilo Clean/Hexagonal:

- `domain/`: entidades, regras de negocio e contratos (interfaces)
- `application/`: casos de uso e orquestracao
- `infrastructure/`: adapters (SAP GUI, email, Slack)
- `api/`: endpoints FastAPI e injecao de dependencias
- `ui/`: componente React do dashboard

## Estrutura do repositorio

```bash

api/
  dependencies.py
  routes/po_routes.py
application/
  use_cases/
domain/
  entities/
  events/
  exceptions/
  interfaces/
infrastructure/
  messaging/
  sap/
ui/
  components/POPRDashboard.jsx
```

## Endpoints (API)

Base: `/api/v1/pos`

- `POST /process` - processa uma PO completa
- `POST /approve` - aprova uma PO manualmente
- `POST /reject` - rejeita uma PO
- `GET /{po_number}` - busca uma PO por numero
- `GET /` - lista POs (com filtro opcional de status)
- `GET /pending-approval/` - lista POs aguardando aprovacao

Exemplo (processar PO):

```bash
curl -X POST http://localhost:8000/api/v1/pos/process ^
  -H "Content-Type: application/json" ^
  -d "{\"po_number\":\"PO-12345\",\"user\":\"maria\"}"
```

### Materiais (ProcessPOUseCase simplificado)

Endpoints adicionais:

- `POST /process-material` - processa o fluxo de materiais
- `GET /history/{material_id}` - retorna o historico de status do material

Exemplo (processar material):

```bash
curl -X POST http://localhost:8000/process-material \
  -H "Content-Type: application/json" \
  -d "{\"material_id\":\"MAT-002\",\"minimum_stock\":10,\"notify_email\":\"compras@empresa.com\"}"
```

Resposta esperada:

```json
{
  "success": true,
  "material_id": "MAT-002",
  "message": "Material sem PO aberta.",
  "history": [
    { "status": "RECEBIDO", "timestamp": "2024-01-10T10:00:00" },
    { "status": "VERIFICANDO_CADASTRO", "timestamp": "2024-01-10T10:00:00" },
    { "status": "CONSULTANDO_ESTOQUE", "timestamp": "2024-01-10T10:00:01" },
    { "status": "SEM_ESTOQUE", "timestamp": "2024-01-10T10:00:01" },
    { "status": "CONSULTANDO_PO", "timestamp": "2024-01-10T10:00:02" },
    { "status": "SEM_PO", "timestamp": "2024-01-10T10:00:02" }
  ]
}
```

## UI (Dashboard)

O dashboard React esta em `ui/components/POPRDashboard.jsx` e:

- consome a API em `http://localhost:8000/api/v1`
- permite processar, aprovar ou rejeitar POs
- oferece filtros por status e exportacao CSV

## Configuracao

Algumas configuracoes estao hardcoded em `api/dependencies.py` e devem ser movidas para variaveis de ambiente:

- `DATABASE_URL`
- credenciais do SAP
- SMTP para email
- webhook do Slack (se usado)

### Demo data

Arquivo de exemplo para o provider DEMO:

- `infrastructure/erp/demo_data.json`

## Dependencias principais (observadas no codigo)

- API: FastAPI, Pydantic, SQLAlchemy (async), aiosqlite
- Infra: pywin32 (SAP GUI Scripting), aiohttp (Slack)
- UI: React, lucide-react

## Observacoes

- Existe um app FastAPI em `api/main.py` que registra as rotas de PO e materiais.
- O caminho `infrastructure/persistence/...` e referenciado, mas nao esta presente neste repositorio.
