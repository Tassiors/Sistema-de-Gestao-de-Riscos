"""
Roteador de Mapeamento e Avaliação de Riscos (HC-UFPE)
======================================================
Padrão Default-Private Router: protegido por token JWT corporativo.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..auth.auth import auth_handler
from ..resources.database import get_app_db_session
from ..controllers import risco_controller

router = APIRouter(
    prefix="/api/riscos",
    tags=["Gestão de Riscos"],
    dependencies=[Depends(auth_handler.decode_token)]
)


class PreviewCalculoInput(BaseModel):
    probabilidade: int
    impacto: int
    num_controles: int


@router.post("/calcular-preview")
async def preview_calculo_severidade(payload: PreviewCalculoInput):
    """Calcula instantaneamente Risco Inerente, Fator de Mitigação, Risco Residual e Classificação."""
    return risco_controller.calcular_severidade_risco(
        probabilidade=payload.probabilidade,
        impacto=payload.impacto,
        num_controles=payload.num_controles
    )


@router.get("", response_model=List[Dict[str, Any]])
async def listar_mapeamentos_risco(
    unidade_id: Optional[int] = Query(None, description="Filtrar por unidade organizacional"),
    status_filtro: Optional[str] = Query(None, alias="status", description="Filtrar por status"),
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """Lista todos os mapeamentos de risco autorizados para o usuário logado."""
    return await risco_controller.listar_mapeamentos(
        db=db,
        current_user=current_user,
        unidade_id=unidade_id,
        status_filtro=status_filtro
    )


@router.get("/painel/matriz", response_model=Dict[str, Any])
async def obter_dados_matriz_riscos(
    unidade_id: Optional[int] = Query(None, description="Filtrar por unidade organizacional"),
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """Retorna a contagem agregada de riscos nos quadrantes da matriz 5x5 e agrupamento por gerências."""
    return await risco_controller.obter_estatisticas_matriz(
        db=db,
        current_user=current_user,
        unidade_id=unidade_id
    )


class ExcluirLoteRequest(BaseModel):
    ids: List[int]


@router.post("/excluir-lote", response_model=Dict[str, Any])
async def excluir_mapeamentos_em_lote(
    payload: ExcluirLoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """
    Exclui múltiplas fichas de riscos do sistema em lote numa única transação atômica:
    - Administradores podem deletar quaisquer fichas selecionadas.
    - Gestores de unidade podem deletar apenas fichas pertencentes à sua própria unidade.
    - Registra auditoria individualizada para cada ficha.
    """
    ip_origem = request.client.host if request.client else None
    return await risco_controller.excluir_mapeamentos_em_lote(
        db=db,
        mapeamento_ids=payload.ids,
        current_user=current_user,
        ip_origem=ip_origem
    )


class ObterLoteRequest(BaseModel):
    ids: List[int]


@router.post("/detalhes-lote", response_model=List[Dict[str, Any]])
async def obter_detalhes_em_lote(
    payload: ObterLoteRequest,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """
    Retorna dados detalhados de múltiplos mapeamentos para impressão unificada em lote.
    """
    return await risco_controller.obter_mapeamentos_detalhados_em_lote(
        db=db,
        mapeamento_ids=payload.ids,
        current_user=current_user
    )


@router.get("/{id}", response_model=Dict[str, Any])
async def obter_detalhes_mapeamento(
    id: int,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """Retorna a ficha completa de um mapeamento de risco."""
    return await risco_controller.obter_mapeamento_por_id(
        db=db,
        mapeamento_id=id,
        current_user=current_user
    )


@router.post("", response_model=Dict[str, Any])
async def salvar_mapeamento_risco(
    payload: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """Cria ou atualiza um mapeamento de risco (Rascunho ou Submetido para a UGERC)."""
    ip_origem = request.client.host if request.client else None
    return await risco_controller.salvar_mapeamento(
        db=db,
        dados=payload,
        current_user=current_user,
        ip_origem=ip_origem
    )


@router.delete("/{id}", response_model=Dict[str, Any])
async def deletar_mapeamento_risco(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: Dict[str, Any] = Depends(auth_handler.decode_token)
):
    """
    Deleta uma ficha de risco do sistema.
    - Administradores podem deletar quaisquer fichas.
    - Gestores podem deletar apenas fichas da sua própria unidade.
    - Chefias de instâncias superiores não poderão deletar fichas de unidades vinculadas.
    """
    ip_origem = request.client.host if request.client else None
    return await risco_controller.excluir_mapeamento(
        db=db,
        mapeamento_id=id,
        current_user=current_user,
        ip_origem=ip_origem
    )


