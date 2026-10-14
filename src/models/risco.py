"""
Modelos SQLAlchemy para Gestão, Avaliação e Tratamento de Riscos
================================================================
Implementa as 5 etapas do Guia Prático da UGERC (HC-UFPE / EBSERH).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from ..resources.database import Base


class MapeamentoRisco(Base):
    """
    Cabeçalho do Mapeamento de Risco (Etapa 1 - Contexto, Unidade, Processo e Entrega).
    """
    __tablename__ = "mapeamentos_risco"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    unidade_id = Column(Integer, ForeignKey("unidades_organizacionais.id"), nullable=False, index=True)
    processo_id = Column(Integer, ForeignKey("processos.id"), nullable=False, index=True)
    possui_projeto = Column(Boolean, default=False, nullable=False)
    nome_projeto = Column(String(200), nullable=True)
    pilar_estrategico_id = Column(Integer, ForeignKey("pilares_estrategicos.id"), nullable=True)
    entrega_processo = Column(Text, nullable=False)
    processo_outro = Column(String(250), nullable=True)
    status = Column(String(50), default="RASCUNHO", nullable=False, index=True)  # RASCUNHO, SUBMETIDO, EM_MONITORAMENTO, REVISAO_SOLICITADA, ENCERRADO
    observacoes_ugerc = Column(Text, nullable=True)
    criado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    atualizado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relacionamentos
    unidade = relationship("UnidadeOrganizacional", back_populates="mapeamentos")
    processo = relationship("Processo", back_populates="mapeamentos")
    pilar_estrategico = relationship("PilarEstrategico")
    criado_por = relationship("Usuario")
    eventos = relationship("EventoRisco", back_populates="mapeamento", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MapeamentoRisco id={self.id} unidade_id={self.unidade_id} status='{self.status}'>"


class EventoRisco(Base):
    """
    Identificação do Evento de Risco (Etapa 2 - Causa, Risco, Consequência e Categoria).
    """
    __tablename__ = "eventos_risco"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mapeamento_id = Column(Integer, ForeignKey("mapeamentos_risco.id", ondelete="CASCADE"), nullable=False, index=True)
    descricao_evento = Column(Text, nullable=False)
    causa = Column(Text, nullable=False)
    consequencia = Column(Text, nullable=False)
    categoria = Column(String(50), nullable=False, default="OPERACIONAL", index=True)
    # Categorias: OPERACIONAL, LEGAL_CONFORMIDADE, FINANCEIRO_ORCAMENTARIO, IMAGEM_REPUTACAO, SEGURANCA_INFORMACAO, ASSISTENCIAL_PACIENTE, INTEGRIDADE

    # Relacionamentos
    mapeamento = relationship("MapeamentoRisco", back_populates="eventos")
    avaliacao = relationship("AvaliacaoRisco", back_populates="evento", uselist=False, cascade="all, delete-orphan")
    planos_acao = relationship("PlanoAcao5W2H", back_populates="evento", cascade="all, delete-orphan")
    planos_contingencia = relationship("PlanoContingencia", back_populates="evento", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EventoRisco id={self.id} mapeamento_id={self.mapeamento_id} categoria='{self.categoria}'>"


class AvaliacaoRisco(Base):
    """
    Avaliação Numérica do Risco (Etapa 3 - Probabilidade, Impacto e Controles).
    Calcula Risco Inerente, Fator de Mitigação e Risco Residual.
    """
    __tablename__ = "avaliacoes_risco"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evento_risco_id = Column(Integer, ForeignKey("eventos_risco.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    probabilidade = Column(Integer, nullable=False, default=1)  # 1 a 5
    impacto = Column(Integer, nullable=False, default=1)        # 1 a 5
    risco_inerente = Column(Integer, nullable=False, default=1) # P * I (1 a 25)
    fator_mitigacao = Column(Float, nullable=False, default=1.0) # 1.0, 0.8, 0.6, 0.4, 0.2
    nivel_controle = Column(String(50), nullable=True, default="INEXISTENTE") # INEXISTENTE, FRACO, MEDIANO, SATISFATORIO, FORTE
    risco_residual = Column(Integer, nullable=False, default=1)  # round(inerente * fator)
    classificacao = Column(String(50), nullable=False, default="BAIXO") # BAIXO, MEDIO, ALTO, EXTREMO
    acima_apetite = Column(Boolean, nullable=False, default=False)       # True se residual > 7.99

    # Relacionamentos
    evento = relationship("EventoRisco", back_populates="avaliacao")
    controles = relationship("ControleExistente", back_populates="avaliacao", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AvaliacaoRisco id={self.id} residual={self.risco_residual} class='{self.classificacao}'>"


class ControleExistente(Base):
    """
    Medidas de Controle Interno Existentes (Etapa 3).
    """
    __tablename__ = "controles_existentes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    avaliacao_id = Column(Integer, ForeignKey("avaliacoes_risco.id", ondelete="CASCADE"), nullable=False, index=True)
    descricao_controle = Column(Text, nullable=False)

    avaliacao = relationship("AvaliacaoRisco", back_populates="controles")

    def __repr__(self):
        return f"<ControleExistente id={self.id} avaliacao_id={self.avaliacao_id}>"


class PlanoAcao5W2H(Base):
    """
    Plano de Ação e Tratamento de Risco (Etapa 4 - 5W2H).
    Obrigatório para riscos Alto e Extremo (acima do apetite > 7.99).
    """
    __tablename__ = "planos_acao_5w2h"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evento_risco_id = Column(Integer, ForeignKey("eventos_risco.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_resposta = Column(String(50), nullable=False, default="MITIGAR") # MITIGAR, EVITAR, COMPARTILHAR, ACEITAR
    o_que = Column(Text, nullable=False)
    como = Column(Text, nullable=False)
    quem = Column(String(200), nullable=False)
    data_inicio = Column(String(20), nullable=False)
    data_termino = Column(String(20), nullable=False)
    status = Column(String(50), nullable=False, default="PLANEJADO") # PLANEJADO, EM_ANDAMENTO, CONCLUIDO, CANCELADO

    evento = relationship("EventoRisco", back_populates="planos_acao")

    def __repr__(self):
        return f"<PlanoAcao5W2H id={self.id} evento_risco_id={self.evento_risco_id}>"


class PlanoContingencia(Base):
    """
    Plano de Contingência (Etapa 4 - Ação imediata caso o risco se manifeste).
    """
    __tablename__ = "planos_contingencia"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evento_risco_id = Column(Integer, ForeignKey("eventos_risco.id", ondelete="CASCADE"), nullable=False, index=True)
    gatilho = Column(Text, nullable=False)
    o_que = Column(Text, nullable=False)
    como = Column(Text, nullable=False)
    responsavel = Column(String(200), nullable=False)

    evento = relationship("EventoRisco", back_populates="planos_contingencia")

    def __repr__(self):
        return f"<PlanoContingencia id={self.id} evento_risco_id={self.evento_risco_id}>"
