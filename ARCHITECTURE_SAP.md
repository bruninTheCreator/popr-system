# SAP no POPR — visão executiva

## Ideia central
O **SAP não é parte do POPR**.  
Ele é um sistema externo e soberano que o POPR **pilota**.

**Em resumo:**
- SAP = **sistema de estado** (a verdade)
- POPR = **sistema de decisão** (o que fazer)

---

## Papel do SAP dentro do POPR

O SAP atua como:
- **Fonte da verdade dos dados**
- **Executor de transações**
- **Validador das regras corporativas**

O POPR:
1) recebe um evento  
2) decide o que precisa  
3) chama o SAP  
4) lê o resultado  
5) decide o próximo passo

---

## Fluxo real (simplificado)

1. POPR recebe um evento  
2. POPR decide: “preciso consultar estoque”  
3. POPR abre SAP GUI e executa MB52  
4. SAP responde com os dados  
5. POPR lê a tela e extrai a tabela  
6. POPR decide: “tem estoque?”  
   - se sim: encerra  
   - se não: roda ME2M  
7. POPR consolida e gera saída (ex.: Excel + email)

---

## Camadas já preparadas no sistema

**Domain**
- Contrato SAP: `domain/interfaces/sap_gateway.py`

**Application**
- Fluxo principal que chama SAP: `application/use_cases/process_po.py`

**Infrastructure**
- Adapter SAP GUI: `infrastructure/sap/sap_gui_adapter.py`
- Demo SAP: `infrastructure/sap/demo_sap_gateway.py`
- Transações (esqueleto): `infrastructure/sap/transactions/*`

---

## O que precisamos obrigatoriamente (sem inventar)

1) **Ambiente Windows com SAP GUI instalado**
2) **SAP GUI Scripting habilitado**
3) **Credenciais válidas de SAP**
4) **Acesso de rede ao SAP**
5) **pywin32 instalado no Python do backend**
6) **Backend rodando no mesmo Windows do SAP GUI**

---

## O que eu preciso de você (objetivo)

- Endereço do SAP (system/client)  
- Usuário e senha (ou usuário técnico)  
- Confirmação de que o SAP GUI Scripting está habilitado  
- Quais transações são obrigatórias (ex.: MB52, ME2M)  
- Campos mínimos que devemos ler e salvar

---

## Próximo passo
Com esses itens, conectamos o adapter real e substituímos o demo sem quebrar o resto do sistema.
