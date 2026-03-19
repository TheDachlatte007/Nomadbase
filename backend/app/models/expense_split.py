from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin


class ExpenseSplit(TimestampMixin, Base):
    __tablename__ = "expense_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    expense_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trip_participants.id"),
        nullable=False,
        index=True,
    )
    share_amount = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "expense_id",
            "participant_id",
            name="uq_expense_split_participant",
        ),
    )
