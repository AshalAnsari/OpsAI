from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.role import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthUserResponse, LoginRequest, RegisterRequest, TokenResponse
from app.utils.exceptions import AppError


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditRepository(db)

    def register(self, payload: RegisterRequest) -> tuple[TokenResponse, AuthUserResponse]:
        existing = self.users.get_by_email(payload.email.lower())
        if existing:
            raise AppError("EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", 409)

        role = self.users.get_role_by_name("customer")
        if not role:
            raise AppError("ROLE_NOT_FOUND", "Customer role is not configured.", 500)

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            is_active=True,
            roles=[role],
        )
        self.users.create(user)
        self.audit.create(
            user_id=user.id,
            action="user.registered",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"email": user.email},
        )
        self.db.commit()
        self.db.refresh(user)

        token = TokenResponse(access_token=create_access_token(str(user.id), {"roles": user.role_names}))
        return token, self._to_auth_user(user)

    def login(self, payload: LoginRequest) -> tuple[TokenResponse, AuthUserResponse]:
        user = self.users.get_by_email(payload.email.lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
        if not user.is_active:
            raise AppError("ACCOUNT_DISABLED", "This account has been deactivated.", 403)

        self.audit.create(
            user_id=user.id,
            action="user.login",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"email": user.email},
        )
        self.db.commit()

        token = TokenResponse(access_token=create_access_token(str(user.id), {"roles": user.role_names}))
        return token, self._to_auth_user(user)

    def get_me(self, user: User) -> AuthUserResponse:
        return self._to_auth_user(user)

    @staticmethod
    def _to_auth_user(user: User) -> AuthUserResponse:
        return AuthUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            roles=user.role_names,
        )
