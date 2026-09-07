from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.role import User
from app.models.support import SupportMessage, SupportTicket, TicketStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.support_repository import SupportRepository
from app.schemas.support import (
    SupportMessageResponse,
    SupportTicketResponse,
    TicketCreate,
    TicketMessageCreate,
    TicketStatusUpdate,
)
from app.services.notification_service import NotificationService
from app.utils.email import send_email
from app.utils.exceptions import AppError
from app.utils.pagination import PaginatedResponse, PaginationParams

settings = get_settings()


class SupportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tickets = SupportRepository(db)
        self.audit = AuditRepository(db)
        self.notifications = NotificationService(db)

    def create_ticket(self, customer: User, payload: TicketCreate) -> SupportTicketResponse:
        ticket = SupportTicket(
            customer_id=customer.id,
            subject=payload.subject.strip(),
            status=TicketStatus.OPEN,
        )
        self.tickets.create_ticket(ticket)
        self.db.flush()
        message = SupportMessage(
            ticket_id=ticket.id,
            sender_id=customer.id,
            body=payload.message.strip(),
            is_staff=False,
        )
        self.tickets.add_message(message)
        self.audit.create(
            user_id=customer.id,
            action="support.ticket_created",
            entity_type="support_ticket",
            entity_id=str(ticket.id),
            metadata={"subject": ticket.subject},
        )
        self.db.commit()
        refreshed = self.tickets.get_ticket(ticket.id)
        assert refreshed is not None
        return self._to_response(refreshed)

    def list_customer_tickets(
        self,
        customer: User,
        pagination: PaginationParams,
    ) -> PaginatedResponse[SupportTicketResponse]:
        items, total = self.tickets.list_for_customer(
            customer.id,
            offset=pagination.offset,
            limit=pagination.page_size,
        )
        return PaginatedResponse.create(
            [self._to_response(t, include_messages=False) for t in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    def get_customer_ticket(self, customer: User, ticket_id: int) -> SupportTicketResponse:
        ticket = self.tickets.get_ticket(ticket_id)
        if not ticket or ticket.customer_id != customer.id:
            raise AppError("TICKET_NOT_FOUND", "Support ticket not found.", 404)
        return self._to_response(ticket)

    def customer_reply(self, customer: User, ticket_id: int, payload: TicketMessageCreate) -> SupportTicketResponse:
        ticket = self.tickets.get_ticket(ticket_id)
        if not ticket or ticket.customer_id != customer.id:
            raise AppError("TICKET_NOT_FOUND", "Support ticket not found.", 404)
        if ticket.status == TicketStatus.CLOSED:
            raise AppError("TICKET_CLOSED", "This ticket is closed.", 400)

        self.tickets.add_message(
            SupportMessage(
                ticket_id=ticket.id,
                sender_id=customer.id,
                body=payload.body.strip(),
                is_staff=False,
            )
        )
        if ticket.status == TicketStatus.RESOLVED:
            ticket.status = TicketStatus.OPEN
        self.db.commit()
        refreshed = self.tickets.get_ticket(ticket.id)
        assert refreshed is not None
        return self._to_response(refreshed)

    def list_admin_tickets(
        self,
        pagination: PaginationParams,
        status: TicketStatus | None = None,
    ) -> PaginatedResponse[SupportTicketResponse]:
        items, total = self.tickets.list_all(
            offset=pagination.offset,
            limit=pagination.page_size,
            status=status,
        )
        return PaginatedResponse.create(
            [self._to_response(t, include_messages=False) for t in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    def get_admin_ticket(self, ticket_id: int) -> SupportTicketResponse:
        ticket = self.tickets.get_ticket(ticket_id)
        if not ticket:
            raise AppError("TICKET_NOT_FOUND", "Support ticket not found.", 404)
        return self._to_response(ticket)

    def admin_reply(self, admin: User, ticket_id: int, payload: TicketMessageCreate) -> SupportTicketResponse:
        ticket = self.tickets.get_ticket(ticket_id)
        if not ticket:
            raise AppError("TICKET_NOT_FOUND", "Support ticket not found.", 404)

        self.tickets.add_message(
            SupportMessage(
                ticket_id=ticket.id,
                sender_id=admin.id,
                body=payload.body.strip(),
                is_staff=True,
            )
        )
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS

        self.notifications.notify(
            user_id=ticket.customer_id,
            title="Support reply received",
            body=f"Harbor Dock Station support replied to {ticket.display_id}: {ticket.subject}",
            link=f"/support/{ticket.id}",
        )
        self.audit.create(
            user_id=admin.id,
            action="support.staff_replied",
            entity_type="support_ticket",
            entity_id=str(ticket.id),
        )

        customer_email = ticket.customer.email if ticket.customer else None
        if customer_email:
            send_email(
                to_email=customer_email,
                subject=f"[Harbor Dock Station] Reply on {ticket.display_id}: {ticket.subject}",
                body=(
                    f"Hello,\n\n"
                    f"Our support team replied to your ticket {ticket.display_id}.\n\n"
                    f"Subject: {ticket.subject}\n\n"
                    f"Reply:\n{payload.body.strip()}\n\n"
                    f"View the conversation: {settings.frontend_url}/support/{ticket.id}\n\n"
                    f"— Harbor Dock Station Support\n"
                ),
            )

        self.db.commit()
        refreshed = self.tickets.get_ticket(ticket.id)
        assert refreshed is not None
        return self._to_response(refreshed)

    def update_status(self, admin: User, ticket_id: int, payload: TicketStatusUpdate) -> SupportTicketResponse:
        ticket = self.tickets.get_ticket(ticket_id)
        if not ticket:
            raise AppError("TICKET_NOT_FOUND", "Support ticket not found.", 404)
        ticket.status = payload.status
        self.audit.create(
            user_id=admin.id,
            action="support.status_changed",
            entity_type="support_ticket",
            entity_id=str(ticket.id),
            metadata={"status": payload.status.value},
        )
        self.db.commit()
        refreshed = self.tickets.get_ticket(ticket.id)
        assert refreshed is not None
        return self._to_response(refreshed)

    def _to_response(self, ticket: SupportTicket, include_messages: bool = True) -> SupportTicketResponse:
        messages: list[SupportMessageResponse] = []
        if include_messages:
            messages = [
                SupportMessageResponse(
                    id=m.id,
                    ticket_id=m.ticket_id,
                    sender_id=m.sender_id,
                    sender_name=(
                        f"{m.sender.first_name} {m.sender.last_name}" if m.sender else None
                    ),
                    body=m.body,
                    is_staff=m.is_staff,
                    created_at=m.created_at,
                )
                for m in ticket.messages
            ]
        return SupportTicketResponse(
            id=ticket.id,
            display_id=ticket.display_id,
            customer_id=ticket.customer_id,
            customer_email=ticket.customer.email if ticket.customer else None,
            customer_name=(
                f"{ticket.customer.first_name} {ticket.customer.last_name}" if ticket.customer else None
            ),
            subject=ticket.subject,
            status=ticket.status,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            messages=messages,
        )
