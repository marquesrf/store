"""Database schema (SQLAlchemy 2.0 Core).

Only tables live here — no mapping onto the domain classes. The domain stays
pure (frozen value objects, dict-keyed lines); the repository translates
rows <-> domain objects by hand. This is the data-mapper approach: the ORM
never dictates the shape of the domain.

``metadata`` is also what Alembic diffs against to autogenerate migrations.
"""

from __future__ import annotations

import sqlalchemy as sa

metadata = sa.MetaData()

orders = sa.Table(
    "orders",
    metadata,
    sa.Column("order_id", sa.String, primary_key=True),
    sa.Column("currency", sa.String(3), nullable=False),
    sa.Column("status", sa.String, nullable=False),
)

order_lines = sa.Table(
    "order_lines",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "order_id",
        sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("sku", sa.String, nullable=False),
    sa.Column("quantity", sa.Integer, nullable=False),
    sa.Column("unit_price_cents", sa.Integer, nullable=False),
    sa.UniqueConstraint("order_id", "sku", name="uq_order_sku"),
)
