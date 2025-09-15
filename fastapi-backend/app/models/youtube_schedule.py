from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class YouTubeSchedule(Base):
    __tablename__ = "youtube_schedules"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    playlist_id = Column(String)
    playlist_url = Column(String)
    playlist_title = Column(String)
    daily_minutes = Column(Integer)
    schedule = Column(JSONB)  # [{day, videos: [{videoId, title, thumbnail, duration}]}]
    start_time = Column(String, nullable=True)  # e.g. '21:00'
    duration_minutes = Column(Integer, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="youtube_schedules") 