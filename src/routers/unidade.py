"""
Roteador de Unidades Organizacionais (HC-UFPE)
==============================================
Padrão Default-Private Router: protegido por token JWT corporativo.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..resources.database import get_app_db_session
from ..models.unidade_organizacional import UnidadeOrganizacional

router = APIRouter(
    prefix="/api/unidades",
    tags=["Unidades Organizacionais"],
    dependencies=[Depends(auth_handler.decode_token)]
)


@router.get("", response_model=List[Dict[str, Any]])
async def listar_unidades(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ORGAO_INDEPENDENTE, GERENCIA, DIVISAO, SETOR, UNIDADE)"),
    db: AsyncSession = Depends(get_app_db_session)
):
    """Lista todas as unidades organizacionais e órgãos independentes ativos do HC-UFPE."""
    stmt = select(UnidadeOrganizacional).where(UnidadeOrganizacional.ativa == True)
    if tipo:
        stmt = stmt.where(UnidadeOrganizacional.tipo == tipo)
    stmt = stmt.order_by(UnidadeOrganizacional.nome)

    result = await db.execute(stmt)
    unidades = result.scalars().all()

    return [
        {
            "id": u.id,
            "sigla": u.sigla,
            "nome": u.nome,
            "tipo": u.tipo,
            "unidade_pai_id": u.unidade_pai_id
        }
        for u in unidades
    ]
