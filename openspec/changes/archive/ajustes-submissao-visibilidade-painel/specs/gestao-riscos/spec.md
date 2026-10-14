## ADDED Requirements

### Requirement: Submissão Condicionada ao Preenchimento das 5 Etapas
The system SHALL enable the "Submeter para UGERC" action only when all five wizard steps are complete, and the API SHALL reject a `SUBMETIDO` payload that fails the same completeness rules with HTTP 400.

Critérios de completude:
- Etapa 1: unidade, processo, nome do processo quando `Outro`, entrega do processo e, se houver projeto, nome do projeto e pilar estratégico.
- Etapa 2: categoria, causa, evento e consequência.
- Etapa 3: probabilidade e impacto entre 1 e 5 e todo controle adicionado com descrição.
- Etapa 4: derivada da Etapa 3 (priorização calculada).
- Etapa 5: se o risco residual estiver acima do apetite (> 7,99), ao menos um Plano de Ação 5W2H e um Plano de Contingência; todo plano adicionado com todos os campos preenchidos.

#### Scenario: Botão de submissão desabilitado
- **GIVEN** a risk mapping with at least one incomplete step,
- **WHEN** the user views the wizard header,
- **THEN** the "Submeter para UGERC" button SHALL be disabled and the pending steps SHALL be indicated.

#### Scenario: Submissão incompleta via API
- **GIVEN** a payload with `status = SUBMETIDO` and an empty consequence,
- **WHEN** it is posted to `POST /api/riscos`,
- **THEN** the API SHALL respond HTTP 400 with a `detail` message describing the pending step.

---

### Requirement: Visibilidade de Processos Cadastrados como "Outro"
The system SHALL offer previously registered custom processes (`processo_outro`) for reuse only to the unit that created them and to its ancestor units in the organizational tree (`unidade_pai_id`); administrators SHALL see all of them.

#### Scenario: Reuso pela unidade criadora
- **GIVEN** a manager of UGPIA who registered the custom process "X" under `Outro`,
- **WHEN** the manager opens the process selector for UGPIA,
- **THEN** the system SHALL list "X" in a dedicated section of processes registered as `Outro`.

#### Scenario: Unidade não relacionada
- **GIVEN** a manager of SETISD (not an ancestor of UGPIA),
- **WHEN** they request custom processes,
- **THEN** the system SHALL NOT return "X".

#### Scenario: Instância hierárquica superior
- **GIVEN** a user whose primary unit is an ancestor of UGPIA,
- **WHEN** they open the process selector for UGPIA or for their own unit,
- **THEN** the system SHALL list "X".

---

### Requirement: Exclusão de Fichas de Risco no Painel
The system SHALL allow deleting risk mappings from the Risk Dashboard according to the following rules: `ADMINISTRADOR` MAY delete any mapping; `GESTOR_UNIDADE` MAY delete only mappings whose `unidade_id` equals their primary unit; users of hierarchically superior units SHALL NOT delete mappings of linked units. Every deletion SHALL be audited with the previous state.

#### Scenario: Administrador exclui qualquer ficha
- **GIVEN** an authenticated administrator,
- **WHEN** they call `DELETE /api/riscos/{id}` for any mapping,
- **THEN** the system SHALL delete it and register an audit log with `dados_anteriores`.

#### Scenario: Gestor de unidade superior tenta excluir ficha vinculada
- **GIVEN** a `GESTOR_UNIDADE` whose primary unit is the parent of the mapping's unit,
- **WHEN** they call `DELETE /api/riscos/{id}`,
- **THEN** the API SHALL respond HTTP 403.

---

### Requirement: Indicadores do Painel Restritos a Fichas Submetidas
The system SHALL compute the 5x5 matrix counts and the dashboard cards using only mappings with status `SUBMETIDO`, and SHALL present the "Risco Extremo" card instead of "Acima do Apetite".

#### Scenario: Rascunho não contabilizado
- **GIVEN** a mapping saved as `RASCUNHO`,
- **WHEN** the dashboard statistics are requested,
- **THEN** the mapping SHALL NOT be counted in the matrix or cards.

## MODIFIED Requirements

### Requirement: Catálogo de Processos EBSERH e Projetos
The system SHALL support the EBSERH Type II process catalog and allow conditional project association for cross-cutting processes. The catalog SHALL NOT expose strategic project entries whose name starts with a bracketed code (e.g., `[P1.01] Nome do Projeto`).

#### Scenario: Associação de Projeto ao Processo de Gestão de Riscos
- **GIVEN** that a user selects the process `REALIZAR IDENTIFICAÇÃO E AVALIAÇÃO DOS EVENTOS DE RISCOS`,
- **WHEN** the user marks the option "Possui Projeto?",
- **THEN** the system SHALL require input for the Project Name (`nome_projeto`) and Strategic Pillar (`pilar_estrategico_id`).

#### Scenario: Ocultação de projetos estratégicos
- **GIVEN** a catalog entry named `[P1.01] Nome do Projeto`,
- **WHEN** the process list is requested,
- **THEN** the entry SHALL NOT be returned.
