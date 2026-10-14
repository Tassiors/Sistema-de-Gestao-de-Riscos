# Design: Ajustes de Submissão, Visibilidade de Processos "Outro" e Painel de Riscos

## Contexto
Não há alteração de esquema. Todas as regras são implementadas nas camadas Controller/Router (backend) e nas views Vue 3.

## Decisões

### 1. Completude das etapas (frontend + backend)
- `MapeamentoWizard.vue` ganha o computed `etapasCompletas: Record<1..5, boolean>` e `podeSubmeter`.
- O stepper exibe um indicador (✓) por etapa completa; o botão "Submeter para UGERC" fica `disabled` com `title` listando as etapas pendentes.
- `risco_controller.validar_submissao(dados)` replica as regras e lança `HTTPException(400)` quando `status == "SUBMETIDO"`. O frontend continua sendo a primeira barreira; o backend garante integridade.

### 2. Projetos estratégicos no catálogo
- Regex `^\s*\[[^\]]+\]` aplicada em `processo_controller.listar_processos_hierarquicos` para ocultar entradas (defesa em profundidade).
- Script idempotente `src/seeds/remover_projetos_estrategicos.py` remove do banco processos com esse padrão que não estejam vinculados a fichas, e imprime a lista do que foi removido para validação.
- **Observação:** no `data/app.db` local, nas planilhas de referência e no XML do REDCap nenhuma entrada com esse padrão foi encontrada no momento da implementação.

### 3. Processos "Outro"
- Nova rota `GET /api/processos/outros?unidade_id=` (Default-Private) → `processo_controller.listar_processos_outro`.
- Escopo do usuário: `None` (todos) para administradores; caso contrário, subárvore da `unidade_principal_id` (`obter_subunidades_recursivas`), o que dá visibilidade à unidade criadora e às instâncias ancestrais.
- Escopo da consulta: subárvore da unidade selecionada no wizard ∩ escopo do usuário.
- Retorno: nomes distintos de `processo_outro` (case-insensitive) com unidade de origem.
- No wizard, nova seção "Processos cadastrados como Outro"; selecionar define `processo_id` = processo "Outro processo" e `processo_outro` = nome.

### 4. Exclusão de fichas
- `DELETE /api/riscos/{id}` → `risco_controller.excluir_mapeamento`.
- Perfil e unidade principal são lidos do banco (`usuarios`) para não depender de claims antigos do JWT; administradores mestres reconhecidos pelos mesmos critérios de `obter_unidades_autorizadas`.
- Regra: admin → permitido; `GESTOR_UNIDADE` e `m.unidade_id == unidade_principal_id` → permitido; demais → 403.
- `listar_mapeamentos` passa a retornar `pode_excluir` por ficha para a UI exibir o botão "Excluir".
- Auditoria `EXCLUIR_MAPEAMENTO_RISCO`, categoria `NEGOCIO_CLINICO`, com `dados_anteriores`.

### 5. Indicadores
- `obter_estatisticas_matriz` filtra `MapeamentoRisco.status == "SUBMETIDO"`.
- Card "Acima do Apetite" → "Risco Extremo" (`totais.EXTREMO`). O campo `ACIMA_APETITE` permanece no payload por compatibilidade.

## Riscos / Trade-offs
- Usuários sem `unidade_principal_id` (não administradores) não verão processos "Outro" de terceiros — comportamento intencional.
- A exclusão é física (cascata ORM em eventos, avaliações, controles e planos); a trilha de auditoria preserva o estado anterior.
