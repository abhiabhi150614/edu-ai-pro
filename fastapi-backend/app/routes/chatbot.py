import re
import requests
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.chatbot import ChatMessage, ChatResponse
from app.core.openai_ai import chatbot
from app.core.security import decode_token
from app.database.db import get_db
from app.core.learning_path_service import LearningPathService
from app.models.quiz import QuizSubmission
from app.models.learning_plan import LearningPlan
from app.models.user import User
from app.core.google_services import get_day_notes, list_drive_files, update_day_notes
from app.core.youtube_services import search_youtube_videos, get_user_playlists, create_playlist, add_video_to_playlist, get_video_summary, get_playlist_summary, extract_video_id_from_url
from app.core.config import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(message: ChatMessage, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Send message to AI chatbot and get response"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id_int = int(user_id)
        
        # Enrich user message with relevant learning context (lightweight, private)
        context_snippets = []
        try:
            # Get user information
            user = db.query(User).filter(User.id == user_id_int).first()
            if user:
                context_snippets.append(f"UserName: {user.google_name or user.email or 'User'}")
                context_snippets.append(f"CurrentDay: {user.current_day}")
                context_snippets.append(f"CurrentMonthIndex: {user.current_month_index}")
                context_snippets.append(f"UserID: {user.id}")
            
            # Get learning plan information
            plan = db.query(LearningPlan).filter(LearningPlan.user_id == user_id_int).first()
            if plan and plan.plan and isinstance(plan.plan, dict) and "months" in plan.plan:
                # Add plan title and creation date
                context_snippets.append(f"PlanTitle: {plan.title}")
                context_snippets.append(f"PlanCreatedAt: {plan.created_at}")
                
                # Current month/day light summary
                months = plan.plan.get("months", [])
                current_month_index = user.current_month_index if user else 1
                current_day = user.current_day if user else 1
                
                # Add plan title
                context_snippets.append(f"CurrentPlanTitle: {plan.title}")
                
                # Get current month information
                current_month = None
                for month in months:
                    if month.get("index") == current_month_index:
                        current_month = month
                        break
                
                if current_month:
                    context_snippets.append(f"CurrentMonth: {current_month.get('title')}")
                    context_snippets.append(f"MonthStatus: {current_month.get('status')}")
                    
                    # Get current day information
                    days = current_month.get("days", [])
                    if days and 0 < current_day <= len(days):
                        current_day_data = days[current_day - 1]
                        context_snippets.append(f"CurrentDayConcept: {current_day_data.get('concept')}")
                        context_snippets.append(f"CurrentDayCompleted: {current_day_data.get('completed', False)}")
                        
                        # Check if there are previous completed days
                        completed_days = []
                        for i, day in enumerate(days):
                            if day.get("completed", False):
                                completed_days.append(i + 1)
                        
                        if completed_days:
                            context_snippets.append(f"CompletedDays: {', '.join(map(str, completed_days))}")
                
                # Get previous month information if available
                if current_month_index > 1 and len(months) >= current_month_index - 1:
                    prev_month = months[current_month_index - 2]
                    context_snippets.append(f"PreviousMonth: {prev_month.get('title')}")
                    context_snippets.append(f"PreviousMonthStatus: {prev_month.get('status')}")
            
            # Comprehensive Learning History & Context
            if plan:
                # Overall progress summary
                summary = LearningPathService.get_user_progress_summary(db, user_id_int, plan.id)
                context_snippets.append(
                    f"Progress: days_completed={summary.get('total_days_completed',0)}, days_started={summary.get('total_days_started',0)}, overall={summary.get('overall_progress_percentage',0)}%"
                )
                
                # Full learning plan structure for context
                months = plan.plan.get("months", []) if isinstance(plan.plan, dict) else []
                context_snippets.append(f"TotalMonths: {len(months)}")
                
                # Previous months completion status
                completed_months = []
                for month in months:
                    if month.get("status") == "completed":
                        completed_months.append(f"M{month.get('index')}:{month.get('title')}")
                if completed_months:
                    context_snippets.append(f"CompletedMonths: {', '.join(completed_months)}")
            
            # Quick Quiz Analysis (optimized)
            recent_attempts = db.query(QuizSubmission).filter(
                QuizSubmission.user_id == user_id_int
            ).order_by(QuizSubmission.created_at.desc()).limit(3).all()
            
            if recent_attempts:
                failed_count = len([qa for qa in recent_attempts if not qa.passed])
                if failed_count > 0:
                    context_snippets.append(f"RecentFailures: {failed_count} failures in last 3 attempts")
                    last_failed = next((qa for qa in recent_attempts if not qa.passed), None)
                    if last_failed:
                        context_snippets.append(f"LastFailedQuiz: M{last_failed.month_index}D{last_failed.day}, score={last_failed.score}%")
            
            # AI Instructions for better responses
            context_snippets.append("InstructAI: Provide detailed, helpful responses with examples. Always suggest relevant YouTube videos and resources. Be encouraging and interactive.")
            context_snippets.append("InstructAI: Format responses with proper markdown, code blocks, and clickable links. Make responses comprehensive (3-5 paragraphs).")
                
            # Check if the user is asking about notes from Google Drive
            if any(keyword in message.message.lower() for keyword in ["notes", "day notes", "my notes", "fetch notes", "get notes", "show notes", "drive", "link"]):
                # Try to get notes for current day first
                if user and user.current_month_index and user.current_day:
                    notes_data = get_day_notes(user_id_int, user.current_month_index, user.current_day)
                    if notes_data:
                        notes_content = notes_data.get("content", "")
                        notes_link = notes_data.get("link", "")
                        context_snippets.append(f"CurrentDayNotes: {notes_content[:500]}..." if len(notes_content) > 500 else f"CurrentDayNotes: {notes_content}")
                        context_snippets.append(f"CurrentDayNotesLink: {notes_link}")
                        context_snippets.append(f"CurrentDayNotesLinkMarkdown: [Click here to access your Day {user.current_day} notes]({notes_link})")
                        context_snippets.append(f"InstructAI: Please provide the user with the clickable link to their notes using the CurrentDayNotesLinkMarkdown format. Also mention what day the notes are for.")
                
                # If user specifically asks for notes from a particular day
                day_match = re.search(r'day\s*(\d+)', message.message.lower())
                month_match = re.search(r'month\s*(\d+)', message.message.lower())
                
                # Check if user wants to add content to notes
                add_content_match = re.search(r'add\s+(.+?)\s+to\s+(?:the\s+)?(?:day\s*(\d+))?\s*(?:notes|note)', message.message.lower())
                
                # Handle "previous day", "yesterday", "next day", "tomorrow" references
                current_day = user.current_day if user else 1
                current_month = user.current_month_index if user else 1
                
                if "previous day" in message.message.lower() or "yesterday" in message.message.lower():
                    specific_day = max(1, current_day - 1)
                    specific_month = current_month
                    context_snippets.append(f"RequestingPreviousDay: Day {specific_day}, Month {specific_month}")
                elif "next day" in message.message.lower() or "tomorrow" in message.message.lower():
                    specific_day = current_day + 1
                    specific_month = current_month
                    context_snippets.append(f"RequestingNextDay: Day {specific_day}, Month {specific_month}")
                elif day_match:
                    specific_day = int(day_match.group(1))
                    specific_month = current_month
                    if month_match:
                        specific_month = int(month_match.group(1))
                    context_snippets.append(f"RequestingSpecificDay: Day {specific_day}, Month {specific_month}")
                
                if "previous day" in message.message.lower() or "yesterday" in message.message.lower() or "next day" in message.message.lower() or "tomorrow" in message.message.lower() or day_match:
                    specific_notes_data = get_day_notes(user_id_int, specific_month, specific_day)
                    if specific_notes_data:
                        specific_notes = specific_notes_data.get("content", "")
                        specific_link = specific_notes_data.get("link", "")
                        context_snippets.append(f"RequestedNotes_M{specific_month}_D{specific_day}: {specific_notes[:1000]}..." if len(specific_notes) > 1000 else f"RequestedNotes_M{specific_month}_D{specific_day}: {specific_notes}")
                        context_snippets.append(f"RequestedNotesLink_M{specific_month}_D{specific_day}: {specific_link}")
                        context_snippets.append(f"RequestedNotesLinkMarkdown_M{specific_month}_D{specific_day}: [Click here to access your Month {specific_month}, Day {specific_day} notes]({specific_link})")
                        context_snippets.append(f"NotesFound: Yes, found notes for Month {specific_month}, Day {specific_day}")
                        context_snippets.append(f"InstructAI: Please provide the user with the clickable link to their requested notes using the RequestedNotesLinkMarkdown format. Also mention what day and month the notes are for.")
                    else:
                        context_snippets.append(f"RequestedNotes_M{specific_month}_D{specific_day}: Not found")
                        context_snippets.append(f"NotesFound: No, could not find notes for Month {specific_month}, Day {specific_day}")
                
                # Handle adding content to notes
                if add_content_match:
                    content_to_add = add_content_match.group(1)
                    target_day = int(add_content_match.group(2)) if add_content_match.group(2) else current_day
                    context_snippets.append(f"AddContentRequest: User wants to add '{content_to_add}' to Day {target_day} notes")
                    
                    # Get existing notes first
                    existing_notes_data = get_day_notes(user_id_int, current_month, target_day)
                    existing_content = ""
                    if existing_notes_data:
                        existing_content = existing_notes_data.get("content", "")
                    
                    # Append new content to existing content
                    updated_content = f"{existing_content}\n\n{content_to_add}" if existing_content else content_to_add
                    
                    # Update notes
                    success = update_day_notes(user_id_int, current_month, target_day, updated_content)
                    if success:
                        # Get updated notes to get the link
                        updated_notes_data = get_day_notes(user_id_int, current_month, target_day)
                        if updated_notes_data:
                            context_snippets.append(f"NotesUpdated: Yes, successfully added content to Day {target_day} notes")
                            notes_link = updated_notes_data.get('link', '')
                            context_snippets.append(f"UpdatedNotesLink: {notes_link}")
                            context_snippets.append(f"UpdatedNotesLinkMarkdown: [Click here to access your updated Day {target_day} notes]({notes_link})")
                            context_snippets.append(f"InstructAI: Please confirm the content was added successfully and provide the user with the clickable link to their updated notes using the UpdatedNotesLinkMarkdown format. Also mention what content was added.")
                    else:
                        context_snippets.append(f"NotesUpdated: No, failed to add content to Day {target_day} notes")
                        context_snippets.append(f"InstructAI: Please inform the user that there was an error updating their notes and suggest they try again or check their Google Drive permissions.")
            

            # LinkedIn MCP functionality
            linkedin_keywords = ["linkedin", "post", "share", "social", "network", "post my", "share my"]
            if any(keyword in message.message.lower() for keyword in linkedin_keywords):
                from app.core.mcp_linkedin import post_to_linkedin_mcp
                
                # Check if user wants to post learning progress
                post_patterns = [
                    r'post.*?(?:day\s*(\d+))?.*?(?:learning|progress|quiz|topic)',
                    r'share.*?(?:day\s*(\d+))?.*?(?:learning|progress|quiz|topic)',
                    r'linkedin.*?(?:day\s*(\d+))?.*?(?:post|share)',
                    r'share.*?(?:day\s*(\d+))?.*?(?:to|on)\s*linkedin',
                    r'post.*?(?:about|regarding).*?(?:learned|learning).*?(\w+)',
                    r'share.*?(?:about|regarding).*?(?:learned|learning).*?(\w+)'
                ]
                
                day_to_post = None
                for pattern in post_patterns:
                    match = re.search(pattern, message.message.lower())
                    if match:
                        day_to_post = int(match.group(1)) if match.group(1) else user.current_day
                        break
                
                if day_to_post or "post" in message.message.lower() or "share" in message.message.lower():
                    target_day = day_to_post if day_to_post else user.current_day
                    
                    # Extract custom topic if mentioned
                    custom_topic = None
                    topic_patterns = [
                        r'(?:about|regarding).*?(?:learned|learning)\s+(\w+(?:\s+\w+)?)',
                        r'share.*?(python|javascript|react|ai|machine learning|data science|\w+).*?to.*?linkedin',
                        r'post.*?(python|javascript|react|ai|machine learning|data science|\w+).*?to.*?linkedin'
                    ]
                    
                    for pattern in topic_patterns:
                        topic_match = re.search(pattern, message.message.lower())
                        if topic_match:
                            custom_topic = topic_match.group(1).title()
                            break
                    
                    try:
                        # Generate shareable LinkedIn link
                        result = post_to_linkedin_mcp(user_id_int, target_day, method="link", custom_topic=custom_topic)
                        
                        if result.get("success"):
                            context_snippets.append(f"LinkedInShareLink: {result.get('share_link')}")
                            context_snippets.append(f"LinkedInContent: {result.get('content', '')[:200]}...")
                            context_snippets.append(f"LinkedInShareLinkMarkdown: [🔗 Click to Share on LinkedIn]({result.get('share_link')})")
                            context_snippets.append(f"InstructAI: Provide the user with the clickable LinkedIn share link using LinkedInShareLinkMarkdown format. Tell them it will open LinkedIn with their post pre-filled.")
                        else:
                            context_snippets.append(f"LinkedInError: {result.get('error', 'Failed to generate share link')}")
                            context_snippets.append(f"InstructAI: Inform user there was an error generating the LinkedIn share link.")
                    except Exception as e:
                        context_snippets.append(f"LinkedInError: {str(e)}")
                        context_snippets.append(f"InstructAI: Inform user about LinkedIn sharing error.")
            
            # YouTube-related functionality
            youtube_keywords = ["youtube", "video", "videos", "playlist", "find video", "search video", "link", "give me", "add to", "summary of", "summarize"]
            if any(keyword in message.message.lower() for keyword in youtube_keywords):
                # Store video search results for later use
                searched_videos = None
                
                # Check for video search request
                video_search_match = re.search(r'(?:find|give|show|get|search for|look for)\s+(?:me\s+)?(?:the\s+)?(?:video|videos|youtube|link)\s+(?:for|about|on|related to|on topic)\s+(.+?)(?:\.|$)', message.message.lower())
                
                # Check for specific learning topic request
                learning_topic_match = None
                if not video_search_match and plan and plan.plan and isinstance(plan.plan, dict) and "months" in plan.plan:
                    months = plan.plan.get("months", [])
                    current_month_index = user.current_month_index if user else 1
                    current_day = user.current_day if user else 1
                    
                    if 1 <= current_month_index <= len(months):
                        current_month = months[current_month_index - 1]
                        days = current_month.get("days", [])
                        if 0 < current_day <= len(days):
                            current_day_data = days[current_day - 1]
                            concept = current_day_data.get('concept')
                            if concept and ("today" in message.message.lower() or "current" in message.message.lower() or "learning" in message.message.lower()):
                                # Extract key terms from the concept for better search results
                                concept_keywords = re.sub(r'[\(\):]', '', concept)  # Remove parentheses and colons
                                concept_parts = concept_keywords.split(':')
                                main_concept = concept_parts[0] if concept_parts else concept_keywords
                                
                                # Create a more focused search query
                                learning_topic_match = f"tutorial {main_concept.strip()}"
                                context_snippets.append(f"YouTubeSearchRequest: User wants videos for today's learning topic: '{concept}'")
                                context_snippets.append(f"SearchQuery: Using optimized search query: '{learning_topic_match}'")
                
                search_query = ""
                if video_search_match:
                    search_query = video_search_match.group(1).strip()
                    context_snippets.append(f"YouTubeSearchRequest: User wants to find videos about '{search_query}'")
                elif learning_topic_match:
                    search_query = learning_topic_match
                elif "today" in message.message.lower() and "learning" in message.message.lower():
                    # If user just asks for today's learning without specific topic match
                    if plan and plan.plan and isinstance(plan.plan, dict) and "months" in plan.plan:
                        months = plan.plan.get("months", [])
                        current_month_index = user.current_month_index if user else 1
                        current_day = user.current_day if user else 1
                        
                        if 1 <= current_month_index <= len(months):
                            current_month = months[current_month_index - 1]
                            days = current_month.get("days", [])
                            if 0 < current_day <= len(days):
                                current_day_data = days[current_day - 1]
                                concept = current_day_data.get('concept')
                                if concept:
                                    # Create a more focused search query
                                    concept_keywords = re.sub(r'[\(\):]', '', concept)  # Remove parentheses and colons
                                    search_query = f"tutorial {concept_keywords.strip()}"
                                    context_snippets.append(f"YouTubeSearchRequest: User wants videos for today's learning topic: '{concept}'")
                                    context_snippets.append(f"SearchQuery: Using optimized search query: '{search_query}'")
                
                if search_query:
                    # Search for videos
                    searched_videos = search_youtube_videos(user_id_int, search_query, 5)  # Limit to 5 videos
                    if searched_videos:
                        context_snippets.append(f"YouTubeSearchResults: Found {len(searched_videos)} videos matching '{search_query}'")
                        
                        # Add detailed information about each video for better responses
                        for i, video in enumerate(searched_videos[:3]):  # Include top 3 videos in context
                            video_title = video.get('title', '')
                            video_url = video.get('url', '')
                            video_id = video.get('id', '')
                            video_duration_mins = video.get('duration_seconds', 0) // 60
                            video_duration_secs = video.get('duration_seconds', 0) % 60
                            video_channel = video.get('channel', '')
                            
                            # Format video information with complete details
                            context_snippets.append(f"Video{i+1}Title: {video_title}")
                            context_snippets.append(f"Video{i+1}URL: {video_url}")
                            context_snippets.append(f"Video{i+1}ID: {video_id}")
                            context_snippets.append(f"Video{i+1}Duration: {video_duration_mins}m{video_duration_secs}s")
                            context_snippets.append(f"Video{i+1}Channel: {video_channel}")
                            context_snippets.append(f"Video{i+1}URLMarkdown: [Watch: {video_title}]({video_url})")
                            
                            # Add a direct instruction for the AI to use this URL
                            if i == 0:  # For the first (most relevant) video
                                context_snippets.append(f"RecommendedVideoURL: {video_url}")
                                context_snippets.append(f"RecommendedVideoTitle: {video_title}")
                                context_snippets.append(f"RecommendedVideoID: {video_id}")
                                context_snippets.append(f"RecommendedVideoURLMarkdown: [Watch: {video_title}]({video_url})")
                                context_snippets.append(f"InstructAI: Please provide the user with the clickable link to the recommended video using the RecommendedVideoURLMarkdown format.")
                    else:
                        context_snippets.append(f"YouTubeSearchResults: No videos found matching '{search_query}'")
                
                # Check for playlist creation request
                create_playlist_match = re.search(r'(?:create|make)\s+(?:a|new)?\s*playlist\s+(?:called|named|with name)?\s*["\'](.+?)["\']', message.message.lower())
                if create_playlist_match:
                    playlist_name = create_playlist_match.group(1).strip()
                    context_snippets.append(f"CreatePlaylistRequest: User wants to create a playlist named '{playlist_name}'")
                    
                    # Create the playlist
                    try:
                        print(f"Creating playlist '{playlist_name}' for user {user_id_int}")
                        
                        # First check if user has Google authentication
                        user = db.query(User).filter(User.id == user_id_int).first()
                        if not user or not user.google_id or not user.google_access_token:
                            context_snippets.append(
                                f"PlaylistCreationError: User does not have proper Google authentication set up"
                            )
                            context_snippets.append(
                                "InstructAI: Please inform the user that they need to connect their Google account first. They should go to their profile settings and link their Google account with YouTube permissions."
                            )
                            logger.error(f"User {user_id_int} does not have Google authentication set up")
                        else:
                            print(f"User has Google authentication: {user.google_id}")
                            new_playlist = create_playlist(
                                user_id_int,
                                playlist_name,
                                f"Learning playlist for {playlist_name} created by EduAI"
                            )

                            print(f"Playlist creation result: {new_playlist}")
                            print(f"Type of result: {type(new_playlist)}")
                            print(f"Has 'id': {new_playlist.get('id') if new_playlist else 'None'}")
                            print(f"Has 'error': {'error' in new_playlist if isinstance(new_playlist, dict) else 'Not a dict'}")

                            if new_playlist and new_playlist.get('id') and 'error' not in new_playlist:
                                context_snippets.append(
                                    f"PlaylistCreated: Yes, created playlist '{playlist_name}' with ID {new_playlist.get('id')}"
                                )
                                context_snippets.append(f"PlaylistURL: {new_playlist.get('url')}")
                                context_snippets.append(
                                    f"PlaylistURLMarkdown: [Click here to access your '{playlist_name}' playlist]({new_playlist.get('url')})"
                                )
                                context_snippets.append(
                                    "InstructAI: Please confirm the playlist was created successfully and provide the user with the clickable link to their playlist using the PlaylistURLMarkdown format. Also mention the playlist name."
                                )

                                # Try to add a video to the newly created playlist
                                video_id = None
                                
                                # First check if there's a video URL in the message
                                video_url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)(?:[&\w=]*))', message.message)
                                if video_url_match:
                                    video_url = video_url_match.group(1)
                                    extracted_video_id = extract_video_id_from_url(video_url)
                                    if extracted_video_id:
                                        video_id = extracted_video_id
                                        print(f"Found video URL in message: {video_url}, extracted ID: {video_id}")
                                        context_snippets.append(f"VideoToAdd: Found video ID {video_id} from message URL")
                                    else:
                                        print(f"Could not extract video ID from URL: {video_url}")
                                        context_snippets.append(f"VideoToAdd: Could not extract video ID from URL {video_url}")
                                
                                # If no URL in message, check if we have recent search results
                                elif searched_videos and len(searched_videos) > 0:
                                    first_video = searched_videos[0]
                                    video_id = first_video.get('id')
                                    print(f"Using first search result video ID: {video_id}")
                                    context_snippets.append(f"VideoToAdd: Using first search result video ID {video_id}")
                                
                                # If still no video ID, check if the message mentions a specific video title
                                else:
                                    video_title_match = re.search(r'(?:video|add)\s+["\'](.+?)["\']', message.message.lower())
                                    if video_title_match:
                                        video_title = video_title_match.group(1)
                                        print(f"Searching for video with title: {video_title}")
                                        # Search for this specific video
                                        specific_videos = search_youtube_videos(user_id_int, video_title, 1)
                                        if specific_videos and len(specific_videos) > 0:
                                            video_id = specific_videos[0].get('id')
                                            print(f"Found video ID {video_id} for title '{video_title}'")
                                            context_snippets.append(f"VideoToAdd: Found video ID {video_id} for title '{video_title}'")
                                
                                if video_id:
                                    print(f"Attempting to add video {video_id} to new playlist '{playlist_name}'")
                                    result = add_video_to_playlist(user_id_int, new_playlist.get("id"), video_id)
                                    print(f"Auto-video addition result: {result}")
                                    
                                    if result is True:
                                        context_snippets.append(
                                            f"VideoAdded: Yes, successfully added video {video_id} to new playlist '{playlist_name}'"
                                        )
                                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                                        context_snippets.append(f"AddedVideoURL: {video_url}")
                                        context_snippets.append(f"AddedVideoURLMarkdown: [Watch the video you added]({video_url})")
                                        context_snippets.append(f"InstructAI: Please confirm the video was successfully added to the new playlist and provide the user with the clickable link to the video using the AddedVideoURLMarkdown format. Also mention which playlist it was added to.")
                                    elif isinstance(result, dict) and 'error' in result:
                                        error_message = result['error']
                                        context_snippets.append(
                                            f"VideoAdded: No, failed to add video {video_id} to playlist '{playlist_name}'. Error: {error_message}"
                                        )
                                        context_snippets.append(f"InstructAI: Please inform the user that there was an error adding the video to the playlist: {error_message}. Suggest they check their YouTube permissions or try again.")
                                    else:
                                        context_snippets.append(
                                            f"VideoAdded: No, failed to add video {video_id} to playlist '{playlist_name}'"
                                        )
                                else:
                                    print(f"No video found to add to new playlist '{playlist_name}'")
                                    context_snippets.append(f"VideoToAdd: No video URL found in message and no recent search results available")
                            else:
                                error_message = new_playlist.get('error', 'Unknown error') if isinstance(new_playlist, dict) else str(new_playlist)
                                context_snippets.append(
                                    f"PlaylistCreationError: Failed to create playlist '{playlist_name}'. Error: {error_message}"
                                )
                                context_snippets.append(
                                    f"InstructAI: Please inform the user that playlist creation failed: {error_message}. Suggest they check their Google authentication and YouTube permissions."
                                )
                                logger.error(f"Failed to create playlist '{playlist_name}' for user {user_id}. Error: {error_message}")

                    except Exception as e:
                        context_snippets.append(f"PlaylistCreationError: Exception occurred: {str(e)}")
                        context_snippets.append(
                            "InstructAI: Please inform the user that there was a technical error creating the playlist. Suggest they try again or contact support if the issue persists."
                        )
                        logger.error(f"Exception creating playlist '{playlist_name}' for user {user_id}: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                # Check for add to playlist request (multiple flexible patterns)
                playlist_match = None
                
                # Pattern 1: "add video to playlist name"
                playlist_match = re.search(r'add\s+(?:this|that|the)?\s*(?:video)?\s*(?:to|into)\s+(?:my|the)?\s*playlist\s*(?:called|named)?\s*["\']?([^"\']+?)["\']?(?:\s|$)', message.message.lower())
                
                # Pattern 2: "add to playlist name"
                if not playlist_match:
                    playlist_match = re.search(r'add\s+to\s+(?:my|the)?\s*playlist\s*(?:called|named)?\s*["\']?([^"\']+?)["\']?(?:\s|$)', message.message.lower())
                
                # Pattern 3: "add to name playlist"
                if not playlist_match:
                    playlist_match = re.search(r'add\s+(?:this|that|the)?\s*(?:video)?\s*(?:to|into)\s+["\']?([^"\']+?)["\']?\s*playlist', message.message.lower())
                
                # Pattern 4: "add video to name" (most flexible)
                if not playlist_match:
                    playlist_match = re.search(r'add\s+(?:this|that|the)?\s*(?:video)?\s*(?:to|into)\s+["\']?([^"\']+?)["\']?(?:\s|$)', message.message.lower())
                
                # Pattern 5: "add to name" (most basic)
                if not playlist_match:
                    playlist_match = re.search(r'add\s+to\s+["\']?([^"\']+?)["\']?(?:\s|$)', message.message.lower())
                
                if playlist_match:
                    playlist_name = playlist_match.group(1).strip()
                    print(f"🎯 DETECTED: Add to playlist request for '{playlist_name}'")
                    print(f"🎯 Original message: '{message.message}'")
                    print(f"🎯 Pattern matched: {playlist_match.group(0)}")
                    context_snippets.append(f"PlaylistRequest: User wants to add a video to playlist '{playlist_name}'")
                    
                    # Get user's playlists
                    playlists = get_user_playlists(user_id_int)
                    print(f"Found {len(playlists)} playlists for user {user_id_int}")
                    
                    # Check if the requested playlist exists
                    playlist_exists = False
                    playlist_id = None
                    playlist_url = None
                    for playlist in playlists:
                        playlist_title = playlist.get('title', '').lower().strip()
                        requested_name = playlist_name.lower().strip()
                        print(f"Checking playlist: '{playlist.get('title', '')}' against '{playlist_name}'")
                        print(f"  Normalized: '{playlist_title}' vs '{requested_name}'")
                        
                        if playlist_title == requested_name:
                            playlist_exists = True
                            playlist_id = playlist.get('id')
                            playlist_url = playlist.get('url')
                            print(f"✅ Found playlist: {playlist_id}")
                            break
                    
                    if playlist_exists:
                        print(f"🎯 SUCCESS: Found existing playlist '{playlist_name}' with ID {playlist_id}")
                        context_snippets.append(f"PlaylistFound: Yes, found playlist '{playlist_name}' with ID {playlist_id}")
                        context_snippets.append(f"PlaylistURL: {playlist_url}")
                        context_snippets.append(f"PlaylistURLMarkdown: [Access your '{playlist_name}' playlist]({playlist_url})")
                        
                        # Check if there's a video URL in the message to add
                        # Handle different YouTube URL formats
                        video_url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)(?:[&\w=]*))', message.message)
                        video_id = None
                        if video_url_match:
                            video_url = video_url_match.group(1)
                            # Use the improved video ID extraction
                            extracted_video_id = extract_video_id_from_url(video_url)
                            if extracted_video_id:
                                video_id = extracted_video_id
                                context_snippets.append(f"VideoToAdd: Found video ID {video_id} to add to playlist")
                                context_snippets.append(f"VideoURL: {video_url}")
                            else:
                                context_snippets.append(f"VideoToAdd: Could not extract video ID from URL {video_url}")
                        
                        # If no URL in message, check if we have recent search results
                        elif searched_videos and len(searched_videos) > 0:
                            first_video = searched_videos[0]
                            video_id = first_video.get('id')
                            context_snippets.append(f"VideoToAdd: Using first search result video ID {video_id} to add to playlist")
                        
                        # If still no video ID, check if the message mentions a specific video
                        else:
                            # Try to extract video title from message
                            video_title_match = re.search(r'(?:video|add)\s+["\'](.+?)["\']', message.message.lower())
                            if video_title_match:
                                video_title = video_title_match.group(1)
                                # Search for this specific video
                                specific_videos = search_youtube_videos(user_id_int, video_title, 1)
                                if specific_videos and len(specific_videos) > 0:
                                    video_id = specific_videos[0].get('id')
                                    context_snippets.append(f"VideoToAdd: Found video ID {video_id} for title '{video_title}'")
                        
                        if video_id:
                            # Add video to playlist
                            try:
                                print(f"🎯 ATTEMPTING: Add video {video_id} to existing playlist '{playlist_name}' (ID: {playlist_id})")
                                result = add_video_to_playlist(user_id_int, playlist_id, video_id)
                                print(f"🎯 VIDEO ADDITION RESULT: {result}")
                                
                                if result is True:
                                    context_snippets.append(f"VideoAdded: Yes, successfully added video {video_id} to playlist '{playlist_name}'")
                                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                                    context_snippets.append(f"AddedVideoURL: {video_url}")
                                    context_snippets.append(f"AddedVideoURLMarkdown: [Watch the video you added]({video_url})")
                                    context_snippets.append(f"InstructAI: Please confirm the video was successfully added to the playlist and provide the user with the clickable link to the video using the AddedVideoURLMarkdown format. Also mention which playlist it was added to.")
                                elif isinstance(result, dict) and 'error' in result:
                                    error_message = result['error']
                                    context_snippets.append(f"VideoAdded: No, failed to add video {video_id} to playlist '{playlist_name}'. Error: {error_message}")
                                    context_snippets.append(f"InstructAI: Please inform the user that there was an error adding the video to the playlist: {error_message}. Suggest they check their YouTube permissions or try again.")
                                    logger.error(f"Failed to add video {video_id} to playlist '{playlist_name}' for user {user_id_int}. Error: {error_message}")
                                else:
                                    context_snippets.append(f"VideoAdded: No, failed to add video {video_id} to playlist '{playlist_name}'")
                                    context_snippets.append(f"InstructAI: Please inform the user that there was an error adding the video to the playlist and suggest they check their YouTube permissions or try again.")
                            except Exception as e:
                                context_snippets.append(f"VideoAddError: {str(e)}")
                                logger.error(f"Error adding video to playlist: {str(e)}")
                        else:
                            context_snippets.append("VideoToAdd: No video URL found in message and no recent search results available")
                            context_snippets.append("InstructAI: Please inform the user that no video was found to add to the playlist. Ask them to provide a YouTube URL or search for a video first.")
                    else:
                        print(f"❌ Playlist '{playlist_name}' not found. Available playlists:")
                        for p in playlists:
                            print(f"  - '{p.get('title', '')}' (ID: {p.get('id', '')})")
                        context_snippets.append(f"PlaylistFound: No, could not find playlist '{playlist_name}'. Available playlists: {[p.get('title', '') for p in playlists]}")
                        
                        # Try to find a video to add to the existing playlist
                        video_id = None
                        
                        # First check if there's a video URL in the message
                        video_url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)(?:[&\w=]*))', message.message)
                        if video_url_match:
                            video_url = video_url_match.group(1)
                            extracted_video_id = extract_video_id_from_url(video_url)
                            if extracted_video_id:
                                video_id = extracted_video_id
                                print(f"Found video URL in message: {video_url}, extracted ID: {video_id}")
                                context_snippets.append(f"VideoToAdd: Found video ID {video_id} from message URL")
                            else:
                                print(f"Could not extract video ID from URL: {video_url}")
                                context_snippets.append(f"VideoToAdd: Could not extract video ID from URL {video_url}")
                        elif searched_videos and len(searched_videos) > 0:
                            first_video = searched_videos[0]
                            video_id = first_video.get('id')
                            print(f"Using first search result video ID: {video_id}")
                            context_snippets.append(f"VideoToAdd: Using first search result video ID {video_id}")
                        
                        # Create the playlist automatically
                        try:
                            print(f"Auto-creating playlist '{playlist_name}' for user {user_id_int}")
                            
                            # First check if user has Google authentication
                            user = db.query(User).filter(User.id == user_id_int).first()
                            if not user or not user.google_id or not user.google_access_token:
                                context_snippets.append(
                                    f"PlaylistCreationError: User does not have proper Google authentication set up"
                                )
                                context_snippets.append(
                                    "InstructAI: Please inform the user that they need to connect their Google account first. They should go to their profile settings and link their Google account with YouTube permissions."
                                )
                                logger.error(f"User {user_id_int} does not have Google authentication set up")
                            else:
                                print(f"User has Google authentication: {user.google_id}")
                                new_playlist = create_playlist(user_id_int, playlist_name, f"Learning playlist for {playlist_name} created by EduAI")
                                print(f"Auto-playlist creation result: {new_playlist}")
                                
                                if new_playlist and new_playlist.get('id') and 'error' not in new_playlist:
                                    context_snippets.append(f"PlaylistCreated: Yes, created playlist '{playlist_name}' with ID {new_playlist.get('id')}")
                                    context_snippets.append(f"PlaylistURL: {new_playlist.get('url')}")
                                    context_snippets.append(f"PlaylistURLMarkdown: [Click here to access your '{playlist_name}' playlist]({new_playlist.get('url')})")
                                    context_snippets.append(f"InstructAI: Please provide the user with the clickable link to their playlist using the PlaylistURLMarkdown format.")
                                    
                                    # Now try to add the video to the newly created playlist
                                    video_url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)(?:[&\w=]*))', message.message)
                                    video_id = None
                                    if video_url_match:
                                        video_url = video_url_match.group(1)
                                        extracted_video_id = extract_video_id_from_url(video_url)
                                        if extracted_video_id:
                                            video_id = extracted_video_id
                                    elif searched_videos and len(searched_videos) > 0:
                                        first_video = searched_videos[0]
                                        video_id = first_video.get('id')
                                    
                                    if video_id:
                                        result = add_video_to_playlist(user_id_int, new_playlist.get('id'), video_id)
                                        print(f"Auto-video addition result (second instance): {result}")
                                        
                                        if result is True:
                                            context_snippets.append(f"VideoAdded: Yes, successfully added video {video_id} to new playlist '{playlist_name}'")
                                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                                            context_snippets.append(f"AddedVideoURL: {video_url}")
                                            context_snippets.append(f"AddedVideoURLMarkdown: [Watch the video you added]({video_url})")
                                            context_snippets.append(f"InstructAI: Please confirm the video was successfully added to the new playlist and provide the user with the clickable link to the video using the AddedVideoURLMarkdown format. Also mention which playlist it was added to.")
                                        elif isinstance(result, dict) and 'error' in result:
                                            error_message = result['error']
                                            context_snippets.append(f"VideoAdded: No, failed to add video {video_id} to playlist '{playlist_name}'. Error: {error_message}")
                                            context_snippets.append(f"InstructAI: Please inform the user that there was an error adding the video to the playlist: {error_message}. Suggest they check their YouTube permissions or try again.")
                                        else:
                                            context_snippets.append(f"VideoAdded: No, failed to add video {video_id} to playlist '{playlist_name}'")
                                            context_snippets.append(f"InstructAI: Please inform the user that there was an error adding the video to the playlist and suggest they check their YouTube permissions or try again.")
                                else:
                                    error_message = new_playlist.get('error', 'Unknown error') if isinstance(new_playlist, dict) else str(new_playlist)
                                    context_snippets.append(f"PlaylistCreated: No, failed to create playlist '{playlist_name}'. Error: {error_message}")
                                    context_snippets.append(f"InstructAI: Please inform the user that playlist creation failed: {error_message}. Suggest they check their Google authentication and YouTube permissions.")
                                    logger.error(f"Failed to create playlist '{playlist_name}' for user {user_id}. Error: {error_message}")
                        except Exception as e:
                            context_snippets.append(f"PlaylistCreationError: Exception occurred: {str(e)}")
                            context_snippets.append(f"InstructAI: Please inform the user that there was a technical error creating the playlist. Suggest they try again or contact support if the issue persists.")
                            logger.error(f"Exception during playlist creation for user {user_id}: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                
                # Check for video summary request
                video_summary_match = re.search(r'(?:summarize|summary)\s+(?:of|for)?\s*(?:the)?\s*(?:video)?\s*(?:https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)(?:[&\w=]*))', message.message.lower())
                if not video_summary_match:
                    # Alternative pattern for video summary
                    video_summary_match = re.search(r'(?:summarize|summary)\s+(?:of|for)?\s*(?:the)?\s*(?:video)?\s*(?:with id)?\s*([\w-]{11})', message.message.lower())
                
                if video_summary_match:
                    video_id = video_summary_match.group(1)
                    
                    # If it's a URL, extract the video ID
                    if video_id.startswith('http'):
                        extracted_video_id = extract_video_id_from_url(video_id)
                        if extracted_video_id:
                            video_id = extracted_video_id
                        else:
                            context_snippets.append(f"VideoSummaryError: Could not extract video ID from URL {video_id}")
                            video_id = None
                    
                    if video_id:
                        context_snippets.append(f"VideoSummaryRequest: User wants a summary of video with ID {video_id}")
                        
                        # Get video summary
                        try:
                            summary = get_video_summary(user_id_int, video_id)
                            if summary:
                                context_snippets.append(f"VideoSummary: {summary}")
                            else:
                                context_snippets.append(f"VideoSummary: Could not generate summary for video with ID {video_id}")
                        except Exception as e:
                            context_snippets.append(f"VideoSummaryError: {str(e)}")
                            logger.error(f"Error generating video summary: {str(e)}")
                    else:
                        context_snippets.append(f"VideoSummaryError: No valid video ID found")
                
                # Check for playlist summary request
                playlist_summary_match = re.search(r'(?:summarize|summary)\s+(?:of|for)?\s*(?:the)?\s*(?:playlist)?\s*(?:https?://(?:www\.)?youtube\.com/playlist\?list=([\w-]+))', message.message.lower())
                if not playlist_summary_match:
                    # Alternative pattern for playlist summary
                    playlist_summary_match = re.search(r'(?:summarize|summary)\s+(?:of|for)?\s*(?:the)?\s*(?:playlist)?\s*(?:with id)?\s*([\w-]+)', message.message.lower())
                
                if playlist_summary_match:
                    playlist_id = playlist_summary_match.group(1)
                    context_snippets.append(f"PlaylistSummaryRequest: User wants a summary of playlist with ID {playlist_id}")
                    
                    # Get playlist summary
                    try:
                        summary = get_playlist_summary(user_id_int, playlist_id)
                        if summary:
                            context_snippets.append(f"PlaylistSummary: Playlist '{summary.get('title')}' has {summary.get('video_count')} videos with total duration {summary.get('total_duration')}")
                            # Add more detailed summary information
                            if 'videos' in summary:
                                for i, video in enumerate(summary['videos'][:3]):
                                    context_snippets.append(f"PlaylistVideo{i+1}: {video.get('title')} ({video.get('duration')})")
                        else:
                            context_snippets.append(f"PlaylistSummary: Could not generate summary for playlist with ID {playlist_id}")
                    except Exception as e:
                        context_snippets.append(f"PlaylistSummaryError: {str(e)}")
                        logger.error(f"Error generating playlist summary: {str(e)}")
        except Exception as e:
            logger.error(f"Context build error: {e}")

        enriched_message = message.message
        if context_snippets:
            # Include all context snippets
            enriched_message = (
                "[USER_CONTEXT]\n" + "\n".join(context_snippets) + "\n[/USER_CONTEXT]\n\n" + message.message
            )

        # Get agentic AI response with context and tool execution
        response_data = await chatbot.get_response(message.message, user_id_int, "\n".join(context_snippets))
        
        # Add memory context for frontend
        from app.core.agent_memory import memory_manager
        memory_context = memory_manager.get_contextual_memory(user_id_int, message.message)
        
        # Simplified memory context for faster responses
        frontend_memory = {
            "current_progress": {
                "day": user.current_day if user else 1,
                "percentage": summary.get('overall_progress_percentage', 0) if 'summary' in locals() else 0
            },
            "last_video": memory_manager.get_last_youtube_link(user_id_int),
            "recent_notes": f"Day {user.current_day} notes" if user else None,
            "playlists": memory_manager.get_user_playlists(user_id_int)
        }
        
        response_data["memory_context"] = frontend_memory
        response_data["learning_context"] = {
            "has_failures": len([qa for qa in recent_attempts if not qa.passed]) > 0 if 'recent_attempts' in locals() else False,
            "needs_help": True
        }
        
        return ChatResponse(
            response=response_data["response"],
            timestamp=response_data["timestamp"],
            message_id=response_data["message_id"]
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")

@router.post("/chat/clear")
async def clear_chat_history(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Clear chat session for user"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Clear chat session
        success = chatbot.clear_session(int(user_id))
        
        return {"message": "Chat history cleared successfully" if success else "No chat session to clear"}
        
    except Exception as e:
        logger.error(f"Clear chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")


@router.get("/notes/{month_index}/{day}")
async def get_notes(month_index: int, day: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get notes for a specific day from Google Drive"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get notes from Google Drive
        notes_data = get_day_notes(int(user_id), month_index, day)
        if not notes_data:
            return {"message": f"No notes found for Month {month_index}, Day {day}", "notes": None, "file_link": None}
        
        return {
            "message": "Notes retrieved successfully", 
            "notes": notes_data.get("content"), 
            "file_link": notes_data.get("link"),
            "file_id": notes_data.get("file_id")
        }
        
    except Exception as e:
        logger.error(f"Get notes error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notes: {str(e)}")


@router.post("/notes/{month_index}/{day}")
async def update_notes(month_index: int, day: int, content: dict, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Update notes for a specific day in Google Drive"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Validate content
        if "content" not in content:
            raise HTTPException(status_code=400, detail="Content field is required")
        
        # Update notes in Google Drive
        success = update_day_notes(int(user_id), month_index, day, content["content"])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update notes")
        
        # Get updated notes to return the link
        updated_notes = get_day_notes(int(user_id), month_index, day)
        
        return {
            "message": "Notes updated successfully",
            "file_link": updated_notes.get("link") if updated_notes else None
        }
        
    except Exception as e:
        logger.error(f"Update notes error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update notes: {str(e)}")


@router.get("/youtube/search")
async def search_videos(query: str, max_results: int = 10, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Search for YouTube videos based on a query"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Search for videos
        videos = search_youtube_videos(int(user_id), query, max_results)
        
        return {
            "message": f"Found {len(videos)} videos matching '{query}'",
            "videos": videos
        }
        
    except Exception as e:
        logger.error(f"YouTube search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search YouTube: {str(e)}")


@router.get("/youtube/playlists")
async def get_playlists(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get the user's YouTube playlists"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get playlists
        playlists = get_user_playlists(int(user_id))
        
        return {
            "message": f"Found {len(playlists)} playlists",
            "playlists": playlists
        }
        
    except Exception as e:
        logger.error(f"YouTube playlists error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get playlists: {str(e)}")


@router.post("/youtube/playlists")
async def create_new_playlist(playlist_data: dict, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Create a new YouTube playlist"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Validate playlist data
        if "title" not in playlist_data:
            raise HTTPException(status_code=400, detail="Title field is required")
        
        # Create playlist
        description = playlist_data.get("description", "")
        playlist = create_playlist(int(user_id), playlist_data["title"], description)
        
        if not playlist:
            raise HTTPException(status_code=500, detail="Failed to create playlist")
        
        return {
            "message": f"Playlist '{playlist_data['title']}' created successfully",
            "playlist": playlist
        }
        
    except Exception as e:
        logger.error(f"YouTube create playlist error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create playlist: {str(e)}")


@router.post("/youtube/playlists/{playlist_id}/videos")
async def add_to_playlist(playlist_id: str, video_data: dict, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Add a video to a YouTube playlist"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Validate video data
        if "video_id" not in video_data:
            raise HTTPException(status_code=400, detail="Video ID field is required")
        
        # Add video to playlist
        success = add_video_to_playlist(int(user_id), playlist_id, video_data["video_id"])
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add video to playlist")
        
        return {
            "message": "Video added to playlist successfully"
        }
        
    except Exception as e:
        logger.error(f"YouTube add to playlist error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add video to playlist: {str(e)}")


@router.get("/youtube/videos/{video_id}/summary")
async def summarize_video(video_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get a summary of a YouTube video"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get video summary
        summary = get_video_summary(int(user_id), video_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Video not found or could not be summarized")
        
        return {
            "message": "Video summary generated successfully",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"YouTube video summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize video: {str(e)}")


@router.get("/youtube/playlists/{playlist_id}/summary")
async def summarize_playlist(playlist_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get a summary of a YouTube playlist"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get playlist summary
        summary = get_playlist_summary(int(user_id), playlist_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Playlist not found or could not be summarized")
        
        return {
            "message": "Playlist summary generated successfully",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"YouTube playlist summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize playlist: {str(e)}")


@router.get("/progress")
async def get_learning_progress(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get detailed learning progress for the user"""
    try:
        # Verify token and get user ID
        token = credentials.credentials
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user information
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get learning plan
        plan = db.query(LearningPlan).filter(LearningPlan.user_id == int(user_id)).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")
        
        # Get progress summary
        summary = LearningPathService.get_user_progress_summary(db, int(user_id), plan.id)
        
        # Get current position details
        current_position = {
            "current_month_index": user.current_month_index,
            "current_day": user.current_day,
            "plan_title": plan.title
        }
        
        # Get detailed month progress
        months = plan.plan.get("months", []) if isinstance(plan.plan, dict) else []
        month_progress = []
        
        for month in months:
            month_data = {
                "index": month.get("index"),
                "title": month.get("title"),
                "status": month.get("status"),
                "started_at": month.get("started_at"),
                "completed_at": month.get("completed_at"),
                "days_completed": 0,
                "total_days": len(month.get("days", [])) if month.get("days") else 0
            }
            
            # Count completed days
            if month.get("days"):
                month_data["days_completed"] = sum(1 for day in month.get("days") if day.get("completed", False))
            
            month_progress.append(month_data)
        
        return {
            "current_position": current_position,
            "summary": summary,
            "month_progress": month_progress
        }
        
    except Exception as e:
        logger.error(f"Get progress error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve progress: {str(e)}")