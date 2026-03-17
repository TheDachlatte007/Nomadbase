from uuid import uuid4
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class SavedPlace(TimestampMixin, Base):
    __tablename__ = "saved_places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"), nullable=False)
    status = Column(String(20), nullable=False)  # "want_to_visit", "visited", "favorite"
    notes = Column(Text, nullable=True)

    place = relationship("Place")
