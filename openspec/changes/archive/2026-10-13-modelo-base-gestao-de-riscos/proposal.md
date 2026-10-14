# Proposal: Modelo Base de Gestão de Riscos (HC-UFPE)

## Why
O Hospital das Clínicas da UFPE (HC-UFPE / EBSERH) realiza atualmente o mapeamento de riscos através de um formulário plano no REDCap. Apesar de funcional, o modelo legado apresenta limitações críticas:
1. **Estrutura rígida e redundante:** Uso de mais de 87 campos condicionais artificiais no REDCap para simular a seleção de Macroprocessos e Processos, além de limites fixos de controles e planos de ação.
2. **Falta de controle de acesso setorial granular:** Inexistência de um controle dinâmico que permita configurar "quem vê o relatório de quem", restringindo o acesso do gestor ao seu setor ou concedendo visões compartilhadas de forma flexível.
3. **Ausência de workflow institucional:** Falta de controle de tramitação (Rascunho, Submetido para UGERC, Em Monitoramento) e validações em tempo real do apetite de risco estabelecido pelo Colegiado Executivo (tolerância ≤ 7,99).

A migração para o **Framework SETISD (FastAPI + Vue 3)** permite transformar esse processo em uma aplicação web corporativa nativa, relacional, integrada ao Active Directory (AD) e plenamente aderente ao *Guia Prático da UGERC (`GU.UGERC.001`)* e à *Arquitetura de Processos EBSERH (Hospital Tipo II)*.

---

## What Changes

1. **Estrutura Organizacional e Processos Hospitalares:**
   * Cadastro oficial das **76 Unidades Organizacionais (UORGs)** do HC-UFPE, contemplando os 4 órgãos independentes (*Colegiado Executivo*, *Conselho Consultivo*, *Ouvidoria* e *Auditoria*) e as Gerências/Superintendência (*SUP*, *GAS*, *GAD*, *GEP*) como unidades com riscos próprios mapeáveis.
   * Carga do catálogo oficial de **Macroprocessos e Processos EBSERH Tipo II** (Slides 169–206), com o macroprocesso *GERIR RISCOS* atribuído à UGERC e suporte a processos corporativos transversais.
   * Suporte a gestão de riscos por Projetos (Interruptor "Possui Projeto?" com Nome do Projeto e Pilar Estratégico associado).

2. **Segurança Híbrida, RBAC e Matriz de Visibilidade:**
   * Autenticação via AD da Ebserh (`EBSERHNET`) com persistência de perfis no banco SQLite local (`data/app.db`).
   * Perfis de Acesso: `ADMINISTRADOR` (acesso total e governança), `GESTOR_UNIDADE` (gestão setorial de riscos) e `CONSULTA_SETORIAL`.
   * *Seed* inicial configurando `tassio.silva@hubrasil.gov.br` e `renata.albuquerque.1@hubrasil.gov.br` como administradores mestres.
   * Matriz de **Visibilidade Compartilhada**: Módulo administrativo para parametrizar quais setores adicionais cada usuário pode visualizar ou auditar.

3. **Motor de Avaliação e Matriz de Riscos 5x5:**
   * Cálculo em tempo real de **Risco Inerente** ($P \times I$), **Fator de Mitigação** pelos controles cadastrados dinamicamente (1:N) e **Risco Residual**.
   * Identificação imediata do Apetite a Risco (≤ 7,99 = Tolerável; > 7,99 = Exige Plano de Ação 5W2H e Plano de Contingência com gatilhos).

4. **Experiência do Usuário (Frontend Vue 3):**
   * *Wizard* em 5 etapas respeitando a metodologia do Guia da UGERC.
   * Suporte a salvamento em *Rascunho* (*Draft*).
   * Painel com Matriz de Riscos interativa e exportação de Fichas de Risco.

---

## Capabilities

### New Capabilities
* `organizacao-processos`: Gestão cadastral de unidades organizacionais do HC-UFPE e catálogo de processos EBSERH Tipo II com categorização transversal.
* `administracao-visibilidade`: Painel de administração de usuários com concessão de perfis e configuração de visibilidade cruzada entre setores.
* `mapeamento-riscos`: Formulário em etapas para identificação, cálculo de severidade e geração de planos de ação (5W2H) e contingência.
* `matriz-risco-painel`: Visualização gráfica e analítica da matriz 5x5 e listagem filtrada por permissões do usuário logado.

---

## Impact

* **Backend:** Novos modelos SQLAlchemy em `src/models/`, rotas REST em `src/routers/`, controladores em `src/controllers/` e migrações Alembic em `alembic/versions/`.
* **Banco de Dados:** Criação de tabelas no SQLite local (`data/app.db`).
* **Frontend:** Novas views (`MapeamentoRiscos.vue`, `PainelRiscos.vue`, `AdminUsuarios.vue`) e componentes visuais (`MatrizRisco5x5.vue`, `WizardForm.vue`).
* **Conformidade:** Preservação de 100% de adesão aos 11 pilares do `audit_framework.py` (Default-Private Routers, HttpOnly cookies, Security Headers e Trilha de Auditoria LGPD).
