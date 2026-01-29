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

## Dependencias principais (observadas no codigo)

- API: FastAPI, Pydantic, SQLAlchemy (async), aiosqlite
- Infra: pywin32 (SAP GUI Scripting), aiohttp (Slack)
- UI: React, lucide-react

## Observacoes

- Ainda nao existe um `main.py` ou app FastAPI no repo. Para expor a API, monte um app e registre o router de `api/routes/po_routes.py`.
- O caminho `infrastructure/persistence/...` e referenciado, mas nao esta presente neste repositorio.
