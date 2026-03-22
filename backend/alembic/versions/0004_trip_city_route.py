"""trip city routing and saved city assignment

Revision ID: 0004_trip_city_route
Revises: 0003_trip_saves
Create Date: 2026-03-22 13:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0004_trip_city_route"
down_revision: Union[str, None] = "0003_trip_saves"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cities",
        sa.Column("sort_order", sa.Integer(), nullable=True, server_default="0"),
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY trip_id
                    ORDER BY created_at ASC, name ASC
                ) - 1 AS computed_sort_order
            FROM cities
        )
        UPDATE cities
        SET sort_order = ranked.computed_sort_order
        FROM ranked
        WHERE cities.id = ranked.id
        """
    )
    op.alter_column("cities", "sort_order", server_default=None, nullable=False)
    op.create_index(
        "ix_cities_trip_sort_order",
        "cities",
        ["trip_id", "sort_order"],
        unique=False,
    )

    op.add_column(
        "saved_places",
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_saved_places_city_id_cities",
        "saved_places",
        "cities",
        ["city_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_saved_places_city_id", "saved_places", ["city_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_saved_places_city_id", table_name="saved_places")
    op.drop_constraint(
        "fk_saved_places_city_id_cities",
        "saved_places",
        type_="foreignkey",
    )
    op.drop_column("saved_places", "city_id")

    op.drop_index("ix_cities_trip_sort_order", table_name="cities")
    op.drop_column("cities", "sort_order")
