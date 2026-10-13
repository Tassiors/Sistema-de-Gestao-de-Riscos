"""
Modelos SQLAlchemy para Catálogo de Processos EBSERH Tipo II e Pilares Estratégicos
==================================================================================
Representa a arquitetura de processos (Slides 169 a 206) e os pilares
do Mapa Estratégico do HC-UFPE.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from ..resources.database import Base


class PilarEstrategico(Base):
    __tablename__ = "pilares_estrategicos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero = Column(Integer, nullable=False, unique=True)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)

    def __repr__(self):
        return f"<PilarEstrategico id={self.id} numero={self.numero} nome='{self.nome}'>"


class Macroprocesso(Base):
    __tablename__ = "macroprocessos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String(50), nullable=True, index=True)
    nome = Column(String(200), nullable=False, unique=True, index=True)
    area_guardia_unidade_id = Column(Integer, ForeignKey("unidades_organizacionais.id"), nullable=True)

    # Relacionamentos
    processos = relationship("Processo", back_populates="macroprocesso", cascade="all, delete-orphan")
    area_guardia = relationship("UnidadeOrganizacional")

    def __repr__(self):
        return f"<Macroprocesso id={self.id} nome='{self.nome}'>"


class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    macroprocesso_id = Column(Integer, ForeignKey("macroprocessos.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=True, index=True)
    nome = Column(String(250), nullable=False, index=True)
    is_transversal = Column(Boolean, default=False, nullable=False)
    permite_projeto = Column(Boolean, default=False, nullable=False)  # Ex: "REALIZAR IDENTIFICAÇÃO E AVALIAÇÃO DOS EVENTOS DE RISCOS"

    # Relacionamentos
    macroprocesso = relationship("Macroprocesso", back_populates="processos")
    mapeamentos = relationship("MapeamentoRisco", back_populates="processo")
    unidades_associadas = relationship("ProcessoUnidade", back_populates="processo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Processo id={self.id} nome='{self.nome}' transversal={self.is_transversal}>"


class ProcessoUnidade(Base):
    """
    Associação explícita entre processos de negócio e unidades organizacionais executoras.
    Processos comuns (transversais) são herdados por todas as unidades sem necessidade de vínculo manual.
    """
    __tablename__ = "processos_unidades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    processo_id = Column(Integer, ForeignKey("processos.id", ondelete="CASCADE"), nullable=False, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades_organizacionais.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("processo_id", "unidade_id", name="uq_processo_unidade"),
    )

    processo = relationship("Processo", back_populates="unidades_associadas")
    unidade = relationship("UnidadeOrganizacional", back_populates="processos_associados")

    def __repr__(self):
        return f"<ProcessoUnidade processo_id={self.processo_id} unidade_id={self.unidade_id}>"

