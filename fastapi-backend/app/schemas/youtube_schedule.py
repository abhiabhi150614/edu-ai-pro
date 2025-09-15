from pydantic import BaseModel
from typing import List, Any, Optional
from datetime import datetime

class VideoItem(BaseModel):
    videoId: str
    title: str
    thumbnail: str
    duration: int

class DaySchedule(BaseModel):
    day: int
    videos: List[VideoItem]

class YouTubeScheduleCreate(BaseModel):
    playlist_id: str
    playlist_url: str
    playlist_title: str
    daily_minutes: int
    schedule: List[DaySchedule]
    start_time: str
    duration_minutes: int

class YouTubeScheduleOut(BaseModel):
    id: int
    playlist_id: str
    playlist_url: str
    playlist_title: str
    daily_minutes: int
    schedule: List[DaySchedule]
    start_time: str
    duration_minutes: int
    created: datetime
    class Config:
        orm_mode = True 