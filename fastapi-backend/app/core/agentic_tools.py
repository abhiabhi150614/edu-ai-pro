"""
LangChain Tool Wrappers for EduAI Agentic System
Plug-and-play tools for extensible agent capabilities
"""

import re
import json
from typing import Dict, Any, List, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from app.core.google_services import get_day_notes, update_day_notes
from app.core.youtube_services import (
    search_youtube_videos, create_playlist, add_video_to_playlist, 
    get_video_summary, extract_video_id_from_url, get_user_playlists
)
from app.core.learning_path_service import LearningPathService
from app.core.agent_memory import memory_manager
from app.models.user import User
from app.models.learning_plan import LearningPlan
from sqlalchemy.orm import Session
from app.database.db import get_db

# Tool Input Schemas
class ToolInput(BaseModel):
    user_id: int = Field(description="User ID")
    params: Dict[str, Any] = Field(description="Tool parameters")
    context: str = Field(description="User context")

class NotesInput(BaseModel):
    query: str = Field(description="Notes query or content to add")
    day: Optional[int] = Field(description="Specific day number")
    month: Optional[int] = Field(description="Specific month number")

class YouTubeInput(BaseModel):
    query: str = Field(description="Search query or playlist name")
    video_url: Optional[str] = Field(description="YouTube video URL")
    playlist_name: Optional[str] = Field(description="Playlist name")

# Core Tool Functions
def get_notes_tool(query: str, user_id: int = None, day: int = None, month: int = None) -> Dict[str, Any]:
    """Get notes for specific day"""
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Extract day/month from query if not provided
        if not day:
            day_match = re.search(r'day\s*(\d+)', query.lower())
            day = int(day_match.group(1)) if day_match else user.current_day
        
        if not month:
            month_match = re.search(r'month\s*(\d+)', query.lower())
            month = int(month_match.group(1)) if month_match else user.current_month_index
        
        notes_data = get_day_notes(user_id, month, day)
        
        if notes_data:
            # Store in memory and create graph links
            memory_manager.store_episodic(user_id, "get_notes", {
                "day": day, "month": month, "notes_link": notes_data.get("link")
            })
            memory_manager.create_learning_path_graph(
                user_id, day, f"day_{day}_notes", [notes_data.get("link")]
            )
            
            return {
                "success": True,
                "content": notes_data.get("content"),
                "link": notes_data.get("link"),
                "markdown_link": f"[📘 Day {day} Notes]({notes_data.get('link')})"
            }
        
        return {"success": False, "message": f"No notes found for Day {day}"}
    finally:
        db.close()

def search_youtube_tool(query: str, user_id: int = None) -> Dict[str, Any]:
    """Search YouTube videos"""
    videos = search_youtube_videos(user_id, query, 5)
    
    if videos:
        video_links = [v.get('url') for v in videos]
        
        # Store in memory and create graph links
        memory_manager.store_episodic(user_id, "search_videos", {
            "query": query, "video_links": video_links
        })
        
        # Link videos to concepts
        concepts = memory_manager._extract_concepts(query)
        for concept in concepts:
            memory_manager.create_learning_path_graph(
                user_id, 0, concept, video_links
            )
        
        return {
            "success": True,
            "videos": videos[:3],
            "top_video_link": videos[0].get('url'),
            "markdown_links": [f"[🎥 {v.get('title')}]({v.get('url')})" for v in videos[:3]]
        }
    
    return {"success": False, "message": f"No videos found for '{query}'"}

def create_playlist_tool(playlist_name: str, user_id: int = None) -> Dict[str, Any]:
    """Create YouTube playlist"""
    result = create_playlist(user_id, playlist_name, f"Learning playlist: {playlist_name}")
    
    if result and result.get('id'):
        # Store in memory and create graph links
        memory_manager.store_episodic(user_id, "create_playlist", {
            "playlist_name": playlist_name,
            "playlist_url": result.get('url')
        })
        memory_manager.link_concepts(user_id, "playlists", playlist_name, "contains")
        
        return {
            "success": True,
            "playlist_name": playlist_name,
            "playlist_url": result.get('url'),
            "markdown_link": f"[🎯 {playlist_name} Playlist]({result.get('url')})"
        }
    
    return {"success": False, "error": "Failed to create playlist"}

def get_progress_tool(user_id: int = None) -> Dict[str, Any]:
    """Get learning progress"""
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        plan = db.query(LearningPlan).filter(LearningPlan.user_id == user_id).first()
        
        if not user or not plan:
            return {"error": "User or plan not found"}
        
        summary = LearningPathService.get_user_progress_summary(db, user_id, plan.id)
        
        progress_data = {
            "current_day": user.current_day,
            "current_month": user.current_month_index,
            "overall_progress": summary.get('overall_progress_percentage', 0),
            "days_completed": summary.get('total_days_completed', 0)
        }
        
        # Store in memory
        memory_manager.store_episodic(user_id, "get_progress", progress_data)
        
        return {"success": True, "progress": progress_data}
    finally:
        db.close()

# LangChain Tool Definitions
NotesTool = StructuredTool.from_function(
    func=get_notes_tool,
    name="NotesTool",
    description="Get or manage learning notes from Google Drive",
    args_schema=NotesInput
)

YouTubeSearchTool = StructuredTool.from_function(
    func=search_youtube_tool,
    name="YouTubeSearchTool", 
    description="Search for educational YouTube videos",
    args_schema=YouTubeInput
)

PlaylistTool = StructuredTool.from_function(
    func=create_playlist_tool,
    name="PlaylistTool",
    description="Create YouTube playlists for learning",
    args_schema=YouTubeInput
)

ProgressTool = StructuredTool.from_function(
    func=get_progress_tool,
    name="ProgressTool",
    description="Get learning progress and recommendations"
)

# Future extensible tools (examples)
def calendar_tool(event_title: str, user_id: int = None) -> Dict[str, Any]:
    """Create calendar events (future implementation)"""
    return {"success": True, "message": "Calendar integration coming soon"}

def linkedin_tool(post_content: str, user_id: int = None, day: int = None) -> Dict[str, Any]:
    """Share learning progress on LinkedIn via MCP"""
    from app.core.mcp_linkedin import post_to_linkedin_mcp
    
    # Use current day if not specified
    if not day:
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            day = user.current_day if user else 1
        finally:
            db.close()
    
    # Generate shareable LinkedIn link
    result = post_to_linkedin_mcp(user_id, day, method="link")
    return result

CalendarTool = StructuredTool.from_function(
    func=calendar_tool,
    name="CalendarTool",
    description="Manage learning schedule in Google Calendar"
)

LinkedInTool = StructuredTool.from_function(
    func=linkedin_tool,
    name="LinkedInTool", 
    description="Share learning achievements on LinkedIn"
)

def get_all_tools() -> List[StructuredTool]:
    """Get all available tools for the agent"""
    return [
        NotesTool,
        YouTubeSearchTool, 
        PlaylistTool,
        ProgressTool,
        CalendarTool,  # Future
        LinkedInTool   # Future
    ]

class AgenticToolsIntegrator:
    """Legacy integrator - kept for backward compatibility"""
    
    @staticmethod
    async def execute_notes_tool(user_id: int, function: str, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Execute notes-related tools"""
        try:
            if function == "get_day_notes":
                return await AgenticToolsIntegrator._get_notes(user_id, params, context, db)
            elif function == "add_note":
                return await AgenticToolsIntegrator._add_note(user_id, params, context, db)
            elif function == "get_notes_link":
                return await AgenticToolsIntegrator._get_notes_link(user_id, params, context, db)
            else:
                return {"error": f"Unknown notes function: {function}"}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def execute_youtube_tool(user_id: int, function: str, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Execute YouTube-related tools"""
        try:
            if function == "search_videos":
                return await AgenticToolsIntegrator._search_videos(user_id, params, context, db)
            elif function == "create_playlist":
                return await AgenticToolsIntegrator._create_playlist(user_id, params, context, db)
            elif function == "add_to_playlist":
                return await AgenticToolsIntegrator._add_to_playlist(user_id, params, context, db)
            elif function == "summarize_video":
                return await AgenticToolsIntegrator._summarize_video(user_id, params, context, db)
            else:
                return {"error": f"Unknown YouTube function: {function}"}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def execute_progress_tool(user_id: int, function: str, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Execute progress-related tools"""
        try:
            if function == "get_progress":
                return await AgenticToolsIntegrator._get_progress(user_id, params, context, db)
            elif function == "recommend_next_step":
                return await AgenticToolsIntegrator._recommend_next(user_id, params, context, db)
            else:
                return {"error": f"Unknown progress function: {function}"}
        except Exception as e:
            return {"error": str(e)}
    
    # Notes tool implementations
    @staticmethod
    async def _get_notes(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Get notes for specific day"""
        message = params.get("message", "")
        
        # Extract day and month from message or context
        day_match = re.search(r'day\s*(\d+)', message.lower())
        month_match = re.search(r'month\s*(\d+)', message.lower())
        
        # Get user's current position if not specified
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        day = int(day_match.group(1)) if day_match else user.current_day
        month = int(month_match.group(1)) if month_match else user.current_month_index
        
        notes_data = get_day_notes(user_id, month, day)
        
        if notes_data:
            # Store in memory
            memory_manager.store_episodic(user_id, "get_notes", {
                "day": day,
                "month": month,
                "notes_link": notes_data.get("link"),
                "content_preview": notes_data.get("content", "")[:100]
            })
            
            return {
                "success": True,
                "day": day,
                "month": month,
                "content": notes_data.get("content"),
                "link": notes_data.get("link"),
                "markdown_link": f"[📘 Access Day {day} Notes]({notes_data.get('link')})",
                "summary": f"Retrieved notes for Month {month}, Day {day}"
            }
        else:
            return {
                "success": False,
                "day": day,
                "month": month,
                "message": f"No notes found for Month {month}, Day {day}",
                "summary": f"No notes found for Month {month}, Day {day}"
            }
    
    @staticmethod
    async def _add_note(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Add content to notes"""
        message = params.get("message", "")
        
        # Extract content to add
        add_match = re.search(r'add\s+(.+?)\s+to\s+(?:day\s*(\d+))?', message.lower())
        if not add_match:
            return {"error": "Could not extract content to add"}
        
        content_to_add = add_match.group(1)
        day = int(add_match.group(2)) if add_match.group(2) else None
        
        # Get user's current position if day not specified
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        target_day = day if day else user.current_day
        target_month = user.current_month_index
        
        # Get existing notes
        existing_notes = get_day_notes(user_id, target_month, target_day)
        existing_content = existing_notes.get("content", "") if existing_notes else ""
        
        # Append new content
        updated_content = f"{existing_content}\n\n{content_to_add}" if existing_content else content_to_add
        
        # Update notes
        success = update_day_notes(user_id, target_month, target_day, updated_content)
        
        if success:
            # Get updated notes for link
            updated_notes = get_day_notes(user_id, target_month, target_day)
            link = updated_notes.get("link") if updated_notes else None
            
            # Store in memory
            memory_manager.store_episodic(user_id, "add_note", {
                "day": target_day,
                "month": target_month,
                "content_added": content_to_add,
                "notes_link": link
            })
            
            return {
                "success": True,
                "day": target_day,
                "month": target_month,
                "content_added": content_to_add,
                "link": link,
                "markdown_link": f"[📘 Access Updated Day {target_day} Notes]({link})" if link else None,
                "summary": f"Added content to Day {target_day} notes"
            }
        else:
            return {
                "success": False,
                "error": "Failed to update notes",
                "summary": "Failed to update notes"
            }
    
    @staticmethod
    async def _get_notes_link(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Get link to notes"""
        # Use get_notes and return just the link
        notes_result = await AgenticToolsIntegrator._get_notes(user_id, params, context, db)
        
        if notes_result.get("success"):
            return {
                "success": True,
                "link": notes_result.get("link"),
                "markdown_link": notes_result.get("markdown_link"),
                "summary": f"Retrieved link for Day {notes_result.get('day')} notes"
            }
        else:
            return notes_result
    
    # YouTube tool implementations
    @staticmethod
    async def _search_videos(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Search for YouTube videos"""
        message = params.get("message", "")
        
        # Extract search query
        search_patterns = [
            r'(?:find|search|get|show).*?videos?.*?(?:about|on|for)\s+(.+?)(?:\.|$)',
            r'(?:find|search|get|show)\s+(.+?)\s+videos?',
            r'videos?\s+(?:about|on|for)\s+(.+?)(?:\.|$)'
        ]
        
        search_query = None
        for pattern in search_patterns:
            match = re.search(pattern, message.lower())
            if match:
                search_query = match.group(1).strip()
                break
        
        if not search_query:
            # Try to get current learning topic from context
            if "CurrentDayConcept:" in context:
                concept_match = re.search(r'CurrentDayConcept:\s*(.+)', context)
                if concept_match:
                    search_query = f"tutorial {concept_match.group(1)}"
        
        if not search_query:
            return {"error": "Could not determine search query"}
        
        # Search for videos
        videos = search_youtube_videos(user_id, search_query, 5)
        
        if videos:
            # Store in memory
            video_links = [video.get('url') for video in videos if video.get('url')]
            memory_manager.store_episodic(user_id, "search_videos", {
                "query": search_query,
                "video_count": len(videos),
                "video_links": video_links,
                "top_video": videos[0] if videos else None
            })
            
            # Format response
            video_list = []
            for i, video in enumerate(videos[:3]):  # Top 3 videos
                video_list.append({
                    "title": video.get('title'),
                    "url": video.get('url'),
                    "channel": video.get('channel'),
                    "duration": f"{video.get('duration_seconds', 0) // 60}m{video.get('duration_seconds', 0) % 60}s",
                    "markdown_link": f"[🎥 {video.get('title')}]({video.get('url')})"
                })
            
            return {
                "success": True,
                "query": search_query,
                "video_count": len(videos),
                "videos": video_list,
                "top_video_link": videos[0].get('url') if videos else None,
                "summary": f"Found {len(videos)} videos for '{search_query}'"
            }
        else:
            return {
                "success": False,
                "query": search_query,
                "message": f"No videos found for '{search_query}'",
                "summary": f"No videos found for '{search_query}'"
            }
    
    @staticmethod
    async def _create_playlist(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Create YouTube playlist"""
        message = params.get("message", "")
        
        # Extract playlist name
        playlist_match = re.search(r'create.*?playlist.*?(?:called|named)\s*["\'](.+?)["\']', message.lower())
        if not playlist_match:
            playlist_match = re.search(r'playlist\s*["\'](.+?)["\']', message.lower())
        
        if not playlist_match:
            return {"error": "Could not extract playlist name"}
        
        playlist_name = playlist_match.group(1).strip()
        description = f"Learning playlist for {playlist_name} created by EduAI"
        
        # Create playlist
        result = create_playlist(user_id, playlist_name, description)
        
        if result and result.get('id') and 'error' not in result:
            # Store in memory
            memory_manager.store_episodic(user_id, "create_playlist", {
                "playlist_name": playlist_name,
                "playlist_id": result.get('id'),
                "playlist_url": result.get('url')
            })
            
            return {
                "success": True,
                "playlist_name": playlist_name,
                "playlist_id": result.get('id'),
                "playlist_url": result.get('url'),
                "markdown_link": f"[🎯 Access '{playlist_name}' Playlist]({result.get('url')})",
                "summary": f"Created playlist '{playlist_name}'"
            }
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            return {
                "success": False,
                "error": error_msg,
                "summary": f"Failed to create playlist '{playlist_name}'"
            }
    
    @staticmethod
    async def _add_to_playlist(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Add video to playlist"""
        message = params.get("message", "")
        
        # Extract playlist name
        playlist_patterns = [
            r'add.*?to.*?playlist\s*["\'](.+?)["\']',
            r'add.*?to\s+(.+?)\s*playlist',
            r'add.*?to\s+(.+?)(?:\s|$)'
        ]
        
        playlist_name = None
        for pattern in playlist_patterns:
            match = re.search(pattern, message.lower())
            if match:
                playlist_name = match.group(1).strip()
                break
        
        if not playlist_name:
            return {"error": "Could not extract playlist name"}
        
        # Get video ID - check for URL in message first
        video_id = None
        video_url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)', message)
        
        if video_url_match:
            video_url = video_url_match.group(1)
            video_id = extract_video_id_from_url(video_url)
        else:
            # Try to get last video from memory
            last_video_link = memory_manager.get_last_youtube_link(user_id)
            if last_video_link:
                video_id = extract_video_id_from_url(last_video_link)
        
        if not video_id:
            return {"error": "No video found to add. Please provide a YouTube URL or search for a video first."}
        
        # Get user's playlists to find the right one
        playlists = get_user_playlists(user_id)
        
        playlist_id = None
        for playlist in playlists:
            if playlist.get('title', '').lower().strip() == playlist_name.lower().strip():
                playlist_id = playlist.get('id')
                break
        
        if not playlist_id:
            # Try to create the playlist
            create_result = create_playlist(user_id, playlist_name, f"Learning playlist for {playlist_name}")
            if create_result and create_result.get('id'):
                playlist_id = create_result.get('id')
            else:
                return {"error": f"Playlist '{playlist_name}' not found and could not be created"}
        
        # Add video to playlist
        result = add_video_to_playlist(user_id, playlist_id, video_id)
        
        if result is True:
            # Store in memory
            memory_manager.store_episodic(user_id, "add_to_playlist", {
                "playlist_name": playlist_name,
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}"
            })
            
            return {
                "success": True,
                "playlist_name": playlist_name,
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "markdown_link": f"[🎥 Watch Added Video](https://www.youtube.com/watch?v={video_id})",
                "summary": f"Added video to '{playlist_name}' playlist"
            }
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            return {
                "success": False,
                "error": error_msg,
                "summary": f"Failed to add video to '{playlist_name}' playlist"
            }
    
    @staticmethod
    async def _summarize_video(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Summarize YouTube video"""
        message = params.get("message", "")
        
        # Extract video URL or ID
        video_url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)', message)
        video_id = None
        
        if video_url_match:
            video_url = video_url_match.group(1)
            video_id = extract_video_id_from_url(video_url)
        else:
            # Try to get last video from memory
            last_video_link = memory_manager.get_last_youtube_link(user_id)
            if last_video_link:
                video_id = extract_video_id_from_url(last_video_link)
        
        if not video_id:
            return {"error": "No video URL found to summarize"}
        
        # Get video summary
        summary = get_video_summary(user_id, video_id)
        
        if summary:
            # Store in memory
            memory_manager.store_episodic(user_id, "summarize_video", {
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "summary": summary[:200]  # Store first 200 chars
            })
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "summary": summary,
                "markdown_link": f"[🎥 Watch Summarized Video](https://www.youtube.com/watch?v={video_id})",
                "summary_text": f"Generated summary for video {video_id}"
            }
        else:
            return {
                "success": False,
                "error": "Could not generate video summary",
                "summary_text": "Failed to generate video summary"
            }
    
    # Progress tool implementations
    @staticmethod
    async def _get_progress(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Get user's learning progress"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            plan = db.query(LearningPlan).filter(LearningPlan.user_id == user_id).first()
            if not plan:
                return {"error": "Learning plan not found"}
            
            # Get progress summary
            summary = LearningPathService.get_user_progress_summary(db, user_id, plan.id)
            
            progress_data = {
                "current_day": user.current_day,
                "current_month": user.current_month_index,
                "plan_title": plan.title,
                "overall_progress": summary.get('overall_progress_percentage', 0),
                "days_completed": summary.get('total_days_completed', 0),
                "days_started": summary.get('total_days_started', 0),
                "total_days": summary.get('total_days', 0)
            }
            
            # Store in memory
            memory_manager.store_episodic(user_id, "get_progress", progress_data)
            
            return {
                "success": True,
                "progress": progress_data,
                "summary": f"You're {progress_data['overall_progress']}% through your learning plan"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def _recommend_next(user_id: int, params: Dict, context: str, db: Session) -> Dict[str, Any]:
        """Recommend next learning step"""
        try:
            progress_result = await AgenticToolsIntegrator._get_progress(user_id, params, context, db)
            
            if not progress_result.get("success"):
                return progress_result
            
            progress = progress_result["progress"]
            
            # Generate recommendation based on progress
            if progress["overall_progress"] < 10:
                recommendation = "Focus on completing your first few days to build momentum"
            elif progress["overall_progress"] < 50:
                recommendation = "You're making good progress! Keep up the daily learning routine"
            elif progress["overall_progress"] < 80:
                recommendation = "Great job! You're in the advanced stages - focus on practical projects"
            else:
                recommendation = "Excellent progress! Consider reviewing and reinforcing key concepts"
            
            return {
                "success": True,
                "recommendation": recommendation,
                "next_day": progress["current_day"] + 1,
                "current_progress": progress["overall_progress"],
                "summary": f"Recommended next step based on {progress['overall_progress']}% progress"
            }
            
        except Exception as e:
            return {"error": str(e)}

# Global tools integrator instance
tools_integrator = AgenticToolsIntegrator()