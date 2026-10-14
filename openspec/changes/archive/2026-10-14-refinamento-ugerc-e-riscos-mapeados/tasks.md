# Tarefas: Refinamento Metodológico UGERC, Riscos Mapeados e Impressão A4

## 1. Backend e Modelos de Dados
- [x] Atualizar modelo `AvaliacaoRisco` em `src/models/risco.py` para incluir campo `nivel_controle`
- [x] Atualizar cálculo de severidade em `src/controllers/risco_controller.py` para mapear os 5 níveis da Tabela 3 da UGERC (FNC 1.0, 0.8, 0.6, 0.4, 0.2) sem variação pela quantidade de medidas
- [x] Atualizar persistência em `salvar_mapeamento` e retorno em `obter_mapeamento`
- [x] Implementar regras estritas de autorização hierárquica e exclusão em `src/routers/risco.py` e `src/controllers/risco_controller.py`
- [x] Atualizar validação rigorosa na submissão à UGERC (`validar_todas_etapas_submissao`)
- [x] Registrar auditoria completa (`audit_logs`) em ações de salvamento, submissão e exclusão

## 2. Frontend: Wizard de Mapeamento de Riscos
- [x] Etapa 1: Implementar campo de pesquisa combinada por nome e sigla da Unidade Organizacional
- [x] Etapa 2: Implementar catálogo oficial de 11 categorias de risco com descrições orientativas
- [x] Etapa 2: Exibir "Síntese da correlação evento-causa-consequência" com aviso pedagógico de coerência
- [x] Etapa 3: Remover pré-seleção de Probabilidade e Impacto (seleção obrigatória)
- [x] Etapa 3: Exibir descrições permanentes das Tabelas 1 e 2 nos botões com gradiente suave do verde ao vermelho
- [x] Etapa 3: Implementar seletor dos 5 níveis de controle (Tabela 3) com FNC fixo
- [x] Etapa 3: Exibir condicionalmente o campo de medidas de controle (ocultar se nível for 'Inexistente')
- [x] Etapa 3: Inserir glossário conceitual (Risco Inerente, FNC e Risco Residual)
- [x] Etapa 4: Alinhar legenda do eixo vertical da Matriz 5x5 e aplicar animação pulsante suave no alerta de Apetite a Risco
- [x] Regra de fluxo: Garantir dependência sequencial estrita entre as 5 etapas (`podeConcluirEtapa`)
- [x] Regra de fluxo: Permitir salvar como Rascunho permanecendo na mesma página/etapa

## 3. Frontend: Tela de Riscos Mapeados e Navegação
- [x] Criar componente `RiscosMapeadosView.vue` com filtros por Unidade (texto + sigla) e Status
- [x] Adicionar link "Riscos Mapeados" no menu lateral (`SidebarNav.vue`) e registrar rota no Vue Router
- [x] Remover tabela de fichas mapeadas da tela de Painel de Riscos (`PainelRiscos.vue`)
- [x] Aplicar regras de visualização e ação (exclusão/edição permitidas apenas para admin ou gestor da própria unidade)

## 4. Frontend: Emissão e Impressão A4 Multi-páginas
- [x] Implementar botão de impressão da ficha completa unificada das 5 etapas no Wizard
- [x] Ocultar componentes de casca (`header`, `aside`, menu mobile) na impressão (`print:hidden`)
- [x] Destravar altura e overflow em `DefaultLayout.vue` e `index.css` para permitir paginação natural em `@media print`
- [x] Configurar regras A4 portrait com quebras de página controladas (`.bloco-impressao`)

## 5. Testes Automatizados e Auditoria de Conformidade
- [x] Atualizar suíte de testes em `tests/test_riscos.py`
- [x] Executar testes com `pytest` (20/20 aprovados)
- [x] Executar auditor de conformidade arquitetural `audit_framework.py` (11/11 pilares - 100%)
- [x] Compilar bundle de produção do frontend (`npm run build`)
