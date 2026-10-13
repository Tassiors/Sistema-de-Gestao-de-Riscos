"""
Modelos SQLAlchemy para Usuários, Perfis e Matriz de Visibilidade Setorial
===========================================================================
Gerencia o controle de acesso e o mecanismo de 'quem vê o relatório de quem'.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from ..resources.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    nome_completo = Column(String(200), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    perfil = Column(String(50), nullable=False, default="GESTOR_UNIDADE", index=True)  # ADMINISTRADOR, GESTOR_UNIDADE, CONSULTA_SETORIAL
    unidade_principal_id = Column(Integer, ForeignKey("unidades_organizacionais.id"), nullable=True, index=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relacionamentos
    unidade_principal = relationship("UnidadeOrganizacional", foreign_keys=[unidade_principal_id])
    visibilidades_concedidas = relationship("UsuarioUnidadeVisibilidade", back_populates="usuario", foreign_keys="UsuarioUnidadeVisibilidade.usuario_id", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Usuario id={self.id} username='{self.username}' perfil='{self.perfil}'>"


class UsuarioUnidadeVisibilidade(Base):
    """
    Controla a permissão cruzada: quais unidades adicionais um gestor pode visualizar ou editar.
    """
    __tablename__ = "usuario_unidades_visibilidade"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades_organizacionais.id", ondelete="CASCADE"), nullable=False, index=True)
    permite_edicao = Column(Boolean, default=False, nullable=False)
    concedido_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    concedido_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_id", "unidade_id", name="uq_usuario_unidade_visibilidade"),
    )

    # Relacionamentos
    usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="visibilidades_concedidas")
    unidade = relationship("UnidadeOrganizacional")
    concedido_por = relationship("Usuario", foreign_keys=[concedido_por_id])

    def __repr__(self):
        return f"<UsuarioUnidadeVisibilidade usuario_id={self.usuario_id} unidade_id={self.unidade_id}>"
