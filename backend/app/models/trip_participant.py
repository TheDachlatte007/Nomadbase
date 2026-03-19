from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class TripParticipant(TimestampMixin, Base):
    __tablename__ = "trip_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    note = Column(Text, nullable=True)

    trip = relationship("Trip", back_populates="participants")
