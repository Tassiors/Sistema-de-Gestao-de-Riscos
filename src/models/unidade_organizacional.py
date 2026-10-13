"""
Modelo SQLAlchemy para Unidades Organizacionais do HC-UFPE
===========================================================
Representa as 76 Unidades Organizacionais, Órgãos Independentes
e Gerências mapeáveis do Hospital das Clínicas da UFPE.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..resources.database import Base


class UnidadeOrganizacional(Base):
    __tablename__ = "unidades_organizacionais"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sigla = Column(String(50), nullable=True, index=True)
    nome = Column(String(200), nullable=False, unique=True, index=True)
    tipo = Column(String(50), nullable=False, default="UNIDADE")  # ORGAO_INDEPENDENTE, GERENCIA, DIVISAO, SETOR, UNIDADE
    unidade_pai_id = Column(Integer, ForeignKey("unidades_organizacionais.id"), nullable=True)
    ativa = Column(Boolean, default=True, nullable=False)

    # Auto-relacionamento hierárquico
    unidade_pai = relationship("UnidadeOrganizacional", remote_side=[id], backref="subunidades")

    # Relacionamento com mapeamentos de riscos
    mapeamentos = relationship("MapeamentoRisco", back_populates="unidade", cascade="all, delete-orphan")
    processos_associados = relationship("ProcessoUnidade", back_populates="unidade", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UnidadeOrganizacional id={self.id} nome='{self.nome}' tipo='{self.tipo}'>"
