from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin


class City(TimestampMixin, Base):
    __tablename__ = "cities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=True)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    trip = relationship("Trip", back_populates="cities")
