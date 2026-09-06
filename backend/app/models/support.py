import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False,
        default=TicketStatus.OPEN,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id])
    messages: Mapped[list["SupportMessage"]] = relationship(
        "SupportMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportMessage.created_at",
    )

    @property
    def display_id(self) -> str:
        return f"SUP-{10000 + self.id}"


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_staff: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["SupportTicket"] = relationship("SupportTicket", back_populates="messages")
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
