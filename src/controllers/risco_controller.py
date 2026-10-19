"""
Controller do Domínio de Gestão de Riscos (HC-UFPE / EBSERH)
============================================================
Implementa o motor de cálculo da matriz de risco 5x5, validações do Guia
da UGERC, controle de acesso setorial e ciclo de vida dos mapeamentos.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..models.risco import (
    MapeamentoRisco,
    EventoRisco,
    AvaliacaoRisco,
    ControleExistente,
    PlanoAcao5W2H,
    PlanoContingencia,
)
from ..models.usuario import Usuario, UsuarioUnidadeVisibilidade
from ..models.unidade_organizacional import UnidadeOrganizacional
from ..models.processo import Processo, Macroprocesso, PilarEstrategico
from ..helpers.audit_helper import registrar_auditoria


TABELA_CONTROLES_INTERNOS = {
    "INEXISTENTE": {
        "fnc": 1.0,
        "classificacao_tcu": "Muito Alto",
        "rotulo": "Inexistente",
        "definicao": "Controles inexistentes, mal desenhados ou mal implementados, isto é, não funcionais."
    },
    "FRACO": {
        "fnc": 0.8,
        "classificacao_tcu": "Alto",
        "rotulo": "Fraco",
        "definicao": "Controles têm abordagens ad hoc, tendem a ser aplicados caso a caso, a responsabilidade é individual, havendo elevado grau de confiança no conhecimento das pessoas."
    },
    "MEDIANO": {
        "fnc": 0.6,
        "classificacao_tcu": "Médio",
        "rotulo": "Mediano",
        "definicao": "Controles implementados mitigam alguns aspectos do risco, mas não contemplam todos os aspectos relevantes do risco devido a deficiências no desenho ou nas ferramentas utilizadas."
    },
    "SATISFATORIO": {
        "fnc": 0.4,
        "classificacao_tcu": "Baixo",
        "rotulo": "Satisfatório",
        "definicao": "Controles implementados e sustentados por ferramentas adequadas e, embora passíveis de aperfeiçoamento, mitigam o risco satisfatoriamente."
    },
    "FORTE": {
        "fnc": 0.2,
        "classificacao_tcu": "Muito Baixo",
        "rotulo": "Forte",
        "definicao": "Controles implementados podem ser considerados a 'melhor prática', mitigando todos os aspectos relevantes do risco."
    }
}


def calcular_severidade_risco(
    probabilidade: int,
    impacto: int,
    nivel_controle: Optional[str] = "INEXISTENTE",
    fator_mitigacao: Optional[float] = None,
    num_controles: int = 0
) -> Dict[str, Any]:
    """
    Motor oficial de cálculo do Risco Inerente e Risco Residual (Guia UGERC.001 / Tabela 3).
    O Fator de Mitigação dos Controles é determinado exclusivamente pelo nível selecionado:
    - INEXISTENTE: 1.0 (Muito Alto)
    - FRACO: 0.8 (Alto)
    - MEDIANO: 0.6 (Médio)
    - SATISFATORIO: 0.4 (Baixo)
    - FORTE: 0.2 (Muito Baixo)
    O número de medidas de controle descritas NÃO altera o Fator de Mitigação.
    """
    p = max(1, min(5, probabilidade)) if probabilidade else 1
    i = max(1, min(5, impacto)) if impacto else 1
    inerente = p * i

    nivel = (nivel_controle or "").strip().upper()
    if nivel in TABELA_CONTROLES_INTERNOS:
        fator = TABELA_CONTROLES_INTERNOS[nivel]["fnc"]
    elif fator_mitigacao is not None:
        fator = float(fator_mitigacao)
        nivel = "INEXISTENTE"
        for k, v in TABELA_CONTROLES_INTERNOS.items():
            if abs(v["fnc"] - fator) < 0.05:
                nivel = k
                break
    else:
        # Fallback de compatibilidade se informado apenas num_controles
        if num_controles <= 0:
            nivel = "INEXISTENTE"
            fator = 1.0
        elif num_controles == 1:
            nivel = "FRACO"
            fator = 0.8
        elif num_controles == 2:
            nivel = "MEDIANO"
            fator = 0.6
        elif num_controles == 3:
            nivel = "SATISFATORIO"
            fator = 0.4
        else:
            nivel = "FORTE"
            fator = 0.2

    residual = round(inerente * fator)

    # Classificação conforme apetite a risco do HC-UFPE:
    # <= 2: BAIXO | <= 7: MEDIO | <= 14: ALTO | <= 25: EXTREMO
    if residual <= 2:
        classificacao = "BAIXO"
    elif residual <= 7:
        classificacao = "MEDIO"
    elif residual <= 14:
        classificacao = "ALTO"
    else:
        classificacao = "EXTREMO"

    # Tolerância deliberada pelo Colegiado Executivo: até 7.99
    # Riscos com residual > 7 estão acima do apetite a risco e exigem tratamento
    acima_apetite = (residual > 7)

    return {
        "probabilidade": p,
        "impacto": i,
        "risco_inerente": inerente,
        "nivel_controle": nivel,
        "fator_mitigacao": fator,
        "risco_residual": residual,
        "classificacao": classificacao,
        "acima_apetite": acima_apetite
    }


def calcular_coordenada_residual(p_in: int, i_in: int, residual_alvo: Optional[Union[int, float]]) -> tuple[int, int]:
    """
    Calcula a coordenada (P_res, I_res) na Matriz de Riscos para exibição em Visão Residual.
    Busca o par (p, i) com p <= p_in e i <= i_in cujo produto seja o mais próximo do residual alvo,
    com prioridade para redução de probabilidade (controles preventivos).
    Se o residual está dentro do apetite a risco (<= 7 ou <= 7.99), a célula DEVE obrigatoriamente
    estar na zona de tolerância (produto <= 7) e ter o valor mais próximo do residual (ex: 6 para residual 7).
    Um residual dentro do apetite NUNCA deve ser representado numa célula na região acima do apetite (produto > 7).
    """
    if not p_in or not i_in:
        return (1, 1)
    if residual_alvo is None:
        return (p_in, i_in)

    inerente = p_in * i_in
    raw_target = float(residual_alvo)
    target = round(raw_target)

    # Limite institucional de tolerância: até 7.99 (Muito Baixo, Baixo ou Médio)
    residual_dentro_apetite = (target <= 7 or raw_target <= 7.99)

    if target >= inerente and (not residual_dentro_apetite or inerente <= 7):
        return (p_in, i_in)

    melhor_p, melhor_i = p_in, i_in
    menor_diff = float("inf")
    melhor_score = float("inf")

    for p in range(p_in, 0, -1):
        for i in range(i_in, 0, -1):
            prod = p * i

            # REGRA INSTITUCIONAL MANDATÓRIA:
            # Se o residual está dentro do apetite (<= 7), a célula DEVE obrigatoriamente estar na zona de tolerância (prod <= 7)
            if residual_dentro_apetite and prod > 7:
                continue

            # Se o residual está acima do apetite (> 7) e inerente > 7, a célula DEVE obrigatoriamente estar acima da tolerância (prod > 7)
            if not residual_dentro_apetite and prod <= 7 and inerente > 7:
                continue

            # Se tem redução de risco, prefere coordenadas diferentes da inerente se houver alternativas
            if p == p_in and i == i_in and inerente > target and menor_diff != float("inf"):
                continue

            diff = abs(prod - target)
            dist_p = abs(p - (target / i_in))
            dist_i = abs(i - i_in)
            score = diff * 100 + dist_p * 10 + dist_i

            if diff < menor_diff or (diff == menor_diff and score < melhor_score):
                menor_diff = diff
                melhor_score = score
                melhor_p = p
                melhor_i = i

    # Fallback 1: se nenhuma célula atendeu ao score, mas o residual está dentro do apetite, busca na área de tolerância (prod <= 7)
    if menor_diff == float("inf") or (residual_dentro_apetite and melhor_p * melhor_i > 7):
        menor_diff = float("inf")
        for p in range(p_in, 0, -1):
            for i in range(i_in, 0, -1):
                prod = p * i
                if residual_dentro_apetite and prod > 7:
                    continue
                if not residual_dentro_apetite and prod <= 7 and inerente > 7:
                    continue
                diff = abs(prod - target)
                if diff < menor_diff:
                    menor_diff = diff
                    melhor_p = p
                    melhor_i = i

    # Fallback 2: garantia estrita de apetite
    if residual_dentro_apetite and melhor_p * melhor_i > 7:
        menor_diff = float("inf")
        for p in range(5, 0, -1):
            for i in range(5, 0, -1):
                prod = p * i
                if prod <= 7:
                    diff = abs(prod - target)
                    if diff < menor_diff:
                        menor_diff = diff
                        melhor_p = p
                        melhor_i = i
    elif not residual_dentro_apetite and inerente > 7 and melhor_p * melhor_i <= 7:
        menor_diff = float("inf")
        for p in range(5, 0, -1):
            for i in range(5, 0, -1):
                prod = p * i
                if prod > 7:
                    diff = abs(prod - target)
                    if diff < menor_diff:
                        menor_diff = diff
                        melhor_p = p
                        melhor_i = i

    return (melhor_p, melhor_i)




async def obter_unidades_autorizadas(db: AsyncSession, current_user: Dict[str, Any]) -> Optional[List[int]]:
    """
    Retorna a lista de IDs de unidades que o usuário tem permissão para visualizar.
    Retorna None se o usuário for ADMINISTRADOR (acesso irrestrito a todas as unidades).
    Chefes de setor, divisão e gerência visualizam sua unidade principal e todas as unidades vinculadas/subordinadas no organograma.
    Gestores só visualizam outras unidades sem vínculo no organograma se concedido via matriz de visibilidade.
    """
    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])

    if perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"]:
        return None  # Acesso total

    stmt = (
        select(Usuario)
        .options(selectinload(Usuario.visibilidades_concedidas))
        .where(Usuario.username == username)
    )
    result = await db.execute(stmt)
    u_obj = result.scalar_one_or_none()
    if not u_obj or not u_obj.ativo:
        return []

    if u_obj.perfil == "ADMINISTRADOR":
        return None

    from .processo_controller import obter_subunidades_recursivas
    unidades_permitidas = set()

    # 1. Unidade principal do usuário e todas as suas unidades vinculadas no organograma
    if u_obj.unidade_principal_id:
        sub_ids = await obter_subunidades_recursivas(db, u_obj.unidade_principal_id)
        unidades_permitidas.update(sub_ids)

    # 2. Unidades concedidas através da matriz de visibilidade (e suas subunidades vinculadas)
    for vis in u_obj.visibilidades_concedidas:
        sub_vis = await obter_subunidades_recursivas(db, vis.unidade_id)
        unidades_permitidas.update(sub_vis)

    return list(unidades_permitidas)


def validar_todas_etapas_submissao(dados: Dict[str, Any]):
    """
    Valida rigorosamente se todas as 5 etapas da metodologia UGERC estão devidamente preenchidas
    antes de permitir tramitar para o status SUBMETIDO.
    """
    erros = []

    # Etapa 1: Contexto e Processo
    if not dados.get("unidade_id"):
        erros.append("Etapa 1: Unidade Organizacional é obrigatória.")
    if not dados.get("processo_id"):
        erros.append("Etapa 1: Processo hospitalar é obrigatório.")
    if not str(dados.get("entrega_processo", "")).strip():
        erros.append("Etapa 1: Entrega do Processo / Produto Entregue é obrigatória.")
    if dados.get("possui_projeto"):
        if not str(dados.get("nome_projeto", "")).strip():
            erros.append("Etapa 1: Nome do Projeto é obrigatório quando 'Possui Projeto' está ativado.")
        if not dados.get("pilar_estrategico_id"):
            erros.append("Etapa 1: Pilar do Mapa Estratégico é obrigatório quando 'Possui Projeto' está ativado.")

    # Etapa 2: Identificação do Risco
    eventos = dados.get("eventos", [])
    if not eventos:
        erros.append("Etapa 2: É necessário cadastrar ao menos um Evento de Risco.")
    else:
        for idx, ev in enumerate(eventos, start=1):
            if not str(ev.get("categoria", "")).strip():
                erros.append(f"Etapa 2: Categoria do Risco do evento #{idx} é obrigatória.")
            if not str(ev.get("causa", "")).strip():
                erros.append(f"Etapa 2: Causa do evento #{idx} é obrigatória.")
            if not str(ev.get("descricao_evento", "")).strip():
                erros.append(f"Etapa 2: Descrição do Evento de Risco #{idx} é obrigatória.")
            if not str(ev.get("consequencia", "")).strip():
                erros.append(f"Etapa 2: Consequência do evento #{idx} é obrigatória.")

            # Etapa 3: Avaliação e Controles
            av = ev.get("avaliacao", {})
            prob = int(av.get("probabilidade", 0) or 0)
            imp = int(av.get("impacto", 0) or 0)
            if prob < 1 or prob > 5:
                erros.append(f"Etapa 3: Probabilidade do evento #{idx} deve ser entre 1 e 5.")
            if imp < 1 or imp > 5:
                erros.append(f"Etapa 3: Impacto do evento #{idx} deve ser entre 1 e 5.")

            nivel_c = str(av.get("nivel_controle", "INEXISTENTE")).strip().upper()
            if nivel_c not in TABELA_CONTROLES_INTERNOS:
                erros.append(f"Etapa 3: Nível de controles internos do evento #{idx} é inválido.")

            controles = av.get("controles", [])
            if nivel_c != "INEXISTENTE":
                if not controles:
                    erros.append(f"Etapa 3: Como o nível de controle selecionado é '{nivel_c}', é obrigatório cadastrar ao menos uma medida de controle existente no evento #{idx}.")
                for c_idx, c in enumerate(controles, start=1):
                    c_desc = c if isinstance(c, str) else c.get("descricao_controle", "")
                    if not str(c_desc).strip():
                        erros.append(f"Etapa 3: A descrição do controle #{c_idx} do evento #{idx} não pode ficar em branco.")

            # Etapa 4 e 5: Severidade e Respostas aos Riscos
            calc = calcular_severidade_risco(prob, imp, nivel_controle=nivel_c, fator_mitigacao=av.get("fator_mitigacao"))
            if calc["classificacao"] in ("ALTO", "EXTREMO"):
                planos_acao = ev.get("planos_acao", [])
                if not planos_acao:
                    erros.append(f"Etapa 5: Risco classificado como {calc['classificacao']} ({calc['risco_residual']}). É obrigatório registrar ao menos um Plano de Ação para o evento #{idx}.")

            # Valida preenchimento dos planos de ação existentes
            for pa_idx, pa in enumerate(ev.get("planos_acao", []), start=1):
                if not str(pa.get("o_que", "")).strip():
                    erros.append(f"Etapa 5: O que fazer do Plano de Ação #{pa_idx} é obrigatório.")
                if not str(pa.get("como", "")).strip():
                    erros.append(f"Etapa 5: Como fazer do Plano de Ação #{pa_idx} é obrigatório.")
                if not str(pa.get("quem", "")).strip():
                    erros.append(f"Etapa 5: Quem (Responsável) do Plano de Ação #{pa_idx} é obrigatório.")
                if not str(pa.get("data_inicio", "")).strip() or not str(pa.get("data_termino", "")).strip():
                    erros.append(f"Etapa 5: Período (Início e Término) do Plano de Ação #{pa_idx} é obrigatório.")

            # Valida preenchimento dos planos de contingência existentes
            for pc_idx, pc in enumerate(ev.get("planos_contingencia", []), start=1):
                if not str(pc.get("gatilho", "")).strip():
                    erros.append(f"Etapa 5: Gatilho do Plano de Contingência #{pc_idx} é obrigatório.")
                if not str(pc.get("responsavel", "")).strip():
                    erros.append(f"Etapa 5: Responsável pela ativação do Plano de Contingência #{pc_idx} é obrigatório.")
                if not str(pc.get("o_que", "")).strip():
                    erros.append(f"Etapa 5: O que fazer do Plano de Contingência #{pc_idx} é obrigatório.")
                if not str(pc.get("como", "")).strip():
                    erros.append(f"Etapa 5: Como fazer do Plano de Contingência #{pc_idx} é obrigatório.")

    if erros:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível submeter para a UGERC pois há pendências: " + "; ".join(erros)
        )


async def listar_mapeamentos(
    db: AsyncSession,
    current_user: Dict[str, Any],
    unidade_id: Optional[int] = None,
    status_filtro: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista mapeamentos de risco respeitando o controle de visibilidade setorial e regras de exclusão."""
    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    subunidades_usuario = set()
    if u_obj and u_obj.unidade_principal_id:
        from .processo_controller import obter_subunidades_recursivas
        sub_ids = await obter_subunidades_recursivas(db, u_obj.unidade_principal_id)
        subunidades_usuario = set(sub_ids)

    stmt = (
        select(MapeamentoRisco)
        .options(
            selectinload(MapeamentoRisco.unidade),
            selectinload(MapeamentoRisco.processo).selectinload(Processo.macroprocesso),
            selectinload(MapeamentoRisco.pilar_estrategico),
            selectinload(MapeamentoRisco.criado_por),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.avaliacao).selectinload(AvaliacaoRisco.controles),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.planos_acao),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.planos_contingencia),
        )
        .order_by(MapeamentoRisco.atualizado_em.desc())
    )

    filtros = []
    if unidades_autorizadas is not None:
        filtros.append(MapeamentoRisco.unidade_id.in_(unidades_autorizadas))
    if unidade_id:
        filtros.append(MapeamentoRisco.unidade_id == unidade_id)
    if status_filtro:
        filtros.append(MapeamentoRisco.status == status_filtro)

    if filtros:
        stmt = stmt.where(and_(*filtros))

    result = await db.execute(stmt)
    mapeamentos = result.scalars().all()

    retorno = []
    for m in mapeamentos:
        # Regra de visibilidade para processos cadastrados na categoria 'Outro':
        # Visíveis apenas para o setor onde foi criado e instâncias hierárquicas superiores (ancestrais).
        if m.processo_outro and not is_admin:
            if m.unidade_id not in subunidades_usuario:
                continue

        # Regra de permissão de edição e exclusão:
        # Administradores podem editar e deletar quaisquer fichas;
        # Gestores podem editar e deletar apenas fichas da sua própria unidade (setor principal);
        # Instâncias superiores não podem editar ou deletar fichas de unidades inferiores, apenas visualizá-las.
        pode_editar = False
        pode_excluir = False
        if is_admin:
            pode_editar = True
            pode_excluir = True
        elif u_obj and u_obj.perfil == "GESTOR_UNIDADE" and u_obj.unidade_principal_id == m.unidade_id:
            pode_editar = True
            pode_excluir = True

        ev_data = []
        for ev in m.eventos:
            av = ev.avaliacao
            ev_data.append({
                "id": ev.id,
                "descricao_evento": ev.descricao_evento,
                "causa": ev.causa,
                "consequencia": ev.consequencia,
                "categoria": ev.categoria,
                "avaliacao": {
                    "probabilidade": av.probabilidade if av else 1,
                    "impacto": av.impacto if av else 1,
                    "risco_inerente": av.risco_inerente if av else 1,
                    "fator_mitigacao": av.fator_mitigacao if av else 1.0,
                    "risco_residual": av.risco_residual if av else 1,
                    "classificacao": av.classificacao if av else "BAIXO",
                    "acima_apetite": av.acima_apetite if av else False,
                    "controles_count": len(av.controles) if av else 0
                } if av else None,
                "planos_acao_count": len(ev.planos_acao),
                "planos_contingencia_count": len(ev.planos_contingencia)
            })

        retorno.append({
            "id": m.id,
            "unidade": {"id": m.unidade.id, "nome": m.unidade.nome, "sigla": m.unidade.sigla} if m.unidade else None,
            "processo": {"id": m.processo.id, "nome": m.processo.nome, "macroprocesso": m.processo.macroprocesso.nome} if m.processo else None,
            "possui_projeto": m.possui_projeto,
            "nome_projeto": m.nome_projeto,
            "pilar_estrategico": {"id": m.pilar_estrategico.id, "nome": m.pilar_estrategico.nome} if m.pilar_estrategico else None,
            "entrega_processo": m.entrega_processo,
            "processo_outro": m.processo_outro,
            "status": m.status,
            "versao": getattr(m, "versao", 1) or 1,
            "tag_versao": getattr(m, "tag_versao", "v1.0 (Original)") or "v1.0 (Original)",
            "submetido_em": m.submetido_em.isoformat() if getattr(m, "submetido_em", None) else None,
            "criado_por": {
                "id": m.criado_por.id,
                "nome": m.criado_por.nome_completo,
                "username": m.criado_por.username
            } if getattr(m, "criado_por", None) else None,
            "criado_em": m.criado_em.isoformat() if m.criado_em else None,
            "observacoes_ugerc": m.observacoes_ugerc,
            "eventos": ev_data,
            "pode_editar": pode_editar,
            "pode_excluir": pode_excluir,
            "atualizado_em": m.atualizado_em.isoformat() if m.atualizado_em else None
        })

    return retorno


async def obter_mapeamento_por_id(
    db: AsyncSession,
    mapeamento_id: int,
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Retorna detalhes completos de um mapeamento com verificação de autorização."""
    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)

    stmt = (
        select(MapeamentoRisco)
        .options(
            selectinload(MapeamentoRisco.unidade),
            selectinload(MapeamentoRisco.processo).selectinload(Processo.macroprocesso),
            selectinload(MapeamentoRisco.pilar_estrategico),
            selectinload(MapeamentoRisco.criado_por),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.avaliacao).selectinload(AvaliacaoRisco.controles),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.planos_acao),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.planos_contingencia),
        )
        .where(MapeamentoRisco.id == mapeamento_id)
    )
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento de risco não encontrado")

    if unidades_autorizadas is not None and m.unidade_id not in unidades_autorizadas:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado para esta unidade")

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    return _formatar_mapeamento_detalhado(m, is_admin, u_obj)


def _formatar_mapeamento_detalhado(
    m: MapeamentoRisco,
    is_admin: bool,
    u_obj: Optional[Usuario]
) -> Dict[str, Any]:
    eventos_detalhados = []
    for ev in m.eventos:
        av = ev.avaliacao
        eventos_detalhados.append({
            "id": ev.id,
            "descricao_evento": ev.descricao_evento,
            "causa": ev.causa,
            "consequencia": ev.consequencia,
            "categoria": ev.categoria,
            "avaliacao": {
                "id": av.id,
                "probabilidade": av.probabilidade,
                "impacto": av.impacto,
                "risco_inerente": av.risco_inerente,
                "nivel_controle": getattr(av, "nivel_controle", None) or ("INEXISTENTE" if av.fator_mitigacao == 1.0 else "FRACO" if av.fator_mitigacao == 0.8 else "MEDIANO" if av.fator_mitigacao == 0.6 else "SATISFATORIO" if av.fator_mitigacao == 0.4 else "FORTE"),
                "fator_mitigacao": av.fator_mitigacao,
                "risco_residual": av.risco_residual,
                "classificacao": av.classificacao,
                "acima_apetite": av.acima_apetite,
                "controles": [{"id": c.id, "descricao_controle": c.descricao_controle} for c in av.controles]
            } if av else None,
            "planos_acao": [
                {
                    "id": pa.id,
                    "tipo_resposta": pa.tipo_resposta,
                    "o_que": pa.o_que,
                    "como": pa.como,
                    "quem": pa.quem,
                    "data_inicio": pa.data_inicio,
                    "data_termino": pa.data_termino,
                    "status": pa.status
                }
                for pa in ev.planos_acao
            ],
            "planos_contingencia": [
                {
                    "id": pc.id,
                    "gatilho": pc.gatilho,
                    "o_que": pc.o_que,
                    "como": pc.como,
                    "responsavel": pc.responsavel
                }
                for pc in ev.planos_contingencia
            ]
        })

    pode_editar = False
    pode_excluir = False
    if is_admin:
        pode_editar = True
        pode_excluir = True
    elif u_obj and u_obj.perfil == "GESTOR_UNIDADE" and u_obj.unidade_principal_id == m.unidade_id:
        pode_editar = True
        pode_excluir = True

    return {
        "id": m.id,
        "unidade_id": m.unidade_id,
        "unidade_nome": m.unidade.nome if m.unidade else "",
        "unidade_sigla": m.unidade.sigla if m.unidade else "",
        "unidade": {
            "id": m.unidade.id,
            "nome": m.unidade.nome,
            "sigla": m.unidade.sigla
        } if m.unidade else None,
        "processo_id": m.processo_id,
        "processo_nome": m.processo.nome if m.processo else "",
        "processo_outro": m.processo_outro,
        "macroprocesso_nome": m.processo.macroprocesso.nome if m.processo and m.processo.macroprocesso else "",
        "processo": {
            "id": m.processo.id,
            "nome": m.processo.nome,
            "macroprocesso": {
                "id": m.processo.macroprocesso.id,
                "nome": m.processo.macroprocesso.nome
            } if m.processo.macroprocesso else None
        } if m.processo else None,
        "possui_projeto": m.possui_projeto,
        "nome_projeto": m.nome_projeto,
        "pilar_estrategico_id": m.pilar_estrategico_id,
        "pilar_estrategico_nome": m.pilar_estrategico.nome if m.pilar_estrategico else "",
        "pilar_estrategico": {
            "id": m.pilar_estrategico.id,
            "nome": m.pilar_estrategico.nome,
            "numero": getattr(m.pilar_estrategico, "numero", None)
        } if m.pilar_estrategico else None,
        "entrega_processo": m.entrega_processo,
        "status": m.status,
        "versao": getattr(m, "versao", 1) or 1,
        "tag_versao": getattr(m, "tag_versao", "v1.0 (Original)") or "v1.0 (Original)",
        "submetido_em": m.submetido_em.isoformat() if getattr(m, "submetido_em", None) else None,
        "criado_por": {
            "id": m.criado_por.id,
            "nome": m.criado_por.nome_completo,
            "username": m.criado_por.username
        } if getattr(m, "criado_por", None) else None,
        "observacoes_ugerc": m.observacoes_ugerc,
        "eventos": eventos_detalhados,
        "pode_editar": pode_editar,
        "pode_excluir": pode_excluir,
        "criado_em": m.criado_em.isoformat() if m.criado_em else None,
        "atualizado_em": m.atualizado_em.isoformat() if m.atualizado_em else None
    }


async def obter_mapeamentos_detalhados_em_lote(
    db: AsyncSession,
    mapeamento_ids: List[int],
    current_user: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Retorna detalhes completos de múltiplos mapeamentos para impressão ou exportação em lote."""
    if not mapeamento_ids:
        return []

    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)

    stmt = (
        select(MapeamentoRisco)
        .options(
            selectinload(MapeamentoRisco.unidade),
            selectinload(MapeamentoRisco.processo).selectinload(Processo.macroprocesso),
            selectinload(MapeamentoRisco.pilar_estrategico),
            selectinload(MapeamentoRisco.criado_por),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.avaliacao).selectinload(AvaliacaoRisco.controles),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.planos_acao),
            selectinload(MapeamentoRisco.eventos).selectinload(EventoRisco.planos_contingencia),
        )
        .where(MapeamentoRisco.id.in_(mapeamento_ids))
        .order_by(MapeamentoRisco.id.asc())
    )
    result = await db.execute(stmt)
    mapeamentos = result.scalars().all()

    if unidades_autorizadas is not None:
        mapeamentos = [m for m in mapeamentos if m.unidade_id in unidades_autorizadas]

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    return [_formatar_mapeamento_detalhado(m, is_admin, u_obj) for m in mapeamentos]


async def salvar_mapeamento(
    db: AsyncSession,
    dados: Dict[str, Any],
    current_user: Dict[str, Any],
    ip_origem: Optional[str] = None
) -> Dict[str, Any]:
    """Salva um mapeamento de risco (criação ou edição, como Rascunho ou Submetido)."""
    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)
    unidade_id = dados.get("unidade_id")
    if not unidade_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unidade organizacional é obrigatória")

    if unidades_autorizadas is not None and unidade_id not in unidades_autorizadas:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para registrar riscos nesta unidade")

    # Validação obrigatória de todas as 5 etapas caso a ação seja SUBMETER para a UGERC
    if dados.get("status") == "SUBMETIDO":
        validar_todas_etapas_submissao(dados)

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if not u_obj and username:
        nome_disp = current_user.get("displayName")
        if isinstance(nome_disp, list):
            nome_disp = nome_disp[0] if nome_disp else username
        nome_default = str(nome_disp or ("Administrador Geral" if is_admin else username))

        email_disp = current_user.get("email")
        if isinstance(email_disp, list):
            email_disp = email_disp[0] if email_disp else f"{username}@hcpe.ebserh.gov.br"
        email_default = str(email_disp or f"{username}@hcpe.ebserh.gov.br")

        u_obj = Usuario(
            username=username,
            nome_completo=nome_default,
            email=email_default,
            perfil="ADMINISTRADOR" if is_admin else "GESTOR_UNIDADE",
            unidade_principal_id=unidade_id or 1,
            ativo=True
        )
        db.add(u_obj)
        await db.flush()

    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    mapeamento_id = dados.get("id")
    novo = False

    if mapeamento_id:
        stmt = (
            select(MapeamentoRisco)
            .options(selectinload(MapeamentoRisco.eventos))
            .where(MapeamentoRisco.id == mapeamento_id)
        )
        res = await db.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento não encontrado para edição")

        # Regra de edição:
        # Administradores podem editar quaisquer fichas.
        # Gestores podem editar apenas fichas de sua própria unidade principal.
        # Instâncias superiores não podem editar fichas de unidades inferiores, apenas visualizá-las.
        if not is_admin:
            if not u_obj or u_obj.perfil != "GESTOR_UNIDADE" or u_obj.unidade_principal_id != m.unidade_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Apenas gestores da própria unidade podem editar fichas de riscos da sua unidade. Chefias de instâncias superiores possuem permissão apenas para visualização."
                )

        m.unidade_id = unidade_id
        m.processo_id = dados.get("processo_id")
        m.processo_outro = dados.get("processo_outro")
        m.possui_projeto = dados.get("possui_projeto", False)
        m.nome_projeto = dados.get("nome_projeto") if m.possui_projeto else None
        m.pilar_estrategico_id = dados.get("pilar_estrategico_id")
        m.entrega_processo = dados.get("entrega_processo", "")
        
        novo_status = dados.get("status", m.status)
        if m.status == "SUBMETIDO" and novo_status == "SUBMETIDO":
            # Re-submissão de ficha editada: incrementa versão e atualiza data de submissão
            m.versao = (getattr(m, "versao", 1) or 1) + 1
            m.tag_versao = f"v{m.versao}.0 (Revisada)"
            m.submetido_em = datetime.now(timezone.utc)
        elif novo_status == "SUBMETIDO":
            # Primeira submissão (de Rascunho para Submetido)
            m.versao = getattr(m, "versao", 1) or 1
            m.tag_versao = "v1.0 (Original)"
            m.submetido_em = datetime.now(timezone.utc)
        elif novo_status == "RASCUNHO":
            m.tag_versao = "Rascunho"

        m.status = novo_status
        m.atualizado_em = datetime.now(timezone.utc)
    else:
        novo = True
        from .processo_controller import obter_subunidades_recursivas
        if not is_admin:
            if not u_obj or not u_obj.unidade_principal_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário sem unidade principal configurada.")
            sub_ids_usuario = await obter_subunidades_recursivas(db, u_obj.unidade_principal_id)
            if unidade_id not in sub_ids_usuario:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você só pode cadastrar novos mapeamentos de risco para a sua própria unidade organizacional ou para unidades subordinadas no organograma."
                )

        novo_status = dados.get("status", "RASCUNHO")
        submetido_data = datetime.now(timezone.utc) if novo_status == "SUBMETIDO" else None
        tag_v = "v1.0 (Original)" if novo_status == "SUBMETIDO" else "Rascunho"

        m = MapeamentoRisco(
            unidade_id=unidade_id,
            processo_id=dados.get("processo_id"),
            processo_outro=dados.get("processo_outro"),
            possui_projeto=dados.get("possui_projeto", False),
            nome_projeto=dados.get("nome_projeto") if dados.get("possui_projeto") else None,
            pilar_estrategico_id=dados.get("pilar_estrategico_id"),
            entrega_processo=dados.get("entrega_processo", ""),
            status=novo_status,
            versao=1,
            tag_versao=tag_v,
            submetido_em=submetido_data,
            criado_por_id=u_obj.id if u_obj else None,
            criado_em=datetime.now(timezone.utc),
            atualizado_em=datetime.now(timezone.utc)
        )
        db.add(m)
        await db.flush()

    # Processa eventos de risco enviados
    eventos_in = dados.get("eventos", [])
    if eventos_in:
        # Se for edição, remove eventos antigos para reconstrução limpa
        if not novo:
            for old_ev in m.eventos:
                await db.delete(old_ev)
            await db.flush()

        for ev_data in eventos_in:
            ev = EventoRisco(
                mapeamento_id=m.id,
                descricao_evento=ev_data.get("descricao_evento", ""),
                causa=ev_data.get("causa", ""),
                consequencia=ev_data.get("consequencia", ""),
                categoria=ev_data.get("categoria", "OPERACIONAL")
            )
            db.add(ev)
            await db.flush()

            # Avaliação numérica
            av_data = ev_data.get("avaliacao", {})
            prob = int(av_data.get("probabilidade", 1) or 1)
            imp = int(av_data.get("impacto", 1) or 1)
            nivel_c = str(av_data.get("nivel_controle", "INEXISTENTE")).strip().upper()
            fator_in = av_data.get("fator_mitigacao")
            controles_list = av_data.get("controles", []) if nivel_c != "INEXISTENTE" else []

            calculos = calcular_severidade_risco(prob, imp, nivel_controle=nivel_c, fator_mitigacao=fator_in)

            av = AvaliacaoRisco(
                evento_risco_id=ev.id,
                probabilidade=calculos["probabilidade"],
                impacto=calculos["impacto"],
                risco_inerente=calculos["risco_inerente"],
                nivel_controle=calculos["nivel_controle"],
                fator_mitigacao=calculos["fator_mitigacao"],
                risco_residual=calculos["risco_residual"],
                classificacao=calculos["classificacao"],
                acima_apetite=calculos["acima_apetite"]
            )
            db.add(av)
            await db.flush()

            # Controles (apenas se nível não for Inexistente)
            if nivel_c != "INEXISTENTE":
                for c_desc in controles_list:
                    desc_str = c_desc if isinstance(c_desc, str) else c_desc.get("descricao_controle", "")
                    if desc_str.strip():
                        ctrl = ControleExistente(avaliacao_id=av.id, descricao_controle=desc_str.strip())
                        db.add(ctrl)


            # Planos de Ação 5W2H
            for pa in ev_data.get("planos_acao", []):
                plano = PlanoAcao5W2H(
                    evento_risco_id=ev.id,
                    tipo_resposta=pa.get("tipo_resposta", "MITIGAR"),
                    o_que=pa.get("o_que", ""),
                    como=pa.get("como", ""),
                    quem=pa.get("quem", ""),
                    data_inicio=str(pa.get("data_inicio", "")),
                    data_termino=str(pa.get("data_termino", "")),
                    status=pa.get("status", "PLANEJADO")
                )
                db.add(plano)

            # Planos de Contingência
            for pc in ev_data.get("planos_contingencia", []):
                pcont = PlanoContingencia(
                    evento_risco_id=ev.id,
                    gatilho=pc.get("gatilho", ""),
                    o_que=pc.get("o_que", ""),
                    como=pc.get("como", ""),
                    responsavel=pc.get("responsavel", "")
                )
                db.add(pcont)

    await registrar_auditoria(
        db=db,
        usuario=current_user.get("username", "sistema"),
        categoria="NEGOCIO_CLINICO",
        acao="CRIAR_MAPEAMENTO_RISCO" if novo else "ATUALIZAR_MAPEAMENTO_RISCO",
        recurso=f"mapeamento_risco:{m.id}",
        dados_novos={"status": m.status, "unidade_id": m.unidade_id, "processo_id": m.processo_id},
        ip_origem=ip_origem
    )

    await db.commit()
    await db.refresh(m)
    return await obter_mapeamento_por_id(db, m.id, current_user)


async def excluir_mapeamento(
    db: AsyncSession,
    mapeamento_id: int,
    current_user: Dict[str, Any],
    ip_origem: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exclui um mapeamento de risco do sistema com validação rigorosa de permissão:
    - Administradores podem deletar quaisquer fichas de riscos mapeados.
    - Para os demais casos, apenas gestores podem deletar fichas de riscos mapeados da sua unidade.
    - Chefias de instâncias superiores não poderão deletar fichas de unidades vinculadas.
    """
    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt = (
        select(MapeamentoRisco)
        .options(
            selectinload(MapeamentoRisco.unidade),
            selectinload(MapeamentoRisco.processo),
            selectinload(MapeamentoRisco.eventos)
        )
        .where(MapeamentoRisco.id == mapeamento_id)
    )
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento de risco não encontrado.")

    # Consulta perfil e unidade principal atual do usuário no banco
    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    if not is_admin:
        # Apenas gestores da própria unidade podem deletar fichas de riscos da sua unidade.
        if not u_obj or u_obj.perfil != "GESTOR_UNIDADE" or u_obj.unidade_principal_id != m.unidade_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas gestores da própria unidade podem deletar fichas de riscos mapeados da sua unidade. Chefias de instâncias superiores ou vinculadas não possuem permissão para deletar."
            )

    dados_anteriores = {
        "id": m.id,
        "unidade_id": m.unidade_id,
        "unidade_nome": m.unidade.nome if m.unidade else None,
        "processo_id": m.processo_id,
        "processo_nome": m.processo.nome if m.processo else None,
        "processo_outro": m.processo_outro,
        "status": m.status
    }

    await registrar_auditoria(
        db=db,
        usuario=username or "sistema",
        categoria="NEGOCIO_CLINICO",
        acao="EXCLUIR_MAPEAMENTO_RISCO",
        recurso=f"mapeamento_risco:{m.id}",
        dados_anteriores=dados_anteriores,
        dados_novos=None,
        ip_origem=ip_origem
    )

    await db.delete(m)
    await db.commit()

    return {"message": "Ficha de risco excluída com sucesso.", "id": mapeamento_id}


async def excluir_mapeamentos_em_lote(
    db: AsyncSession,
    mapeamento_ids: List[int],
    current_user: Dict[str, Any],
    ip_origem: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exclui múltiplos mapeamentos de risco em lote com validação rigorosa de permissão para cada ficha:
    - Administradores podem deletar quaisquer fichas selecionadas.
    - Gestores de unidade podem deletar apenas fichas pertencentes à sua própria unidade.
    - Chefias de instâncias superiores não poderão deletar fichas de unidades vinculadas.
    - Registra trilha de auditoria para cada ficha excluída.
    """
    if not mapeamento_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma ficha foi selecionada para exclusão."
        )

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    stmt = (
        select(MapeamentoRisco)
        .options(
            selectinload(MapeamentoRisco.unidade),
            selectinload(MapeamentoRisco.processo),
            selectinload(MapeamentoRisco.eventos)
        )
        .where(MapeamentoRisco.id.in_(mapeamento_ids))
    )
    res = await db.execute(stmt)
    mapeamentos = res.scalars().all()

    if not mapeamentos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma das fichas informadas foi encontrada."
        )

    # Validar autorização para cada ficha
    for m in mapeamentos:
        if not is_admin:
            if not u_obj or u_obj.perfil != "GESTOR_UNIDADE" or u_obj.unidade_principal_id != m.unidade_id:
                nome_u = m.unidade.nome if m.unidade else f"ID {m.unidade_id}"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão negada para excluir a ficha #{m.id} da unidade '{nome_u}'. Apenas o gestor da própria unidade ou administradores podem excluir."
                )

    total_excluidos = 0
    ids_excluidos = []
    for m in mapeamentos:
        dados_anteriores = {
            "id": m.id,
            "unidade_id": m.unidade_id,
            "unidade_nome": m.unidade.nome if m.unidade else None,
            "processo_id": m.processo_id,
            "processo_nome": m.processo.nome if m.processo else None,
            "processo_outro": m.processo_outro,
            "status": m.status
        }

        await registrar_auditoria(
            db=db,
            usuario=username or "sistema",
            categoria="NEGOCIO_CLINICO",
            acao="EXCLUIR_MAPEAMENTO_RISCO",
            recurso=f"mapeamento_risco:{m.id}",
            dados_anteriores=dados_anteriores,
            dados_novos=None,
            ip_origem=ip_origem
        )

        await db.delete(m)
        total_excluidos += 1
        ids_excluidos.append(m.id)

    await db.commit()

    return {
        "message": f"{total_excluidos} ficha(s) de risco excluída(s) com sucesso.",
        "total_excluidos": total_excluidos,
        "ids": ids_excluidos
    }


async def obter_estatisticas_matriz(
    db: AsyncSession,
    current_user: Dict[str, Any],
    unidade_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retorna dados agregados para preenchimento dos quadrantes da matriz 5x5,
    cards de totais e indicadores por Gerência (SUP, GAS, GAD e GEP).
    Regra: Considera APENAS fichas de riscos com status SUBMETIDO.
    Respeita o escopo de visibilidade setorial e hierárquica do usuário logado.
    """
    from .processo_controller import obter_subunidades_recursivas

    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)

    filtros_stmt = [MapeamentoRisco.status == "SUBMETIDO"]
    unidades_filtro: Optional[List[int]] = None

    if unidade_id:
        unidades_filtro = await obter_subunidades_recursivas(db, unidade_id)
        if unidades_autorizadas is not None:
            unidades_filtro = [uid for uid in unidades_filtro if uid in unidades_autorizadas]
            if not unidades_filtro:
                filtros_stmt.append(MapeamentoRisco.unidade_id == -1)
            else:
                filtros_stmt.append(MapeamentoRisco.unidade_id.in_(unidades_filtro))
        else:
            filtros_stmt.append(MapeamentoRisco.unidade_id.in_(unidades_filtro))
    elif unidades_autorizadas is not None:
        if not unidades_autorizadas:
            filtros_stmt.append(MapeamentoRisco.unidade_id == -1)
        else:
            filtros_stmt.append(MapeamentoRisco.unidade_id.in_(unidades_autorizadas))

    stmt = (
        select(AvaliacaoRisco.probabilidade, AvaliacaoRisco.impacto, AvaliacaoRisco.risco_residual, AvaliacaoRisco.classificacao)
        .join(EventoRisco, AvaliacaoRisco.evento_risco_id == EventoRisco.id)
        .join(MapeamentoRisco, EventoRisco.mapeamento_id == MapeamentoRisco.id)
        .where(and_(*filtros_stmt))
    )

    res = await db.execute(stmt)
    linhas = res.all()

    quadrantes = {}
    totais = {"BAIXO": 0, "MEDIO": 0, "ALTO": 0, "EXTREMO": 0, "TOTAL": 0, "ACIMA_APETITE": 0}

    for p, i, res_val, classif in linhas:
        # Padrão institucional: Visão Residual na Matriz de Riscos
        p_res, i_res = calcular_coordenada_residual(p, i, res_val)
        chave = f"{p_res}_{i_res}"
        quadrantes[chave] = quadrantes.get(chave, 0) + 1
        totais[classif] = totais.get(classif, 0) + 1
        totais["TOTAL"] += 1
        if classif in ["ALTO", "EXTREMO"]:
            totais["ACIMA_APETITE"] += 1

    # Verificação de permissão para visualização dos cards de gerências:
    # Apenas administradores ou usuários com todas as unidades concedidas na matriz de visibilidade
    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).options(selectinload(Usuario.visibilidades_concedidas)).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    stmt_total_u = select(func.count(UnidadeOrganizacional.id)).where(UnidadeOrganizacional.ativa == True)
    res_total_u = await db.execute(stmt_total_u)
    total_unidades_sistema = res_total_u.scalar() or 0

    pode_ver_gerencias = False
    if is_admin:
        pode_ver_gerencias = True
    elif u_obj:
        qtd_vis = len(u_obj.visibilidades_concedidas) if u_obj.visibilidades_concedidas else 0
        if total_unidades_sistema > 0 and qtd_vis >= total_unidades_sistema:
            pode_ver_gerencias = True

    # Contagem agrupada por Gerências do HC-UFPE (SUP, GAS, GAD e GEP)
    gerencias_meta = [
        {"sigla": "SUP", "nome": "Superintendência"},
        {"sigla": "GAS", "nome": "Gerência de Atenção à Saúde"},
        {"sigla": "GAD", "nome": "Gerência Administrativa"},
        {"sigla": "GEP", "nome": "Gerência de Ensino e Pesquisa"}
    ]

    stmt_top = select(UnidadeOrganizacional.id, UnidadeOrganizacional.sigla).where(
        UnidadeOrganizacional.sigla.in_(["SUP", "GAS", "GAD", "GEP"])
    )
    res_top = await db.execute(stmt_top)
    top_map = {sigla: uid for uid, sigla in res_top.all()}

    gerencias_resultado = []
    for g in gerencias_meta:
        sigla = g["sigla"]
        nome = g["nome"]
        ger_id = top_map.get(sigla)
        dados_ger = {
            "id": ger_id,
            "sigla": sigla,
            "nome": nome,
            "total": 0,
            "baixo": 0,
            "medio": 0,
            "alto": 0,
            "extremo": 0,
            "total_unidades": 0,
            "unidades_com_risco": 0,
            "percentual_mapeado": 0.0,
            "unidades_detalhes": []
        }
        if ger_id:
            sub_ids_ger = await obter_subunidades_recursivas(db, ger_id)
            if unidades_autorizadas is not None:
                sub_ids_ger = [uid for uid in sub_ids_ger if uid in unidades_autorizadas]

            # Para relação de unidades e cálculo de cobertura, desconsidera a própria gerência (foca nas unidades subordinadas)
            sub_ids_subordinadas = [uid for uid in sub_ids_ger if uid != ger_id]

            dados_ger["total_unidades"] = len(sub_ids_subordinadas)
            if sub_ids_subordinadas:
                stmt_map = (
                    select(func.count(func.distinct(MapeamentoRisco.unidade_id)))
                    .where(
                        MapeamentoRisco.status == "SUBMETIDO",
                        MapeamentoRisco.unidade_id.in_(sub_ids_subordinadas)
                    )
                )
                res_map = await db.execute(stmt_map)
                qtd_unidades_com_risco = res_map.scalar() or 0
                dados_ger["unidades_com_risco"] = qtd_unidades_com_risco
                if len(sub_ids_subordinadas) > 0:
                    dados_ger["percentual_mapeado"] = round((qtd_unidades_com_risco / len(sub_ids_subordinadas)) * 100, 1)

                # Detalhamento de cada unidade da gerência com sua contagem de riscos (desconsiderando a própria gerência)
                stmt_detalhes = (
                    select(
                        UnidadeOrganizacional.id,
                        UnidadeOrganizacional.nome,
                        UnidadeOrganizacional.sigla,
                        func.count(MapeamentoRisco.id).filter(MapeamentoRisco.status == "SUBMETIDO").label("total_riscos")
                    )
                    .outerjoin(MapeamentoRisco, UnidadeOrganizacional.id == MapeamentoRisco.unidade_id)
                    .where(UnidadeOrganizacional.id.in_(sub_ids_subordinadas))
                    .group_by(UnidadeOrganizacional.id, UnidadeOrganizacional.nome, UnidadeOrganizacional.sigla)
                    .order_by(
                        func.count(MapeamentoRisco.id).filter(MapeamentoRisco.status == "SUBMETIDO").desc(),
                        UnidadeOrganizacional.nome.asc()
                    )
                )
                res_detalhes = await db.execute(stmt_detalhes)
                dados_ger["unidades_detalhes"] = [
                    {
                        "id": row.id,
                        "nome": row.nome,
                        "sigla": row.sigla,
                        "total_riscos": row.total_riscos or 0
                    }
                    for row in res_detalhes.all()
                ]

            sub_ids = sub_ids_ger
            if unidade_id and unidades_filtro is not None:
                sub_ids = [uid for uid in sub_ids if uid in unidades_filtro]

            if sub_ids:
                stmt_g = (
                    select(AvaliacaoRisco.classificacao, func.count(AvaliacaoRisco.id))
                    .join(EventoRisco, AvaliacaoRisco.evento_risco_id == EventoRisco.id)
                    .join(MapeamentoRisco, EventoRisco.mapeamento_id == MapeamentoRisco.id)
                    .where(
                        MapeamentoRisco.status == "SUBMETIDO",
                        MapeamentoRisco.unidade_id.in_(sub_ids)
                    )
                    .group_by(AvaliacaoRisco.classificacao)
                )
                res_g = await db.execute(stmt_g)
                for classif, qtd in res_g.all():
                    if classif == "BAIXO":
                        dados_ger["baixo"] += qtd
                    elif classif == "MEDIO":
                        dados_ger["medio"] += qtd
                    elif classif == "ALTO":
                        dados_ger["alto"] += qtd
                    elif classif == "EXTREMO":
                        dados_ger["extremo"] += qtd
                    dados_ger["total"] += qtd

        gerencias_resultado.append(dados_ger)

    return {
        "quadrantes": quadrantes,
        "totais": totais,
        "gerencias": gerencias_resultado,
        "pode_ver_gerencias": pode_ver_gerencias
    }


