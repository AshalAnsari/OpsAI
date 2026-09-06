from collections.abc import Callable

from fastapi import Depends

from app.dependencies.auth import get_current_user
from app.models.role import User
from app.utils.exceptions import AppError


def require_roles(*role_names: str) -> Callable[[User], User]:
    """Reusable RBAC dependency factory. Do not hardcode role checks in controllers."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if not any(user.has_role(role) for role in role_names):
            raise AppError(
                "FORBIDDEN",
                "You do not have permission to perform this action.",
                403,
                details={"required_roles": list(role_names)},
            )
        return user

    return dependency


require_customer = require_roles("customer")
require_admin = require_roles("admin")
require_customer_or_admin = require_roles("customer", "admin")
