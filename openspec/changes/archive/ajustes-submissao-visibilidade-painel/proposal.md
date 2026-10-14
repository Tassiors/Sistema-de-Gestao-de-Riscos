# Proposal: Ajustes de Submissão, Visibilidade de Processos "Outro" e Painel de Riscos

## Why
Após a entrega do modelo base, a validação com a UGERC identificou lacunas de governança e usabilidade:
1. Fichas podiam ser submetidas à UGERC com etapas incompletas.
2. O seletor de Unidade Organizacional exibia o tipo da unidade entre parênteses, gerando ruído visual.
3. Entradas de projetos estratégicos (código entre colchetes, ex.: `[P1.01] Nome do Projeto`) não devem compor o catálogo de processos.
4. Processos novos informados na categoria `Outro` não eram reaproveitáveis e não tinham regra de visibilidade setorial.
5. Não existia exclusão de fichas de risco nem regra de quem pode excluir.
6. A Matriz 5x5 e os cards do painel contabilizavam rascunhos, distorcendo os indicadores institucionais.

## What Changes
- **Submissão condicionada:** botão "Submeter para UGERC" habilitado somente quando as 5 etapas estiverem completas; validação espelhada no backend.
- **Seletor de Unidade:** remoção do texto entre parênteses (tipo da unidade) nas opções.
- **Catálogo de processos:** exclusão de entradas no formato `[código] Nome` (projetos estratégicos), sem remover processos ou macroprocessos legítimos.
- **Processos "Outro":** processos novos cadastrados via `Outro` passam a ser oferecidos para reuso apenas à unidade criadora e às unidades ancestrais no organograma (`unidade_pai_id`).
- **Exclusão de fichas (Painel de Riscos):** `ADMINISTRADOR` exclui qualquer ficha; `GESTOR_UNIDADE` exclui apenas fichas da sua unidade principal; chefias de instâncias superiores não excluem fichas de unidades vinculadas.
- **Indicadores:** Matriz 5x5 e cards consideram somente fichas com status `SUBMETIDO`; card "Acima do Apetite" substituído por "Risco Extremo".

## Capabilities

### Modified Capabilities
- `gestao-riscos`: requisitos de submissão, catálogo de processos, processos "Outro", exclusão de fichas e indicadores do painel.

## Impact
- **Backend:** `src/controllers/risco_controller.py`, `src/controllers/processo_controller.py`, `src/routers/risco.py`, `src/routers/processo.py`.
- **Frontend:** `frontend/src/views/riscos/MapeamentoWizard.vue`, `frontend/src/views/riscos/PainelRiscos.vue`.
- **Dados:** script idempotente de limpeza de projetos estratégicos (`src/seeds/remover_projetos_estrategicos.py`). Sem migração de esquema.
- **Testes:** atualização de `tests/test_riscos.py` e novos cenários de permissão/indicadores.
