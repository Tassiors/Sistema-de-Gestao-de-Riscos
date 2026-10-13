"""
Módulo de Perfis de Usuários (RBAC Local)
=========================================
Compatibilidade com as diretrizes de governança do Framework SETISD.
Exporta as classes Usuario e UsuarioUnidadeVisibilidade para RBAC local.
"""

from .usuario import Usuario, UsuarioUnidadeVisibilidade

__all__ = ["Usuario", "UsuarioUnidadeVisibilidade"]
