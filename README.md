# POPR System — visão detalhada (linguagem simples)

## O que é

O POPR é um sistema que organiza o ciclo completo de uma Purchase Order (PO).  
Ele pega a PO, confere com o SAP (simulado no demo), valida, aprova quando necessário, finaliza e registra.

## Objetivo em uma frase

Garantir que cada PO passe pelo mesmo fluxo, com rastreabilidade e sem depender de validações manuais fora do sistema.

---

## Visão por partes (bem direto)

### 1) Tela (UI)

Onde o usuário trabalha:

- vê a lista de POs
- filtra por status
- processa, aprova ou rejeita
- exporta CSV

### 2) API

É a “porta de entrada”:

- recebe o clique da tela
- transforma isso em comandos
- envia para a lógica do sistema

### 3) Regras do sistema

Aqui o sistema decide o que fazer:

- valida dados
- compara com SAP
- exige aprovação quando necessário
- conclui e registra o resultado

### 4) Integrações

Onde o sistema grava e consulta:

- banco de dados (SQLite)
- SAP (simulado)
- notificações (simples no demo)

---

## Fluxo completo (passo a passo, sem termos técnicos)

1. O usuário clica **Processar**
2. A API recebe essa ação
3. O sistema busca a PO no banco
4. Valida dados básicos
5. Busca informações no SAP (demo)
6. Confere se os dados batem
7. Se o valor for alto, pede aprovação
8. Se aprovado, finaliza
9. Registra tudo no banco
10. Notifica (no demo é log simples)

---

## Como os arquivos se conectam (visão clara)

### UI → API

- `ui/src/components/POPRDashboard.jsx`
  - faz as chamadas para `/api/v1/pos/*`
- `ui/vite.config.js`
  - aponta a API para `http://localhost:5174`

### API → Lógica

- `api/routes/po_routes.py`
  - recebe a requisição
  - chama o caso de uso correto
- `api/dependencies.py`
  - entrega as dependências certas

### Lógica → Regras

- `application/use_cases/process_po.py`
  - orquestra o fluxo completo
- `domain/entities/purchase_order.py`
  - contém regras e validações reais

### Regras → Infra

- `infrastructure/persistence/sqlalchemy/*`
  - salva e busca dados no banco
- `infrastructure/sap/demo_sap_gateway.py`
  - SAP simulado (para teste)
- `infrastructure/messaging/*`
  - notificações simples

---

## Explicação arquivo por arquivo (detalhada e simples)

### API

- `api/main.py`  
  Cria o servidor e registra as rotas. Também prepara o banco e coloca dados de exemplo.

- `api/dependencies.py`  
  Decide qual implementação será usada (SAP demo, notificações simples, banco SQLite).

- `api/routes/po_routes.py`  
  Endpoints de PO (processar, aprovar, rejeitar, listar).

- `api/routes/material_routes.py`  
  Endpoints do fluxo de materiais (separado do fluxo principal).

### Application (casos de uso)

- `application/use_cases/process_po.py`  
  O “maestro”: chama as etapas uma a uma.

- `application/use_cases/approve_po.py`  
  Aprovação e rejeição manual.

- `application/use_cases/process_material.py`  
  Fluxo mais simples de materiais.

### Domain (regras do negócio)

- `domain/entities/purchase_order.py`  
  Define o que é uma PO e como ela muda de status.

- `domain/interfaces/po_repository.py`  
  Contrato para salvar/buscar POs.

- `domain/interfaces/sap_gateway.py`  
  Contrato de integração com SAP.

- `domain/interfaces/notification_service.py`  
  Contrato de notificações.

- `domain/exceptions/domain_exceptions.py`  
  Erros de negócio padronizados.

### Infrastructure (onde as coisas realmente acontecem)

- `infrastructure/persistence/sqlalchemy/models.py`  
  Estrutura das tabelas no banco.

- `infrastructure/persistence/sqlalchemy/database.py`  
  Conexão com o banco.

- `infrastructure/persistence/sqlalchemy/po_repository_impl.py`  
  Salva e busca POs no banco.

- `infrastructure/persistence/sqlalchemy/seed.py`  
  Cria dados de exemplo no banco.

- `infrastructure/sap/demo_sap_gateway.py`  
  SAP simulado para testes.

- `infrastructure/sap/sap_gui_adapter.py`  
  Integração real via SAP GUI (não usada no demo).

- `infrastructure/messaging/simple_notification_service.py`  
  Notificação simples (apenas log).

- `infrastructure/messaging/email_adapter.py`  
  Envio real de email via SMTP.

- `infrastructure/messaging/slack_adapter.py`  
  Notificação via webhook do Slack.

### UI

- `ui/index.html`  
  Entrada do frontend.

- `ui/src/main.jsx`  
  Inicializa o React.

- `ui/src/App.jsx`  
  Renderiza o dashboard.

- `ui/src/components/POPRDashboard.jsx`  
  Tela principal e ações.

---

## Arquivos de dados

- `infrastructure/erp/demo_po_data.json`  
  Dados de POs simuladas (demo).

- `infrastructure/erp/demo_data.json`  
  Dados de materiais simulados.

- `popr.db`  
  Banco gerado automaticamente.

---

## Como rodar

Backend:

```bash
python -m uvicorn api.main:app --port 5174
```

Frontend:

```bash
cd ui
npm run dev
```
