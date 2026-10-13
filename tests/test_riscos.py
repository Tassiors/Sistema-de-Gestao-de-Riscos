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
    res = calcular_severidade_risco(probabilidade=5, impacto=5, num_controles=0)
    assert res["risco_inerente"] == 25
    assert res["fator_mitigacao"] == 1.0
    assert res["risco_residual"] == 25
    assert res["classificacao"] == "EXTREMO"
    assert res["acima_apetite"] is True


def test_motor_calculo_severidade_baixo_mitigado():
    """Risco com P=3, I=2 com 3 controles deve ser mitigado para BAIXO (dentro do apetite)."""
    # Inerente: 6. 3 controles -> Fator 0.4. Residual: round(6 * 0.4) = 2 -> BAIXO
    res = calcular_severidade_risco(probabilidade=3, impacto=2, num_controles=3)
    assert res["risco_inerente"] == 6
    assert res["fator_mitigacao"] == 0.4
    assert res["risco_residual"] == 2
    assert res["classificacao"] == "BAIXO"
    assert res["acima_apetite"] is False


def test_motor_calculo_tolerancia_limite():
    """Risco com residual 7 deve ser MÉDIO e dentro do apetite (tolerância ≤ 7,99)."""
    # P=3, I=3 (9), 1 controle (0.8) -> round(9 * 0.8) = 7
    res = calcular_severidade_risco(probabilidade=3, impacto=3, num_controles=1)
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

    # 6. Consulta estatísticas da matriz 5x5
    matriz_res = client.get("/api/riscos/painel/matriz", headers=headers)
    assert matriz_res.status_code == 200
    matriz_data = matriz_res.json()
    assert "quadrantes" in matriz_data
    assert "totais" in matriz_data
    assert matriz_data["totais"]["TOTAL"] >= 1
