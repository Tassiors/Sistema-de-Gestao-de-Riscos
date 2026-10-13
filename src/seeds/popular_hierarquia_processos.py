"""
Script de Reconstrução da Arquitetura de Processos e Hierarquia Organizacional EBSERH Tipo II (HC-UFPE)
========================================================================================================
Fontes da Verdade:
1. Planilha 'macroprocessos_processos_hospital_tipo_II_Ebserh.xlsx' (Aba 'Detalhamento') -> Processos por unidade
2. Planilha 'Processos_comuns.xlsx' (Aba 'Planilha1') -> Processos Comuns a todas as áreas

Regras de Negócio e Arquiteturais:
1. As 4 Grandes Gerências (Superintendência ID 28, Gerência Administrativa ID 8,
   Gerência de Atenção à Saúde ID 9, Gerência de Ensino e Pesquisa ID 10) e os
   Órgãos Independentes (Auditoria ID 77, Ouvidoria ID 11, Colegiado Executivo ID 78,
   Conselho Consultivo ID 79) são raízes operacionais independentes (unidade_pai_id = None).
2. Setores, Divisões e Gerências herdam os processos de suas unidades e setores relacionados
   de forma estritamente recursiva conforme o Organograma do HC-UFPE.
3. Processos Comuns (definidos na planilha Processos_comuns.xlsx) são marcados como
   is_transversal = True e ficam disponíveis para TODAS as unidades.
4. Macroprocesso 'Outro' com o processo 'Outro processo' é adicionado como transversal
   para permitir novos processos não cadastrados no sistema.
5. Todos os vínculos da tabela processos_unidades são persistidos e seed_data.json é sincronizado.
"""

import os
import sys
import json
import sqlite3
import openpyxl

def run_update():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "app.db")
    xlsx_det_path = os.path.join(
        base_dir, "docs", "referencias", "processos_ebserh",
        "macroprocessos_processos_hospital_tipo_II_Ebserh.xlsx"
    )
    xlsx_com_path = os.path.join(
        base_dir, "docs", "referencias", "processos_ebserh",
        "Processos_comuns.xlsx"
    )

    if not os.path.exists(xlsx_det_path):
        raise FileNotFoundError(f"Planilha de detalhamento não encontrada em: {xlsx_det_path}")
    if not os.path.exists(xlsx_com_path):
        raise FileNotFoundError(f"Planilha de processos comuns não encontrada em: {xlsx_com_path}")

    print(f"--> Conectando ao banco de dados: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # =========================================================================
    # 1. HIERARQUIA ORGANIZACIONAL HC-UFPE (ORGANOGRAMA OFICIAL)
    # =========================================================================
    print("--> 1. Atualizando hierarquia organizacional (unidade_pai_id)...")

    unidade_hierarquia = {
        # Órgãos Independentes (sem gerência superior)
        "Auditoria": None,
        "Ouvidoria": None,
        "Colegiado Executivo": None,
        "Conselho Consultivo": None,
        
        # As 4 Grandes Gerências Operacionais (Raízes independentes)
        "Superintendência": None,
        "Gerência Administrativa": None,
        "Gerência de Atenção à Saúde": None,
        "Gerência de Ensino e Pesquisa": None,
        
        # Setores e Unidades diretamente vinculadas à Superintendência
        "Setor de Gestão da Qualidade": "Superintendência",
        "Setor de Governança e Estratégia": "Superintendência",
        "Setor de Contratualização": "Superintendência",
        "Setor de Tecnologia da Informação e Saúde Digital": "Superintendência",
        "Unidade de Comunicação Social": "Superintendência",
        
        # Subordinados ao Setor de Gestão da Qualidade (STGQ)
        "Unidade de Gestão da Qualidade e Segurança do Paciente": "Setor de Gestão da Qualidade",
        "Unidade de Vigilância em Saúde": "Setor de Gestão da Qualidade",
        
        # Subordinados ao Setor de Governança e Estratégia (SEGOV)
        "Unidade de Gestão Estratégica, de Riscos e Controles Internos": "Setor de Governança e Estratégia",
        
        # Subordinados ao Setor de Contratualização e Regulação (STCOR)
        "Unidade de Contratualização": "Setor de Contratualização",
        "Unidade de Regulação Interna": "Setor de Contratualização",
        "Unidade de Gestão e Processamento da Informação Assistencial": "Setor de Contratualização",
        
        # Subordinados ao Setor de TI e Saúde Digital (SETISD)
        "Unidade de Sistemas de Informação e Inteligência de Dados": "Setor de Tecnologia da Informação e Saúde Digital",
        "Unidade de Infraestrutura, Suporte e Segurança da Informação": "Setor de Tecnologia da Informação e Saúde Digital",
        
        # Divisões da Gerência Administrativa (GAD)
        "Divisão de Administração e Finanças": "Gerência Administrativa",
        "Divisão de Logística e Infraestrutura": "Gerência Administrativa",
        "Divisão de Gestão de Pessoas": "Gerência Administrativa",
        
        # Subordinados à Divisão de Administração e Finanças (DAF)
        "Setor de Administração": "Divisão de Administração e Finanças",
        "Setor de Gestão Orçamentária e Financeira": "Divisão de Administração e Finanças",
        "Setor de Contabilidade": "Divisão de Administração e Finanças",
        
        # Subordinados ao Setor de Administração (SAD)
        "Unidade de Compras e Licitações": "Setor de Administração",
        "Unidade de Patrimônio": "Setor de Administração",
        "Unidade de Contratos": "Setor de Administração",
        "Unidade de Fiscalização Administrativa de Contratos": "Setor de Administração",
        
        # Subordinados ao Setor de Gestão Orçamentária e Financeira (SGOF)
        "Unidade de Planejamento e Gestão Orçamentária": "Setor de Gestão Orçamentária e Financeira",
        "Unidade de Execução Orçamentária e Financeira": "Setor de Gestão Orçamentária e Financeira",
        
        # Subordinados à Divisão de Logística e Infraestrutura (DLIH)
        "Setor de Infraestrutura Física": "Divisão de Logística e Infraestrutura",
        "Setor de Hotelaria Hospitalar": "Divisão de Logística e Infraestrutura",
        "Setor de Engenharia Clínica": "Divisão de Logística e Infraestrutura",
        "Setor de Abastecimento Farmacêutico e Suprimentos": "Divisão de Logística e Infraestrutura",
        "Unidade de Serviços Gerais": "Divisão de Logística e Infraestrutura",
        
        # Subordinados ao Setor de Abastecimento Farmacêutico e Suprimentos (SAFS)
        "Unidade de Almoxarifado e Controle de Estoques": "Setor de Abastecimento Farmacêutico e Suprimentos",
        "Unidade de Planejamento e Dimensionamento de Estoques": "Setor de Abastecimento Farmacêutico e Suprimentos",
        
        # Subordinados à Divisão de Gestão de Pessoas (DIVGP)
        "Unidade de Administração de Pessoal": "Divisão de Gestão de Pessoas",
        "Unidade de Desenvolvimento de Pessoal": "Divisão de Gestão de Pessoas",
        "Unidade de Saúde Ocupacional e Segurança do Trabalho": "Divisão de Gestão de Pessoas",
        
        # Subordinados à Gerência de Ensino e Pesquisa (GEP)
        "Unidade de e-Saúde": "Gerência de Ensino e Pesquisa",
        "Setor de Gestão do Ensino": "Gerência de Ensino e Pesquisa",
        "Setor de Gestão da Pesquisa e da Inovação Tecnológica em Saúde": "Gerência de Ensino e Pesquisa",
        
        # Subordinados ao Setor de Gestão do Ensino (SEGE)
        "Unidade de Gestão de Graduação, Ensino Técnico e Extensão": "Setor de Gestão do Ensino",
        "Unidade de Gestão de Pós-Graduação": "Setor de Gestão do Ensino",
        
        # Subordinados ao Setor de Gestão da Pesquisa e Inovação (SGPITS)
        "Unidade de Gestão da Pesquisa": "Setor de Gestão da Pesquisa e da Inovação Tecnológica em Saúde",
        "Unidade de Gestão da Inovação Tecnológica em Saúde": "Setor de Gestão da Pesquisa e da Inovação Tecnológica em Saúde",
        
        # Divisões e Setores da Gerência de Atenção à Saúde (GAS)
        "Divisão Médica": "Gerência de Atenção à Saúde",
        "Divisão de Enfermagem": "Gerência de Atenção à Saúde",
        "Divisão de Gestão do Cuidado": "Gerência de Atenção à Saúde",
        "Divisão de Apoio Diagnóstico e Terapêutico": "Gerência de Atenção à Saúde",
        "Setor do Paciente Crítico": "Gerência de Atenção à Saúde",
        "Setor de Farmácia Hospitalar": "Gerência de Atenção à Saúde",
        "Setor de Apoio Diagnóstico e Terapêutico": "Divisão de Apoio Diagnóstico e Terapêutico",
        
        # Subordinados ao Setor do Paciente Crítico
        "Unidade de Terapia Intensiva Adulto": "Setor do Paciente Crítico",
        "Unidade de Terapia Intensiva Pediátrica e Neonatal": "Setor do Paciente Crítico",
        "Unidade de Urgência e Emergência": "Setor do Paciente Crítico",
        "Unidade de Bloco Cirúrgico e Processamento de Material Esterilizado": "Setor do Paciente Crítico",
        
        # Subordinados ao Setor de Farmácia Hospitalar
        "Unidade de Farmácia Clínica e Dispensação Farmacêutica": "Setor de Farmácia Hospitalar",
        
        # Subordinados ao Setor de Apoio Diagnóstico e Terapêutico
        "Unidade de Diagnóstico por Imagem": "Setor de Apoio Diagnóstico e Terapêutico",
        "Unidade de Diagnósticos Especializados": "Setor de Apoio Diagnóstico e Terapêutico",
        "Unidade de Análises Clínicas e Anatomia Patológica": "Setor de Apoio Diagnóstico e Terapêutico",
        
        # Subordinados às Divisões Assistenciais e GAS
        "Unidade de Clínica Médica": "Divisão Médica",
        "Unidade de Clínica Cirúrgica": "Divisão Médica",
        "Unidade de Apoio à Gestão em Enfermagem": "Divisão de Enfermagem",
        "Unidade Multiprofissional": "Divisão de Gestão do Cuidado",
        "Unidade de Ambulatório": "Gerência de Atenção à Saúde",
        "Unidade da Criança e do Adolescente": "Gerência de Atenção à Saúde",
        "Unidade de Cabeça e Pescoço": "Gerência de Atenção à Saúde",
        "Unidade de Hematologia, Hemoterapia e Oncologia": "Gerência de Atenção à Saúde",
        "Unidade de Saúde da Mulher": "Gerência de Atenção à Saúde",
        "Unidade de Saúde Mental": "Gerência de Atenção à Saúde",
        "Unidade de Sistema Urinário": "Gerência de Atenção à Saúde",
        "Unidade de Transplantes": "Gerência de Atenção à Saúde",
        "Unidade do Sistema Cardiovascular": "Gerência de Atenção à Saúde",
        "Unidade do Sistema Neuro-Músculo-Esquelético": "Gerência de Atenção à Saúde"
    }

    cursor.execute("SELECT id, nome FROM unidades_organizacionais")
    unidades_db = {row[1]: row[0] for row in cursor.fetchall()}

    for nome_filho, nome_pai in unidade_hierarquia.items():
        filho_id = unidades_db.get(nome_filho)
        pai_id = unidades_db.get(nome_pai) if nome_pai else None
        if filho_id:
            cursor.execute("UPDATE unidades_organizacionais SET unidade_pai_id = ? WHERE id = ?", (pai_id, filho_id))

    conn.commit()
    print("[OK] Hierarquia organizacional das 79 unidades atualizada!")

    # =========================================================================
    # 2. CARREGAR PLANILHAS
    # =========================================================================
    print(f"--> 2. Carregando dados de {xlsx_det_path}...")
    wb_det = openpyxl.load_workbook(xlsx_det_path, data_only=True)
    ws_det = wb_det['Detalhamento']

    sheet_rows = []
    for r in range(2, ws_det.max_row + 1):
        area_gestao = ws_det.cell(r, 1).value
        caminho = ws_det.cell(r, 2).value
        macro = ws_det.cell(r, 3).value
        proc = ws_det.cell(r, 4).value
        pagina = ws_det.cell(r, 5).value
        if caminho and proc:
            sheet_rows.append({
                "area_gestao": str(area_gestao).strip() if area_gestao else "",
                "caminho": str(caminho).strip(),
                "macroprocesso": str(macro).strip() if macro else "",
                "processo": str(proc).strip(),
                "pagina": pagina
            })

    print(f"[OK] {len(sheet_rows)} registros lidos da aba 'Detalhamento'.")

    # Carrega planilha de processos comuns
    print(f"--> Carregando dados de {xlsx_com_path}...")
    wb_com = openpyxl.load_workbook(xlsx_com_path, data_only=True)
    ws_com = wb_com['Planilha1']

    # Dicionário de padronização de macroprocessos comuns
    macro_comuns_map = {
        "GERIR PROJETOS": "Gerir projetos",
        "MONITORAR RESULTADOS": "Monitorar resultados",
        "GERIR RISCOS": "Gerir riscos",
        "REALIZAR A GESTÃO E MELHORIA DE PROCESSOS": "Realizar a gestão e melhoria de processos",
        "DESENVOLVER E RETER PESSOAS": "Desenvolver e reter pessoas",
        "PROMOVER TRANSPARÊNCIA INSTITUCIONAL": "Promover transparência institucional",
        "GERIR ÓRGÃOS COLEGIADOS": "Gerir órgãos colegiados",
        "REALIZAR CONTRATAÇÕES": "Realizar contratações",
        "GERIR CONTRATOS E ATAS DE REGISTRO DE PREÇOS": "Gerir contratos e atas de registro de preços",
        "INSTITUCIONALIZAR SOLUÇÕES DE TI": "Institucionalizar soluções de TI",
        "REALIZAR GESTÃO DOCUMENTAL": "Realizar gestão documental",
        "PROVER PAINÉIS DE ANÁLISE DE DADOS": "Prover painéis de análise de dados",
    }

    # Processos comuns indexados em minúsculo: proc_lower -> (macro_padronizado, nome_oficial)
    comuns_config = {}
    for r in range(2, ws_com.max_row + 1):
        m_val = ws_com.cell(r, 1).value
        p_val = ws_com.cell(r, 2).value
        if m_val and p_val:
            m_str = str(m_val).strip()
            m_padrao = macro_comuns_map.get(m_str.upper(), m_str)
            items = [x.strip() for x in str(p_val).split(';') if x.strip()]
            for item in items:
                comuns_config[item.lower()] = (m_padrao, item)

    print(f"[OK] {len(comuns_config)} Processos Comuns identificados em {len(set(m for m, _ in comuns_config.values()))} Macroprocessos.")

    # =========================================================================
    # 3. SINCRONIZAR MACROPROCESSOS E PROCESSOS
    # =========================================================================
    print("--> 3. Sincronizando catálogo completo de Macroprocessos e Processos...")

    # Mapeamento consolidado: proc_nome -> macro_nome
    proc_to_macro = {}
    for r in sheet_rows:
        p_nome = r['processo']
        m_nome = r['macroprocesso']
        # Se for um dos processos comuns de melhoria de processos, ajustar nome do macroprocesso
        if p_nome.lower() in ["realizar gestão do dia a dia", "realizar transformação de processos"]:
            proc_to_macro[p_nome] = "Realizar a gestão e melhoria de processos"
        else:
            proc_to_macro[p_nome] = m_nome

    # Adiciona os processos comuns que podem não estar na planilha de unidades
    for p_lower, (m_nome, p_oficial) in comuns_config.items():
        # Busca se já existe com outra capitalização
        matched_key = next((k for k in proc_to_macro.keys() if k.lower() == p_lower), None)
        if matched_key:
            proc_to_macro[matched_key] = m_nome
        else:
            proc_to_macro[p_oficial] = m_nome

    # Adiciona o Macroprocesso 'Outro' e seu processo
    proc_to_macro["Outro processo"] = "Outro"

    # Conjunto de processos transversais (comuns + Outro)
    transversais_set = set(k.lower() for k in comuns_config.keys())
    transversais_set.add("outro processo")

    # Lista de todos os macroprocessos únicos
    all_macros = sorted(list(set(proc_to_macro.values())))

    # Sincroniza macroprocessos no banco
    cursor.execute("SELECT id, nome FROM macroprocessos")
    existing_macros = {row[1]: row[0] for row in cursor.fetchall()}

    macro_id_map = {}
    for m_nome in all_macros:
        if m_nome in existing_macros:
            mid = existing_macros[m_nome]
            macro_id_map[m_nome] = mid
        else:
            cursor.execute("INSERT INTO macroprocessos (nome) VALUES (?)", (m_nome,))
            macro_id_map[m_nome] = cursor.lastrowid

    # Sincroniza processos no banco
    cursor.execute("SELECT id, nome FROM processos")
    existing_procs = {row[1]: row[0] for row in cursor.fetchall()}

    proc_id_map = {}
    for proc_nome, macro_nome in proc_to_macro.items():
        mid = macro_id_map[macro_nome]
        is_trans = 1 if proc_nome.lower() in transversais_set else 0

        # Verifica se processo já existe no banco
        matched_pid = None
        for ep_nome, ep_id in existing_procs.items():
            if ep_nome.lower() == proc_nome.lower():
                matched_pid = ep_id
                break

        if matched_pid:
            cursor.execute(
                "UPDATE processos SET macroprocesso_id = ?, nome = ?, is_transversal = ? WHERE id = ?",
                (mid, proc_nome, is_trans, matched_pid)
            )
            proc_id_map[proc_nome] = matched_pid
        else:
            cursor.execute(
                "INSERT INTO processos (macroprocesso_id, nome, is_transversal, permite_projeto) VALUES (?, ?, ?, 0)",
                (mid, proc_nome, is_trans)
            )
            proc_id_map[proc_nome] = cursor.lastrowid

    # Remove processos obsoletos
    valid_proc_ids = set(proc_id_map.values())
    cursor.execute("SELECT id FROM processos")
    all_db_proc_ids = [row[0] for row in cursor.fetchall()]
    procs_to_del = [pid for pid in all_db_proc_ids if pid not in valid_proc_ids]
    if procs_to_del:
        cursor.execute(f"DELETE FROM processos_unidades WHERE processo_id IN ({','.join(map(str, procs_to_del))})")
        cursor.execute(f"DELETE FROM processos WHERE id IN ({','.join(map(str, procs_to_del))})")

    # Remove macroprocessos obsoletos
    valid_macro_ids = set(macro_id_map.values())
    cursor.execute("SELECT id FROM macroprocessos")
    all_db_macro_ids = [row[0] for row in cursor.fetchall()]
    macros_to_del = [mid for mid in all_db_macro_ids if mid not in valid_macro_ids]
    if macros_to_del:
        cursor.execute(f"DELETE FROM macroprocessos WHERE id IN ({','.join(map(str, macros_to_del))})")

    conn.commit()
    print(f"[OK] {len(all_macros)} Macroprocessos e {len(proc_to_macro)} Processos sincronizados no banco.")

    # =========================================================================
    # 4. MAPEAMENTO DE PROCESSOS POR UNIDADE (PROCESSOS_UNIDADES)
    # =========================================================================
    print("--> 4. Atualizando tabela processos_unidades...")

    caminho_to_unidades = {
        "Hospital Tipo II > Auditoria": [77],
        "Hospital Tipo II > Ouvidoria": [11],
        "Hospital Tipo II > Superintendência > STGQ/Unidade de Gestão da Qualidade e Segurança do Paciente": [52],
        "Hospital Tipo II > Superintendência > STGQ/Unidade de Vigilância em Saúde": [73],
        "Hospital Tipo II > Superintendência > SEGOV/Unidade de Planejamento, Gestão de Riscos e Controles Internos": [56],
        "Hospital Tipo II > Superintendência > SETISD/Unidade de Sistemas da Informação e Inteligência de Dados": [68],
        "Hospital Tipo II > Superintendência > SETISD/Unidade de Infraestrutura, Suporte e Segurança de Tecnologia da Informação": [58],
        "Hospital Tipo II > Superintendência > STCOR/Unidade de Regulação Assistencial": [62],
        "Hospital Tipo II > Superintendência > STCOR/Unidade de Contratualização": [42],
        "Hospital Tipo II > Superintendência > STCOR/Unidade de Gestão e Processamento da Informação Assistencial": [55],
        "Hospital Tipo II > Superintendência > Unidade de Comunicação Social": [40],
        "Hospital Tipo II > GAD > DAF/SAD/Unidade de Compras e Licitações": [39],
        "Hospital Tipo II > GAD > DAF/SAD/Unidade de Patrimônio": [59],
        "Hospital Tipo II > GAD > DAF/SAD/Unidade de Contratos": [41],
        "Hospital Tipo II > GAD > DAF/SAD/Unidade de Fiscalização Administrativa de Contratos": [49],
        "Hospital Tipo II > GAD > DAF/SGOF/Unidade de Planejamento e Gestão Orçamentária": [61],
        "Hospital Tipo II > GAD > DAF/SGOF/Unidade de Execução Orçamentária e Financeira": [47],
        "Hospital Tipo II > GAD > DAF/Setor de Contabilidade": [15],
        "Hospital Tipo II > GAD > DLIH/Setor de Engenharia Clínica": [17],
        "Hospital Tipo II > GAD > DLIH/Unidade de Serviços Gerais": [66],
        "Hospital Tipo II > GAD > DLIH/Setor de Infraestrutura Física": [25],
        "Hospital Tipo II > GAD > DLIH/SAFS/Unidade de Planejamento e Dimensionamento de Estoques": [60],
        "Hospital Tipo II > GAD > DLIH/SAFS/Unidade de Almoxarifado e Controle de Estoques": [31],
        "Hospital Tipo II > GAD > DLIH/Setor de Hotelaria Hospitalar": [24],
        "Hospital Tipo II > GAD > DIVGP/Unidade de Administração de Pessoal": [30],
        "Hospital Tipo II > GAD > DIVGP/Unidade de Desenvolvimento de Pessoal": [43],
        "Hospital Tipo II > GAD > DIVGP/Unidade de Saúde Ocupacional e Segurança do Trabalho": [65],
        "Hospital Tipo II > GEP > Unidade de e-Saúde": [46],
        "Hospital Tipo II > GEP > SEGE/Unidade de Gestão de Graduação, Ensino Técnico e Extensão": [53],
        "Hospital Tipo II > GEP > SEGE/Unidade de Gestão de Pós-graduação": [54],
        "Hospital Tipo II > GEP > SGPITS/Unidade de Gestão da Pesquisa": [51],
        "Hospital Tipo II > GEP > SGPITS/Unidade de Gestão da Inovação Tecnológica em Saúde": [50],
    }

    gas_assistencial_map = {
        "Implantar as unidades de produção": [9],
        "Realizar exames de imagem": [9, 2, 14, 44],
        "Realizar exames laboratoriais": [9, 2, 14, 33],
        "Realizar exames de métodos gráficos": [9, 2, 14, 45],
        "Gerir admissão na urgência e emergência": [9, 27, 72],
        "Gerir alta por óbito": [9, 33, 37, 38, 69, 70, 72],
        "Gerir doação de órgãos": [9, 71, 69, 72],
        "Realizar necrópsia": [9, 33],
        "Realizar consulta ambulatorial": [9, 32, 29, 36, 57, 63, 64, 67, 74, 75],
        "Realizar cirurgia ambulatorial": [9, 32, 35, 37],
        "Realizar tratamento em hospital dia": [9, 32, 57],
        "Realizar tratamento ambulatorial especializado": [9, 32, 29, 36, 57, 63, 64, 67, 74, 75],
        "Realizar internação clínica": [9, 38, 29, 36, 57, 63, 64, 67, 74, 75],
        "Realizar tratamento em terapia intensiva": [9, 69, 70],
        "Realizar tratamento cirúrgico": [9, 37, 35],
        "Realizar atendimento domiciliar": [9, 32, 5],
        "Realizar atendimento em urgência e emergência": [9, 72],
        "Processar produtos para saúde (CME)": [9, 35],
        "Gerir banco de material biológico": [9, 33, 71],
        "Gerir cuidados médicos": [9, 7, 37, 38],
        "Gerir cuidado de enfermagem": [9, 3, 34],
        "Gerir cuidados da equipe multiprofissional": [9, 5, 76],
        "Definir linhas de cuidado": [9, 5],
        "Estruturar linhas de cuidado": [9, 5],
        "Implementar linhas de cuidado": [9, 5],
        "Realizar teleconsulta": [9, 46, 32],
        "Realizar teleconsultoria": [9, 46, 32],
        "Realizar teleinterconsulta": [9, 46, 32],
    }

    farmacia_map = {
        "Distribuir medicamentos e produtos para a saúde": [48, 18],
        "Controlar estoque de medicamentos e produtos para a saúde": [48, 18],
    }

    cursor.execute("DELETE FROM processos_unidades")

    links_to_insert = set()
    for r in sheet_rows:
        c = r['caminho']
        p = r['processo']
        pid = proc_id_map.get(p)
        if not pid:
            continue

        if c in caminho_to_unidades:
            for uid in caminho_to_unidades[c]:
                links_to_insert.add((pid, uid))
        elif "Atenção à Saúde" in c:
            uids = gas_assistencial_map.get(p, [9])
            for uid in uids:
                links_to_insert.add((pid, uid))

    for p, uids in farmacia_map.items():
        pid = proc_id_map.get(p)
        if pid:
            for uid in uids:
                links_to_insert.add((pid, uid))

    for pid, uid in links_to_insert:
        cursor.execute(
            "INSERT INTO processos_unidades (processo_id, unidade_id) VALUES (?, ?)",
            (pid, uid)
        )

    conn.commit()
    print(f"[OK] {len(links_to_insert)} associações de unidades persistidas na tabela processos_unidades.")

    # =========================================================================
    # 5. ATUALIZAR SEED_DATA.JSON PARA REPRODUTIBILIDADE
    # =========================================================================
    print("--> 5. Atualizando seed_data.json...")
    seed_json_path = os.path.join(base_dir, "src", "seeds", "seed_data.json")
    if os.path.exists(seed_json_path):
        with open(seed_json_path, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        macro_map_json = {}
        for p_nome, m_nome in proc_to_macro.items():
            is_trans = p_nome.lower() in transversais_set
            macro_map_json.setdefault(m_nome, []).append({
                "nome": p_nome,
                "is_transversal": is_trans,
                "permite_projeto": False
            })

        new_macros_json = []
        for m_nome, p_list in sorted(macro_map_json.items()):
            new_macros_json.append({
                "nome": m_nome,
                "processos": p_list
            })

        seed_data["macroprocessos"] = new_macros_json
        with open(seed_json_path, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, ensure_ascii=False, indent=2)
        print("[OK] seed_data.json atualizado com sucesso!")

    cursor.close()
    conn.close()
    print("\n[OK] Sincronização de processos comuns e catálogo finalizada com êxito!")

if __name__ == "__main__":
    run_update()
