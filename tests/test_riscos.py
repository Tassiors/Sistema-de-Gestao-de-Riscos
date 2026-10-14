"""
Suíte de Testes Automatizados para o Sistema de Gestão de Riscos (HC-UFPE)
==========================================================================
Cobre:
1. Motor de cálculo de severidade e apetite a risco (Guia UGERC).
2. Endpoints protegidos (Default-Private Router pattern).
3. Mapeamento de riscos (Rascunho e Submissão).
4. Matriz de visibilidade e administração de gestores.
"""

import pytest
from src.controllers.risco_controller import calcular_severidade_risco


def test_motor_calculo_severidade_extremo():
    """Risco com Probabilidade 5 e Impacto 5 sem controles deve ser EXTREMO e acima do apetite."""
    res = calcular_severidade_risco(probabilidade=5, impacto=5, nivel_controle="INEXISTENTE")
    assert res["risco_inerente"] == 25
    assert res["fator_mitigacao"] == 1.0
    assert res["risco_residual"] == 25
    assert res["classificacao"] == "EXTREMO"
    assert res["acima_apetite"] is True


def test_motor_calculo_severidade_tabela3_fnc_fixo():
    """Testa a Tabela 3 do Guia UGERC: o FNC é fixo pelo nível e não varia com o número de medidas."""
    # Nível Fraco (0.8) com 1 medida ou com 10 medidas continua 0.8
    res1 = calcular_severidade_risco(probabilidade=4, impacto=3, nivel_controle="FRACO")
    res2 = calcular_severidade_risco(probabilidade=4, impacto=3, nivel_controle="FRACO", num_controles=5)
    assert res1["fator_mitigacao"] == 0.8
    assert res2["fator_mitigacao"] == 0.8
    assert res1["risco_residual"] == round(12 * 0.8)  # 10

    # Níveis da Tabela 3
    assert calcular_severidade_risco(5, 5, nivel_controle="INEXISTENTE")["fator_mitigacao"] == 1.0
    assert calcular_severidade_risco(5, 5, nivel_controle="FRACO")["fator_mitigacao"] == 0.8
    assert calcular_severidade_risco(5, 5, nivel_controle="MEDIANO")["fator_mitigacao"] == 0.6
    assert calcular_severidade_risco(5, 5, nivel_controle="SATISFATORIO")["fator_mitigacao"] == 0.4
    assert calcular_severidade_risco(5, 5, nivel_controle="FORTE")["fator_mitigacao"] == 0.2


def test_motor_calculo_tolerancia_limite():
    """Risco com residual 7 deve ser MÉDIO e dentro do apetite (tolerância ≤ 7,99)."""
    # P=3, I=3 (9), Fraco (0.8) -> round(9 * 0.8) = 7
    res = calcular_severidade_risco(probabilidade=3, impacto=3, nivel_controle="FRACO")
    assert res["risco_residual"] == 7
    assert res["classificacao"] == "MEDIO"
    assert res["acima_apetite"] is False



def test_rotas_protegidas_default_private(client):
    """Garante que requisições não autenticadas sejam bloqueadas com HTTP 401."""
    assert client.get("/api/unidades").status_code == 401
    assert client.get("/api/processos").status_code == 401
    assert client.get("/api/riscos").status_code == 401
    assert client.get("/api/admin/usuarios").status_code == 401


def test_fluxo_mapeamento_e_consulta(client):
    """Testa o fluxo completo de login, consulta de unidades e criação de mapeamento."""
    # 1. Login com o administrador Tássio Silva
    login_res = client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Consulta unidades
    unidades_res = client.get("/api/unidades", headers=headers)
    assert unidades_res.status_code == 200
    unidades = unidades_res.json()
    assert len(unidades) > 0
    primeira_unidade = unidades[0]["id"]

    # 3. Consulta processos
    proc_res = client.get("/api/processos", headers=headers)
    assert proc_res.status_code == 200
    macros = proc_res.json()
    assert len(macros) > 0
    primeiro_proc = macros[0]["processos"][0]["id"]

    # 4. Criação de mapeamento de risco em rascunho
    payload = {
        "unidade_id": primeira_unidade,
        "processo_id": primeiro_proc,
        "possui_projeto": True,
        "nome_projeto": "Projeto Piloto Teste",
        "pilar_estrategico_id": 1,
        "entrega_processo": "Relatório de conformidade entregue",
        "status": "RASCUNHO",

        "eventos": [
            {
                "categoria": "OPERACIONAL",
                "causa": "Instabilidade temporária de rede",
                "descricao_evento": "Interrupção momentânea do acesso aos prontuários",
                "consequencia": "Atraso no atendimento ambulatorial",
                "avaliacao": {
                    "probabilidade": 2,
                    "impacto": 3,
                    "nivel_controle": "FRACO",
                    "controles": ["Link redundante de contingência"]
                },
                "planos_acao": [
                    {
                        "tipo_resposta": "MITIGAR",
                        "o_que": "Testar comutação automática de rede",
                        "como": "Simular queda e validar tempo de resposta",
                        "quem": "Equipe de Redes SETISD",
                        "data_inicio": "2026-11-01",
                        "data_termino": "2026-11-15",
                        "status": "PLANEJADO"
                    }
                ],
                "planos_contingencia": [
                    {
                        "gatilho": "Queda simultânea dos dois links",
                        "o_que": "Acionar plano impresso de contingência",
                        "como": "Distribuição de fichas manuais",
                        "responsavel": "Chefe de Plantão"
                    }
                ]
            }
        ]
    }

    create_res = client.post("/api/riscos", json=payload, headers=headers)
    assert create_res.status_code == 200
    mapeamento = create_res.json()
    assert mapeamento["id"] is not None
    assert mapeamento["status"] == "RASCUNHO"
    assert len(mapeamento["eventos"]) == 1
    assert mapeamento["eventos"][0]["avaliacao"]["risco_residual"] > 0

    # 5. Consulta listagem de mapeamentos
    list_res = client.get("/api/riscos", headers=headers)
    assert list_res.status_code == 200
    assert any(m["id"] == mapeamento["id"] for m in list_res.json())

    # 6. Consulta estatísticas da matriz 5x5: como está RASCUNHO, NÃO deve contabilizar na matriz/cards
    matriz_res = client.get("/api/riscos/painel/matriz", headers=headers)
    assert matriz_res.status_code == 200
    matriz_data = matriz_res.json()
    total_submetidos_antes = matriz_data["totais"]["TOTAL"]

    # 7. Submeter a ficha completa para a UGERC
    payload["id"] = mapeamento["id"]
    payload["status"] = "SUBMETIDO"
    submeter_res = client.post("/api/riscos", json=payload, headers=headers)
    assert submeter_res.status_code == 200
    assert submeter_res.json()["status"] == "SUBMETIDO"

    # Agora a matriz 5x5 e cards DEVEM contabilizar a ficha submetida
    matriz_res_depois = client.get("/api/riscos/painel/matriz", headers=headers)
    assert matriz_res_depois.status_code == 200
    assert matriz_res_depois.json()["totais"]["TOTAL"] == total_submetidos_antes + 1


def test_bloqueio_submissao_etapas_incompletas(client):
    """Submeter para UGERC sem preencher todas as etapas deve retornar HTTP 400 com detalhes."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Tentativa de submissão sem preencher causa e consequência da Etapa 2
    payload_incompleto = {
        "unidade_id": 1,
        "processo_id": 1,
        "entrega_processo": "Entrega teste",
        "status": "SUBMETIDO",
        "eventos": [
            {
                "categoria": "OPERACIONAL",
                "causa": "",  # Vazio
                "descricao_evento": "Evento teste",
                "consequencia": "",  # Vazio
                "avaliacao": {"probabilidade": 3, "impacto": 3, "controles": []}
            }
        ]
    }

    res = client.post("/api/riscos", json=payload_incompleto, headers=headers)
    assert res.status_code == 400
    assert "Não é possível submeter para a UGERC" in res.json()["detail"]


def test_exclusao_ficha_risco_administrador(client):
    """Administrador pode deletar qualquer ficha de risco mapeada."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Cria uma ficha em rascunho
    payload = {
        "unidade_id": 1,
        "processo_id": 1,
        "entrega_processo": "Entrega para exclusão",
        "status": "RASCUNHO",
        "eventos": []
    }
    create_res = client.post("/api/riscos", json=payload, headers=headers)
    assert create_res.status_code == 200
    ficha_id = create_res.json()["id"]

    # Deleta a ficha
    del_res = client.delete(f"/api/riscos/{ficha_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["id"] == ficha_id

    # Verifica que não existe mais
    get_res = client.get(f"/api/riscos/{ficha_id}", headers=headers)
    assert get_res.status_code == 404


def test_endpoint_processos_outros(client):
    """Garante que o endpoint /api/processos/outros responde com sucesso e respeita permissões."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = client.get("/api/processos/outros", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

