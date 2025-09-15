import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from app.core.config import settings

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")

# Scopes for Gmail and other Google services needed for MCP
SCOPES = [
    'openid',  # Required for Google OAuth
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube'  # Added full YouTube scope for edit capabilities
]

def create_google_flow():
    """Create Google OAuth flow"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials not configured")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow

def verify_google_token(token):
    """Verify Google ID token and return user info"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', '')
        }
    except Exception as e:
        raise ValueError(f'Invalid token: {str(e)}')

def get_google_oauth2_session(google_id):
    """Get OAuth2 session for Google API calls with token refresh capability"""
    try:
        import requests
        import time
        from app.database.db import get_db
        from app.models.user import User
        from sqlalchemy.orm import Session
        
        # Get the database session
        db = next(get_db())
        
        # Find user by google_id and get their access token
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            raise ValueError("User not found")
        
        if not user.google_access_token:
            raise ValueError("No access token available")
            
        # Check if we need to refresh the token
        # If we have a refresh token and the access token might be expired
        if user.google_refresh_token:
            try:
                # Try to refresh the token
                refresh_payload = {
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'refresh_token': user.google_refresh_token,
                    'grant_type': 'refresh_token'
                }
                
                refresh_response = requests.post(
                    'https://oauth2.googleapis.com/token',
                    data=refresh_payload
                )
                
                if refresh_response.status_code == 200:
                    token_data = refresh_response.json()
                    # Update the access token in the database
                    user.google_access_token = token_data['access_token']
                    db.commit()
                    print("Successfully refreshed Google access token")
            except Exception as refresh_error:
                print(f"Error refreshing token: {refresh_error}")
                # Continue with the existing token
        
        # Create a session for Google API calls
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {user.google_access_token}',
            'Content-Type': 'application/json'
        })
        
        return session
    except Exception as e:
        raise ValueError(f"Failed to create Google OAuth session: {str(e)}")

def get_google_auth_url():
    """Get Google OAuth authorization URL"""
    try:
        flow = create_google_flow()
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url
    except Exception as e:
        print(f"Error creating auth URL: {str(e)}")
        raise

def exchange_code_for_tokens(code):
    """Exchange authorization code for access and refresh tokens"""
    try:
        flow = create_google_flow()
        
        # Add error handling for invalid_grant
        try:
            flow.fetch_token(code=code)
        except Exception as token_error:
            if "invalid_grant" in str(token_error).lower():
                raise ValueError("Authorization code has expired or already been used. Please try signing in again.")
            else:
                raise token_error
        
        if not flow.oauth2session.token:
            raise ValueError("Failed to obtain tokens from Google")
        
        return {
            'access_token': flow.oauth2session.token['access_token'],
            'refresh_token': flow.oauth2session.token.get('refresh_token'),
            'expires_at': flow.oauth2session.token.get('expires_at')
        }
    except Exception as e:
        print(f"Error exchanging code for tokens: {str(e)}")
        raise