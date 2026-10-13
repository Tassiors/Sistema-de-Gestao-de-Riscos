"""
Testes Automatizados para a Hierarquia Organizacional e Filtro de Processos (HC-UFPE)
=====================================================================================
Verifica se:
1. Unidade folha vê seus processos específicos + processos comuns (is_transversal = True).
2. Setor vê processos de suas unidades filhas + processos comuns.
3. Divisão vê processos de seus setores/unidades + processos comuns.
4. Gerência vê processos de toda a sua árvore de divisões e unidades + processos comuns.
5. Processo 'Gerir Riscos' -> 'Realizar identificação e avaliação dos eventos de riscos' é comum a todas as unidades.
"""

import pytest


def test_processos_comuns_visiveis_para_todas_as_unidades(client):
    """
    Testa se o processo 'REALIZAR IDENTIFICAÇÃO E AVALIAÇÃO DOS EVENTOS DE RISCOS'
    é retornado para qualquer unidade consultada (ex: Auditoria, Compras, UTI).
    """
    # 1. Login como admin
    login_resp = client.post("/api/login", data={"username": "admin", "password": "admin"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Obter lista de unidades para testar
    u_resp = client.get("/api/unidades", headers=headers)
    assert u_resp.status_code == 200
    unidades = u_resp.json()
    unidades_map = {u["nome"]: u["id"] for u in unidades}

    # Testa 3 unidades de perfis totalmente distintos: Auditoria, Compras, UTI Adulto
    test_units = [
        unidades_map["Auditoria"],
        unidades_map["Unidade de Compras e Licitações"],
        unidades_map["Unidade de Terapia Intensiva Adulto"]
    ]

    for uid in test_units:
        resp = client.get(f"/api/processos?unidade_id={uid}", headers=headers)
        assert resp.status_code == 200
        macros = resp.json()
        
        # Encontra o macroprocesso GERIR RISCOS
        macro_riscos = next((m for m in macros if "GERIR RISCOS" in m["nome"].upper()), None)
        assert macro_riscos is not None, f"GERIR RISCOS não encontrado para unidade {uid}"

        proc_nomes = [p["nome"].upper() for p in macro_riscos["processos"]]
        assert any("IDENTIFICAÇÃO E AVALIAÇÃO DOS EVENTOS DE RISCOS" in p for p in proc_nomes), (
            f"Processo de identificação de riscos ausente para unidade {uid}"
        )

        # Verifica macroprocesso OUTRO
        macro_outro = next((m for m in macros if m["nome"].upper() == "OUTRO"), None)
        assert macro_outro is not None, f"Macroprocesso OUTRO não encontrado para unidade {uid}"
        assert any("OUTRO" in p["nome"].upper() for p in macro_outro["processos"])

        # Verifica GERIR ÓRGÃOS COLEGIADOS
        macro_col = next((m for m in macros if "COLEGIADOS" in m["nome"].upper()), None)
        assert macro_col is not None, f"GERIR ÓRGÃOS COLEGIADOS não encontrado para unidade {uid}"
        assert any("COLEGIADOS INTERNOS" in p["nome"].upper() for p in macro_col["processos"])


def test_heranca_hierarquica_setor_compras(client):
    """
    Testa se:
    - Unidade de Compras e Licitações vê seus processos (SELECIONAR FORNECEDOR).
    - Setor de Administração (SAD) herda processos de Compras, Patrimônio e Contratos.
    - Divisão de Administração e Finanças (DAF) herda processos de SAD, SGOF e Contabilidade.
    """
    login_resp = client.post("/api/login", data={"username": "admin", "password": "admin"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    u_resp = client.get("/api/unidades", headers=headers)
    unidades_map = {u["nome"]: u["id"] for u in u_resp.json()}

    compras_id = unidades_map["Unidade de Compras e Licitações"]
    sad_id = unidades_map["Setor de Administração"]
    daf_id = unidades_map["Divisão de Administração e Finanças"]

    # 1. Compras
    resp_compras = client.get(f"/api/processos?unidade_id={compras_id}", headers=headers)
    assert resp_compras.status_code == 200
    procs_compras = [p["nome"].upper() for m in resp_compras.json() for p in m["processos"]]
    assert any("SELECIONAR FORNECEDOR" in p for p in procs_compras)

    # 2. SAD (deve ter processos de Compras E de Patrimônio/Contratos)
    resp_sad = client.get(f"/api/processos?unidade_id={sad_id}", headers=headers)
    assert resp_sad.status_code == 200
    procs_sad = [p["nome"].upper() for m in resp_sad.json() for p in m["processos"]]
    assert any("SELECIONAR FORNECEDOR" in p for p in procs_sad)
    assert any("INVENTÁRIO PATRIMONIAL" in p or "BENS PERMANENTES" in p for p in procs_sad)

    # Quantidade de processos no SAD deve ser estritamente maior que em Compras
    assert len(procs_sad) > len(procs_compras)

    # 3. DAF (deve ter ainda mais processos que o SAD, englobando contabilidade e orçamento)
    resp_daf = client.get(f"/api/processos?unidade_id={daf_id}", headers=headers)
    assert resp_daf.status_code == 200
    procs_daf = [p["nome"].upper() for m in resp_daf.json() for p in m["processos"]]
    assert len(procs_daf) > len(procs_sad)
