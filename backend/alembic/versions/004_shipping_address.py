"""Add shipping street address fields to orders.

Revision ID: 004_shipping_address
Revises: 003_fulfillment
Create Date: 2026-09-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_shipping_address"
down_revision: Union[str, None] = "003_fulfillment"
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
    )
    return int(rows.scalar() or 0) > 0


def upgrade() -> None:
    columns = [
        ("shipping_address_line1", sa.String(length=200)),
        ("shipping_address_line2", sa.String(length=200)),
        ("shipping_city", sa.String(length=100)),
        ("shipping_state", sa.String(length=100)),
        ("shipping_postal_code", sa.String(length=20)),
    ]
    for name, col_type in columns:
        if not _has_column("orders", name):
            op.add_column("orders", sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    for name in (
        "shipping_postal_code",
        "shipping_state",
        "shipping_city",
        "shipping_address_line2",
        "shipping_address_line1",
    ):
        if _has_column("orders", name):
            op.drop_column("orders", name)
