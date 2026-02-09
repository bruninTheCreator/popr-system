# Arquitetura POPR

## Objetivo do sistema

Automatizar o ciclo de uma Purchase Order (PO): conferir dados, validar com SAP, aprovar quando necessário, registrar e notificar.

## Visão em camadas (de fora para dentro)

1) **Interface (UI)**

- Tela única onde o usuário acompanha e executa ações.
- Botões: processar, aprovar, rejeitar, filtrar, exportar.

1) **API**

- Porta de entrada do sistema.
- Recebe as ações da tela e envia para a lógica de negócio.

1) **Lógica de negócio**

- Onde o sistema decide o que fazer com cada PO.
- Regras de aprovação, validação e sequência do processo.

1) **Integrações**

- Banco de dados (guarda as POs).
- SAP (consulta e registro).
- Notificações (email/Slack).

## Fluxo principal (simples)

1. Usuário clica **Processar**
2. A API recebe e chama a lógica
3. A lógica valida e busca dados do SAP
4. Se precisar, entra em **aguardando aprovação**
5. Se aprovado, finaliza e notifica
6. Tudo fica registrado no banco

## Como os arquivos se conectam (visão curta)

**Tela**
→ `ui/src/components/POPRDashboard.jsx`
→ chama **API** em `/api/v1/pos/*`

**API**
→ `api/routes/po_routes.py`
→ chama **casos de uso**

**Casos de uso**
→ `application/use_cases/process_po.py`
→ usa **entidades e regras**

**Entidades/Regras**
→ `domain/entities/purchase_order.py`
→ validação e status

**Infraestrutura**
→ Banco: `infrastructure/persistence/sqlalchemy/*`
→ SAP demo: `infrastructure/sap/demo_sap_gateway.py`
→ Notificações: `infrastructure/messaging/*`

## O que está pronto para testes

- Processar PO
- Aprovar / Rejeitar PO
- Listar POs por status
- Integração SAP simulada
- Banco local com dados demo

## Observações para reunião

- A simulação permite validar o fluxo completo sem depender do SAP real.
- As camadas estão separadas: mudar a UI não muda regras, e mudar integração não muda a tela.

## SAP no POPR (visão executiva)

Existe um documento específico e direto para reunião:

- `ARCHITECTURE_SAP.md`
