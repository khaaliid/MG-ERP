"""
SQLAlchemy models for the Ads service
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Ad(Base):
    """An advertisement entry served to the frontend AdSlot."""
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)  # higher value = shown first
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
