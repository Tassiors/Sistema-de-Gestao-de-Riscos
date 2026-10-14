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
    O Fator Numérico do Controle (FNC) é determinado exclusivamente pelo nível selecionado:
    - INEXISTENTE: 1.0 (Muito Alto)
    - FRACO: 0.8 (Alto)
    - MEDIANO: 0.6 (Médio)
    - SATISFATORIO: 0.4 (Baixo)
    - FORTE: 0.2 (Muito Baixo)
    O número de medidas de controle descritas NÃO altera o FNC.
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



async def obter_unidades_autorizadas(db: AsyncSession, current_user: Dict[str, Any]) -> Optional[List[int]]:
    """
    Retorna a lista de IDs de unidades que o usuário tem permissão para visualizar.
    Retorna None se o usuário for ADMINISTRADOR (acesso irrestrito a todas as unidades).
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
    if not u_obj:
        return []

    unidades_permitidas = set()
    if u_obj.unidade_principal_id:
        unidades_permitidas.add(u_obj.unidade_principal_id)
    for vis in u_obj.visibilidades_concedidas:
        unidades_permitidas.add(vis.unidade_id)

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
                    erros.append(f"Etapa 5: Risco classificado como {calc['classificacao']} ({calc['risco_residual']}). É obrigatório registrar ao menos um Plano de Ação 5W2H para o evento #{idx}.")

            # Valida preenchimento dos planos de ação existentes
            for pa_idx, pa in enumerate(ev.get("planos_acao", []), start=1):
                if not str(pa.get("o_que", "")).strip():
                    erros.append(f"Etapa 5: O que fazer (What) do Plano de Ação #{pa_idx} é obrigatório.")
                if not str(pa.get("como", "")).strip():
                    erros.append(f"Etapa 5: Como fazer (How) do Plano de Ação #{pa_idx} é obrigatório.")
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
            "unidade": {"id": m.unidade.id, "nome": m.unidade.nome} if m.unidade else None,
            "processo": {"id": m.processo.id, "nome": m.processo.nome, "macroprocesso": m.processo.macroprocesso.nome} if m.processo else None,
            "possui_projeto": m.possui_projeto,
            "nome_projeto": m.nome_projeto,
            "pilar_estrategico": {"id": m.pilar_estrategico.id, "nome": m.pilar_estrategico.nome} if m.pilar_estrategico else None,
            "entrega_processo": m.entrega_processo,
            "processo_outro": m.processo_outro,
            "status": m.status,
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

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

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
        "processo_id": m.processo_id,
        "processo_nome": m.processo.nome if m.processo else "",
        "processo_outro": m.processo_outro,
        "macroprocesso_nome": m.processo.macroprocesso.nome if m.processo and m.processo.macroprocesso else "",
        "possui_projeto": m.possui_projeto,
        "nome_projeto": m.nome_projeto,
        "pilar_estrategico_id": m.pilar_estrategico_id,
        "pilar_estrategico_nome": m.pilar_estrategico.nome if m.pilar_estrategico else "",
        "entrega_processo": m.entrega_processo,
        "status": m.status,
        "observacoes_ugerc": m.observacoes_ugerc,
        "eventos": eventos_detalhados,
        "pode_editar": pode_editar,
        "pode_excluir": pode_excluir,
        "criado_em": m.criado_em.isoformat() if m.criado_em else None,
        "atualizado_em": m.atualizado_em.isoformat() if m.atualizado_em else None
    }


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
        m.status = dados.get("status", m.status)
        m.atualizado_em = datetime.now(timezone.utc)
    else:
        novo = True
        if not is_admin:
            if not u_obj or u_obj.perfil != "GESTOR_UNIDADE" or u_obj.unidade_principal_id != unidade_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você só pode cadastrar novos mapeamentos de risco para a sua própria unidade organizacional."
                )

        m = MapeamentoRisco(
            unidade_id=unidade_id,
            processo_id=dados.get("processo_id"),
            processo_outro=dados.get("processo_outro"),
            possui_projeto=dados.get("possui_projeto", False),
            nome_projeto=dados.get("nome_projeto") if dados.get("possui_projeto") else None,
            pilar_estrategico_id=dados.get("pilar_estrategico_id"),
            entrega_processo=dados.get("entrega_processo", ""),
            status=dados.get("status", "RASCUNHO"),
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


async def obter_estatisticas_matriz(
    db: AsyncSession,
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Retorna dados agregados para preenchimento dos quadrantes da matriz 5x5 e cards.
    Regra: Considera APENAS fichas de riscos com status SUBMETIDO.
    """
    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)

    stmt = (
        select(AvaliacaoRisco.probabilidade, AvaliacaoRisco.impacto, AvaliacaoRisco.classificacao, func.count(AvaliacaoRisco.id))
        .join(EventoRisco, AvaliacaoRisco.evento_risco_id == EventoRisco.id)
        .join(MapeamentoRisco, EventoRisco.mapeamento_id == MapeamentoRisco.id)
        .where(MapeamentoRisco.status == "SUBMETIDO")
    )

    if unidades_autorizadas is not None:
        stmt = stmt.where(MapeamentoRisco.unidade_id.in_(unidades_autorizadas))

    stmt = stmt.group_by(AvaliacaoRisco.probabilidade, AvaliacaoRisco.impacto, AvaliacaoRisco.classificacao)
    res = await db.execute(stmt)
    linhas = res.all()

    quadrantes = {}
    totais = {"BAIXO": 0, "MEDIO": 0, "ALTO": 0, "EXTREMO": 0, "TOTAL": 0, "ACIMA_APETITE": 0}

    for p, i, classif, qtd in linhas:
        chave = f"{p}_{i}"
        quadrantes[chave] = quadrantes.get(chave, 0) + qtd
        totais[classif] = totais.get(classif, 0) + qtd
        totais["TOTAL"] += qtd
        if classif in ["ALTO", "EXTREMO"]:
            totais["ACIMA_APETITE"] += qtd

    return {
        "quadrantes": quadrantes,
        "totais": totais
    }

