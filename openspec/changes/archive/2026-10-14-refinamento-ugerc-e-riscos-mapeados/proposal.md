# Proposta: Refinamento Metodológico UGERC, Gestão de Riscos Mapeados e Impressão A4

## Contexto & Motivação
Para consolidação das diretrizes do Guia Prático de Aplicação da Gestão de Riscos no HC-UFPE (`GU.UGERC.001 - versão 1`) e aprimoramento da usabilidade e governança institucional, esta mudança implementa um conjunto integrado de melhorias:
1. **Fidelidade Metodológica UGERC (Etapas 2 e 3):**
   - Catálogo oficial das 11 categorias de risco com descrições orientativas.
   - Síntese da correlação evento-causa-consequência com orientação sobre coerência lógica da oração.
   - Seleção consciente de Probabilidade e Impacto (sem pré-seleção) com descrições literais das Tabelas 1 e 2 permanentemente visíveis nos botões estilizados com gradiente suave do verde ao vermelho.
   - Glossário conceitual de Risco Inerente, Fator de Mitigação (FNC) e Risco Residual.
   - Análise de controles internos baseada na Tabela 3 da UGERC: 5 níveis com FNC fixo (1.0 a 0.2) sem variação pela contagem de medidas, ocultando a lista de medidas se o nível for "Inexistente".
   - Alerta de "Dentro do Apetite a Risco" com realce visual pulsante suave e alinhamento do eixo vertical da Matriz 5x5.
2. **Navegação, Validação e Usabilidade no Mapeamento:**
   - Campo de pesquisa combinada por texto e sigla para Unidades Organizacionais na Etapa 1.
   - Validação de dependência sequencial estrita: uma etapa só pode ser concluída e acessada se a imediatamente anterior estiver válida.
   - Salvamento em Rascunho sem redirecionamento: o usuário permanece no formulário para continuar o preenchimento ininterruptamente.
3. **Tela Dedicada de Riscos Mapeados (`/riscos/mapeados`):**
   - Desacoplamento da tabela do Painel de Riscos para uma visualização específica no menu lateral.
   - Filtros dinâmicos por Unidade Organizacional (com busca textual e sigla) e Status de tramitação (Rascunho / Submetido).
   - Políticas de controle de acesso (RBAC): Administradores gerenciam todas as fichas; Gestores de Unidade visualizam, editam e excluem apenas fichas de sua própria lotação; unidades superiores possuem permissão estritamente de consulta sobre unidades filhas vinculadas.
4. **Emissão e Impressão A4 Multi-páginas da Ficha Completa:**
   - Relatório institucional unificado das 5 etapas com bloco formal de assinaturas.
   - Ocultação completa da casca da aplicação (cabeçalhos, breadcrumbs e menus) na impressão.
   - Destravamento de rolagem e altura para geração de PDF / impressão contínua em formato A4 com proteção contra corte no meio de blocos.

## Escopo das Modificações
- **Frontend (`MapeamentoWizard.vue`, `RiscosMapeadosView.vue`, `DefaultLayout.vue`, `index.css`, `router/index.ts`, `SidebarNav.vue`):**
  - Implementação de todas as etapas metodológicas refinadas, busca por sigla, validação sequencial, persistência local de rascunho sem redirecionamento, nova rota e view de riscos mapeados e estilos de impressão limpa.
- **Backend (`risco_controller.py`, `models/risco.py`, `routers/risco.py`):**
  - Motor de cálculo de severidade com FNC da Tabela 3, persistência de `nivel_controle`, endpoints de listagem com filtros e validação rigorosa de permissões hierárquicas.
- **Testes e Auditoria:**
  - Suíte de testes automatizados com Pytest (20/20 aprovados) e auditoria de 11 pilares com 100% de conformidade (`audit_framework.py`).
