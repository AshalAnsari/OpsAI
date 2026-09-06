# Re-export user/role models from role module for clean imports
from app.models.role import Role, User, user_roles

__all__ = ["Role", "User", "user_roles"]
