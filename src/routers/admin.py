from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..resources.database import get_app_db_session
from ..controllers import admin_controller

router = APIRouter(prefix="/api", tags=["Admin"])

class AdminData(BaseModel):
    message: str
    user_groups: List[str]

async def verify_admin_group(current_user: dict = Depends(auth_handler.decode_token)):
    ADMIN_GROUP = "GLO-SEC-HCPE-SETISD"
    username = current_user.get("username", "")
    perfil = current_user.get("perfil", "")
    groups = current_user.get("groups", [])

    if perfil == "ADMINISTRADOR" or ADMIN_GROUP in groups or username in ["admin", "tassio.silva", "renata.albuquerque.1"]:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

@router.get("/admin-only-data", response_model=AdminData)
async def get_admin_data(current_user: dict = Depends(verify_admin_group)):
    """
    Returns data only accessible by users with admin privileges.
    """
    return AdminData(
        message="This is highly confidential admin data!",
        user_groups=current_user.get("groups", [])
    )

class ADUserSearchResponse(BaseModel):
    exists: bool
    username: str
    displayName: str
    email: str
    department: str

@router.get("/admin/ad-user-search/{username}", response_model=ADUserSearchResponse)
async def search_ad_user(username: str, current_user: dict = Depends(verify_admin_group)):
    """
    Busca e valida um usuário no Active Directory (ou Mock) pelo login de rede.
    Restrito a administradores do sistema.
    """
    res = auth_handler.search_ad_user(username)
    return ADUserSearchResponse(**res)

@router.get("/admin/usuarios", response_model=List[Dict[str, Any]])
async def listar_usuarios(
    db: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(verify_admin_group)
):
    """Lista todos os gestores cadastrados e suas permissões setoriais."""
    return await admin_controller.listar_usuarios(db)

@router.post("/admin/usuarios", response_model=Dict[str, Any])
async def salvar_usuario(
    payload: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(verify_admin_group)
):
    """Cadastra ou atualiza o perfil de um gestor no banco de dados local."""
    ip_origem = request.client.host if request.client else None
    return await admin_controller.salvar_usuario(
        db=db,
        dados=payload,
        usuario_operador=current_user.get("username", "admin"),
        ip_origem=ip_origem
    )

class ConfigurarVisibilidadePayload(BaseModel):
    unidades_ids: List[int]

@router.post("/admin/usuarios/{usuario_id}/visibilidade", response_model=List[Dict[str, Any]])
async def configurar_visibilidade(
    usuario_id: int,
    payload: ConfigurarVisibilidadePayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(verify_admin_group)
):
    """Configura o mecanismo 'quem vê o relatório de quem', concedendo acesso a setores adicionais."""
    ip_origem = request.client.host if request.client else None
    return await admin_controller.configurar_visibilidade_usuario(
        db=db,
        usuario_id=usuario_id,
        unidades_ids=payload.unidades_ids,
        usuario_operador=current_user.get("username", "admin"),
        ip_origem=ip_origem
    )
