# Delta Spec: Refinamento do Painel de Riscos, Cards por Gerência, Filtros e Ordem do Menu

## MODIFIED Requirements

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
The Risk Dashboard SHALL replace separated text input and standard select elements with a unified searchable combobox dropdown. The trigger SHALL display the selected unit's acronym badge and name, and the dropdown popover SHALL provide an embedded real-time search input that immediately filters units simultaneously by name and by acronym, with one-click selection and click-outside dismissal.

---

### Requirement: Refinamentos Textuais do Wizard e Layout da Ficha Impressa A4
The system SHALL refine the Risk Mapping Wizard (`MapeamentoWizard.vue`) and Print Layout (`ficha-impressao-a4`) as follows:
1. **Remoção de referências ao manual interno:** The labels and sub-labels mentioning `'Conforme Guia Prático GU.UGERC.001 (HC-UFPE / EBSERH)'`, `'Tabela 2 - Escala de Probabilidade (GU.UGERC.001)'`, `'Tabela 1 - Escala de Impacto (GU.UGERC.001)'` and `'Sistema Corporativo de Gestão de Riscos por Processo (GU.UGERC.001)'` SHALL be removed.
2. **Tolerância Institucional:** The institutional tolerance in `MatrizRisco5x5.vue` SHALL be displayed as `'Tolerância Institucional ao Risco: até 7,99'`.
3. **Subtítulo e Seção de Planos:** The subtitle of step 5 SHALL be `'Elabore o plano de ação e plano de contingência com gatilhos operacionais.'`, the Action Plan header SHALL display `'PLANOS DE AÇÃO'` (without 5W2H), and the Contingency Plan section SHALL feature a distinct visual badge `'OPCIONAL'`.
4. **Posicionamento do Botão de Impressão:** The button `'Imprimir Ficha Completa (PDF)'` SHALL be positioned in the fixed header bar directly next to the `'Submeter para UGERC'` button.
5. **Condicionamento de Metadados Estratégicos na Impressão:** In the printed sheet (`ficha-impressao-a4`), the sections for `'Pilar Estratégico HC-UFPE'` and `'Projeto Vinculado'` SHALL ONLY be displayed if there is registered content for them in the risk mapping (`v-if`).
6. **Margens e Integridade de Impressão:** Print stylesheet and table layout SHALL be constrained to `8mm 7mm` page margins, `max-width: 99%`, and `table-layout: fixed` with proportional column widths to prevent clipping or interrupted borders across page sections during browser print / PDF export.

---

### Requirement: Impressão de Fichas e Exibição de Unidades em Riscos Mapeados
1. **Ícone de Impressão:** The mapped risks table (`RiscosMapeadosView.vue`) SHALL provide a dedicated "Imprimir" button with print icon for every registered risk sheet row. Clicking the button SHALL asynchronously retrieve the complete risk sheet details and automatically trigger the browser print dialogue using `FichaImpressaoA4.vue`.
2. **Coluna Setor / Unidade:** In the mapped risks table, the "Setor / Unidade" column SHALL display exclusively the unit name (and metadata like sheet ID, version badge, creator, and submission date), without rendering the acronym badge next to the unit name, while continuing to support search by both unit name and acronym.
3. **Exclusão em Lote (Bulk Delete):** The mapped risks table SHALL support multiple-row selection via master checkbox in the table header and individual checkboxes per row. Only sheets for which the active user has explicit delete privileges (`m.pode_excluir`) SHALL be selectable (displaying a lock icon for non-deletable sheets). When one or more sheets are selected, an action bar in the header and a floating bottom action pill SHALL display the count of selected items, an option to cancel selection, and a primary destructive button "Excluir Selecionadas" requiring confirmation before triggering `POST /api/riscos/excluir-lote` with transactional deletion and immutable audit logging.



