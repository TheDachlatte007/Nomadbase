from uuid import uuid4
from sqlalchemy import Column, String, Text, ForeignKey, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"), nullable=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=True)
    date = Column(Date, nullable=False, server_default=func.current_date())
