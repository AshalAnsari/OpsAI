from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.utils.pagination import PaginatedResponse, PaginationParams

NOTIFICATION_TTL_DAYS = 7


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: int,
        title: str,
        body: str,
        link: str | None = None,
    ) -> Notification:
        now = datetime.now(UTC)
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            link=link,
            is_read=False,
            expires_at=now + timedelta(days=NOTIFICATION_TTL_DAYS),
        )
        self.db.add(notification)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def _active_filter(self, user_id: int):
        now = datetime.now(UTC)
        return and_(
            Notification.user_id == user_id,
            Notification.expires_at > now,
        )

    def list_for_user(
        self,
        user_id: int,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Notification], int]:
        query = select(Notification).where(self._active_filter(user_id))
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            self.db.scalars(query.order_by(Notification.created_at.desc()).offset(offset).limit(limit))
        )
        return items, total

    def unread_count(self, user_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(Notification.id)).where(
                    self._active_filter(user_id),
                    Notification.is_read.is_(False),
                )
            )
            or 0
        )

    def get_for_user(self, notification_id: int, user_id: int) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                self._active_filter(user_id),
            )
        )

    def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.db.add(notification)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def mark_all_read(self, user_id: int) -> int:
        items, _ = self.list_for_user(user_id, offset=0, limit=500)
        count = 0
        for item in items:
            if not item.is_read:
                item.is_read = True
                self.db.add(item)
                count += 1
        self.db.flush()
        return count
