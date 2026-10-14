"""
Roteador de Catálogo de Processos EBSERH e Pilares Estratégicos
==============================================================
Padrão Default-Private Router: protegido por token JWT corporativo.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..resources.database import get_app_db_session
from ..controllers import processo_controller

router = APIRouter(
    prefix="/api/processos",
    tags=["Processos e Pilares Estratégicos"],
    dependencies=[Depends(auth_handler.decode_token)]
)


@router.get("", response_model=List[Dict[str, Any]])
async def listar_macroprocessos_e_processos(
    unidade_id: Optional[int] = Query(None, description="Filtrar processos vinculados à unidade, suas subunidades e processos comuns"),
    transversal_only: bool = Query(False, description="Filtrar apenas processos transversais/comuns"),
    db: AsyncSession = Depends(get_app_db_session)
):
    """
    Retorna o catálogo hierárquico de Macroprocessos e Processos do Hospital Tipo II.
    Se unidade_id for fornecida, retorna apenas os processos específicos da unidade/setor/gerência
    (incluindo suas subunidades no organograma) juntamente com os Processos Comuns a todas as áreas.
    """
    return await processo_controller.listar_processos_hierarquicos(
        db=db,
        unidade_id=unidade_id,
        transversal_only=transversal_only
    )


@router.get("/pilares-estrategicos", response_model=List[Dict[str, Any]])
async def listar_pilares_estrategicos(db: AsyncSession = Depends(get_app_db_session)):
    """Retorna os 5 pilares do Mapa Estratégico do HC-UFPE."""
    return await processo_controller.listar_pilares_estrategicos(db=db)


@router.get("/outros", response_model=List[Dict[str, Any]])
async def listar_processos_categoria_outro(
    unidade_id: Optional[int] = Query(None, description="Filtrar por unidade organizacional"),
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """
    Retorna processos customizados criados na categoria 'Outro' visíveis para a unidade
    e instâncias hierárquicas superiores (ancestrais).
    """
    return await processo_controller.listar_processos_outro(
        db=db,
        current_user=current_user,
        unidade_id=unidade_id
    )


