# Proposal: Refinamento do Painel de Riscos, Cards por Gerência, Filtros e Ordem do Menu

## Why
A evolução do Sistema de Gestão de Riscos do HC-UFPE demanda melhorias na experiência de navegação e consolidação de indicadores estratégicos:
1. **Limpeza Visual do Painel de Riscos:** O Painel de Riscos continha botões e banners redundantes de "+ Novo Mapeamento" e atalhos para "Riscos Mapeados", sobrecarregando a interface analítica.
2. **Visão Estratégica por Gerência:** A gestão hospitalar necessita visualizar rapidamente o volume e a severidade dos riscos submetidos divididos pelas 4 grandes gerências/direções: Superintendência (SUP), Gerência de Atenção à Saúde (GAS), Gerência Administrativa (GAD) e Gerência de Ensino e Pesquisa (GEP).
3. **Filtro Avançado de Unidade Organizacional:** O Painel de Riscos precisa de um seletor de unidade com pesquisa em tempo real por nome e sigla, permitindo analisar os dados sob a perspectiva setorial ou institucional.
4. **Correção de Pesquisa por Sigla em Riscos Mapeados:** A listagem de fichas mapeadas não estava filtrando por sigla de unidade porque o backend não retornava o campo `sigla` no objeto `unidade`.
5. **Ergonomia do Menu Lateral:** No menu de navegação, a ação primária de criar um registro ("Novo Mapeamento") deve preceder a consulta analítica ("Riscos Mapeados").
6. **Escopo de Visibilidade Setorial e Hierárquica:** O Painel de Riscos deve exibir exclusivamente dados do setor do usuário logado, estendendo-se às unidades vinculadas/subordinadas no organograma para chefes de setor, divisão e gerência, e restringindo o acesso a unidades externas àquelas expressamente liberadas na matriz de visibilidade.

## What Changes
- **Remoção de Elementos Redundantes:** Remoção dos botões de "+ Novo Mapeamento" (cabeçalho e card lateral) e do banner inferior de atalho para fichas mapeadas no Painel de Riscos.
- **Cards Estruturados por Gerência (SUP, GAS, GAD e GEP):** Adição de 4 cards com: Total Mapeados (status `SUBMETIDO`), Risco Baixo, Risco Médio, Risco Alto e Risco Extremo, agregando os riscos da gerência e de todas as suas subunidades vinculadas.
- **Filtro de Unidade no Painel:** Seletor de Unidade Organizacional com suporte a busca textual por nome e por sigla oficial (ex: `GAS`, `SETISD`, `UTIAD`), atualizando os indicadores dinamicamente.
- **Correção da Busca por Sigla:** Inclusão do campo `sigla` no retorno de unidades em `GET /api/riscos` (`listar_mapeamentos`) e exibição formatada da sigla na tabela de Riscos Mapeados.
- **Reordenação do Menu Lateral:** Reposicionamento do link "Novo Mapeamento" antes de "Riscos Mapeados" no menu de navegação.
- **Restrição de Visibilidade Setorial e Hierárquica:** `obter_unidades_autorizadas` passa a incluir recursivamente as subunidades vinculadas da unidade principal do usuário e das unidades concedidas pela matriz de visibilidade, filtrando a matriz e o seletor de unidades apenas para o que o usuário tem autorização.

## Capabilities

### Modified Capabilities
- `gestao-riscos`: especificações de indicadores do painel, agrupamento por gerências, filtros por nome/sigla e layout de navegação.

## Impact
- **Backend:** `src/controllers/risco_controller.py`, `src/routers/risco.py`.
- **Frontend:** `frontend/src/views/riscos/PainelRiscos.vue`, `frontend/src/views/riscos/RiscosMapeadosView.vue`, `frontend/src/layouts/DefaultLayout.vue`.
- **Testes:** `tests/test_riscos.py`.
