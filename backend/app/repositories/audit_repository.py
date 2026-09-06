from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata,
        )
        self.db.add(log)
        self.db.flush()
        self.db.refresh(log)
        return log

    def list_logs(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).options(selectinload(AuditLog.user))
        if action:
            query = query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        logs = list(
            self.db.scalars(query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit))
        )
        return logs, total

    def recent(self, limit: int = 10) -> list[AuditLog]:
        return list(
            self.db.scalars(
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
        )
