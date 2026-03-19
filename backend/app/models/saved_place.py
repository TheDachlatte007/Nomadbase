from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class SavedPlace(TimestampMixin, Base):
    __tablename__ = "saved_places"
    __table_args__ = (
        Index(
            "ix_saved_places_trip_id",
            "trip_id",
        ),
        Index(
            "uq_saved_places_place_global",
            "place_id",
            unique=True,
            postgresql_where=text("trip_id IS NULL"),
        ),
        Index(
            "uq_saved_places_place_trip",
            "place_id",
            "trip_id",
            unique=True,
            postgresql_where=text("trip_id IS NOT NULL"),
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=True)
    status = Column(String(20), nullable=False)  # "want_to_visit", "visited", "favorite"
    notes = Column(Text, nullable=True)

    place = relationship("Place")
    trip = relationship("Trip")
