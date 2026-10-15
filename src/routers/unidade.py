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
    apenas_autorizadas: bool = Query(False, description="Filtrar apenas unidades autorizadas para o usuário logado"),
    apenas_mapeamento: bool = Query(False, description="Filtrar apenas unidades que o usuário pode mapear (sua unidade e subordinadas)"),
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """Lista todas as unidades organizacionais e órgãos independentes ativos do HC-UFPE."""
    stmt = select(UnidadeOrganizacional).where(UnidadeOrganizacional.ativa == True)
    if tipo:
        stmt = stmt.where(UnidadeOrganizacional.tipo == tipo)

    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])
    is_admin = (perfil == "ADMINISTRADOR" or "GLO-SEC-HCPE-SETISD" in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"])

    if apenas_mapeamento and not is_admin:
        from ..models.usuario import Usuario
        from ..controllers.processo_controller import obter_subunidades_recursivas
        stmt_u = select(Usuario).where(Usuario.username == username)
        res_u = await db.execute(stmt_u)
        u_obj = res_u.scalar_one_or_none()
        if not u_obj or not u_obj.unidade_principal_id:
            return []
        sub_ids = await obter_subunidades_recursivas(db, u_obj.unidade_principal_id)
        stmt = stmt.where(UnidadeOrganizacional.id.in_(sub_ids))
    elif apenas_autorizadas:
        from ..controllers.risco_controller import obter_unidades_autorizadas
        unidades_autorizadas = await obter_unidades_autorizadas(db, current_user)
        if unidades_autorizadas is not None:
            if not unidades_autorizadas:
                return []
            stmt = stmt.where(UnidadeOrganizacional.id.in_(unidades_autorizadas))

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
