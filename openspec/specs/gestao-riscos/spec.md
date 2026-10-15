# Gestão de Riscos Specification

## Requirements

### Requirement: Autenticação AD e Perfis de Acesso
The system SHALL authenticate users against Active Directory (AD / EBSERHNET) and resolve local RBAC profiles stored in SQLite (`data/app.db`).

#### Scenario: Login de usuário administrador
- **GIVEN** that a user with email `tassio.silva@hubrasil.gov.br` or `renata.albuquerque.1@hubrasil.gov.br` authenticates via AD,
- **WHEN** the authentication succeeds,
- **THEN** the system SHALL grant the `ADMINISTRADOR` profile with global management permissions.

#### Scenario: Login de gestor setorial
- **GIVEN** that a user without global administrator role authenticates via AD,
- **WHEN** their local profile is verified,
- **THEN** the system SHALL restrict risk registration and reporting to their assigned unit (`unidade_id`) and explicitly granted visible units.

---

### Requirement: Gestão de Unidades e Órgãos Independentes
The system SHALL maintain the organizational hierarchy of HC-UFPE without forcing independent administrative bodies under any hierarchical management.

#### Scenario: Cadastro de Órgãos Independentes
- **GIVEN** the entities `Colegiado Executivo`, `Conselho Consultivo`, `Ouvidoria` and `Auditoria`,
- **WHEN** these units are created in the database,
- **THEN** the system SHALL classify them as independent bodies with no parent management linkage (`unidade_pai_id IS NULL`).

#### Scenario: Mapeamento de Riscos em Gerências de Topo
- **GIVEN** the top management units `Superintendência`, `Gerência de Atenção à Saúde`, `Gerência Administrativa` and `Gerência de Ensino e Pesquisa`,
- **WHEN** a risk mapping is initiated,
- **THEN** the system SHALL allow direct association of risks to these top entities.

---

### Requirement: Catálogo de Processos EBSERH e Projetos
The system SHALL support the EBSERH Type II process catalog and allow conditional project association for cross-cutting processes.

#### Scenario: Associação de Projeto ao Processo de Gestão de Riscos
- **GIVEN** that a user selects the process `REALIZAR IDENTIFICAÇÃO E AVALIAÇÃO DOS EVENTOS DE RISCOS`,
- **WHEN** the user marks the option "Possui Projeto?",
- **THEN** the system SHALL require input for the Project Name (`nome_projeto`) and Strategic Pillar (`pilar_estrategico_id`).

---

### Requirement: Matriz de Visibilidade Configurável ("Quem vê de Quem")
The system SHALL provide an administrative interface allowing administrators to grant users visibility over one or more hospital units beyond their primary assignment.

#### Scenario: Concessão de visualização adicional
- **GIVEN** an authenticated administrator,
- **WHEN** they associate unit $B$ to a manager whose primary unit is $A$,
- **THEN** the system SHALL allow that manager to view risk dashboards and reports from both unit $A$ and unit $B$.

#### Scenario: Bloqueio de acesso a setores não autorizados
- **GIVEN** a sector manager attempting to query reports for unit $C$ which has not been granted,
- **WHEN** the query request is sent,
- **THEN** the API SHALL reject the request with HTTP 403 Forbidden.

---

### Requirement: Motor de Cálculo de Severidade e Apetite de Risco
The system SHALL calculate risk severity based on Probability, Impact and Mitigation Controls, enforcing action plans when the risk exceeds the institutional risk appetite.

#### Scenario: Cálculo de Risco Inerente e Risco Residual
- **GIVEN** a risk with Probability $P \in [1, 5]$ and Impact $I \in [1, 5]$,
- **WHEN** the user declares $C$ active controls,
- **THEN** the system SHALL compute:
  - $\text{Risco Inerente} = P \times I$
  - $\text{Fator de Mitigação} \in \{1.0, 0.8, 0.6, 0.4, 0.2\}$
  - $\text{Risco Residual} = \text{round}(\text{Risco Inerente} \times \text{Fator de Mitigação})$

#### Scenario: Risco acima da tolerância institucional
- **GIVEN** a calculated residual risk score $> 7.99$ (classifications `Alto` or `Extremo`),
- **WHEN** the user completes the risk evaluation,
- **THEN** the system SHALL mandate the registration of at least one 5W2H Action Plan and at least one Contingency Plan with an operational trigger.

---

### Requirement: Salvamento em Rascunho e Submissão
The system SHALL allow saving risk mappings in `RASCUNHO` status without requiring mandatory validation of advanced fields, enforcing full validation only upon final submission (`SUBMETIDO`).

---

### Requirement: Processos Comuns e Processo Extra ("Outro")
The system SHALL provide the 20 common transversal processes across all 76 organizational units, allow text searching on macroprocesses and processes, present common processes in a separate visual section below unit-specific processes, and offer a macroprocess `Outro` with a mandatory text field `processo_outro` for newly mapped processes.

#### Scenario: Seleção de Processo Comum
- **GIVEN** an organizational unit selected in the risk mapping wizard,
- **WHEN** the user inspects available processes,
- **THEN** the system SHALL display unit-specific processes at the top and common transversal processes in a distinct section below without mixing them.

#### Scenario: Mapeamento de Processo "Outro"
- **GIVEN** that a process to be mapped does not yet exist in the catalog,
- **WHEN** the user selects the macroprocess `Outro`,
- **THEN** the system SHALL prompt for a text input with the custom process name and persist it in `processo_outro`.

---

### Requirement: Matriz de Visibilidade Integrada e Restrição Administrativa
The system SHALL allow administrators to configure multi-sector visibility directly during manager registration or editing, providing a "Select All" / "Deselect All" control, and restricting access to administrative management solely to users with the `ADMINISTRADOR` profile.

---

### Requirement: Submissão Condicionada ao Preenchimento das 5 Etapas
The system SHALL enable the "Submeter para UGERC" action only when all five wizard steps are complete, and the API SHALL reject a `SUBMETIDO` payload that fails the completeness rules with HTTP 400.

---

### Requirement: Visibilidade de Processos Cadastrados como "Outro"
The system SHALL offer previously registered custom processes (`processo_outro`) for reuse only to the unit that created them and to its ancestor units in the organizational tree (`unidade_pai_id`); administrators SHALL see all of them.

---

### Requirement: Exclusão de Fichas de Risco no Painel
The system SHALL allow deleting risk mappings from the Risk Dashboard according to the following rules: `ADMINISTRADOR` MAY delete any mapping; `GESTOR_UNIDADE` MAY delete only mappings whose `unidade_id` equals their primary unit; users of hierarchically superior units SHALL NOT delete mappings of linked units. Every deletion SHALL be audited with the previous state.

---

### Requirement: Indicadores do Painel Restritos a Fichas Submetidas
The system SHALL compute the 5x5 matrix counts and the dashboard cards using only mappings with status `SUBMETIDO`, SHALL present the "Risco Extremo" card instead of "Acima do Apetite", and SHALL present dedicated summary cards for the four institutional managements (`SUP`, `GAS`, `GAD`, `GEP`), each aggregating submitted risks of the management and its subordinate units across Low, Medium, High and Extreme residual severity.

#### Scenario: Contabilização de Riscos por Gerência
- **GIVEN** registered risk mappings with status `SUBMETIDO`,
- **WHEN** the dashboard metrics are requested,
- **THEN** the system SHALL return for each management (`SUP`, `GAS`, `GAD`, `GEP`):
  - `total`: count of submitted risks in that management and its recursive sub-units;
  - `baixo`: count of Low residual risks;
  - `medio`: count of Medium residual risks;
  - `alto`: count of High residual risks;
  - `extremo`: count of Extreme residual risks.

---

### Requirement: Filtro de Unidades no Painel de Riscos e Pesquisa por Sigla
The system SHALL provide an organizational unit filter in the Risk Dashboard allowing search by full textual name and by acronym, and the API list endpoint `GET /api/riscos` SHALL include the unit acronym (`sigla`) in the returned `unidade` payload so that filtering by acronym in the list view correctly finds corresponding records.

#### Scenario: Filtro por Sigla em Riscos Mapeados
- **GIVEN** mappings belonging to unit with acronym `SETISD`,
- **WHEN** the user types `SETISD` in the unit search field on `/riscos/mapeados`,
- **THEN** the list view SHALL display all mappings associated with `SETISD`.

---

### Requirement: Layout do Menu Lateral de Navegação
The system SHALL display the navigation links in the main sidebar in the following priority order:
1. Painel de Riscos (`/riscos`)
2. Novo Mapeamento (`/riscos/novo`)
3. Riscos Mapeados (`/riscos/mapeados`)
4. Gestores & Visibilidade (`/admin/usuarios`, conditional on administrator profile).

---

### Requirement: Escopo de Visibilidade Setorial e Hierárquica no Painel de Riscos
The Risk Dashboard SHALL restrict displayed risk statistics, matrix distribution and management cards to the authenticated user's assigned organizational unit and its subordinate units in the organogram tree; users SHALL only access data from units without hierarchical link if explicitly authorized via the institutional visibility matrix (`usuario_unidades_visibilidade`). Administrators SHALL retain unrestricted institutional visibility.

#### Scenario: Visualização restrita a unidades vinculadas
- **GIVEN** a sector, division or management chief authenticated in the system,
- **WHEN** the user opens the Risk Dashboard,
- **THEN** the system SHALL compute metrics considering only risks from their unit and its subordinate organogram units.

#### Scenario: Visualização de unidade externa concedida via matriz
- **GIVEN** a unit manager who has been granted additional visibility to unit $X$ via the visibility matrix,
- **WHEN** the dashboard is loaded or unit $X$ is selected in the unit filter,
- **THEN** the system SHALL display the submitted risks and metrics for unit $X$ and its subordinate units.

---

### Requirement: Categorização Oficial e Síntese de Correlação (Etapa 2)
The system SHALL provide the 11 official risk categories from the HC-UFPE Risk Guide (`ACIDENTE`, `BIOLOGICO`, `COMPLIANCE`, `ERGONOMICO`, `ESTRATEGICO`, `FINANCEIRO`, `FISICO`, `OPERACIONAL`, `QUIMICO`, `REPUTACAO`, `SEGURANCA_INFORMACAO`) with contextual descriptions, and SHALL display the correlation synthesis titled "Síntese da correlação evento-causa-consequência" with explanatory guidance on semantic coherence.

---

### Requirement: Escalas de Avaliação e Análise de Controles Internos (Etapa 3)
The system SHALL NOT pre-select Probability or Impact, SHALL display literal scale descriptions permanently visible on buttons styled with smooth pastel gradients from green (1) to red (5), SHALL show conceptual definitions for Inherent Risk, Mitigation Factor and Residual Risk, and SHALL implement Internal Control Analysis based on Table 3 (Inexistente = 1.0, Fraco = 0.8, Mediano = 0.6, Satisfatório = 0.4, Forte = 0.2) where FNC is static and does not vary by the count of measures, hiding control measures input when "Inexistente" is selected.

---

### Requirement: Busca Combinada de Unidades por Nome e Sigla (Etapa 1)
The system SHALL support simultaneous searching of Organizational Units by both full textual name and official hospital acronym (e.g., `UGERC`, `GAS`, `DAIA`).

---

### Requirement: Dependência Sequencial Estrita de Etapas no Mapeamento
The wizard SHALL enforce sequential dependency among mapping steps, allowing step $N+1$ to be marked complete or advanced to only when steps $1 \dots N$ are fully validated.

---

### Requirement: Salvamento em Rascunho sem Redirecionamento
The system SHALL persist mappings in `RASCUNHO` status while maintaining the user on the current page and step, providing a visual confirmation without interrupting workflow.

---

### Requirement: Tela Dedicada de Riscos Mapeados e Políticas RBAC
The system SHALL provide a dedicated route `/riscos/mapeados` in the main navigation menu with filtering by unit (name + acronym) and workflow status (`RASCUNHO` / `SUBMETIDO`). Administrators SHALL manage all mappings; sector managers SHALL manage only mappings of their primary unit; managers of superior units SHALL only view subordinate units' mappings in read-only mode.

---

### Requirement: Impressão e Exportação A4 Multi-páginas da Ficha de Mapeamento
The system SHALL provide unified multi-page printing and PDF export of the completed mapping:
- Shell interface components (headers, avatars, sidebars, mobile menus) SHALL be completely hidden on print (`print:hidden`).
- Document layout SHALL unlock heights and scrolling for clean multi-page pagination on standard A4 portrait format with block-break protection (`page-break-inside: avoid`).
- The report SHALL include institutional headers (UGERC / EBSERH / HC-UFPE) and formal signature sections.

---

### Requirement: Filtro de Tramitação e Versionamento de Fichas Mapeadas
The system SHALL limit the workflow status options in the list view (`/riscos/mapeados`) to only `SUBMETIDO` and `RASCUNHO` (in addition to "Todos os Status"). When editing an already submitted risk mapping (`SUBMETIDO`), the system SHALL only enable the "Submeter para UGERC" button if at least one field has been modified (dirty check). Upon re-submitting an edited mapping, the system SHALL automatically increment its version number (`versao`) and assign a version tag (`v2.0 (Revisada)`). All risk mappings SHALL store creator metadata (`criado_por_id`), creation timestamp (`criado_em`), and submission timestamp (`submetido_em`).

#### Scenario: Dirty check e exigência da etapa 5 para re-submissão de ficha
- **GIVEN** a risk mapping opened for editing,
- **WHEN** the user is in steps 1 to 4,
- **THEN** the button "Submeter para UGERC" SHALL remain disabled requiring the user to advance through all steps up to step 5.
- **WHEN** the user arrives at step 5 and at least one field has been modified,
- **THEN** the button "Submeter para UGERC" SHALL be enabled.

#### Scenario: Incremento de versão e auditoria
- **GIVEN** an existing submitted risk mapping with version 1 (`v1.0 (Original)`),
- **WHEN** the user modifies the mapping and submits it,
- **THEN** the system SHALL increment its version to 2, update `tag_versao` to `v2.0 (Revisada)`, and record the updated `submetido_em` timestamp.

---

### Requirement: Regras de Permissão de Edição e Criação Hierárquica
The system SHALL strictly enforce that:
1. When mapping, editing or viewing a risk, users can select only their own organizational unit (or authorized subordinate units for upper instances);
2. Upper hierarchical instances linked in the organogram tree SHALL NOT be allowed to edit mappings created by subordinate units (read-only consultation mode);
3. Upper hierarchical instances SHALL only map and consult risks of their subordinate units;
4. Units without an organogram hierarchical link SHALL only be allowed to view risks of other units when explicitly granted via the visibility matrix.

---

### Requirement: Indicador de Cobertura, Infocard de Unidades e Visibilidade dos Cards de Gerência
The Management cards (`SUP`, `GAS`, `GAD`, `GEP`) SHALL only be displayed to administrators or to users granted full visibility across all institutional units in the visibility matrix (`pode_ver_gerencias`).
The coverage indicator in each card SHALL be displayed directly below the total mapped risks in the format: `Cobertura: x/xx unidades (yy.y%)` without status/progress bars, accompanied by a modernized SVG information icon. Clicking the info icon SHALL open an Infocard listing exclusively the subordinate organizational units of that management (strictly excluding the management node itself from the list), their respective counts of submitted risks, and a clear visual highlight for units with mapped risks.

---

### Requirement: Mapa de Calor com Células em Cores Suavizadas e Card com Fundo Branco
EXCLUSIVELY in the Risk Dashboard, the risk distribution SHALL be rendered using `MapaCalorRiscos.vue` with a clean, neutral background (without gradient styling) and each 5×5 cell displaying softened pastel tones adhering strictly to the HC-UFPE institutional risk scale: Low (soft emerald green for scores <= 2), Medium (soft amber/yellow for scores 3 to 7), High (soft orange for scores 8 to 14), and Extreme (soft rose/red for scores 15 to 25).
The header of the heat map SHALL feature an executive card displaying the "Total de Riscos Mapeados" with a clean white background, subtle border, shield integrity icon, and high-contrast typography (`text-3xl font-black font-mono`).

---

### Requirement: Seletor Combobox Pesquisável Unificado de Unidades
---

### Requirement: Exclusão de Fichas de Risco em Lote (Bulk Deletion)
The system SHALL provide bulk selection checkboxes on `/riscos/mapeados` permitting users to select multiple risk mapping records simultaneously and trigger atomic bulk deletion via `POST /api/riscos/excluir-lote`.
The endpoint SHALL strictly validate permissions per record, removing all associated risk events, evaluations, controls, and action plans, auditing every removed record in `audit_logs` under category `NEGOCIO_CLINICO`.

---

### Requirement: Impressão de Fichas de Risco em Lote (Bulk Printing)
The system SHALL allow users on `/riscos/mapeados` to select multiple risk mapping records (or all visible records across filters) and trigger bulk printing via `POST /api/riscos/detalhes-lote`.
The backend endpoint SHALL retrieve the complete structured data of all requested mapping IDs in a single query with pre-loaded relations.
The print template `FichaImpressaoA4.vue` SHALL render all selected mapping records sequentially, applying automatic page-break styling (`page-break-after: always; break-after: page;`) between distinct risk mapping records so that each risk mapping starts cleanly on a fresh sheet without overlap or cut-off tables.






