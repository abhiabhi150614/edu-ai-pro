import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from app.core.google_auth import get_google_oauth2_session
from app.models.user import User
from app.database.db import get_db


def _get_session_for_user(user_id: int):
    db = next(get_db())
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.google_id:
        raise ValueError("Google account not linked for this user")
    return get_google_oauth2_session(user.google_id)


def ensure_drive_folder(user_id: int, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
    try:
        session = _get_session_for_user(user_id)
        # Search for folder by name
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        search = session.get('https://www.googleapis.com/drive/v3/files', params={'q': q}).json()
        files = search.get('files', [])
        if files:
            return files[0]['id']
        # Create folder
        payload = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            payload['parents'] = [parent_id]
        resp = session.post('https://www.googleapis.com/drive/v3/files', data=json.dumps(payload))
        if resp.status_code in (200, 201):
            return resp.json().get('id')
    except Exception as e:
        print(f"Drive ensure folder error: {e}")
    return None


def create_drive_file(user_id: int, name: str, content: str, parent_id: Optional[str] = None) -> Optional[str]:
    try:
        session = _get_session_for_user(user_id)
        metadata = {'name': name}
        if parent_id:
            metadata['parents'] = [parent_id]
        files_endpoint = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
        boundary = 'foo_bar_baz'
        body = (
            f'--{boundary}\r\n'
            'Content-Type: application/json; charset=UTF-8\r\n\r\n'
            f'{json.dumps(metadata)}\r\n'
            f'--{boundary}\r\n'
            'Content-Type: text/plain; charset=UTF-8\r\n\r\n'
            f'{content}\r\n'
            f'--{boundary}--'
        )
        headers = {
            'Content-Type': f'multipart/related; boundary={boundary}'
        }
        resp = session.post(files_endpoint, data=body.encode('utf-8'), headers=headers)
        if resp.status_code in (200, 201):
            return resp.json().get('id')
    except Exception as e:
        print(f"Drive create file error: {e}")
    return None


def create_calendar_event(user_id: int, title: str, start_time: datetime, duration_minutes: int = 60, description: str = "") -> bool:
    try:
        session = _get_session_for_user(user_id)
        end_time = start_time + timedelta(minutes=duration_minutes)
        event = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': end_time.isoformat()}
        }
        resp = session.post('https://www.googleapis.com/calendar/v3/calendars/primary/events', data=json.dumps(event))
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"Calendar event creation error: {e}")
        return False


def list_drive_files(user_id: int, folder_name: Optional[str] = None, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List files in a user's Google Drive, optionally filtered by folder name or parent ID.
    Returns a list of file metadata including id, name, mimeType, and createdTime.
    """
    try:
        session = _get_session_for_user(user_id)
        query_parts = ["trashed=false"]
        
        # If folder name is provided, first find the folder ID
        if folder_name and not parent_id:
            folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_search = session.get('https://www.googleapis.com/drive/v3/files', params={'q': folder_query}).json()
            folder_files = folder_search.get('files', [])
            if folder_files:
                parent_id = folder_files[0]['id']
        
        # If parent_id is available (either provided or found by folder name), filter by it
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")
        
        # Construct the final query
        query = " and ".join(query_parts)
        
        # Get files with extended metadata
        response = session.get(
            'https://www.googleapis.com/drive/v3/files',
            params={
                'q': query,
                'fields': 'files(id,name,mimeType,createdTime,modifiedTime,size)',
                'pageSize': 100  # Adjust as needed
            }
        ).json()
        
        return response.get('files', [])
    except Exception as e:
        print(f"Drive list files error: {e}")
        return []


def get_drive_file_content(user_id: int, file_id: str) -> Optional[str]:
    """
    Retrieve the content of a specific file from Google Drive by its ID.
    Returns the file content as a string, or None if retrieval fails.
    """
    try:
        session = _get_session_for_user(user_id)
        response = session.get(f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media')
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to get file content. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Drive get file content error: {e}")
        return None


def get_day_notes(user_id: int, month_index: int, day: int) -> Optional[Dict[str, Any]]:
    """
    Helper function to retrieve notes for a specific day from Google Drive.
    First finds the root folder, then the month folder, then the day notes file.
    Returns a dictionary with content and file_id if found.
    """
    try:
        print(f"Getting day notes for user {user_id}, month {month_index}, day {day}")
        # Get user info to construct root folder name
        db = next(get_db())
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            print(f"User {user_id} not found")
            return None
            
        # Construct root folder name
        root_name = f"EDUAI_{(user.google_name or user.email or 'USER').split(' ')[0]}_LEARNING_MAIN_PATH"
        print(f"Looking for root folder: {root_name}")
        
        # Find root folder
        root_id = None
        root_folders = list_drive_files(user_id)
        print(f"Found {len(root_folders)} root level folders")
        for folder in root_folders:
            if folder.get('name') == root_name and folder.get('mimeType') == 'application/vnd.google-apps.folder':
                root_id = folder.get('id')
                print(f"Found root folder with ID: {root_id}")
                break
        
        if not root_id:
            print(f"Root folder '{root_name}' not found")
            return None
            
        # Find month folder
        month_folder_name = f"MONTH_{month_index}"
        print(f"Looking for month folder: {month_folder_name}")
        month_id = None
        month_folders = list_drive_files(user_id, parent_id=root_id)
        print(f"Found {len(month_folders)} folders in root")
        for folder in month_folders:
            if folder.get('name') == month_folder_name and folder.get('mimeType') == 'application/vnd.google-apps.folder':
                month_id = folder.get('id')
                print(f"Found month folder with ID: {month_id}")
                break
                
        if not month_id:
            print(f"Month folder '{month_folder_name}' not found")
            return None
            
        # Find day notes file
        day_file_name = f"DAY_{day}_NOTES.txt"
        print(f"Looking for day file: {day_file_name}")
        day_files = list_drive_files(user_id, parent_id=month_id)
        print(f"Found {len(day_files)} files in month folder")
        for file in day_files:
            if file.get('name') == day_file_name:
                file_id = file.get('id')
                print(f"Found day file with ID: {file_id}")
                content = get_drive_file_content(user_id, file_id)
                if content is None:
                    print(f"Failed to retrieve content for file ID: {file_id}")
                file_link = f"https://drive.google.com/file/d/{file_id}/view"
                print(f"Generated file link: {file_link}")
                return {
                    "content": content,
                    "file_id": file_id,
                    "link": file_link
                }
        
        print(f"Day file '{day_file_name}' not found")
        return None
    except Exception as e:
        print(f"Get day notes error: {e}")
        return None


def update_day_notes(user_id: int, month_index: int, day: int, content: str) -> bool:
    """
    Update or create notes for a specific day in Google Drive.
    First ensures the folder structure exists, then creates or updates the file.
    """
    try:
        # Get user info to construct root folder name
        db = next(get_db())
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return False
            
        # Construct root folder name
        root_name = f"EDUAI_{(user.google_name or user.email or 'USER').split(' ')[0]}_LEARNING_MAIN_PATH"
        
        # Ensure root folder exists
        root_id = ensure_drive_folder(user_id, root_name)
        if not root_id:
            return False
            
        # Ensure month folder exists
        month_folder_name = f"MONTH_{month_index}"
        month_id = ensure_drive_folder(user_id, month_folder_name, parent_id=root_id)
        if not month_id:
            return False
            
        # Check if day notes file already exists
        day_file_name = f"DAY_{day}_NOTES.txt"
        day_files = list_drive_files(user_id, parent_id=month_id)
        file_id = None
        
        for file in day_files:
            if file.get('name') == day_file_name:
                file_id = file.get('id')
                break
                
        # If file exists, update it (would need to implement update method)
        if file_id:
            # This would require implementing a file update method
            # For now, we'll just create a new file with the same name
            session = _get_session_for_user(user_id)
            metadata = {'name': day_file_name}
            files_endpoint = f'https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=multipart'
            boundary = 'foo_bar_baz'
            body = (
                f'--{boundary}\r\n'
                'Content-Type: application/json; charset=UTF-8\r\n\r\n'
                f'{json.dumps(metadata)}\r\n'
                f'--{boundary}\r\n'
                'Content-Type: text/plain; charset=UTF-8\r\n\r\n'
                f'{content}\r\n'
                f'--{boundary}--'
            )
            headers = {
                'Content-Type': f'multipart/related; boundary={boundary}'
            }
            resp = session.patch(files_endpoint, data=body.encode('utf-8'), headers=headers)
            return resp.status_code in (200, 201)
        else:
            # Create new file
            new_file_id = create_drive_file(user_id, day_file_name, content, parent_id=month_id)
            return new_file_id is not None
    except Exception as e:
        print(f"Update day notes error: {e}")
        return False


def send_email(user_id: int, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    """
    Send an email using the user's Gmail account via the Gmail API.
    
    Args:
        user_id: The ID of the user sending the email
        to_email: The recipient's email address
        subject: The email subject
        html_content: HTML content of the email
        text_content: Plain text content of the email (optional)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        session = _get_session_for_user(user_id)
        
        # Get user info to get sender email
        db = next(get_db())
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.email:
            print(f"User {user_id} not found or has no email")
            return False
            
        # Create message container
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = user.email
        message['To'] = to_email
        
        # Add text and HTML parts
        if text_content:
            message.attach(MIMEText(text_content, 'plain'))
        message.attach(MIMEText(html_content, 'html'))
        
        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create the email request body
        email_request = {
            'raw': encoded_message
        }
        
        # Send the email
        response = session.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            json=email_request
        )
        
        if response.status_code in (200, 201):
            print(f"Email sent successfully to {to_email}")
            return True
        else:
            print(f"Failed to send email. Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"Send email error: {e}")
        return False


def send_notification_email(user_id: int, notification_type: str, context: Dict[str, Any]) -> bool:
    """
    Send a notification email based on the notification type and context.
    
    Args:
        user_id: The ID of the user to send the notification to
        notification_type: The type of notification (quiz_completion, learning_progress, etc.)
        context: Dictionary containing context data for the notification
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get user info
        db = next(get_db())
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.email:
            print(f"User {user_id} not found or has no email")
            return False
        
        # Define email templates based on notification type
        if notification_type == "quiz_completion":
            quiz_score = context.get("score", 0)
            quiz_passed = context.get("passed", False)
            quiz_title = context.get("title", "Quiz")
            month_index = context.get("month_index", 0)
            day = context.get("day", 0)
            
            # Create email subject and content
            subject = f"Quiz Results: {quiz_title}"
            
            # HTML content with styling
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4f8cff; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .result {{ font-size: 18px; font-weight: bold; margin: 20px 0; text-align: center; }}
                    .score {{ font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; }}
                    .passed {{ color: #28a745; }}
                    .failed {{ color: #dc3545; }}
                    .next-steps {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                    .button {{ display: inline-block; background-color: #4f8cff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Your Quiz Results</h1>
                    </div>
                    <div class="content">
                        <p>Hello {user.google_name or user.email.split('@')[0]},</p>
                        <p>You have completed the quiz for Month {month_index}, Day {day}.</p>
                        
                        <div class="score">Score: {quiz_score}%</div>
                        
                        <div class="result {"passed" if quiz_passed else "failed"}">
                            {"Congratulations! You passed the quiz." if quiz_passed else "You did not pass the quiz. Please review the material and try again."}
                        </div>
                        
                        <div class="next-steps">
                            <h3>Next Steps:</h3>
                            {"<p>You can now proceed to the next day in your learning plan.</p>" if quiz_passed else "<p>Review the material for this day and attempt the quiz again.</p>"}
                            <p>Continue your learning journey to master new concepts!</p>
                            <a href="http://localhost:3000/learning-plans" class="button">Go to Learning Dashboard</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text content as fallback
            text_content = f"""
            Your Quiz Results
            
            Hello {user.google_name or user.email.split('@')[0]},
            
            You have completed the quiz for Month {month_index}, Day {day}.
            
            Score: {quiz_score}%
            
            {"Congratulations! You passed the quiz." if quiz_passed else "You did not pass the quiz. Please review the material and try again."}
            
            Next Steps:
            {"You can now proceed to the next day in your learning plan." if quiz_passed else "Review the material for this day and attempt the quiz again."}
            Continue your learning journey to master new concepts!
            
            Go to Learning Dashboard: http://localhost:3000/learning-plans
            """
            
        elif notification_type == "learning_progress":
            month_index = context.get("month_index", 0)
            day = context.get("day", 0)
            days_completed = context.get("days_completed", 0)
            total_days = context.get("total_days", 0)
            progress_percentage = context.get("progress_percentage", 0)
            
            # Create email subject and content
            subject = "Your Learning Progress Update"
            
            # HTML content with styling
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4f8cff; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .progress {{ margin: 20px 0; }}
                    .progress-bar {{ background-color: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }}
                    .progress-fill {{ background-color: #4f8cff; height: 100%; width: {progress_percentage}%; }}
                    .progress-text {{ text-align: center; margin-top: 5px; font-size: 14px; }}
                    .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                    .stat-item {{ text-align: center; }}
                    .stat-value {{ font-size: 24px; font-weight: bold; color: #4f8cff; }}
                    .stat-label {{ font-size: 14px; color: #666; }}
                    .button {{ display: inline-block; background-color: #4f8cff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Learning Progress Update</h1>
                    </div>
                    <div class="content">
                        <p>Hello {user.google_name or user.email.split('@')[0]},</p>
                        <p>Here's an update on your learning progress:</p>
                        
                        <div class="progress">
                            <div class="progress-bar">
                                <div class="progress-fill"></div>
                            </div>
                            <div class="progress-text">{progress_percentage}% Complete</div>
                        </div>
                        
                        <div class="stats">
                            <div class="stat-item">
                                <div class="stat-value">{days_completed}</div>
                                <div class="stat-label">Days Completed</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">{total_days}</div>
                                <div class="stat-label">Total Days</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">{month_index}</div>
                                <div class="stat-label">Current Month</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">{day}</div>
                                <div class="stat-label">Current Day</div>
                            </div>
                        </div>
                        
                        <p>Keep up the good work! Continue your learning journey to master new concepts.</p>
                        <a href="http://localhost:3000/progress" class="button">View Detailed Progress</a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text content as fallback
            text_content = f"""
            Learning Progress Update
            
            Hello {user.google_name or user.email.split('@')[0]},
            
            Here's an update on your learning progress:
            
            Progress: {progress_percentage}% Complete
            Days Completed: {days_completed}
            Total Days: {total_days}
            Current Month: {month_index}
            Current Day: {day}
            
            Keep up the good work! Continue your learning journey to master new concepts.
            
            View Detailed Progress: http://localhost:3000/progress
            """
        else:
            # Default generic notification
            subject = "Notification from EduAI"
            html_content = f"""
            <html>
            <body>
                <p>Hello {user.google_name or user.email.split('@')[0]},</p>
                <p>You have a new notification from EduAI.</p>
                <p>Please check your dashboard for more details.</p>
                <p><a href="http://localhost:3000/dashboard">Go to Dashboard</a></p>
            </body>
            </html>
            """
            text_content = f"""
            Hello {user.google_name or user.email.split('@')[0]},
            
            You have a new notification from EduAI.
            Please check your dashboard for more details.
            
            Go to Dashboard: http://localhost:3000/dashboard
            """
        
        # Send the email
        return send_email(user_id, user.email, subject, html_content, text_content)
    except Exception as e:
        print(f"Send notification email error: {e}")
        return False
