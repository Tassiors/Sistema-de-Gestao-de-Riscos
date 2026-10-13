"""
Controller Administrativo de Gestão de Usuários e Matriz de Visibilidade
========================================================================
Gerencia o cadastro de gestores setoriais e a configuração do mecanismo
de 'quem vê o relatório de quem'.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..models.usuario import Usuario, UsuarioUnidadeVisibilidade
from ..models.unidade_organizacional import UnidadeOrganizacional
from ..helpers.audit_helper import registrar_auditoria


async def listar_usuarios(db: AsyncSession) -> List[Dict[str, Any]]:
    """Lista todos os usuários com suas unidades principais e visibilidades concedidas."""
    stmt = (
        select(Usuario)
        .options(
            selectinload(Usuario.unidade_principal),
            selectinload(Usuario.visibilidades_concedidas).selectinload(UsuarioUnidadeVisibilidade.unidade)
        )
        .order_by(Usuario.nome_completo)
    )
    result = await db.execute(stmt)
    usuarios = result.scalars().all()

    retorno = []
    for u in usuarios:
        retorno.append({
            "id": u.id,
            "username": u.username,
            "nome_completo": u.nome_completo,
            "email": u.email,
            "perfil": u.perfil,
            "ativo": u.ativo,
            "unidade_principal": {
                "id": u.unidade_principal.id,
                "nome": u.unidade_principal.nome
            } if u.unidade_principal else None,
            "visibilidades_adicionais": [
                {
                    "unidade_id": v.unidade_id,
                    "unidade_nome": v.unidade.nome if v.unidade else "",
                    "permite_edicao": v.permite_edicao
                }
                for v in u.visibilidades_concedidas
            ]
        })
    return retorno


async def salvar_usuario(
    db: AsyncSession,
    dados: Dict[str, Any],
    usuario_operador: str,
    ip_origem: Optional[str] = None
) -> Dict[str, Any]:
    """Cadastra ou atualiza um usuário gestor no sistema."""
    username = dados.get("username", "").strip().lower()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome de usuário é obrigatório")

    stmt = select(Usuario).where(Usuario.username == username)
    result = await db.execute(stmt)
    usuario = result.scalar_one_or_none()

    dados_anteriores = None
    if usuario:
        dados_anteriores = {
            "perfil": usuario.perfil,
            "unidade_principal_id": usuario.unidade_principal_id,
            "ativo": usuario.ativo
        }
        usuario.nome_completo = dados.get("nome_completo", usuario.nome_completo)
        usuario.email = dados.get("email", usuario.email)
        usuario.perfil = dados.get("perfil", usuario.perfil)
        usuario.unidade_principal_id = dados.get("unidade_principal_id")
        usuario.ativo = dados.get("ativo", True)
        acao = "ATUALIZAR_USUARIO"
    else:
        usuario = Usuario(
            username=username,
            nome_completo=dados.get("nome_completo", username),
            email=dados.get("email", f"{username}@ebserh.gov.br"),
            perfil=dados.get("perfil", "GESTOR_UNIDADE"),
            unidade_principal_id=dados.get("unidade_principal_id"),
            ativo=dados.get("ativo", True),
            criado_em=datetime.now(timezone.utc)
        )
        db.add(usuario)
        acao = "CRIAR_USUARIO"

    await db.flush()

    if "visibilidades_ids" in dados and dados["visibilidades_ids"] is not None:
        vis_ids = dados["visibilidades_ids"]
        await db.execute(delete(UsuarioUnidadeVisibilidade).where(UsuarioUnidadeVisibilidade.usuario_id == usuario.id))
        for uid in set(vis_ids):
            if uid != usuario.unidade_principal_id:
                vis = UsuarioUnidadeVisibilidade(
                    usuario_id=usuario.id,
                    unidade_id=uid,
                    permite_edicao=False,
                    concedido_em=datetime.now(timezone.utc)
                )
                db.add(vis)

    dados_novos = {
        "perfil": usuario.perfil,
        "unidade_principal_id": usuario.unidade_principal_id,
        "ativo": usuario.ativo
    }

    await registrar_auditoria(
        db=db,
        usuario=usuario_operador,
        categoria="SEGURANCA",
        acao=acao,
        recurso=f"usuario:{username}",
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        ip_origem=ip_origem
    )

    await db.commit()
    await db.refresh(usuario)

    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome_completo": usuario.nome_completo,
        "perfil": usuario.perfil,
        "unidade_principal_id": usuario.unidade_principal_id,
        "ativo": usuario.ativo
    }


async def configurar_visibilidade_usuario(
    db: AsyncSession,
    usuario_id: int,
    unidades_ids: List[int],
    usuario_operador: str,
    ip_origem: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Configura a matriz de visibilidade: define quais unidades adicionais o usuário pode visualizar."""
    stmt_u = select(Usuario).where(Usuario.id == usuario_id)
    res_u = await db.execute(stmt_u)
    usuario = res_u.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    # Obter visibilidades atuais para trilha de auditoria
    stmt_v = select(UsuarioUnidadeVisibilidade).where(UsuarioUnidadeVisibilidade.usuario_id == usuario_id)
    res_v = await db.execute(stmt_v)
    atuais = [v.unidade_id for v in res_v.scalars().all()]

    # Remove visibilidades antigas
    await db.execute(delete(UsuarioUnidadeVisibilidade).where(UsuarioUnidadeVisibilidade.usuario_id == usuario_id))

    # Cria novas visibilidades
    novas = []
    for uid in set(unidades_ids):
        # Não adiciona a unidade principal como adicional
        if uid != usuario.unidade_principal_id:
            vis = UsuarioUnidadeVisibilidade(
                usuario_id=usuario_id,
                unidade_id=uid,
                permite_edicao=False,
                concedido_em=datetime.now(timezone.utc)
            )
            db.add(vis)
            novas.append(uid)

    await registrar_auditoria(
        db=db,
        usuario=usuario_operador,
        categoria="SEGURANCA",
        acao="CONFIGURAR_VISIBILIDADE_SETORES",
        recurso=f"usuario:{usuario.username}",
        dados_anteriores={"unidades_adicionais": atuais},
        dados_novos={"unidades_adicionais": novas},
        ip_origem=ip_origem
    )

    await db.commit()
    return [{"unidade_id": uid} for uid in novas]
