import uuid
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from sqlalchemy.ext.mutable import MutableList

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)

    current_status = Column(String, nullable=False, default="pending")

    # ✅ IMPORTANT: this makes SQLAlchemy detect JSON list changes and persist them
    status_history = Column(MutableList.as_mutable(JSON), nullable=False, default=list)

    extracted_text = Column(Text, nullable=True)
    analysis_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())