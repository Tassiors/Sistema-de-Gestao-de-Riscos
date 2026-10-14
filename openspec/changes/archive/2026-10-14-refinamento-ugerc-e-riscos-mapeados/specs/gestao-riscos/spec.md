# Delta Spec: Gestão de Riscos — Refinamentos Metodológicos, Riscos Mapeados e Impressão A4

## MODIFIED REQUIREMENTS

### Requirement: Identificação e Categorização do Risco (Etapa 2)
O sistema DEVE disponibilizar o catálogo oficial de 11 categorias de risco:
1. `ACIDENTE`
2. `BIOLOGICO`
3. `COMPLIANCE`
4. `ERGONOMICO`
5. `ESTRATEGICO`
6. `FINANCEIRO`
7. `FISICO`
8. `OPERACIONAL`
9. `QUIMICO`
10. `REPUTACAO`
11. `SEGURANCA_INFORMACAO`

Cada categoria DEVE apresentar descrição resumida que auxilie o usuário na escolha adequada.
O sistema DEVE exibir a "Síntese da correlação evento-causa-consequência" acompanhada de legenda explicativa sobre a coerência lógica da oração.

### Requirement: Mensuração de Severidade e Escalas Oficiais (Etapa 3)
O sistema NÃO DEVE pré-selecionar opções de probabilidade e impacto no formulário de mapeamento.
As descrições da Tabela 2 (Probabilidade) e Tabela 1 (Impacto) DEVEM estar permanentemente visíveis nos seletores de peso 1 a 5 com estilização gradiente do verde ao vermelho.

### Requirement: Conceitos Metodológicos e Análise de Controles Internos (Etapa 3)
O sistema DEVE exibir definições conceituais de:
- **Risco Inerente**: $P \times I$ sem considerar controles.
- **Fator de Mitigação**: Fator Numérico do Controle (FNC) mensurado pela Tabela 3.
- **Risco Residual**: $\text{Inerente} \times \text{FNC}$.

O sistema DEVE implementar a análise de controles internos conforme a Tabela 3 da UGERC:
- Nível `INEXISTENTE`: FNC = 1,0 (não disponibiliza campo para medidas de controle).
- Nível `FRACO`: FNC = 0,8 (permite listar medidas).
- Nível `MEDIANO`: FNC = 0,6 (permite listar medidas).
- Nível `SATISFATORIO`: FNC = 0,4 (permite listar medidas).
- Nível `FORTE`: FNC = 0,2 (permite listar medidas).

O Fator Numérico de Controle NÃO DEVE variar em função da quantidade de medidas elencadas.

### Requirement: Salvamento em Rascunho sem Redirecionamento
Ao salvar um mapeamento com status `RASCUNHO`, o sistema DEVE persistir os dados e manter o usuário na mesma página e etapa de trabalho, emitindo notificação de confirmação.

## ADDED REQUIREMENTS

### Requirement: Busca Combinada de Unidades por Nome e Sigla (Etapa 1)
O campo de seleção de Unidade Organizacional DEVE permitir busca textual tanto pelo nome por extenso quanto pela sigla da unidade (ex: `UGERC`, `GAS`, `DAIA`).

### Requirement: Dependência Sequencial Estrita de Etapas no Mapeamento
O assistente de mapeamento DEVE impor dependência sequencial entre as etapas: a conclusão ou avanço para uma etapa $N+1$ exige que todas as etapas anteriores ($1 \dots N$) estejam plenamente preenchidas e válidas.

### Requirement: Tela Dedicada de Riscos Mapeados e Políticas RBAC
O sistema DEVE disponibilizar rota e tela exclusiva `/riscos/mapeados` acessível pelo menu lateral:
- Deve permitir filtragem por texto/sigla de Unidade e Status de tramitação.
- `ADMINISTRADOR` pode visualizar, editar e excluir qualquer ficha.
- `GESTOR_UNIDADE` pode visualizar, editar e excluir apenas fichas vinculadas à sua unidade principal.
- Usuários com acesso a unidades superiores visualizam as fichas de setores subordinados em modo somente-leitura, sem permissão para editar ou excluir.
- Toda exclusão deve ser auditada salvando o registro completo no log de auditoria.

### Requirement: Impressão e Exportação A4 Multi-páginas da Ficha de Mapeamento
O sistema DEVE fornecer funcionalidade de impressão e geração de PDF para a ficha completa:
- O layout de impressão DEVE ocultar todos os elementos da interface do sistema (menu lateral, cabeçalho, avatar, navegação).
- O relatório institucional unificado DEVE contemplar as 5 etapas e campo de assinaturas formais da UGERC.
- O estilo de impressão DEVE garantir quebra natural de páginas em formato A4 (`page-break-inside: avoid`) sem barras de rolagem ou cortes de conteúdo.
