"""
core/models.py
Database models for the surveillance system.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Alert(Base):
    """Alert database model."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), nullable=False)
    activity_type = Column(String(50), nullable=False)
    event_state = Column(String(20), nullable=False)
    track_ids = Column(String(255), nullable=False)  # JSON string of track IDs
    camera_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    message = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string of extra data
    snapshot_path = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.activity_type}, camera={self.camera_id})>"


class Zone(Base):
    """Configurable polygon zone for a camera."""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String(50), nullable=False, index=True)
    zone_name = Column(String(100), nullable=False)
    zone_type = Column(String(50), nullable=False)
    points = Column(Text, nullable=False)  # JSON string of [x, y] points
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Zone(id={self.id}, type={self.zone_type}, camera={self.camera_id})>"


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./artifacts/surveillance.db")
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
