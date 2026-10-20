"""
Suíte de Testes Automatizados de Perfis de Usuário, Hierarquia e Matriz de Acesso (HC-UFPE)
=============================================================================================
Objetivos:
1. Verificar se cada tipo de perfil (ADMINISTRADOR, GESTOR_UNIDADE, CONSULTA_SETORIAL)
   possui acesso às funcionalidades próprias e se cada uma funciona corretamente.
2. Verificar se unidades superiores (Superintendência, Gerências, Divisões e Setores)
   conseguem APENAS VISUALIZAR (somente-leitura) as fichas de suas unidades subordinadas,
   sendo impedidas de editar ou excluir fichas dessas unidades.
3. Certificar que qualquer unidade organizacional (incluindo Superintendência, Gerências,
   Divisões, Setores, Unidades e Órgãos Independentes) tem acesso completo a operações
   de CRUD (Create, Read, Update, Delete) referentes ao SEU PRÓPRIO setor.
4. Validar matriz de visibilidade cruzada adicional e isolamento entre ramos distintos.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def setup_cenario(client):
    """
    Cria todos os usuários de teste para cada perfil e nível hierárquico,
    e identifica as unidades organizacionais necessárias.
    """
    # 1. Login como admin padrão
    admin_login = client.post("/api/login", data={"username": "admin", "password": "admin"})
    assert admin_login.status_code == 200, "Falha ao logar como admin padrão"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Obter mapa de unidades
    resp_u = client.get("/api/unidades", headers=admin_headers)
    assert resp_u.status_code == 200
    unidades = resp_u.json()
    unidades_map = {u["nome"]: u["id"] for u in unidades}

    # Unidades da cadeia hierárquica administrativa:
    # Gerência Administrativa (GAD) -> Divisão de Administração e Finanças (DAF)
    # -> Setor de Administração (SAD) -> Unidade de Compras e Licitações (Compras)
    gad_id = unidades_map["Gerência Administrativa"]
    daf_id = unidades_map["Divisão de Administração e Finanças"]
    sad_id = unidades_map["Setor de Administração"]
    compras_id = unidades_map["Unidade de Compras e Licitações"]

    # Superintendência e subordinada direta
    super_id = unidades_map["Superintendência"]
    ugerc_id = unidades_map.get("Unidade de Gestão Estratégica, de Riscos e Controles Internos") or unidades_map.get("Setor de Governança e Estratégia")

    # Órgão independente
    auditoria_id = unidades_map["Auditoria"]

    # Unidade de outro ramo independente (Atenção à Saúde)
    uti_id = unidades_map["Unidade de Terapia Intensiva Adulto"]

    # 3. Processo e Pilar Estratégico para cadastros
    resp_proc = client.get("/api/processos?transversal_only=true", headers=admin_headers)
    assert resp_proc.status_code == 200
    processo_id = resp_proc.json()[0]["processos"][0]["id"]

    resp_pil = client.get("/api/processos/pilares-estrategicos", headers=admin_headers)
    assert resp_pil.status_code == 200
    pilar_id = resp_pil.json()[0]["id"]

    # 4. Cadastro dos usuários de teste via API administrativa
    usuarios_para_criar = [
        {
            "username": "admin.teste",
            "nome_completo": "Administrador de Teste",
            "email": "admin.teste@ebserh.gov.br",
            "perfil": "ADMINISTRADOR",
            "unidade_principal_id": gad_id,
            "ativo": True
        },
        {
            "username": "gestor.superintendencia",
            "nome_completo": "Gestor da Superintendência",
            "email": "gestor.superintendencia@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": super_id,
            "ativo": True
        },
        {
            "username": "gestor.gerencia",
            "nome_completo": "Gestor da Gerência Administrativa",
            "email": "gestor.gerencia@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": gad_id,
            "ativo": True
        },
        {
            "username": "gestor.divisao",
            "nome_completo": "Gestor da Divisão de Administração e Finanças",
            "email": "gestor.divisao@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": daf_id,
            "ativo": True
        },
        {
            "username": "gestor.setor",
            "nome_completo": "Gestor do Setor de Administração",
            "email": "gestor.setor@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": sad_id,
            "ativo": True
        },
        {
            "username": "gestor.compras",
            "nome_completo": "Gestor de Compras e Licitações",
            "email": "gestor.compras@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": compras_id,
            "ativo": True
        },
        {
            "username": "gestor.auditoria",
            "nome_completo": "Gestor da Auditoria",
            "email": "gestor.auditoria@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": auditoria_id,
            "ativo": True
        },
        {
            "username": "gestor.visibilidade",
            "nome_completo": "Gestor com Visibilidade Cruzada",
            "email": "gestor.visibilidade@ebserh.gov.br",
            "perfil": "GESTOR_UNIDADE",
            "unidade_principal_id": auditoria_id,
            "ativo": True
        },
        {
            "username": "usuario.consulta",
            "nome_completo": "Usuário Somente Consulta de Compras",
            "email": "usuario.consulta@ebserh.gov.br",
            "perfil": "CONSULTA_SETORIAL",
            "unidade_principal_id": compras_id,
            "ativo": True
        }
    ]

    usuarios_db_ids = {}
    for u in usuarios_para_criar:
        res = client.post("/api/admin/usuarios", json=u, headers=admin_headers)
        assert res.status_code == 200, f"Erro ao criar usuário {u['username']}: {res.text}"
        usuarios_db_ids[u["username"]] = res.json()["id"]

    # 5. Configurar visibilidade cruzada para gestor.visibilidade (acesso adicional à unidade de Compras)
    vis_res = client.post(
        f"/api/admin/usuarios/{usuarios_db_ids['gestor.visibilidade']}/visibilidade",
        json={"unidades_ids": [compras_id]},
        headers=admin_headers
    )
    assert vis_res.status_code == 200, f"Erro ao conceder visibilidade cruzada: {vis_res.text}"

    # Helper para obter token de qualquer usuário
    tokens = {}
    for u in usuarios_para_criar:
        l_res = client.post("/api/login", data={"username": u["username"], "password": "password"})
        assert l_res.status_code == 200, f"Erro no login de {u['username']}: {l_res.text}"
        tokens[u["username"]] = l_res.json()["access_token"]

    tokens["admin"] = admin_token

    return {
        "tokens": tokens,
        "unidades": {
            "super": super_id,
            "ugerc": ugerc_id,
            "gad": gad_id,
            "daf": daf_id,
            "sad": sad_id,
            "compras": compras_id,
            "auditoria": auditoria_id,
            "uti": uti_id
        },
        "processo_id": processo_id,
        "pilar_id": pilar_id
    }


def get_headers(setup_cenario, username: str) -> Dict[str, str]:
    token = setup_cenario["tokens"][username]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. TESTES DO PERFIL ADMINISTRADOR
# =============================================================================

def test_administrador_acesso_modulo_admin(client, setup_cenario):
    """
    Verifica se o ADMINISTRADOR tem acesso completo a todos os endpoints administrativos.
    """
    headers = get_headers(setup_cenario, "admin.teste")

    # 1. Dados confidenciais de administração
    res_conf = client.get("/api/admin-only-data", headers=headers)
    assert res_conf.status_code == 200
    assert "confidential admin data" in res_conf.json()["message"]

    # 2. Listagem de usuários
    res_users = client.get("/api/admin/usuarios", headers=headers)
    assert res_users.status_code == 200
    assert len(res_users.json()) >= 9

    # 3. Consulta no AD
    res_ad = client.get("/api/admin/ad-user-search/admin", headers=headers)
    assert res_ad.status_code == 200
    assert res_ad.json()["exists"] is True


def test_administrador_crud_global_qualquer_unidade(client, setup_cenario):
    """
    Verifica se o ADMINISTRADOR consegue realizar CRUD em qualquer unidade do hospital.
    """
    headers = get_headers(setup_cenario, "admin.teste")
    u_compras = setup_cenario["unidades"]["compras"]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # 1. CREATE na unidade de Compras
    payload = {
        "unidade_id": u_compras,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Processo licitatório mapeado pelo Admin",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": "Risco de desabastecimento por fornecedor",
                "causa": "Atraso na entrega",
                "consequencia": "Paralisação de insumos",
                "categoria": "OPERACIONAL",
                "avaliacao": {"probabilidade": 3, "impacto": 4, "controles": []}
            }
        ]
    }
    res_create = client.post("/api/riscos", json=payload, headers=headers)
    assert res_create.status_code == 200
    ficha_id = res_create.json()["id"]

    # 2. READ detalhes da ficha criada
    res_read = client.get(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_read.status_code == 200
    ficha_data = res_read.json()
    assert ficha_data["pode_editar"] is True
    assert ficha_data["pode_excluir"] is True

    # 3. UPDATE na ficha
    payload["id"] = ficha_id
    payload["entrega_processo"] = "Processo licitatório atualizado pelo Admin"
    res_update = client.post("/api/riscos", json=payload, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["entrega_processo"] == "Processo licitatório atualizado pelo Admin"

    # 4. DELETE na ficha
    res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_del.status_code == 200

    # Confirma exclusão
    assert client.get(f"/api/riscos/{ficha_id}", headers=headers).status_code == 404


# =============================================================================
# 2. BLOQUEIO DE ROTAS ADMINISTRATIVAS PARA NÃO-ADMINISTRADORES
# =============================================================================

@pytest.mark.parametrize("username", [
    "gestor.superintendencia",
    "gestor.gerencia",
    "gestor.divisao",
    "gestor.setor",
    "gestor.compras",
    "gestor.auditoria",
    "usuario.consulta"
])
def test_bloqueio_endpoints_admin_para_demais_perfis(client, setup_cenario, username):
    """
    Garante que gestores de unidade e usuários de consulta NUNCA acessem rotas de administração.
    """
    headers = get_headers(setup_cenario, username)

    assert client.get("/api/admin-only-data", headers=headers).status_code == 403
    assert client.get("/api/admin/usuarios", headers=headers).status_code == 403
    assert client.post("/api/admin/usuarios", json={}, headers=headers).status_code == 403
    assert client.post("/api/admin/usuarios/1/visibilidade", json={"unidades_ids": []}, headers=headers).status_code == 403
    assert client.get("/api/admin/ad-user-search/admin", headers=headers).status_code == 403


# =============================================================================
# 3. CRUD SETORIAL PRÓPRIO PARA CADA NÍVEL HIERÁRQUICO
# =============================================================================

@pytest.mark.parametrize("gestor_user,unidade_key", [
    ("gestor.superintendencia", "super"),
    ("gestor.gerencia", "gad"),
    ("gestor.divisao", "daf"),
    ("gestor.setor", "sad"),
    ("gestor.compras", "compras"),
    ("gestor.auditoria", "auditoria"),
])
def test_crud_proprio_setorial_todas_as_unidades(client, setup_cenario, gestor_user, unidade_key):
    """
    Certifica que, qualquer que seja a unidade organizacional (Superintendência, Gerências,
    Divisões, Setores, Unidades ou Órgãos Independentes), o gestor tenha acesso
    a operações completas de CRUD referentes ao SEU PRÓPRIO setor.
    """
    headers = get_headers(setup_cenario, gestor_user)
    u_id = setup_cenario["unidades"][unidade_key]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # 1. CREATE para a sua própria unidade
    payload = {
        "unidade_id": u_id,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": f"Entrega setorial mapeada por {gestor_user}",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": f"Evento de risco específico de {unidade_key}",
                "causa": "Causa operacional interna",
                "consequencia": "Impacto no setor",
                "categoria": "OPERACIONAL",
                "avaliacao": {"probabilidade": 2, "impacto": 3, "controles": []}
            }
        ]
    }
    res_create = client.post("/api/riscos", json=payload, headers=headers)
    assert res_create.status_code == 200, f"Falha no CREATE para {gestor_user}: {res_create.text}"
    ficha_id = res_create.json()["id"]

    # 2. READ da ficha criada pelo próprio setor
    res_read = client.get(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_read.status_code == 200
    ficha_data = res_read.json()
    assert ficha_data["pode_editar"] is True, f"{gestor_user} deveria ter pode_editar=True em seu próprio setor"
    assert ficha_data["pode_excluir"] is True, f"{gestor_user} deveria ter pode_excluir=True em seu próprio setor"

    # 3. UPDATE na ficha do próprio setor
    payload["id"] = ficha_id
    payload["entrega_processo"] = f"Entrega setorial revisada por {gestor_user}"
    res_update = client.post("/api/riscos", json=payload, headers=headers)
    assert res_update.status_code == 200, f"Falha no UPDATE para {gestor_user}: {res_update.text}"
    assert res_update.json()["entrega_processo"] == f"Entrega setorial revisada por {gestor_user}"

    # 4. DELETE na ficha do próprio setor
    res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers)
    assert res_del.status_code == 200, f"Falha no DELETE para {gestor_user}: {res_del.text}"

    # Confirma exclusão
    assert client.get(f"/api/riscos/{ficha_id}", headers=headers).status_code == 404


# =============================================================================
# 4. UNIDADES SUPERIORES x SUBORDINADAS: APENAS VISUALIZAÇÃO
# =============================================================================

def test_unidades_superiores_apenas_visualizam_fichas_subordinadas(client, setup_cenario):
    """
    Testa rigorosamente a hierarquia administrativa GAD -> DAF -> SAD -> Compras:
    1. A Unidade de Compras (subordinada folha) cria uma ficha de risco do seu setor.
    2. Instâncias superiores (SAD, DAF, GAD) conseguem VISUALIZAR a ficha (GET = 200).
    3. As propriedades retornadas para as instâncias superiores são 'pode_editar=False' e 'pode_excluir=False'.
    4. Tentativas de EDITAR a ficha por SAD, DAF ou GAD são rejeitadas com HTTP 403 Forbidden.
    5. Tentativas de EXCLUIR a ficha por SAD, DAF ou GAD são rejeitadas com HTTP 403 Forbidden.
    6. Tentativa de exclusão em LOTE por SAD, DAF ou GAD é rejeitada com HTTP 403 Forbidden.
    """
    headers_compras = get_headers(setup_cenario, "gestor.compras")
    headers_sad = get_headers(setup_cenario, "gestor.setor")
    headers_daf = get_headers(setup_cenario, "gestor.divisao")
    headers_gad = get_headers(setup_cenario, "gestor.gerencia")

    u_compras = setup_cenario["unidades"]["compras"]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # 1. Compras cria sua própria ficha
    payload = {
        "unidade_id": u_compras,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Aquisição de Insumos Hospitalares Críticos",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": "Fracasso licitatório por desinteresse de mercado",
                "causa": "Preço de referência defasado",
                "consequencia": "Desabastecimento das enfermarias",
                "categoria": "OPERACIONAL",
                "avaliacao": {"probabilidade": 3, "impacto": 4, "controles": []}
            }
        ]
    }
    res_create = client.post("/api/riscos", json=payload, headers=headers_compras)
    assert res_create.status_code == 200
    ficha_id = res_create.json()["id"]

    # 2. Instâncias superiores conseguem VISUALIZAR (GET) a ficha
    superiores = [
        ("gestor.setor", headers_sad, "Setor (SAD)"),
        ("gestor.divisao", headers_daf, "Divisão (DAF)"),
        ("gestor.gerencia", headers_gad, "Gerência (GAD)")
    ]

    for nome_u, headers_sup, rotulo in superiores:
        res_view = client.get(f"/api/riscos/{ficha_id}", headers=headers_sup)
        assert res_view.status_code == 200, f"{rotulo} deveria conseguir visualizar a ficha da subordinada"
        data_view = res_view.json()
        assert data_view["id"] == ficha_id
        # Garante que as flags de permissão de escrita venham como False
        assert data_view["pode_editar"] is False, f"{rotulo} NÃO deve ter permissão de edição em ficha subordinada"
        assert data_view["pode_excluir"] is False, f"{rotulo} NÃO deve ter permissão de exclusão em ficha subordinada"

    # 3. Tentativas de EDIÇÃO por instâncias superiores -> DEVEM SER BLOQUEADAS (403)
    payload_edicao = dict(payload)
    payload_edicao["id"] = ficha_id
    payload_edicao["entrega_processo"] = "Tentativa indevida de edição pela chefia superior"

    for nome_u, headers_sup, rotulo in superiores:
        res_edit = client.post("/api/riscos", json=payload_edicao, headers=headers_sup)
        assert res_edit.status_code == 403, f"{rotulo} NÃO deveria conseguir editar ficha da subordinada (esperado 403)"
        assert "Apenas gestores da própria unidade podem editar" in res_edit.json()["detail"]

    # 4. Tentativas de EXCLUSÃO INDIVIDUAL por instâncias superiores -> DEVEM SER BLOQUEADAS (403)
    for nome_u, headers_sup, rotulo in superiores:
        res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers_sup)
        assert res_del.status_code == 403, f"{rotulo} NÃO deveria conseguir excluir ficha da subordinada (esperado 403)"
        assert "Apenas gestores da própria unidade podem deletar" in res_del.json()["detail"]

    # 5. Tentativa de EXCLUSÃO EM LOTE contendo ficha subordinada -> DEVE SER BLOQUEADA (403)
    for nome_u, headers_sup, rotulo in superiores:
        res_lote = client.post("/api/riscos/excluir-lote", json={"ids": [ficha_id]}, headers=headers_sup)
        assert res_lote.status_code == 403, f"{rotulo} NÃO deveria conseguir excluir em lote ficha subordinada (esperado 403)"

    # 6. Apenas a própria Unidade de Compras (ou o Administrador) consegue excluir
    res_del_ok = client.delete(f"/api/riscos/{ficha_id}", headers=headers_compras)
    assert res_del_ok.status_code == 200, "A própria unidade de Compras deve conseguir deletar sua ficha"


def test_superintendencia_apenas_visualiza_fichas_de_unidades_subordinadas(client, setup_cenario):
    """
    Testa a relação entre Superintendência e suas unidades subordinadas (ex: UGERC / Governança):
    - A ficha criada pela unidade subordinada pode ser visualizada pela Superintendência.
    - A Superintendência NÃO pode editar nem excluir a ficha da subordinada.
    """
    headers_super = get_headers(setup_cenario, "gestor.superintendencia")
    headers_admin = get_headers(setup_cenario, "admin.teste")

    u_ugerc = setup_cenario["unidades"]["ugerc"]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # Admin cria uma ficha simulando ser da unidade subordinada (UGERC)
    payload = {
        "unidade_id": u_ugerc,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Plano de Gestão de Riscos Institucional",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": "Não adesão setorial à metodologia",
                "causa": "Falta de treinamento",
                "consequencia": "Subnotificação de riscos",
                "categoria": "COMPLIANCE",
                "avaliacao": {"probabilidade": 2, "impacto": 3, "controles": []}
            }
        ]
    }
    create_res = client.post("/api/riscos", json=payload, headers=headers_admin)
    assert create_res.status_code == 200
    ficha_id = create_res.json()["id"]

    # 1. Superintendência consegue VISUALIZAR a ficha da sua subordinada
    res_view = client.get(f"/api/riscos/{ficha_id}", headers=headers_super)
    assert res_view.status_code == 200
    data_view = res_view.json()
    assert data_view["pode_editar"] is False
    assert data_view["pode_excluir"] is False

    # 2. Superintendência NÃO consegue EDITAR a ficha da subordinada
    payload["id"] = ficha_id
    payload["entrega_processo"] = "Tentativa de alteração pela Superintendência"
    res_edit = client.post("/api/riscos", json=payload, headers=headers_super)
    assert res_edit.status_code == 403
    assert "Apenas gestores da própria unidade podem editar" in res_edit.json()["detail"]

    # 3. Superintendência NÃO consegue EXCLUIR a ficha da subordinada
    res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers_super)
    assert res_del.status_code == 403
    assert "Apenas gestores da própria unidade podem deletar" in res_del.json()["detail"]

    # Limpeza
    client.delete(f"/api/riscos/{ficha_id}", headers=headers_admin)


# =============================================================================
# 5. ISOLAMENTO ENTRE RAMOS HIERÁRQUICOS DIFERENTES
# =============================================================================

def test_isolamento_entre_ramos_organizacionais_distintos(client, setup_cenario):
    """
    Garante que gestores de um ramo (ex: Gerência Administrativa) não consigam
    visualizar, alterar nem excluir fichas de outro ramo (ex: UTI Adulto / Atenção à Saúde).
    """
    headers_gad = get_headers(setup_cenario, "gestor.gerencia")
    headers_admin = get_headers(setup_cenario, "admin.teste")

    u_uti = setup_cenario["unidades"]["uti"]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # Admin cria uma ficha na UTI
    payload = {
        "unidade_id": u_uti,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Atendimento Intensivo Seguro",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": "Falha no suprimento de oxigênio",
                "causa": "Vazamento em duto",
                "consequencia": "Risco à vida dos pacientes",
                "categoria": "ASSISTENCIAL",
                "avaliacao": {"probabilidade": 1, "impacto": 5, "controles": []}
            }
        ]
    }
    create_res = client.post("/api/riscos", json=payload, headers=headers_admin)
    assert create_res.status_code == 200
    ficha_id = create_res.json()["id"]

    # Gestor da Gerência Administrativa (GAD) tenta acessar a ficha da UTI Adulto
    # 1. Tentativa de LEITURA direta -> 403 Forbidden
    res_view = client.get(f"/api/riscos/{ficha_id}", headers=headers_gad)
    assert res_view.status_code == 403
    assert "Acesso não autorizado para esta unidade" in res_view.json()["detail"]

    # 2. Tentativa de LISTAGEM filtrando pela UTI -> Lista deve vir vazia
    res_list = client.get(f"/api/riscos?unidade_id={u_uti}", headers=headers_gad)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 0

    # 3. Tentativa de EDIÇÃO -> 403 Forbidden
    payload["id"] = ficha_id
    res_edit = client.post("/api/riscos", json=payload, headers=headers_gad)
    assert res_edit.status_code == 403

    # 4. Tentativa de EXCLUSÃO -> 403 Forbidden
    res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers_gad)
    assert res_del.status_code == 403

    # Limpeza
    client.delete(f"/api/riscos/{ficha_id}", headers=headers_admin)


# =============================================================================
# 6. MATRIZ DE VISIBILIDADE CRUZADA (CONCESSÃO EXTRA)
# =============================================================================

def test_matriz_visibilidade_cruzada_permite_apenas_leitura(client, setup_cenario):
    """
    Testa o gestor da Auditoria com concessão adicional para Compras:
    - Consegue VISUALIZAR a ficha de Compras.
    - NÃO consegue EDITAR nem DELETAR a ficha de Compras.
    """
    headers_vis = get_headers(setup_cenario, "gestor.visibilidade")
    headers_compras = get_headers(setup_cenario, "gestor.compras")

    u_compras = setup_cenario["unidades"]["compras"]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # Compras cria a ficha
    payload = {
        "unidade_id": u_compras,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Licitação de Equipamentos Biomédicos",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": "Impugnação de edital",
                "causa": "Especificação restritiva",
                "consequencia": "Atraso na contratação",
                "categoria": "COMPLIANCE",
                "avaliacao": {"probabilidade": 2, "impacto": 3, "controles": []}
            }
        ]
    }
    create_res = client.post("/api/riscos", json=payload, headers=headers_compras)
    assert create_res.status_code == 200
    ficha_id = create_res.json()["id"]

    # 1. Usuário com visibilidade cruzada consegue VISUALIZAR
    res_view = client.get(f"/api/riscos/{ficha_id}", headers=headers_vis)
    assert res_view.status_code == 200
    data_view = res_view.json()
    assert data_view["pode_editar"] is False
    assert data_view["pode_excluir"] is False

    # 2. Usuário com visibilidade cruzada tenta EDITAR -> Bloqueado com 403
    payload["id"] = ficha_id
    payload["entrega_processo"] = "Tentativa de alteração com visibilidade cruzada"
    res_edit = client.post("/api/riscos", json=payload, headers=headers_vis)
    assert res_edit.status_code == 403

    # 3. Usuário com visibilidade cruzada tenta EXCLUIR -> Bloqueado com 403
    res_del = client.delete(f"/api/riscos/{ficha_id}", headers=headers_vis)
    assert res_del.status_code == 403

    # Limpeza
    client.delete(f"/api/riscos/{ficha_id}", headers=headers_compras)


# =============================================================================
# 7. TESTES DO PERFIL CONSULTA_SETORIAL (SOMENTE-LEITURA)
# =============================================================================

def test_perfil_consulta_setorial_somente_leitura_completo(client, setup_cenario):
    """
    Verifica que o perfil CONSULTA_SETORIAL:
    1. Consegue consultar listagem e detalhes de fichas da sua unidade autorizada.
    2. Consegue consultar os indicadores da matriz de risco.
    3. É rigorosamente impedido de CRIAR novas fichas (POST sem id -> 403).
    4. É rigorosamente impedido de EDITAR fichas existentes (POST com id -> 403).
    5. É rigorosamente impedido de EXCLUIR fichas individuais (DELETE -> 403).
    6. É rigorosamente impedido de EXCLUIR fichas em lote (POST excluir-lote -> 403).
    """
    headers_consulta = get_headers(setup_cenario, "usuario.consulta")
    headers_compras = get_headers(setup_cenario, "gestor.compras")

    u_compras = setup_cenario["unidades"]["compras"]
    proc_id = setup_cenario["processo_id"]
    pil_id = setup_cenario["pilar_id"]

    # Gestor de Compras cria uma ficha
    payload = {
        "unidade_id": u_compras,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Ficha para teste de somente-leitura",
        "status": "RASCUNHO",
        "eventos": [
            {
                "descricao_evento": "Evento para consulta",
                "causa": "Causa de teste",
                "consequencia": "Consequência de teste",
                "categoria": "OPERACIONAL",
                "avaliacao": {"probabilidade": 2, "impacto": 2, "controles": []}
            }
        ]
    }
    create_res = client.post("/api/riscos", json=payload, headers=headers_compras)
    assert create_res.status_code == 200
    ficha_id = create_res.json()["id"]

    # 1. READ: Consegue listar fichas autorizadas da sua unidade
    res_list = client.get(f"/api/riscos?unidade_id={u_compras}", headers=headers_consulta)
    assert res_list.status_code == 200
    assert any(m["id"] == ficha_id for m in res_list.json())

    # 2. READ: Consegue visualizar os detalhes completos da ficha
    res_view = client.get(f"/api/riscos/{ficha_id}", headers=headers_consulta)
    assert res_view.status_code == 200
    data_view = res_view.json()
    assert data_view["pode_editar"] is False
    assert data_view["pode_excluir"] is False

    # 3. READ: Consegue acessar as estatísticas do painel da matriz
    res_matriz = client.get(f"/api/riscos/painel/matriz?unidade_id={u_compras}", headers=headers_consulta)
    assert res_matriz.status_code == 200

    # 4. WRITE: Tenta CRIAR um novo risco -> DEVE SER BLOQUEADO (403)
    payload_novo = {
        "unidade_id": u_compras,
        "processo_id": proc_id,
        "pilar_estrategico_id": pil_id,
        "entrega_processo": "Tentativa de cadastro por usuário de consulta",
        "status": "RASCUNHO",
        "eventos": []
    }
    res_create_block = client.post("/api/riscos", json=payload_novo, headers=headers_consulta)
    assert res_create_block.status_code == 403, "Usuário de consulta NÃO deve conseguir criar novos riscos"
    assert "Apenas gestores de unidade possuem permissão" in res_create_block.json()["detail"]

    # 5. WRITE: Tenta EDITAR a ficha existente -> DEVE SER BLOQUEADO (403)
    payload["id"] = ficha_id
    payload["entrega_processo"] = "Tentativa de alteração por usuário de consulta"
    res_edit_block = client.post("/api/riscos", json=payload, headers=headers_consulta)
    assert res_edit_block.status_code == 403, "Usuário de consulta NÃO deve conseguir editar riscos"

    # 6. WRITE: Tenta EXCLUIR individualmente a ficha -> DEVE SER BLOQUEADO (403)
    res_del_block = client.delete(f"/api/riscos/{ficha_id}", headers=headers_consulta)
    assert res_del_block.status_code == 403, "Usuário de consulta NÃO deve conseguir excluir riscos"

    # 7. WRITE: Tenta EXCLUIR em lote -> DEVE SER BLOQUEADO (403)
    res_lote_block = client.post("/api/riscos/excluir-lote", json={"ids": [ficha_id]}, headers=headers_consulta)
    assert res_lote_block.status_code == 403, "Usuário de consulta NÃO deve conseguir excluir riscos em lote"

    # Limpeza com o gestor de compras
    client.delete(f"/api/riscos/{ficha_id}", headers=headers_compras)
