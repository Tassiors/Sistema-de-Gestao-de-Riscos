# Tasks: Refinamento do Painel de Riscos, Cards por Gerência, Filtros e Ordem do Menu

## 1. Backend
- [x] 1.1 Incluir `sigla` no payload de `unidade` em `listar_mapeamentos` (`src/controllers/risco_controller.py`).
- [x] 1.2 Atualizar `obter_estatisticas_matriz` para aceitar `unidade_id` opcional e retornar o array `gerencias` com totais de riscos submetidos (total, baixo, medio, alto, extremo) por SUP, GAS, GAD e GEP.
- [x] 1.3 Atualizar o endpoint `GET /api/riscos/painel/matriz` em `src/routers/risco.py` com o parâmetro `unidade_id`.
- [x] 1.4 Refinar `obter_unidades_autorizadas` para incluir subunidades vinculadas recursivas no organograma para chefias e respeitar a matriz de visibilidade para unidades sem vínculo.
- [x] 1.5 Atualizar `GET /api/unidades` com parâmetro `apenas_autorizadas` para filtrar o seletor pelo escopo do usuário.

## 2. Frontend - Menu Lateral
- [x] 2.1 Reordenar itens de menu em `frontend/src/layouts/DefaultLayout.vue` colocando "Novo Mapeamento" antes de "Riscos Mapeados".

## 3. Frontend - Painel de Riscos
- [x] 3.1 Remover elementos solicitados do `PainelRiscos.vue` (botão de novo mapeamento no cabeçalho, bloco de links no card lateral e banner gradiente inferior).
- [x] 3.2 Adicionar barra de filtro por Unidade Organizacional com busca por texto e sigla.
- [x] 3.3 Adicionar os cards de Gerências (SUP, GAS, GAD, GEP) exibindo total submetido, risco baixo, médio, alto e extremo, com clique para filtrar.

## 4. Frontend - Riscos Mapeados
- [x] 4.1 Garantir o correto funcionamento da pesquisa textual por nome e por sigla da unidade organizacional.
- [x] 4.2 Omitir a badge/tag de sigla ao lado do nome da unidade na coluna "Setor / Unidade" da tabela de fichas cadastradas.
- [x] 4.3 Adicionar botão com ícone de impressão (`Imprimir`) para todas as fichas cadastradas na tabela de ações, integrando o componente de impressão A4 (`FichaImpressaoA4.vue`).
- [x] 4.4 Implementar funcionalidade de exclusão em lote (bulk delete) de fichas cadastradas, com seleção via checkbox master e individual, validação estrita de permissões (apenas fichas elegíveis), barra de ações superior e barra flutuante inferior, diálogo de confirmação seguro, trilha de auditoria e endpoint `POST /api/riscos/excluir-lote`.

## 5. Frontend - Riscos Mapeados & Wizard
- [x] 5.1 Restringir o filtro de Status da Tramitação exclusivamente a "SUBMETIDO" e "RASCUNHO" (além de "Todos os Status").
- [x] 5.2 Implementar dirty check no Wizard para reativar "Submeter para UGERC" apenas se houver alterações em fichas já submetidas.
- [x] 5.3 Implementar versionamento automático (`v1.0 (Original)`, `v2.0 (Revisada)`), registrando criador, criado_em e submetido_em.
- [x] 5.4 Bloquear edição de fichas por instâncias superiores ou unidades externas (modo somente leitura, apenas gestor da própria unidade ou admin pode editar).
- [x] 5.5 Parâmetro `?apenas_mapeamento=true` em `/api/unidades` para permitir mapear apenas a unidade permitida.
- [x] 5.6 Exigir que o usuário avance até a Etapa 5 antes de liberar a submissão para a UGERC ao editar uma ficha.

## 6. Frontend - Painel de Riscos & Mapa de Calor
- [x] 6.1 Condicionar exibição dos cards de gerências estritamente a administradores ou usuários com todas as unidades na matriz de visibilidade (`pode_ver_gerencias`).
- [x] 6.2 Reorganizar indicador de cobertura nos cards de gerência para `Unidades com riscos mapeados (i): N / total (Y.Y%)` com barra de progresso.
- [x] 6.3 Implementar Infocard `(i)` detalhando a relação de todas as unidades da gerência com seus respectivos totais de riscos e destaque visual para quem possui risco mapeado.
- [x] 6.4 Remover div redundante de totais no Painel de Riscos.
- [x] 6.5 Redesenhar `MapaCalorRiscos.vue` com fundo suave em gradiente diagonal térmico contínuo (Baixo, Médio, Alto, Extremo), eixos X e Y nítidos e destaque evidente da zona de maior concentração de riscos.
- [x] 6.6 Unificar o filtro de Unidade Organizacional em um único combobox dropdown pesquisável que suporta simultaneamente busca textual por nome e por sigla.
- [x] 6.7 Ampliar o card do "Total de Riscos Mapeados" no topo do Mapa de Calor com tipografia destacada e visual executivo.
- [x] 6.8 Corrigir a orientação do gradiente térmico da matriz 5x5 (45°: canto inferior esquerdo Verde/Baixo ao superior direito Vermelho/Extremo) e aplicar classes exatas de cores de fundo e bordas por faixa de risco em cada célula.
- [x] 6.9 Exibir `Cobertura: x/xx unidades (yy.y%)`, remover barra de status dos cards de gerência, refinar ícone de info SVG e desconsiderar a própria gerência na lista do infocard.
- [x] 6.10 Redesenhar a matriz do Mapa de Calor sem fundo gradiente e com células em cores pastéis suaves correspondentes a cada faixa de risco.
- [x] 6.11 Aplicar fundo branco suave e ícone institucional no card de "Total de Riscos Mapeados" para harmonização com o painel.

## 8. Frontend - Wizard de Novo Mapeamento e Ficha Impressa A4
- [x] 8.1 Retirar referências textuais a 'Conforme Guia Prático GU.UGERC.001 (HC-UFPE / EBSERH)', 'Tabela 2 - Escala de Probabilidade (GU.UGERC.001)' e 'Tabela 1 - Escala de Impacto (GU.UGERC.001)'.
- [x] 8.2 Alterar tolerância institucional para 'Tolerância Institucional ao Risco: até 7,99' no componente `MatrizRisco5x5.vue`.
- [x] 8.3 Alterar subtítulo da etapa 5 para 'Elabore o plano de ação e plano de contingência com gatilhos operacionais.'.
- [x] 8.4 Adicionar badge 'OPCIONAL' na sessão de Planos de Contingência.
- [x] 8.5 Posicionar o botão 'Imprimir Ficha Completa (PDF)' no topo fixo ao lado do botão 'Submeter para UGERC'.
- [x] 8.6 Na ficha impressa: remover menção a 'Sistema Corporativo de Gestão de Riscos por Processo (GU.UGERC.001)'.
- [x] 8.7 Na ficha impressa: exibir 'Pilar Estratégico HC-UFPE' e 'Projeto Vinculado' exclusivamente se preenchidos na ficha.
- [x] 8.8 Na ficha impressa: substituir 'PLANOS DE AÇÃO (5W2H)' por 'PLANOS DE AÇÃO'.
- [x] 8.9 Na ficha impressa: recalibrar layout com margens reduzidas (`8mm 7mm`), `table-layout: fixed` e colunas percentuais seguras para evitar corte de margens e bordas nas seções em impressoras/PDFs.

## 9. Qualidade e Conformidade
- [x] 9.1 Atualizar testes em `tests/test_riscos.py` para cobrir sigla em listagem, breakdown de gerências na matriz, indicador de cobertura, permissões e versionamento.
- [x] 9.2 Executar suíte de testes com `pytest` (24/24 passando).
- [x] 9.3 Executar build de produção do frontend com `npm run build`.
- [x] 9.4 Executar auditoria de conformidade com `python audit_framework.py .` (11/11 100%).
- [x] 9.5 Sincronizar as especificações no OpenSpec.

