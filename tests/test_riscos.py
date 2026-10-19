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


def test_coordenada_residual_respeita_apetite_risco():
    """
    Garante que para um risco dentro do apetite (residual <= 7), a célula destacada
    na Matriz de Riscos obrigatoriamente tenha produto <= 7 (zona de tolerância),
    nunca caindo em células de risco alto (prod >= 8).
    """
    from src.controllers.risco_controller import calcular_coordenada_residual

    # Caso 1: P=4, I=3 (Inerente=12), Residual Alvo=7 (Dentro do apetite)
    # Entre 6 (Médio) e 8 (Alto), DEVE obrigatoriamente selecionar a célula de valor 6
    p_res, i_res = calcular_coordenada_residual(4, 3, 7)
    prod = p_res * i_res
    assert prod <= 7, f"Esperava célula na zona de tolerância (<= 7), mas obteve produto {prod} (P={p_res}, I={i_res})"
    assert prod == 6

    # Caso 1.1: P=4, I=3 (Inerente=12), Residual Alvo=7.2 (FNC 0.6 float)
    # Deve arredondar e manter estritamente dentro da tolerância (<= 7), resultando em produto 6
    p_res, i_res = calcular_coordenada_residual(4, 3, 7.2)
    assert p_res * i_res == 6

    # Caso 2: P=3, I=3 (Inerente=9), Residual Alvo=7 (Dentro do apetite)
    p_res, i_res = calcular_coordenada_residual(3, 3, 7)
    prod = p_res * i_res
    assert prod <= 7
    assert prod == 6

    # Caso 2.1: P=4, I=2 (Inerente=8), Residual Alvo=7 (Dentro do apetite)
    p_res, i_res = calcular_coordenada_residual(4, 2, 7)
    assert p_res * i_res == 6

    # Caso 3: P=4, I=3 (Inerente=12), Residual Alvo=8 (Acima do apetite)
    # DEVE obrigatoriamente selecionar uma célula com prod > 7
    p_res, i_res = calcular_coordenada_residual(4, 3, 8)
    prod = p_res * i_res
    assert prod > 7
    assert prod == 8

    # Varredura exaustiva: nenhum residual <= 7.99 pode cair em célula com produto > 7
    for p in range(1, 6):
        for i in range(1, 6):
            for res_teste in [1, 2, 3, 4, 5, 6, 7, 7.2, 7.99]:
                pr, ir = calcular_coordenada_residual(p, i, res_teste)
                assert pr * ir <= 7, f"Falha para P={p}, I={i}, residual={res_teste}: caiu em {pr}x{ir}={pr*ir}"




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


def test_sigla_unidade_na_listagem_de_riscos(client):
    """Garante que a listagem de mapeamentos inclui o campo 'sigla' no objeto da unidade."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = client.get("/api/riscos", headers=headers)
    assert res.status_code == 200
    mapeamentos = res.json()
    assert isinstance(mapeamentos, list)
    if mapeamentos:
        primeiro = mapeamentos[0]
        if primeiro.get("unidade"):
            assert "sigla" in primeiro["unidade"]


def test_painel_matriz_gerencias_e_filtro_unidade(client):
    """Garante que o painel de riscos retorna os cards por gerência e aceita filtro por unidade_id."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Consulta geral sem filtro
    res = client.get("/api/riscos/painel/matriz", headers=headers)
    assert res.status_code == 200
    dados = res.json()
    assert "quadrantes" in dados
    assert "pode_ver_gerencias" in dados
    assert dados["pode_ver_gerencias"] is True  # Admin tem acesso total

    gerencias = dados["gerencias"]
    assert len(gerencias) == 4
    siglas = [g["sigla"] for g in gerencias]
    assert set(siglas) == {"SUP", "GAS", "GAD", "GEP"}

    for g in gerencias:
        assert "total" in g
        assert "baixo" in g
        assert "medio" in g
        assert "alto" in g
        assert "extremo" in g
        assert g["total"] == g["baixo"] + g["medio"] + g["alto"] + g["extremo"]
        # Indicador de unidades com risco mapeado
        assert "total_unidades" in g
        assert "unidades_com_risco" in g
        assert "percentual_mapeado" in g
        assert isinstance(g["percentual_mapeado"], (int, float))
        assert "unidades_detalhes" in g
        assert isinstance(g["unidades_detalhes"], list)

    # 2. Consulta filtrando por unidade_id
    res_filtrado = client.get("/api/riscos/painel/matriz?unidade_id=1", headers=headers)
    assert res_filtrado.status_code == 200
    dados_filtrados = res_filtrado.json()
    assert "quadrantes" in dados_filtrados
    assert "gerencias" in dados_filtrados
    assert "pode_ver_gerencias" in dados_filtrados


def test_versionamento_e_resubmissao_ficha(client):
    """Garante que ao criar e submeter uma ficha, ela ganha metadados de versão e autor, e ao re-submeter, a versão é incrementada."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Criação com status SUBMETIDO
    payload = {
        "unidade_id": 1,
        "processo_id": 1,
        "possui_projeto": False,
        "entrega_processo": "Entrega inicial para versionamento",
        "status": "SUBMETIDO",
        "eventos": [
            {
                "categoria": "OPERACIONAL",
                "causa": "Causa teste versionamento",
                "descricao_evento": "Evento teste versionamento",
                "consequencia": "Consequência teste versionamento",
                "avaliacao": {
                    "probabilidade": 2,
                    "impacto": 2,
                    "nivel_controle": "INEXISTENTE",
                    "controles": []
                },
                "planos_acao": [],
                "planos_contingencia": []
            }
        ]
    }
    res_create = client.post("/api/riscos", json=payload, headers=headers)
    assert res_create.status_code == 200
    ficha = res_create.json()
    ficha_id = ficha["id"]
    assert ficha["versao"] == 1
    assert "v1.0 (Original)" in ficha["tag_versao"]
    assert ficha["submetido_em"] is not None
    assert ficha["criado_por"] is not None

    # 2. Re-submissão após edição de campo
    payload["id"] = ficha_id
    payload["entrega_processo"] = "Entrega revisada e aprimorada"
    res_edit = client.post("/api/riscos", json=payload, headers=headers)
    assert res_edit.status_code == 200
    ficha_v2 = res_edit.json()
    assert ficha_v2["versao"] == 2
    assert "v2.0 (Revisada)" in ficha_v2["tag_versao"]
    assert ficha_v2["submetido_em"] is not None

    # Limpeza
    client.delete(f"/api/riscos/{ficha_id}", headers=headers)


def test_unidades_apenas_mapeamento_param(client):
    """Garante que o parâmetro apenas_mapeamento=true responde corretamente."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = client.get("/api/unidades?apenas_mapeamento=true", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_exclusao_lote_fichas_risco(client):
    """Valida a exclusão em lote de fichas cadastradas via POST /api/riscos/excluir-lote."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Obtém unidade e processo válidos
    unidades_res = client.get("/api/unidades", headers=headers)
    assert unidades_res.status_code == 200
    unidade_id = unidades_res.json()[0]["id"]

    proc_res = client.get("/api/processos", headers=headers)
    assert proc_res.status_code == 200
    processo_id = proc_res.json()[0]["processos"][0]["id"]

    # 1. Cria 2 fichas de teste
    ids_criados = []
    for i in range(2):
        payload = {
            "unidade_id": unidade_id,
            "processo_id": processo_id,
            "entrega_processo": f"Entrega Lote {i}",
            "status": "RASCUNHO",
            "eventos": [
                {
                    "categoria": "OPERACIONAL",
                    "causa": f"Causa Lote {i}",
                    "descricao_evento": f"Evento Lote {i}",
                    "consequencia": f"Consequência Lote {i}",
                    "avaliacao": {
                        "probabilidade": 2,
                        "impacto": 2,
                        "nivel_controle": "INEXISTENTE",
                        "controles": []
                    },
                    "planos_acao": [],
                    "planos_contingencia": []
                }
            ]
        }
        res_create = client.post("/api/riscos", json=payload, headers=headers)
        assert res_create.status_code == 200
        ids_criados.append(res_create.json()["id"])

    assert len(ids_criados) == 2

    # 2. Testa exclusão em lote com lista vazia (deve retornar 400)
    res_vazia = client.post("/api/riscos/excluir-lote", json={"ids": []}, headers=headers)
    assert res_vazia.status_code == 400

    # 3. Executa exclusão em lote com os 2 IDs criados
    res_lote = client.post("/api/riscos/excluir-lote", json={"ids": ids_criados}, headers=headers)
    assert res_lote.status_code == 200
    dados_resp = res_lote.json()
    assert dados_resp["total_excluidos"] == 2
    assert set(dados_resp["ids"]) == set(ids_criados)

    # 4. Garante que as fichas foram realmente removidas
    for id_removido in ids_criados:
        res_get = client.get(f"/api/riscos/{id_removido}", headers=headers)
        assert res_get.status_code == 404


def test_obter_detalhes_em_lote_para_impressao(client):
    """Testa a obtenção dos dados detalhados de múltiplas fichas para impressão em lote."""
    login_res = client.post("/api/login", data={"username": "admin", "password": "admin"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    unidades_res = client.get("/api/unidades", headers=headers)
    unidade_id = unidades_res.json()[0]["id"]

    proc_res = client.get("/api/processos", headers=headers)
    processo_id = proc_res.json()[0]["processos"][0]["id"]

    # Cria 2 fichas com dados completos
    ids = []
    for i in range(2):
        payload = {
            "unidade_id": unidade_id,
            "processo_id": processo_id,
            "entrega_processo": f"Entrega Impressao {i}",
            "status": "SUBMETIDO",
            "eventos": [
                {
                    "categoria": "ASSISTENCIAL",
                    "causa": f"Causa Impressao {i}",
                    "descricao_evento": f"Evento Impressao {i}",
                    "consequencia": f"Consequência Impressao {i}",
                    "avaliacao": {
                        "probabilidade": 3,
                        "impacto": 4,
                        "nivel_controle": "MEDIANO",
                        "controles": [{"descricao_controle": f"Controle {i}"}]
                    },
                    "planos_acao": [
                        {
                            "tipo_resposta": "MITIGAR",
                            "o_que": f"Ação {i}",
                            "como": "Procedimento padrão",
                            "quem": "Equipe",
                            "data_inicio": "2026-01-01",
                            "data_termino": "2026-06-01"
                        }
                    ],
                    "planos_contingencia": []
                }
            ]
        }
        res_create = client.post("/api/riscos", json=payload, headers=headers)
        assert res_create.status_code == 200
        ids.append(res_create.json()["id"])

    # 1. Consulta em lote
    res_lote = client.post("/api/riscos/detalhes-lote", json={"ids": ids}, headers=headers)
    assert res_lote.status_code == 200
    fichas = res_lote.json()
    assert len(fichas) == 2

    # Verifica se os dados necessários para o layout A4 estão presentes
    for ficha in fichas:
        assert ficha["id"] in ids
        assert ficha["unidade"] is not None
        assert ficha["processo"] is not None
        assert len(ficha["eventos"]) == 1
        assert ficha["eventos"][0]["avaliacao"]["probabilidade"] == 3
        assert len(ficha["eventos"][0]["avaliacao"]["controles"]) == 1
        assert len(ficha["eventos"][0]["planos_acao"]) == 1

    # Limpeza
    client.post("/api/riscos/excluir-lote", json={"ids": ids}, headers=headers)


def test_consultar_e_excluir_ficha_individual(client):
    """
    Testa a consulta detalhada de uma ficha de risco (GET /api/riscos/{id})
    e sua posterior exclusão individual (DELETE /api/riscos/{id}).
    """
    token = client.post("/api/login", data={"username": "admin", "password": "admin"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    unidade_id = client.get("/api/unidades", headers=headers).json()[0]["id"]
    macros = client.get("/api/processos", headers=headers).json()
    processo_id = macros[0]["processos"][0]["id"]

    # 1. Cria a ficha
    payload = {
        "unidade_id": unidade_id,
        "processo_id": processo_id,
        "entrega_processo": "Entrega Teste Individual",
        "status": "SUBMETIDO",
        "eventos": [
            {
                "categoria": "ASSISTENCIAL",
                "causa": "Falha no processo de triagem",
                "descricao_evento": "Atraso no atendimento clínico",
                "consequencia": "Prejuízo à assistência",
                "avaliacao": {
                    "probabilidade": 4,
                    "impacto": 3,
                    "nivel_controle": "MEDIANO",
                    "controles": [{"descricao_controle": "Protocolo de acolhimento"}]
                },
                "planos_acao": [
                    {
                        "tipo_resposta": "MITIGAR",
                        "o_que": "Capacitação contínua",
                        "como": "Treinamento em serviço",
                        "quem": "Gestão Assistencial",
                        "data_inicio": "2026-02-01",
                        "data_termino": "2026-08-01"
                    }
                ],
                "planos_contingencia": []
            }
        ]
    }
    res_create = client.post("/api/riscos", json=payload, headers=headers)
    assert res_create.status_code == 200
    ficha_id = res_create.json()["id"]

    # 2. Consulta detalhada (GET /api/riscos/{id})
    res_get = client.get(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_get.status_code == 200
    ficha = res_get.json()
    assert ficha["id"] == ficha_id
    assert ficha["pode_editar"] is True
    assert ficha["pode_excluir"] is True
    assert ficha["unidade"]["id"] == unidade_id
    assert ficha["processo"]["id"] == processo_id
    assert len(ficha["eventos"]) == 1
    assert ficha["eventos"][0]["descricao_evento"] == "Atraso no atendimento clínico"
    assert ficha["eventos"][0]["avaliacao"]["probabilidade"] == 4
    assert ficha["eventos"][0]["avaliacao"]["impacto"] == 3
    assert len(ficha["eventos"][0]["avaliacao"]["controles"]) == 1
    assert len(ficha["eventos"][0]["planos_acao"]) == 1

    # 3. Exclusão individual (DELETE /api/riscos/{id})
    res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_del.status_code == 200
    assert "excluíd" in res_del.json().get("message", "").lower()

    # 4. Verifica que não existe mais (404)
    res_pos_del = client.get(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_pos_del.status_code == 404





