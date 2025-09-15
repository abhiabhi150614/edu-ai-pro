from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.youtube_schedule import YouTubeSchedule
from app.models.user import User
from app.schemas.youtube_schedule import YouTubeScheduleCreate, YouTubeScheduleOut
from app.core.security import decode_token
from app.core.google_auth import get_google_oauth2_session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import requests
from datetime import datetime, timedelta

bearer_scheme = HTTPBearer()
router = APIRouter()

@router.get("/youtube-schedules", response_model=List[YouTubeScheduleOut])
def get_youtube_schedules(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    schedules = db.query(YouTubeSchedule).filter(YouTubeSchedule.user_id == int(user_id)).all()
    return schedules

@router.post("/youtube-schedules", response_model=YouTubeScheduleOut)
def add_youtube_schedule(data: YouTubeScheduleCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    schedule = YouTubeSchedule(
        user_id=int(user_id),
        playlist_id=data.playlist_id,
        playlist_url=data.playlist_url,
        playlist_title=data.playlist_title,
        daily_minutes=data.daily_minutes,
        schedule=[d.dict() for d in data.schedule],
        start_time=data.start_time,
        duration_minutes=data.duration_minutes
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/youtube-schedules/{schedule_id}")
def delete_youtube_schedule(schedule_id: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    schedule = db.query(YouTubeSchedule).filter(YouTubeSchedule.id == schedule_id, YouTubeSchedule.user_id == int(user_id)).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"msg": "Deleted"}

# In Google Calendar sync, use schedule.start_time and schedule.duration_minutes
@router.post("/youtube-schedules/{schedule_id}/sync-to-google-calendar")
def sync_schedule_to_google_calendar(schedule_id: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    schedule = db.query(YouTubeSchedule).filter(YouTubeSchedule.id == schedule_id, YouTubeSchedule.user_id == int(user_id)).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user.is_google_authenticated:
        raise HTTPException(status_code=400, detail="User must be authenticated with Google to sync to calendar")
    try:
        session = get_google_oauth2_session(user.google_id)
        
        # Parse start_time (e.g. '21:00') - this is user's local time
        hour, minute = 21, 0
        if schedule.start_time:
            try:
                hour, minute = map(int, schedule.start_time.split(':'))
            except Exception:
                pass
        
        duration_window = schedule.duration_minutes or 60
        
        # Use today's date with user's specified time (local time)
        today = datetime.now()
        start_date = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
        created_events = []
        
        for day_schedule in schedule.schedule:
            day_number = day_schedule.get('day', 1)
            videos = day_schedule.get('videos', [])
            event_date = start_date + timedelta(days=day_number - 1)
            
            # Calculate total video duration for this day
            total_video_duration = sum(video.get('duration', 600) for video in videos)
            total_video_minutes = total_video_duration // 60
            
            # If total video duration exceeds user's time window, distribute proportionally
            if total_video_minutes > duration_window:
                # Scale down video durations to fit within time window
                scale_factor = duration_window / total_video_minutes
                current_time = event_date.replace(hour=hour, minute=minute)
                
                for video in videos:
                    video_duration_seconds = video.get('duration', 600)
                    scaled_duration_minutes = max(1, int((video_duration_seconds // 60) * scale_factor))
                    
                    event = {
                        'summary': f"📚 {video.get('title', 'Learning Video')}",
                        'description': f"Learning video from playlist: {schedule.playlist_title}\n\nVideo URL: {video.get('url', '')}\nOriginal Duration: {video_duration_seconds // 60} minutes\nScheduled Duration: {scaled_duration_minutes} minutes",
                        'start': {
                            'dateTime': current_time.isoformat(),
                            'timeZone': 'Asia/Kolkata'  # Use India timezone
                        },
                        'end': {
                            'dateTime': (current_time + timedelta(minutes=scaled_duration_minutes)).isoformat(),
                            'timeZone': 'Asia/Kolkata'  # Use India timezone
                        },
                        'colorId': '4',
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'popup', 'minutes': 15}
                            ]
                        }
                    }
                    
                    response = session.post(
                        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                        json=event
                    )
                    if response.status_code == 200:
                        created_events.append(response.json())
                    else:
                        print(f"Failed to create event: {response.status_code} - {response.text}")
                    
                    current_time += timedelta(minutes=scaled_duration_minutes)
            else:
                # Videos fit within time window, use actual durations
                current_time = event_date.replace(hour=hour, minute=minute)
                
                for video in videos:
                    video_duration_seconds = video.get('duration', 600)
                    video_duration_minutes = max(1, video_duration_seconds // 60)
                    
                    event = {
                        'summary': f"📚 {video.get('title', 'Learning Video')}",
                        'description': f"Learning video from playlist: {schedule.playlist_title}\n\nVideo URL: {video.get('url', '')}\nDuration: {video_duration_minutes} minutes",
                        'start': {
                            'dateTime': current_time.isoformat(),
                            'timeZone': 'Asia/Kolkata'  # Use India timezone
                        },
                        'end': {
                            'dateTime': (current_time + timedelta(minutes=video_duration_minutes)).isoformat(),
                            'timeZone': 'Asia/Kolkata'  # Use India timezone
                        },
                        'colorId': '4',
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'popup', 'minutes': 15}
                            ]
                        }
                    }
                    
                    response = session.post(
                        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                        json=event
                    )
                    if response.status_code == 200:
                        created_events.append(response.json())
                    else:
                        print(f"Failed to create event: {response.status_code} - {response.text}")
                    
                    current_time += timedelta(minutes=video_duration_minutes)
        
        return {
            "message": f"Successfully synced {len(created_events)} events to Google Calendar",
            "events_created": len(created_events),
            "schedule_title": schedule.playlist_title
        }
    except Exception as e:
        print(f"Error syncing to Google Calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync to Google Calendar: {str(e)}")

@router.post("/youtube-schedules/sync-all-to-google-calendar")
def sync_all_schedules_to_google_calendar(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user.is_google_authenticated:
        raise HTTPException(status_code=400, detail="User must be authenticated with Google to sync to calendar")
    schedules = db.query(YouTubeSchedule).filter(YouTubeSchedule.user_id == int(user_id)).all()
    if not schedules:
        raise HTTPException(status_code=404, detail="No schedules found")
    try:
        session = get_google_oauth2_session(user.google_id)
        total_events_created = 0
        
        for schedule in schedules:
            # Parse start_time (e.g. '21:00') - this is user's local time
            hour, minute = 21, 0
            if schedule.start_time:
                try:
                    hour, minute = map(int, schedule.start_time.split(':'))
                except Exception:
                    pass
            
            duration_window = schedule.duration_minutes or 60
            
            # Use today's date with user's specified time (local time)
            today = datetime.now()
            start_date = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            for day_schedule in schedule.schedule:
                day_number = day_schedule.get('day', 1)
                videos = day_schedule.get('videos', [])
                event_date = start_date + timedelta(days=day_number - 1)
                
                # Calculate total video duration for this day
                total_video_duration = sum(video.get('duration', 600) for video in videos)
                total_video_minutes = total_video_duration // 60
                
                # If total video duration exceeds user's time window, distribute proportionally
                if total_video_minutes > duration_window:
                    # Scale down video durations to fit within time window
                    scale_factor = duration_window / total_video_minutes
                    current_time = event_date.replace(hour=hour, minute=minute)
                    
                    for video in videos:
                        video_duration_seconds = video.get('duration', 600)
                        scaled_duration_minutes = max(1, int((video_duration_seconds // 60) * scale_factor))
                        
                        event = {
                            'summary': f"📚 {video.get('title', 'Learning Video')}",
                            'description': f"Learning video from playlist: {schedule.playlist_title}\n\nVideo URL: {video.get('url', '')}\nOriginal Duration: {video_duration_seconds // 60} minutes\nScheduled Duration: {scaled_duration_minutes} minutes",
                            'start': {
                                'dateTime': current_time.isoformat(),
                                'timeZone': 'Asia/Kolkata'  # Use India timezone
                            },
                            'end': {
                                'dateTime': (current_time + timedelta(minutes=scaled_duration_minutes)).isoformat(),
                                'timeZone': 'Asia/Kolkata'  # Use India timezone
                            },
                            'colorId': '4',
                            'reminders': {
                                'useDefault': False,
                                'overrides': [
                                    {'method': 'popup', 'minutes': 15}
                                ]
                            }
                        }
                        
                        response = session.post(
                            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                            json=event
                        )
                        if response.status_code == 200:
                            total_events_created += 1
                        else:
                            print(f"Failed to create event: {response.status_code} - {response.text}")
                        
                        current_time += timedelta(minutes=scaled_duration_minutes)
                else:
                    # Videos fit within time window, use actual durations
                    current_time = event_date.replace(hour=hour, minute=minute)
                    
                    for video in videos:
                        video_duration_seconds = video.get('duration', 600)
                        video_duration_minutes = max(1, video_duration_seconds // 60)
                        
                        event = {
                            'summary': f"📚 {video.get('title', 'Learning Video')}",
                            'description': f"Learning video from playlist: {schedule.playlist_title}\n\nVideo URL: {video.get('url', '')}\nDuration: {video_duration_minutes} minutes",
                            'start': {
                                'dateTime': current_time.isoformat(),
                                'timeZone': 'Asia/Kolkata'  # Use India timezone
                            },
                            'end': {
                                'dateTime': (current_time + timedelta(minutes=video_duration_minutes)).isoformat(),
                                'timeZone': 'Asia/Kolkata'  # Use India timezone
                            },
                            'colorId': '4',
                            'reminders': {
                                'useDefault': False,
                                'overrides': [
                                    {'method': 'popup', 'minutes': 15}
                                ]
                            }
                        }
                        
                        response = session.post(
                            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                            json=event
                        )
                        if response.status_code == 200:
                            total_events_created += 1
                        else:
                            print(f"Failed to create event: {response.status_code} - {response.text}")
                        
                        current_time += timedelta(minutes=video_duration_minutes)
        
        return {
            "message": f"Successfully synced {total_events_created} events to Google Calendar",
            "events_created": total_events_created,
            "schedules_synced": len(schedules)
        }
    except Exception as e:
        print(f"Error syncing to Google Calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync to Google Calendar: {str(e)}") 