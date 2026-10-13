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
