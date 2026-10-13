# src/dependencies.py
"""
Módulo de injeção de dependências do FastAPI.
"""
from .resources.database import get_app_db_session

__all__ = ["get_app_db_session"]
