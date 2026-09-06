from sqlalchemy.orm import Session

from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.utils.exceptions import AppError
from app.utils.pagination import PaginatedResponse, PaginationParams


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notifications = NotificationRepository(db)

    def notify(
        self,
        *,
        user_id: int,
        title: str,
        body: str,
        link: str | None = None,
        commit: bool = False,
    ) -> None:
        self.notifications.create(user_id=user_id, title=title, body=body, link=link)
        if commit:
            self.db.commit()

    def list_notifications(
        self,
        user_id: int,
        pagination: PaginationParams,
    ) -> PaginatedResponse[NotificationResponse]:
        items, total = self.notifications.list_for_user(
            user_id,
            offset=pagination.offset,
            limit=pagination.page_size,
        )
        return PaginatedResponse.create(
            [NotificationResponse.model_validate(item) for item in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    def unread_count(self, user_id: int) -> UnreadCountResponse:
        return UnreadCountResponse(unread_count=self.notifications.unread_count(user_id))

    def mark_read(self, user_id: int, notification_id: int) -> NotificationResponse:
        item = self.notifications.get_for_user(notification_id, user_id)
        if not item:
            raise AppError("NOTIFICATION_NOT_FOUND", "Notification not found.", 404)
        self.notifications.mark_read(item)
        self.db.commit()
        return NotificationResponse.model_validate(item)

    def mark_all_read(self, user_id: int) -> dict:
        count = self.notifications.mark_all_read(user_id)
        self.db.commit()
        return {"marked": count}
