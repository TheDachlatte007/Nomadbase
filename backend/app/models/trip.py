from uuid import uuid4
from sqlalchemy import Column, String, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    cities = relationship(
        "City",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="City.sort_order",
    )
    participants = relationship(
        "TripParticipant", back_populates="trip", cascade="all, delete-orphan"
    )
