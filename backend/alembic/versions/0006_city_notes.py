"""city notes

Revision ID: 0006_city_notes
Revises: 0005_import_job_history
Create Date: 2026-03-23 11:15:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0006_city_notes"
down_revision: Union[str, None] = "0005_import_job_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cities", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("cities", "notes")
