# Design: Refinamento do Painel de Riscos, Cards por Gerência, Filtros e Ordem do Menu

## 1. Visão Geral da Arquitetura e Decisões de Projeto

### 1.1 Backend: Agregação por Gerências e Suporte a Filtro por Unidade
No endpoint `GET /api/riscos/painel/matriz`:
- Adiciona o parâmetro opcional `unidade_id: Optional[int] = Query(None)`.
- Se `unidade_id` for informado, as estatísticas da matriz e os totais gerais são filtrados para essa unidade (e suas subunidades recursivas).
- Para o cálculo dos cards das Gerências (`SUP`, `GAS`, `GAD`, `GEP`):
  - Localiza os IDs dessas unidades raiz via `UnidadeOrganizacional.sigla.in_(["SUP", "GAS", "GAD", "GEP"])`.
  - Para cada gerência, recupera todos os IDs de subunidades usando a função existente `obter_subunidades_recursivas(db, gerencia_id)`.
  - Agrega contagens de fichas `SUBMETIDO` e suas classificações residuais (`BAIXO`, `MEDIO`, `ALTO`, `EXTREMO`).
  - Retorna um array `gerencias` contendo os dados estruturados de cada gerência.

### 1.2 Backend: Serialização da Sigla na Listagem de Riscos
No método `listar_mapeamentos`:
- O dicionário `unidade` de cada mapeamento passa a conter `"sigla": m.unidade.sigla if m.unidade else None`.
- Isso garante que a propriedade `m.unidade?.sigla` esteja preenchida no frontend.

### 1.3 Frontend: Painel de Riscos (`PainelRiscos.vue`)
- **Remoção de Elementos:**
  - Remoção do botão `+ Novo Mapeamento` do cabeçalho.
  - Remoção do bloco de ações no card lateral de Governança (`Ver Todas as Fichas Mapeadas` e `+ Novo Mapeamento`).
  - Remoção do banner gradiente inferior de atalho para `Riscos Mapeados`.
- **Filtro de Unidade Organizacional:**
  - Seletor inteligente de unidade com campo de busca textual e por sigla.
  - Exibição de `Nome da Unidade (SIGLA)`.
  - Botão para limpar filtro e voltar à visualização institucional completa.
- **Cards por Gerência:**
  - 4 cards no topo ou em destaque para `SUP`, `GAS`, `GAD` e `GEP`.
  - Cada card exibe:
    - Sigla em badge e Nome completo da gerência;
    - Total de riscos submetidos com tipografia destacada;
    - Grade/Pills com contadores específicos para: Baixo (Verde), Médio (Âmbar), Alto (Laranja) e Extremo (Vermelho).
    - Opção de clicar no card para filtrar rapidamente o painel por aquela gerência.

### 1.4 Frontend: Riscos Mapeados (`RiscosMapeadosView.vue`)
- Atualização do filtro computado `mapeamentosFiltrados` para validar `siglaU.includes(qUnidade)` com a sigla agora fornecida pelo backend.
- Exibição da sigla junto ao nome da unidade na coluna da tabela.

### 1.5 Frontend: Menu Lateral (`DefaultLayout.vue`)
- Reordenação da tag `<nav>`:
  1. `/riscos` (Painel de Riscos)
  2. `/riscos/novo` (Novo Mapeamento)
  3. `/riscos/mapeados` (Riscos Mapeados)
  4. `/admin/usuarios` (Gestores & Visibilidade)
