from uuid import uuid4
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, TimestampMixin


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
