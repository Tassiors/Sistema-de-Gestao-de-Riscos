# Tasks: Modelo Base de Gestão de Riscos (HC-UFPE)

## Fase 1: Modelos de Dados, Migrações e Cargas Iniciais (Seeds)
- [x] 1.1 Criar modelos SQLAlchemy em `src/models/`:
  - `unidade_organizacional.py` (Unidades do HC-UFPE, órgãos independentes e gerências).
  - `processo.py` (Macroprocessos e Processos EBSERH Tipo II).
  - `usuario.py` e `usuario_visibilidade.py` (Perfis e controle "quem vê o que").
  - `risco.py` (Mapeamentos, Eventos, Avaliações, Controles, 5W2H e Contingência).
- [x] 1.2 Gerar e aplicar migração Alembic para o SQLite local (`data/app.db`).
- [x] 1.3 Criar script de seed (`src/seeds/seed_inicial.py`) para popular:
  - As 76 Unidades Organizacionais do HC-UFPE e Órgãos Independentes.
  - Catálogo de Processos EBSERH Tipo II (incluindo o macroprocesso da UGERC e processos transversais).
  - Os 4 Pilares do Mapa Estratégico do HC-UFPE.
  - Usuários administradores mestres (`tassio.silva` e `renata.albuquerque.1`).

## Fase 2: Backend — Serviços, Controladores e Roteadores FastAPI
- [x] 2.1 Implementar `src/controllers/admin_controller.py` para gestão de gestores e configuração de visibilidade setorial.
- [x] 2.2 Implementar `src/controllers/risco_controller.py` com o motor de cálculo de Risco Inerente, Fator de Mitigação e Risco Residual.
- [x] 2.3 Implementar `src/routers/unidade.py` e `src/routers/processo.py` (Default-Private Routers).
- [x] 2.4 Implementar `src/routers/risco.py` com endpoints para cadastro em Rascunho, submissão e painel de riscos.
- [x] 2.5 Atualizar `src/routers/admin.py` com endpoints para a matriz de visibilidade.
- [x] 2.6 Integrar chamadas a `registrar_auditoria()` em todas as operações de mutação (LGPD).

## Fase 3: Frontend — Módulo Administrativo de Usuários e Visibilidade
- [x] 3.1 Criar view `src/views/admin/GestaoUsuariosVisibilidade.vue` no Vue 3.
- [x] 3.2 Integrar consulta ao AD e formulário de cadastro de gestor com vinculação de unidade principal.
- [x] 3.3 Desenvolver modal interativo para concessão e revogação de visibilidade em múltiplos setores.

## Fase 4: Frontend — Wizard de Mapeamento e Matriz 5x5
- [x] 4.1 Criar componente visual `src/components/riscos/MatrizRisco5x5.vue` com indicação de apetite a risco (≤ 7,99).
- [x] 4.2 Desenvolver a view `src/views/riscos/MapeamentoWizard.vue` com as 5 etapas da UGERC:
  - Etapa 1: Contexto, Unidade, Processo (com flag e campos de Projeto) e Entrega.
  - Etapa 2: Causa, Evento, Consequência (com frase-síntese gerada em tempo real) e Categoria.
  - Etapa 3: Probabilidade, Impacto e Medidas de Controle dinâmicas.
  - Etapa 4: Matriz de Calor e feedback do Apetite de Risco.
  - Etapa 5: Planos de Ação 5W2H e Plano de Contingência com gatilhos.
- [x] 4.3 Desenvolver a view `src/views/riscos/PainelRiscos.vue` com listagem filtrada por permissões do usuário logado e filtros avançados.
- [x] 4.4 Atualizar o menu lateral (`SidebarNav`) com as novas opções de navegação.

## Fase 5: Testes Automatizados e Auditoria Institucional
- [x] 5.1 Criar suíte de testes em `tests/test_riscos.py` e `tests/test_processos_hierarquia.py`.
- [x] 5.2 Executar a suíte de testes (`pytest`) garantindo 100% de aprovação.
- [x] 5.3 Executar `python audit_framework.py .` e garantir 100% de conformidade nos 11 pilares mandatórios.

## Fase 6: Refinamento dos Processos Comuns e Mapeamento Customizado
- [x] 6.1 Sincronizar catálogo de Processos Comuns a partir de `Processos_comuns.xlsx` (12 Macroprocessos e 20 Processos Comuns transversais).
- [x] 6.2 Implementar herança de processos pelas 76 unidades organizacionais a partir das planilhas oficiais.
- [x] 6.3 Implementar Macroprocesso e Processo "Outro" com campo `processo_outro` no banco e na API.
- [x] 6.4 Implementar seletor com busca textual e separação entre Processos Próprios e Processos Comuns (sem tags ruidosas).

## Fase 7: Usabilidade, Segurança Administrativa e Limpeza Legada
- [x] 7.1 Remover exibição de matrícula no card de perfil logado (`ProfileDropdown.vue`).
- [x] 7.2 Remover rotas e links desnecessários do menu lateral (Início, Componentes, Exemplo, Configurações).
- [x] 7.3 Definir Painel de Riscos (`/riscos`) como página inicial da aplicação e destino do login.
- [x] 7.4 Restringir exibição e acesso à tela `Gestores & Visibilidade` exclusivamente a administradores (`ADMINISTRADOR`).
- [x] 7.5 Integrar seleção de visibilidade setorial diretamente na etapa de Cadastrar/Editar Gestor, com opção "Selecionar Tudo".
- [x] 7.6 Remover dados e código legados de pacientes e AGHUX, preservando integração AD/LDAP e conectividade híbrida.
