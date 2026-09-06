"""Add product media/specs, support tickets, and notifications.

Revision ID: 002_support_media
Revises: 001_initial
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_support_media"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            """
        ),
        {"table": table, "column": column},
    ).scalar()
    return bool(rows)


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
            """
        ),
        {"table": table},
    ).scalar()
    return bool(rows)


def upgrade() -> None:
    if not _has_column("products", "image_urls"):
        op.add_column("products", sa.Column("image_urls", sa.JSON(), nullable=True))
    if not _has_column("products", "specs"):
        op.add_column("products", sa.Column("specs", sa.JSON(), nullable=True))

    if not _has_table("support_tickets"):
        op.create_table(
            "support_tickets",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("subject", sa.String(length=200), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_support_tickets_customer_id", "support_tickets", ["customer_id"])
        op.create_index("ix_support_tickets_status", "support_tickets", ["status"])

    if not _has_table("support_messages"):
        op.create_table(
            "support_messages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("ticket_id", sa.Integer(), nullable=False),
            sa.Column("sender_id", sa.Integer(), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("is_staff", sa.Boolean(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["ticket_id"], ["support_tickets.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_support_messages_ticket_id", "support_messages", ["ticket_id"])
        op.create_index("ix_support_messages_sender_id", "support_messages", ["sender_id"])

    if not _has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("link", sa.String(length=500), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
        op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
        op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
        op.create_index("ix_notifications_expires_at", "notifications", ["expires_at"])


def downgrade() -> None:
    if _has_table("notifications"):
        op.drop_table("notifications")
    if _has_table("support_messages"):
        op.drop_table("support_messages")
    if _has_table("support_tickets"):
        op.drop_table("support_tickets")
    if _has_column("products", "specs"):
        op.drop_column("products", "specs")
    if _has_column("products", "image_urls"):
        op.drop_column("products", "image_urls")
