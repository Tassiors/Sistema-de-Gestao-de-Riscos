"""
Script de Carga Inicial (Seeds) para o Sistema de Gestão de Riscos (HC-UFPE)
===========================================================================
Popula:
1. As 79 Unidades Organizacionais e Órgãos Independentes do HC-UFPE.
2. Os 5 Pilares do Mapa Estratégico do HC-UFPE.
3. Os Macroprocessos e Processos EBSERH Tipo II.
4. Os administradores mestres iniciais (Tássio Silva e Renata Albuquerque).
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.unidade_organizacional import UnidadeOrganizacional
from src.models.processo import PilarEstrategico, Macroprocesso, Processo
from src.models.usuario import Usuario


async def run_seed():
    db_url = os.getenv("SQLITE_DSN") or os.getenv("APP_DB_URL") or "sqlite+aiosqlite:///data/app.db"
    print(f"Iniciando Seed Inicial no banco: {db_url}")
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    seed_json_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    with open(seed_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    async with async_session() as session:
        # 1. Popula Unidades Organizacionais
        print("Populando Unidades Organizacionais...")
        unidades_map = {}
        for u in data.get("unidades", []):
            stmt = select(UnidadeOrganizacional).where(UnidadeOrganizacional.nome == u["nome"])
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                obj = UnidadeOrganizacional(
                    nome=u["nome"],
                    sigla=u.get("sigla"),
                    tipo=u.get("tipo", "UNIDADE"),
                    ativa=True
                )
                session.add(obj)
                await session.flush()
            else:
                if u.get("sigla") and obj.sigla != u.get("sigla"):
                    obj.sigla = u.get("sigla")
            unidades_map[u["nome"]] = obj.id

        # 2. Popula Pilares Estratégicos
        print("Populando Pilares Estratégicos...")
        for p in data.get("pilares", []):
            stmt = select(PilarEstrategico).where(PilarEstrategico.numero == p["numero"])
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                obj = PilarEstrategico(
                    numero=p["numero"],
                    nome=p["nome"]
                )
                session.add(obj)

        # 3. Popula Macroprocessos e Processos
        print("Populando Macroprocessos e Processos...")
        for m in data.get("macroprocessos", []):
            stmt = select(Macroprocesso).where(Macroprocesso.nome == m["nome"])
            res = await session.execute(stmt)
            m_obj = res.scalar_one_or_none()
            if not m_obj:
                m_obj = Macroprocesso(
                    codigo=m.get("codigo"),
                    nome=m["nome"]
                )
                session.add(m_obj)
                await session.flush()

            for p in m.get("processos", []):
                stmt_p = select(Processo).where(
                    Processo.macroprocesso_id == m_obj.id,
                    Processo.nome == p["nome"]
                )
                res_p = await session.execute(stmt_p)
                p_obj = res_p.scalar_one_or_none()
                if not p_obj:
                    p_obj = Processo(
                        macroprocesso_id=m_obj.id,
                        nome=p["nome"],
                        is_transversal=p.get("is_transversal", False),
                        permite_projeto=p.get("permite_projeto", False)
                    )
                    session.add(p_obj)

        # 4. Popula Administradores Mestres Iniciais
        print("Populando Administradores Mestres...")
        ugerc_id = unidades_map.get("Unidade de Gestão Estratégica, de Riscos e Controles Internos") or unidades_map.get("Superintendência")

        admins = [
            {
                "username": "tassio.silva",
                "email": "tassio.silva@hubrasil.gov.br",
                "nome_completo": "Tássio Silva",
                "perfil": "ADMINISTRADOR",
                "unidade_principal_id": ugerc_id
            },
            {
                "username": "renata.albuquerque.1",
                "email": "renata.albuquerque.1@hubrasil.gov.br",
                "nome_completo": "Renata Albuquerque",
                "perfil": "ADMINISTRADOR",
                "unidade_principal_id": ugerc_id
            }
        ]

        for adm in admins:
            stmt_adm = select(Usuario).where(Usuario.username == adm["username"])
            res_adm = await session.execute(stmt_adm)
            u_obj = res_adm.scalar_one_or_none()
            if not u_obj:
                u_obj = Usuario(
                    username=adm["username"],
                    nome_completo=adm["nome_completo"],
                    email=adm["email"],
                    perfil=adm["perfil"],
                    unidade_principal_id=adm["unidade_principal_id"],
                    ativo=True,
                    criado_em=datetime.now(timezone.utc)
                )
                session.add(u_obj)
            else:
                # Garante privilégio de administrador
                u_obj.perfil = "ADMINISTRADOR"
                u_obj.ativo = True

        await session.commit()
        print("Seed Inicial concluído com sucesso!")

    await engine.dispose()

    # Aplica a hierarquia do organograma e os vínculos da arquitetura de processos
    from .popular_hierarquia_processos import run_update
    run_update()


if __name__ == "__main__":
    asyncio.run(run_seed())
