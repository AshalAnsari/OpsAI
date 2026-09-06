from sqlalchemy.orm import Session

from app.models.role import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import CustomerProfileResponse, UserProfileUpdate, UserResponse
from app.utils.exceptions import AppError


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def get_profile(self, user: User) -> CustomerProfileResponse:
        stats = (
            self.users.customer_profile_stats(user.id)
            if user.has_role("customer")
            else {
                "order_count": 0,
                "paid_order_count": 0,
                "pending_orders": 0,
                "delivered_orders": 0,
                "cancelled_orders": 0,
                "total_spent": 0.0,
                "average_order_value": 0.0,
            }
        )
        return CustomerProfileResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            roles=user.role_names,
            created_at=user.created_at,
            updated_at=user.updated_at,
            initials=self._initials(user),
            **stats,
        )

    def update_profile(self, user: User, payload: UserProfileUpdate) -> CustomerProfileResponse:
        if payload.first_name is not None:
            cleaned = payload.first_name.strip()
            if not cleaned:
                raise AppError("INVALID_NAME", "First name cannot be empty.", 400)
            user.first_name = cleaned
        if payload.last_name is not None:
            cleaned = payload.last_name.strip()
            if not cleaned:
                raise AppError("INVALID_NAME", "Last name cannot be empty.", 400)
            user.last_name = cleaned
        self.users.update(user)
        self.db.commit()
        self.db.refresh(user)
        return self.get_profile(user)

    def get_customer_or_404(self, customer_id: int) -> User:
        user = self.users.get_by_id(customer_id)
        if not user or not user.has_role("customer"):
            raise AppError("CUSTOMER_NOT_FOUND", "Customer not found.", 404)
        return user

    @staticmethod
    def _initials(user: User) -> str:
        first = (user.first_name or "").strip()
        last = (user.last_name or "").strip()
        if first and last:
            return f"{first[0]}{last[0]}".upper()
        if first:
            return first[:2].upper()
        return "OP"

    @staticmethod
    def _to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            roles=user.role_names,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
