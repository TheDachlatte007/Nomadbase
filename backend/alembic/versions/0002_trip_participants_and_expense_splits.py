"""trip participants and expense splits

Revision ID: 0002_trip_participants_and_expense_splits
Revises: 0001_initial_schema
Create Date: 2026-03-19 22:40:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0002_trip_participants_and_expense_splits"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trip_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trip_participants_trip_id"),
        "trip_participants",
        ["trip_id"],
        unique=False,
    )

    op.add_column(
        "expenses",
        sa.Column(
            "paid_by_participant_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_expenses_paid_by_participant_id_trip_participants",
        "expenses",
        "trip_participants",
        ["paid_by_participant_id"],
        ["id"],
    )

    op.create_table(
        "expense_splits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("share_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_id"], ["trip_participants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_expense_splits_expense_id"),
        "expense_splits",
        ["expense_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_expense_splits_participant_id"),
        "expense_splits",
        ["participant_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_expense_split_participant",
        "expense_splits",
        ["expense_id", "participant_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_expense_split_participant",
        "expense_splits",
        type_="unique",
    )
    op.drop_index(op.f("ix_expense_splits_participant_id"), table_name="expense_splits")
    op.drop_index(op.f("ix_expense_splits_expense_id"), table_name="expense_splits")
    op.drop_table("expense_splits")
    op.drop_constraint(
        "fk_expenses_paid_by_participant_id_trip_participants",
        "expenses",
        type_="foreignkey",
    )
    op.drop_column("expenses", "paid_by_participant_id")
    op.drop_index(op.f("ix_trip_participants_trip_id"), table_name="trip_participants")
    op.drop_table("trip_participants")
