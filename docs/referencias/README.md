# Documentos de Referência e Insumos do Sistema

Esta pasta armazena os arquivos de referência, regras de negócio e insumos institucionais fornecidos para subsidiar a especificação e o desenvolvimento do **Sistema de Gestão de Riscos (HC-UFPE / EBSERH)**.

---

## 📁 Estrutura de Pastas

| Pasta | Descrição | Arquivos Esperados |
| :--- | :--- | :--- |
| [`redcap/`](./redcap/) | Projeto legado/matriz no REDCap | Arquivo XML exportado do REDCap contendo dicionário de dados, formulários, eventos e campos. |
| [`manuais/`](./manuais/) | Guia prático de utilização | Manual de instruções e regras operacionais do sistema atual/esperado. |
| [`processos_ebserh/`](./processos_ebserh/) | Arquitetura de Processos EBSERH | Mapeamento de processos da rede EBSERH com foco nos processos de **Hospital Tipo II**. |
| [`organograma_hc/`](./organograma_hc/) | Estrutura Organizacional HC-UFPE | Organograma oficial, setores, divisões e hierarquia do hospital para parametrização de áreas e permissões. |

---

## 📌 Como estes arquivos serão utilizados pelo Agente de IA

1. **REDCap (XML):** Extração automatizada do modelo de dados (tabelas, campos, regras de validação, tipos de dados e lógica de branching).
2. **Guia Prático:** Extração das regras de negócio, perfis de usuários, transições de status e fluxos de tela.
3. **Processos EBSERH (Tipo II):** Alinhamento da taxonomia de riscos, incidentes, eventos adversos e fluxos de encaminhamento aos padrões da sede EBSERH.
4. **Organograma HC-UFPE:** Mapeamento de lotações, unidades demandantes e instâncias de aprovação no hospital.
