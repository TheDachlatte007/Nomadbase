from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin


class Place(TimestampMixin, Base):
    __tablename__ = "places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    osm_id = Column(BigInteger, unique=True, index=True, nullable=True)
    name = Column(String(500), nullable=False, index=True)
    place_type = Column(String(100), nullable=False, index=True)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    tags = Column(JSONB, default=dict)
    description = Column(Text, nullable=True)
    source = Column(String(50), default="osm")
    raw_osm_tags = Column(JSONB, default=dict)
    region = Column(String(200), nullable=True, index=True)

    __table_args__ = (
        Index("idx_places_location", "location", postgresql_using="gist"),
        Index("idx_places_type_region", "place_type", "region"),
    )
