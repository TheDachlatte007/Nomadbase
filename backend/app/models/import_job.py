from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin


class ImportJob(TimestampMixin, Base):
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    city = Column(String(200), nullable=False)
    country = Column(String(100), nullable=True)
    region = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="running")
    imported_count = Column(Integer, nullable=False, default=0)
    total_elements = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
