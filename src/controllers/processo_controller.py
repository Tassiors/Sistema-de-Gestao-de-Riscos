"""
Controller para Gestão do Catálogo de Processos e Hierarquia Organizacional
=============================================================================
Implementa a resolução hierárquica onde Setores, Divisões e Gerências herdam
os processos de suas subunidades, e todas as unidades recebem os Processos Comuns.
"""

import re
from typing import List, Dict, Any, Optional, Set
from sqlalchemy import select, or_, and_, distinct
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.processo import Macroprocesso, Processo, PilarEstrategico, ProcessoUnidade
from ..models.unidade_organizacional import UnidadeOrganizacional
from ..models.usuario import Usuario
from ..models.risco import MapeamentoRisco


async def obter_subunidades_recursivas(db: AsyncSession, unidade_id: int) -> List[int]:
    """
    Retorna o ID da unidade e, recursivamente, todos os IDs de suas subunidades
    subordinadas no organograma (filhas, netas, etc.).
    """
    subunidades_ids: Set[int] = {unidade_id}
    fila: List[int] = [unidade_id]

    while fila:
        atual = fila.pop(0)
        stmt = select(UnidadeOrganizacional.id).where(UnidadeOrganizacional.unidade_pai_id == atual)
        res = await db.execute(stmt)
        filhos = res.scalars().all()
        for f_id in filhos:
            if f_id not in subunidades_ids:
                subunidades_ids.add(f_id)
                fila.append(f_id)

    return list(subunidades_ids)


async def listar_processos_hierarquicos(
    db: AsyncSession,
    unidade_id: Optional[int] = None,
    transversal_only: bool = False,
    incluir_processo_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna os macroprocessos e processos elegíveis para a unidade indicada.
    
    Regra EBSERH Hospital Tipo II:
    - Se unidade_id for informada: exibe os processos específicos da própria unidade,
      os processos de todas as unidades/setores subordinados a ela no organograma,
      e todos os Processos Comuns a todas as áreas (is_transversal = True).
    - Se incluir_processo_id for fornecido: garante a presença do processo indicado.
    - Se unidade_id for None: exibe o catálogo completo.
    - Oculta projetos estratégicos (iniciados com padrão [código]).
    """
    # 1. Se unidade_id foi fornecida, identificar processos permitidos
    processos_permitidos_ids: Optional[Set[int]] = None

    if unidade_id:
        sub_ids = await obter_subunidades_recursivas(db, unidade_id)
        
        # Busca IDs de processos associados a essa árvore na tabela processos_unidades
        stmt_assoc = (
            select(ProcessoUnidade.processo_id)
            .where(ProcessoUnidade.unidade_id.in_(sub_ids))
        )
        res_assoc = await db.execute(stmt_assoc)
        processos_permitidos_ids = set(res_assoc.scalars().all())
        if incluir_processo_id:
            processos_permitidos_ids.add(incluir_processo_id)

    # 2. Carrega os macroprocessos e processos
    stmt = (
        select(Macroprocesso)
        .options(selectinload(Macroprocesso.processos))
        .order_by(Macroprocesso.nome)
    )
    result = await db.execute(stmt)
    macros = result.scalars().all()

    retorno = []
    padrao_projeto = re.compile(r"^\s*\[[^\]]+\]")

    for m in macros:
        processos_filtrados = []
        for p in m.processos:
            # Não exibir projetos estratégicos no catálogo de processos (ex: [P1.01] Nome)
            if padrao_projeto.search(p.nome):
                continue

            # Se for filtro estrito de transversais
            if transversal_only and not p.is_transversal:
                continue

            # Se houver filtro de unidade:
            # Processos comuns (is_transversal = True) são sempre incluídos para qualquer unidade.
            # Processos específicos só são incluídos se vinculados à unidade ou a suas subunidades.
            if processos_permitidos_ids is not None:
                if not (p.is_transversal or p.id in processos_permitidos_ids):
                    continue

            processos_filtrados.append({
                "id": p.id,
                "codigo": p.codigo,
                "nome": p.nome,
                "is_transversal": p.is_transversal,
                "permite_projeto": p.permite_projeto
            })

        # Ordena processos alfabeticamente
        processos_filtrados.sort(key=lambda x: x["nome"])

        if processos_filtrados:
            retorno.append({
                "id": m.id,
                "codigo": m.codigo,
                "nome": m.nome,
                "processos": processos_filtrados
            })

    return retorno


async def listar_processos_outro(
    db: AsyncSession,
    current_user: Dict[str, Any],
    unidade_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna os processos customizados cadastrados na categoria 'Outro' que estão
    visíveis para a unidade e para o usuário logado.

    Regra de Negócio:
    - Ficam visíveis apenas para o setor onde foi criado, podendo ser visualizados
      pelas instâncias hierárquicas vinculadas à unidade (unidades ancestrais: Divisão, Gerência, etc.).
    - Administradores têm visão global.
    """
    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    stmt_u = select(Usuario).where(Usuario.username == username)
    res_u = await db.execute(stmt_u)
    u_obj = res_u.scalar_one_or_none()
    if u_obj and u_obj.perfil == "ADMINISTRADOR":
        is_admin = True

    # Busca todas as fichas com processo_outro cadastrado
    stmt = (
        select(
            MapeamentoRisco.processo_outro,
            MapeamentoRisco.unidade_id,
            UnidadeOrganizacional.nome.label("unidade_nome")
        )
        .join(UnidadeOrganizacional, MapeamentoRisco.unidade_id == UnidadeOrganizacional.id)
        .where(
            and_(
                MapeamentoRisco.processo_outro.isnot(None),
                MapeamentoRisco.processo_outro != ""
            )
        )
    )

    if unidade_id:
        stmt = stmt.where(MapeamentoRisco.unidade_id == unidade_id)

    res = await db.execute(stmt)
    linhas = res.all()

    # Subunidades do usuário (caso não seja admin)
    subunidades_usuario = set()
    if not is_admin and u_obj and u_obj.unidade_principal_id:
        sub_ids = await obter_subunidades_recursivas(db, u_obj.unidade_principal_id)
        subunidades_usuario = set(sub_ids)

    # Filtra e agrupa processos únicos por nome
    processos_outro_vistos = set()
    resultado = []

    for p_outro, u_id, u_nome in linhas:
        nome_limpo = str(p_outro).strip()
        if not nome_limpo:
            continue

        chave = nome_limpo.lower()
        if chave in processos_outro_vistos:
            continue

        # Verifica permissão de visibilidade do setor criador
        if not is_admin:
            # O processo só é visível se a unidade criadora for a própria unidade do usuário
            # ou se for uma subunidade vinculada à hierarquia do usuário
            if u_id not in subunidades_usuario:
                continue

        processos_outro_vistos.add(chave)
        resultado.append({
            "nome": nome_limpo,
            "unidade_id": u_id,
            "unidade_nome": u_nome
        })

    resultado.sort(key=lambda x: x["nome"])
    return resultado



async def listar_pilares_estrategicos(db: AsyncSession) -> List[Dict[str, Any]]:
    """Retorna os pilares estratégicos do mapa do HC-UFPE."""
    stmt = select(PilarEstrategico).order_by(PilarEstrategico.numero)
    result = await db.execute(stmt)
    pilares = result.scalars().all()
    return [
        {
            "id": p.id,
            "numero": p.numero,
            "nome": p.nome,
            "descricao": p.descricao
        }
        for p in pilares
    ]
