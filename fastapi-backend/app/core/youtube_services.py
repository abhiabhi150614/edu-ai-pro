import json
import requests
from typing import Optional, List, Dict, Any, Union
import re
from app.core.google_auth import get_google_oauth2_session
from app.models.user import User
from app.database.db import get_db


def _get_session_for_user(user_id: int):
    try:
        print(f"Getting session for user {user_id}")
        db = next(get_db())
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            print(f"User {user_id} not found in database")
            raise ValueError("User not found")
        
        if not user.google_id:
            print(f"User {user_id} does not have google_id")
            raise ValueError("Google account not linked for this user")
        
        if not user.google_access_token:
            print(f"User {user_id} does not have google_access_token")
            raise ValueError("No access token available for this user")
        
        print(f"User {user_id} has Google ID: {user.google_id}")
        print(f"User {user_id} has access token: {user.google_access_token[:20]}..." if user.google_access_token else "No access token")
            
        session = get_google_oauth2_session(user.google_id)
        print(f"Successfully got session for user {user_id}")
        return session
    except Exception as e:
        print(f"Error getting session for user {user_id}: {e}")
        raise


def search_youtube_videos(user_id: int, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for YouTube videos based on a query.
    Returns a list of video metadata including id, title, description, thumbnail, and channel.
    """
    try:
        session = _get_session_for_user(user_id)
        
        # Call YouTube Data API search endpoint
        response = session.get(
            'https://www.googleapis.com/youtube/v3/search',
            params={
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'relevanceLanguage': 'en'
            }
        ).json()
        
        # Extract relevant information from search results
        videos = []
        for item in response.get('items', []):
            if item.get('id', {}).get('kind') == 'youtube#video':
                video_id = item.get('id', {}).get('videoId')
                snippet = item.get('snippet', {})
                videos.append({
                    'id': video_id,
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'channel': snippet.get('channelTitle', ''),
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })
        
        # Get video durations in a separate call
        if videos:
            video_ids = [video['id'] for video in videos]
            video_details = get_video_details(user_id, video_ids)
            
            # Merge duration information into video data
            for video in videos:
                for detail in video_details:
                    if video['id'] == detail['id']:
                        video['duration'] = detail.get('duration', '')
                        video['duration_seconds'] = detail.get('duration_seconds', 0)
                        break
        
        return videos
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []


def get_video_details(user_id: int, video_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get detailed information for specific YouTube videos by their IDs.
    Returns duration and other metadata.
    """
    try:
        session = _get_session_for_user(user_id)
        
        # Call YouTube Data API videos endpoint
        response = session.get(
            'https://www.googleapis.com/youtube/v3/videos',
            params={
                'part': 'contentDetails,statistics,snippet',
                'id': ','.join(video_ids)
            }
        ).json()
        
        # Extract relevant information from video details
        videos = []
        for item in response.get('items', []):
            video_id = item.get('id')
            content_details = item.get('contentDetails', {})
            statistics = item.get('statistics', {})
            snippet = item.get('snippet', {})
            
            # Parse ISO 8601 duration format
            duration = content_details.get('duration', 'PT0S')
            duration_seconds = parse_duration(duration)
            
            videos.append({
                'id': video_id,
                'duration': duration,
                'duration_seconds': duration_seconds,
                'views': statistics.get('viewCount', '0'),
                'likes': statistics.get('likeCount', '0'),
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel': snippet.get('channelTitle', ''),
                'url': f'https://www.youtube.com/watch?v={video_id}'
            })
        
        return videos
    except Exception as e:
        print(f"YouTube video details error: {e}")
        return []


def parse_duration(duration_str: str) -> int:
    """
    Parse ISO 8601 duration format (e.g., PT1H30M15S) to seconds.
    """
    try:
        hours = re.search(r'(\d+)H', duration_str)
        minutes = re.search(r'(\d+)M', duration_str)
        seconds = re.search(r'(\d+)S', duration_str)
        
        total_seconds = 0
        if hours:
            total_seconds += int(hours.group(1)) * 3600
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        if seconds:
            total_seconds += int(seconds.group(1))
            
        return total_seconds
    except Exception:
        return 0


def get_user_playlists(user_id: int) -> List[Dict[str, Any]]:
    """
    Get the user's YouTube playlists.
    Returns a list of playlist metadata including id, title, and thumbnail.
    """
    try:
        print(f"Getting playlists for user {user_id}")
        session = _get_session_for_user(user_id)
        
        # Call YouTube Data API playlists endpoint
        response = session.get(
            'https://www.googleapis.com/youtube/v3/playlists',
            params={
                'part': 'snippet,contentDetails',
                'mine': 'true',
                'maxResults': 50
            }
        )
        
        print(f"Playlists API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error getting playlists: {response.status_code}")
            print(f"Response: {response.text}")
            return []
        
        response_data = response.json()
        print(f"Found {len(response_data.get('items', []))} playlists")
        
        # Extract relevant information from playlists
        playlists = []
        for item in response_data.get('items', []):
            playlist_id = item.get('id')
            snippet = item.get('snippet', {})
            content_details = item.get('contentDetails', {})
            
            playlist_info = {
                'id': playlist_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'item_count': content_details.get('itemCount', 0),
                'url': f'https://www.youtube.com/playlist?list={playlist_id}'
            }
            
            print(f"Playlist: '{playlist_info['title']}' (ID: {playlist_id})")
            playlists.append(playlist_info)
        
        return playlists
    except Exception as e:
        print(f"YouTube playlists error: {e}")
        import traceback
        traceback.print_exc()
        return []


def create_playlist(user_id: int, title: str, description: str = "") -> Optional[Dict[str, Any]]:
    """
    Create a new YouTube playlist.
    Returns the playlist metadata if successful.
    """
    try:
        print(f"Starting playlist creation for user {user_id}, title: {title}")
        
        # Get the session
        session = _get_session_for_user(user_id)
        print(f"Got session for user {user_id}")
        
        # Call YouTube Data API playlists endpoint to create a new playlist
        payload = {
            'snippet': {
                'title': title,
                'description': description,
            },
            'status': {
                'privacyStatus': 'private'  # Default to private
            }
        }
        
        print(f"Making API request to create playlist '{title}'")
        
        response = session.post(
            'https://www.googleapis.com/youtube/v3/playlists',
            params={'part': 'snippet,status'},
            json=payload
        )
        
        print(f"API Response Status: {response.status_code}")
        
        # Check for HTTP errors
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 401:
                print("Authentication error: Token expired or invalid")
                return {"error": "Authentication failed. Please refresh your Google connection."}
            elif response.status_code == 403:
                print("Permission error: YouTube API access denied")
                return {"error": "YouTube permissions not granted. Please check your Google account settings."}
            elif response.status_code == 400:
                print("Bad request error")
                return {"error": "Invalid request format."}
            else:
                return {"error": f"YouTube API error: {response.status_code}"}
        
        # Parse successful response
        response_data = response.json()
        print(f"Success Response: {response_data}")
        
        if 'id' in response_data:
            playlist_id = response_data.get('id')
            snippet = response_data.get('snippet', {})
            
            print(f"✅ Successfully created playlist '{title}' with ID {playlist_id}")
            
            result = {
                'id': playlist_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'url': f'https://www.youtube.com/playlist?list={playlist_id}'
            }
            return result
        else:
            error_message = response_data.get('error', {}).get('message', 'Unknown error')
            print(f"❌ Failed to create playlist: {error_message}")
            return {"error": f"YouTube API error: {error_message}"}
            
    except ValueError as ve:
        print(f"ValueError in create_playlist: {ve}")
        return {"error": str(ve)}
    except Exception as e:
        print(f"Unexpected error in create_playlist: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Unexpected error: {str(e)}"}


def extract_video_id_from_url(url: str) -> Optional[str]:
    """
    Extract video ID from various YouTube URL formats.
    Handles both simple video URLs and playlist URLs with additional parameters.
    """
    import re
    
    # Pattern for standard YouTube video URLs
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def add_video_to_playlist(user_id: int, playlist_id: str, video_id: str) -> Union[bool, Dict[str, str]]:
    """
    Add a video to a YouTube playlist.
    Returns True if successful, or a dict with 'error' key if failed.
    """
    try:
        print(f"Starting video addition: user {user_id}, playlist {playlist_id}, video {video_id}")
        
        session = _get_session_for_user(user_id)
        if not session:
            print(f"Could not get session for user {user_id}")
            return {"error": "Could not authenticate with YouTube. Please check your Google connection."}
        print(f"Got session for user {user_id}")
        
        # Clean video_id if it's a URL
        if video_id.startswith('http'):
            extracted_id = extract_video_id_from_url(video_id)
            if extracted_id:
                video_id = extracted_id
                print(f"Extracted video ID: {video_id}")
            else:
                print(f"Could not extract video ID from URL: {video_id}")
                return {"error": f"Could not extract video ID from URL: {video_id}"}
        
        # Call YouTube Data API playlistItems endpoint to add a video
        payload = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        
        print(f"Making API request to add video {video_id} to playlist {playlist_id}")
        print(f"Payload: {payload}")
        
        response = session.post(
            'https://www.googleapis.com/youtube/v3/playlistItems',
            params={'part': 'snippet'},
            json=payload
        )
        
        print(f"API Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Check for HTTP errors
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 401:
                print("Authentication error: Token expired or invalid")
                return {"error": "Authentication failed. Please refresh your Google connection."}
            elif response.status_code == 403:
                print("Permission error: YouTube API access denied")
                return {"error": "YouTube permissions not granted. Please check your Google account settings."}
            elif response.status_code == 404:
                print("Not found error: The playlist or video ID might be invalid")
                return {"error": "Playlist or video not found. Please check the playlist name and video URL."}
            elif response.status_code == 400:
                print("Bad request error")
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Bad request')
                    return {"error": f"YouTube API error: {error_message}"}
                except:
                    return {"error": "Invalid request format."}
            else:
                print(f"Other HTTP error: {response.status_code}")
                return {"error": f"YouTube API error: {response.status_code}"}
        
        # Success
        response_data = response.json()
        print(f"✅ Successfully added video {video_id} to playlist {playlist_id}")
        print(f"Response data: {response_data}")
        return True
            
    except ValueError as ve:
        print(f"ValueError in add_video_to_playlist: {ve}")
        return {"error": f"Invalid data format: {str(ve)}"}
    except Exception as e:
        print(f"Unexpected error in add_video_to_playlist: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Unexpected error: {str(e)}"}


def get_video_summary(user_id: int, video_id: str) -> Optional[str]:
    """
    Get a summary of a YouTube video using the video transcript and AI.
    This would typically involve getting the transcript and then using an AI service to summarize it.
    For now, we'll just return the video details as a placeholder.
    """
    try:
        # Get video details first
        video_details = get_video_details(user_id, [video_id])
        if not video_details:
            return None
            
        video = video_details[0]
        
        # In a real implementation, you would:
        # 1. Get the video transcript using YouTube's captions API or a third-party service
        # 2. Use an AI service (like Gemini) to summarize the transcript
        # 3. Return the summary
        
        # For now, we'll just return a placeholder message with the video details
        return f"Summary of '{video['title']}' (Duration: {video['duration_seconds'] // 60}m {video['duration_seconds'] % 60}s):\n\n" + \
               f"This video by {video['channel']} has {video['views']} views. " + \
               f"A full summary would require transcript analysis with AI."
    except Exception as e:
        print(f"YouTube video summary error: {e}")
        return None


def get_playlist_summary(user_id: int, playlist_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a summary of a YouTube playlist, including video count, total duration, and topics.
    """
    try:
        session = _get_session_for_user(user_id)
        
        # First, get playlist details
        playlist_response = session.get(
            'https://www.googleapis.com/youtube/v3/playlists',
            params={
                'part': 'snippet,contentDetails',
                'id': playlist_id
            }
        ).json()
        
        if not playlist_response.get('items'):
            return None
            
        playlist_info = playlist_response['items'][0]
        playlist_title = playlist_info['snippet']['title']
        video_count = playlist_info['contentDetails']['itemCount']
        
        # Then, get all videos in the playlist
        videos = []
        next_page_token = None
        
        while True:
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': 50
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
                
            playlist_items_response = session.get(
                'https://www.googleapis.com/youtube/v3/playlistItems',
                params=params
            ).json()
            
            # Extract video IDs
            for item in playlist_items_response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                videos.append({
                    'id': video_id,
                    'title': item['snippet']['title'],
                    'position': item['snippet']['position']
                })
            
            next_page_token = playlist_items_response.get('nextPageToken')
            if not next_page_token:
                break
        
        # Get video details for duration information
        video_ids = [video['id'] for video in videos]
        video_details = []
        
        # Process in batches of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            batch_details = get_video_details(user_id, batch_ids)
            video_details.extend(batch_details)
        
        # Calculate total duration
        total_duration_seconds = sum(video.get('duration_seconds', 0) for video in video_details)
        hours = total_duration_seconds // 3600
        minutes = (total_duration_seconds % 3600) // 60
        seconds = total_duration_seconds % 60
        
        # Format total duration
        total_duration = f"{hours}h {minutes}m {seconds}s"
        
        # Merge video details with playlist positions
        for video in videos:
            for detail in video_details:
                if video['id'] == detail['id']:
                    video.update(detail)
                    break
        
        # Sort by playlist position
        videos.sort(key=lambda x: x.get('position', 0))
        
        return {
            'id': playlist_id,
            'title': playlist_title,
            'video_count': video_count,
            'total_duration': total_duration,
            'total_duration_seconds': total_duration_seconds,
            'videos': videos,
            'url': f'https://www.youtube.com/playlist?list={playlist_id}'
        }
    except Exception as e:
        print(f"YouTube playlist summary error: {e}")
        return None