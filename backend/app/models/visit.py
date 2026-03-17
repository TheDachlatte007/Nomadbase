from uuid import uuid4
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class Visit(TimestampMixin, Base):
    __tablename__ = "visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"), nullable=False)
    visited_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes = Column(Text, nullable=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=True)
