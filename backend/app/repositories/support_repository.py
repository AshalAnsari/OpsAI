from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.support import SupportMessage, SupportTicket, TicketStatus


class SupportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_ticket(self, ticket: SupportTicket) -> SupportTicket:
        self.db.add(ticket)
        self.db.flush()
        self.db.refresh(ticket)
        return ticket

    def add_message(self, message: SupportMessage) -> SupportMessage:
        self.db.add(message)
        self.db.flush()
        self.db.refresh(message)
        return message

    def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        return self.db.scalar(
            select(SupportTicket)
            .options(
                selectinload(SupportTicket.messages).selectinload(SupportMessage.sender),
                selectinload(SupportTicket.customer),
            )
            .where(SupportTicket.id == ticket_id)
        )

    def list_for_customer(
        self,
        customer_id: int,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[SupportTicket], int]:
        query = (
            select(SupportTicket)
            .options(selectinload(SupportTicket.messages), selectinload(SupportTicket.customer))
            .where(SupportTicket.customer_id == customer_id)
        )
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            self.db.scalars(query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit))
        )
        return items, total

    def list_all(
        self,
        *,
        offset: int,
        limit: int,
        status: TicketStatus | None = None,
    ) -> tuple[list[SupportTicket], int]:
        query = select(SupportTicket).options(
            selectinload(SupportTicket.messages),
            selectinload(SupportTicket.customer),
        )
        if status:
            query = query.where(SupportTicket.status == status)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            self.db.scalars(query.order_by(SupportTicket.updated_at.desc()).offset(offset).limit(limit))
        )
        return items, total
