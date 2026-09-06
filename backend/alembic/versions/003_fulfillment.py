"""Add fulfillment shipping fields, statuses, and job runs.

Revision ID: 003_fulfillment
Revises: 002_support_media
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_fulfillment"
down_revision: Union[str, None] = "002_support_media"
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
    if not _has_column("orders", "shipping_country"):
        op.add_column(
            "orders",
            sa.Column("shipping_country", sa.String(length=2), nullable=False, server_default="US"),
        )
    if not _has_column("orders", "shipping_country_name"):
        op.add_column("orders", sa.Column("shipping_country_name", sa.String(length=100), nullable=True))
    if not _has_column("orders", "current_location"):
        op.add_column("orders", sa.Column("current_location", sa.String(length=255), nullable=True))
    if not _has_column("orders", "status_changed_at"):
        op.add_column("orders", sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True))

    # Map legacy shipped → dispatched for existing rows.
    op.execute(sa.text("UPDATE orders SET status = 'dispatched' WHERE status = 'shipped'"))
    op.execute(
        sa.text(
            """
            UPDATE orders
            SET current_location = 'New York, NY, USA'
            WHERE payment_status = 'paid'
              AND status NOT IN ('pending', 'cancelled', 'delivered')
              AND (current_location IS NULL OR current_location = '')
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE orders
            SET status_changed_at = COALESCE(updated_at, created_at)
            WHERE status_changed_at IS NULL
              AND status NOT IN ('pending', 'cancelled')
            """
        )
    )

    if not _has_table("fulfillment_job_runs"):
        op.create_table(
            "fulfillment_job_runs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("run_date", sa.Date(), nullable=False),
            sa.Column("triggered_by", sa.String(length=32), nullable=False),
            sa.Column("advanced_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_fulfillment_job_runs_run_date", "fulfillment_job_runs", ["run_date"])


def downgrade() -> None:
    if _has_table("fulfillment_job_runs"):
        op.drop_index("ix_fulfillment_job_runs_run_date", table_name="fulfillment_job_runs")
        op.drop_table("fulfillment_job_runs")

    op.execute(sa.text("UPDATE orders SET status = 'shipped' WHERE status = 'dispatched'"))
    op.execute(
        sa.text(
            """
            UPDATE orders SET status = 'shipped'
            WHERE status IN ('out_for_delivery', 'in_transit_international', 'customs_clearance')
            """
        )
    )

    if _has_column("orders", "status_changed_at"):
        op.drop_column("orders", "status_changed_at")
    if _has_column("orders", "current_location"):
        op.drop_column("orders", "current_location")
    if _has_column("orders", "shipping_country_name"):
        op.drop_column("orders", "shipping_country_name")
    if _has_column("orders", "shipping_country"):
        op.drop_column("orders", "shipping_country")
