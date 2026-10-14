# Tasks: Ajustes de Submissão, Visibilidade de Processos "Outro" e Painel de Riscos

## 1. Wizard de Mapeamento
- [x] 1.1 Habilitar "Submeter para UGERC" apenas com as 5 etapas completas (indicador por etapa no stepper).
- [x] 1.2 Validar completude no backend ao receber `status = SUBMETIDO` (HTTP 400).
- [x] 1.3 Remover o texto entre parênteses (tipo) das opções de Unidade Organizacional.

## 2. Catálogo de Processos
- [x] 2.1 Ocultar entradas de projetos estratégicos (`[código] Nome`) na listagem de processos.
- [x] 2.2 Criar script idempotente de remoção dessas entradas no banco, com relatório do que foi excluído.
- [x] 2.3 Expor `GET /api/processos/outros` com visibilidade restrita à unidade criadora e ancestrais.
- [x] 2.4 Exibir no wizard a seção de processos cadastrados como "Outro" para reuso.

## 3. Painel de Riscos
- [x] 3.1 Implementar `DELETE /api/riscos/{id}` com regras de permissão (admin / gestor da unidade) e auditoria.
- [x] 3.2 Retornar `pode_excluir` na listagem e exibir botão "Excluir" com confirmação.
- [x] 3.3 Matriz 5x5 e cards considerando apenas fichas `SUBMETIDO`.
- [x] 3.4 Substituir card "Acima do Apetite" por "Risco Extremo".

## 4. Qualidade
- [x] 4.1 Atualizar/criar testes (indicadores, exclusão, validação de submissão, processos "Outro").
- [x] 4.2 Executar `pytest` com 100% de aprovação.
- [x] 4.3 Executar `python audit_framework.py .` mantendo 100% de conformidade.
- [x] 4.4 Sincronizar a spec principal `openspec/specs/gestao-riscos/spec.md`.

