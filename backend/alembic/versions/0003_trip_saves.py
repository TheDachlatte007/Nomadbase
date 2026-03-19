"""trip scoped saved places

Revision ID: 0003_trip_saves
Revises: 0002_trip_shared_finance
Create Date: 2026-03-20 00:20:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0003_trip_saves"
down_revision: Union[str, None] = "0002_trip_shared_finance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "saved_places",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_saved_places_trip_id_trips",
        "saved_places",
        "trips",
        ["trip_id"],
        ["id"],
    )
    op.create_index("ix_saved_places_trip_id", "saved_places", ["trip_id"], unique=False)
    op.create_index(
        "uq_saved_places_place_global",
        "saved_places",
        ["place_id"],
        unique=True,
        postgresql_where=sa.text("trip_id IS NULL"),
    )
    op.create_index(
        "uq_saved_places_place_trip",
        "saved_places",
        ["place_id", "trip_id"],
        unique=True,
        postgresql_where=sa.text("trip_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_saved_places_place_trip", table_name="saved_places")
    op.drop_index("uq_saved_places_place_global", table_name="saved_places")
    op.drop_index("ix_saved_places_trip_id", table_name="saved_places")
    op.drop_constraint(
        "fk_saved_places_trip_id_trips",
        "saved_places",
        type_="foreignkey",
    )
    op.drop_column("saved_places", "trip_id")
