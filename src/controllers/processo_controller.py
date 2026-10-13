"""
Controller para Gestão do Catálogo de Processos e Hierarquia Organizacional
=============================================================================
Implementa a resolução hierárquica onde Setores, Divisões e Gerências herdam
os processos de suas subunidades, e todas as unidades recebem os Processos Comuns.
"""

from typing import List, Dict, Any, Optional, Set
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.processo import Macroprocesso, Processo, PilarEstrategico, ProcessoUnidade
from ..models.unidade_organizacional import UnidadeOrganizacional


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
    transversal_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Retorna os macroprocessos e processos elegíveis para a unidade indicada.
    
    Regra EBSERH Hospital Tipo II:
    - Se unidade_id for informada: exibe os processos específicos da própria unidade,
      os processos de todas as unidades/setores subordinados a ela no organograma,
      e todos os Processos Comuns a todas as áreas (is_transversal = True).
    - Se unidade_id for None: exibe o catálogo completo.
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

    # 2. Carrega os macroprocessos e processos
    stmt = (
        select(Macroprocesso)
        .options(selectinload(Macroprocesso.processos))
        .order_by(Macroprocesso.nome)
    )
    result = await db.execute(stmt)
    macros = result.scalars().all()

    retorno = []
    for m in macros:
        processos_filtrados = []
        for p in m.processos:
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
