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


def calcular_severidade_risco(probabilidade: int, impacto: int, num_controles: int) -> Dict[str, Any]:
    """
    Motor oficial de cálculo do Risco Inerente e Risco Residual (Guia UGERC.001 / REDCap).
    """
    p = max(1, min(5, probabilidade))
    i = max(1, min(5, impacto))
    inerente = p * i

    # Fator de Mitigação pelos controles existentes:
    # 0 -> 1.0; 1 -> 0.8; 2 -> 0.6; 3 -> 0.4; 4+ -> 0.2
    if num_controles <= 0:
        fator = 1.0
    elif num_controles == 1:
        fator = 0.8
    elif num_controles == 2:
        fator = 0.6
    elif num_controles == 3:
        fator = 0.4
    else:
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


async def listar_mapeamentos(
    db: AsyncSession,
    current_user: Dict[str, Any],
    unidade_id: Optional[int] = None,
    status_filtro: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista mapeamentos de risco respeitando o controle de visibilidade setorial."""
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
            prob = int(av_data.get("probabilidade", 1))
            imp = int(av_data.get("impacto", 1))
            controles_list = av_data.get("controles", [])
            num_controles = len(controles_list)

            calculos = calcular_severidade_risco(prob, imp, num_controles)

            av = AvaliacaoRisco(
                evento_risco_id=ev.id,
                probabilidade=calculos["probabilidade"],
                impacto=calculos["impacto"],
                risco_inerente=calculos["risco_inerente"],
                fator_mitigacao=calculos["fator_mitigacao"],
                risco_residual=calculos["risco_residual"],
                classificacao=calculos["classificacao"],
                acima_apetite=calculos["acima_apetite"]
            )
            db.add(av)
            await db.flush()

            # Controles
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


async def obter_estatisticas_matriz(
    db: AsyncSession,
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Retorna dados agregados para preenchimento dos quadrantes da matriz 5x5."""
    unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)

    stmt = (
        select(AvaliacaoRisco.probabilidade, AvaliacaoRisco.impacto, AvaliacaoRisco.classificacao, func.count(AvaliacaoRisco.id))
        .join(EventoRisco, AvaliacaoRisco.evento_risco_id == EventoRisco.id)
        .join(MapeamentoRisco, EventoRisco.mapeamento_id == MapeamentoRisco.id)
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
