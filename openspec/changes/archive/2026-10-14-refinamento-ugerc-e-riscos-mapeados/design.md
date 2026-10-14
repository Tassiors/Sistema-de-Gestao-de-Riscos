# Design Arquitetural: Refinamento Metodológico UGERC, Gestão de Riscos Mapeados e Impressão A4

## 1. Catálogo de Categorias de Risco (Etapa 2)
Implementado catálogo oficial das 11 categorias de risco com descrições orientativas claras:
- `ACIDENTE`, `BIOLOGICO`, `COMPLIANCE`, `ERGONOMICO`, `ESTRATEGICO`, `FINANCEIRO`, `FISICO`, `OPERACIONAL`, `QUIMICO`, `REPUTACAO`, `SEGURANCA_INFORMACAO`.
- Síntese da correlação evento-causa-consequência exibida com legenda pedagógica destacando a importância da harmonia e coerência textual entre os campos.

## 2. Mensuração Consciente e Escalas Oficiais (Etapa 3)
- Probabilidade e Impacto inicializados sem pré-seleção (`null`).
- Descrições normativas da Tabela 2 (Probabilidade) e Tabela 1 (Impacto) permanentemente visíveis nos botões de seleção de 1 a 5.
- Botões estilizados com paleta gradiente suave em tons pastel do verde (1) ao vermelho (5).
- Painel conceituais integrados definindo formalmente Risco Inerente ($P \times I$), Fator de Mitigação (FNC) e Risco Residual ($\text{Inerente} \times \text{FNC}$).

## 3. Análise de Controles Internos (Tabela 3 UGERC)
- 5 níveis estáticos de maturidade de controle:
  - `INEXISTENTE`: FNC = 1,0 (Muito Alto)
  - `FRACO`: FNC = 0,8 (Alto)
  - `MEDIANO`: FNC = 0,6 (Médio)
  - `SATISFATORIO`: FNC = 0,4 (Baixo)
  - `FORTE`: FNC = 0,2 (Muito Baixo)
- **Regra de Negócio:** O FNC é determinado exclusivamente pela classificação selecionada e **não varia** com o número de medidas descritas.
- **Exibição Condicional:** Se `nivel_controle === 'INEXISTENTE'`, a área de cadastro de medidas de controle é ocultada e a lista é limpa.

## 4. Usabilidade e Navegação Sequencial no Wizard
- **Busca Dupla na Etapa 1:** Campo de busca com suporte simultâneo a nome por extenso e sigla da Unidade Organizacional.
- **Dependência Estrita de Etapas:** Cada etapa só pode ser concluída e navegada se a etapa anterior estiver estritamente válida (`podeConcluirEtapa`), evitando inconsistências de preenchimento.
- **Rascunho Não-Bloqueante:** Ao clicar em "Salvar Rascunho", o registro é salvo no banco via API e o usuário permanece na mesma tela e etapa, com feedback visual.

## 5. Arquitetura da Tela de Riscos Mapeados (`/riscos/mapeados`)
- Rota dedicada desmembrada do Painel de Riscos.
- Tabela com paginação, filtros de texto/sigla de unidade e filtro por status de tramitação (`RASCUNHO` / `SUBMETIDO`).
- **Políticas de Autorização (RBAC):**
  - `ADMINISTRADOR`: Permissão completa (visualizar, editar e excluir qualquer ficha).
  - `GESTOR_UNIDADE`: Visualiza, edita e exclui exclusivamente fichas de sua unidade principal.
  - Usuários com acesso a unidades superiores apenas visualizam fichas das unidades filhas subordinadas, com botões de edição e exclusão desabilitados ou ocultos.
  - Toda exclusão gera log imutável na tabela `audit_logs` contendo o snapshot anterior completo.

## 6. Sistema de Impressão Formal A4 Multi-páginas
- Utilização de bloco de impressão dedicado `#secao-relatorio-impressao` com fluxo estático normal no DOM (sem `position: absolute`).
- Ocultação dos componentes de shell (`DefaultLayout.vue`): cabeçalho do sistema, avatar, menu lateral e mobile marcados com `print:hidden`.
- Destravamento global via `@media print`:
  - `html, body, #app, .h-screen, .h-full, .overflow-y-auto` definidos como `overflow: visible !important; height: auto !important;`.
  - Configuração de `@page { size: A4 portrait; margin: 1.2cm 1cm; }`.
  - Blocos de conteúdo com `.bloco-impressao { break-inside: avoid !important; page-break-inside: avoid !important; }` prevenindo cortes feios em tabelas e seções.
