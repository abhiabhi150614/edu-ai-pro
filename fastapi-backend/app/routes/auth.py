from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut, GoogleAuthRequest, GoogleUserInfo, PhoneVerificationRequest, PhoneVerificationCodeRequest
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.core.google_auth import get_google_auth_url, exchange_code_for_tokens, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from app.database.db import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
import requests

router = APIRouter()

bearer_scheme = HTTPBearer()

@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    # ✅ Create token with user ID (not email)
    access_token = create_access_token(data={"sub": str(user.id)})

    # ✅ Return token directly
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Google OAuth endpoints
@router.get("/auth/google/url")
def get_google_auth_url_endpoint():
    """Get Google OAuth authorization URL"""
    try:
        auth_url = get_google_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

@router.post("/auth/google/callback")
def google_auth_callback(data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Handle Google OAuth callback and create/update user"""
    try:
        # Exchange authorization code for tokens
        tokens = exchange_code_for_tokens(data.code)
        access_token = tokens['access_token']
        
        # Get user info from Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        user_info = user_info_response.json()
        
        # Check if user exists by Google ID or email
        existing_user = db.query(User).filter(
            (User.google_id == user_info['id']) | 
            (User.email == user_info['email'])
        ).first()
        
        if existing_user:
            # Update existing user with Google info
            existing_user.google_id = user_info['id']
            existing_user.google_email = user_info['email']
            existing_user.google_name = user_info.get('name', '')
            existing_user.google_picture = user_info.get('picture', '')
            existing_user.google_access_token = access_token  # Store the access token
            existing_user.google_refresh_token = tokens.get('refresh_token')  # Store the refresh token
            existing_user.is_google_authenticated = True
            
            # If user was created with email/password, keep the original email
            if not existing_user.email:
                existing_user.email = user_info['email']
                
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            # Create new user with Google info
            user = User(
                email=user_info['email'],
                google_id=user_info['id'],
                google_email=user_info['email'],
                google_name=user_info.get('name', ''),
                google_picture=user_info.get('picture', ''),
                google_access_token=access_token,  # Store the access token
                google_refresh_token=tokens.get('refresh_token'),  # Store the refresh token
                is_google_authenticated=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "is_google_authenticated": user.is_google_authenticated,
                "google_name": user.google_name,
                "google_picture": user.google_picture
            }
        }
        
    except ValueError as ve:
        # Handle specific validation errors (like invalid_grant)
        print(f"Google OAuth validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")  # Debug logging
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@router.get("/auth/google/verify")
def verify_google_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Verify if user has completed Google authentication"""
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "is_google_authenticated": user.is_google_authenticated,
        "google_name": user.google_name,
        "google_picture": user.google_picture
    }

@router.post("/auth/google/connect")
def connect_google_account(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get Google OAuth URL for existing users to connect their Google account"""
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_google_authenticated:
        raise HTTPException(status_code=400, detail="Google account already connected")
    
    try:
        auth_url = get_google_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

@router.post("/auth/google/refresh")
def refresh_google_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Manually refresh Google OAuth token"""
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_google_authenticated:
        raise HTTPException(status_code=400, detail="Google account not connected")
    
    if not user.google_refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")
    
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
        
        refresh_response.raise_for_status()
        token_data = refresh_response.json()
        
        # Update the access token in the database
        user.google_access_token = token_data['access_token']
        db.commit()
        
        return {"status": "success", "message": "Google token refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to refresh token: {str(e)}")

@router.post("/phone/send-verification")
def send_phone_verification(request: PhoneVerificationRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # For demo purposes, we'll simulate SMS sending
    # In production, integrate with Twilio, AWS SNS, or similar service
    verification_code = "123456"  # In production, generate random 6-digit code
    
    # Store verification code temporarily (in production, use Redis or similar)
    # For now, we'll just update the user's phone number
    user.phone_number = request.phone_number
    user.phone_verified = False
    db.commit()
    
    return {
        "message": f"Verification code sent to {request.phone_number}",
        "demo_code": verification_code  # Remove this in production
    }

@router.post("/phone/verify")
def verify_phone_code(request: PhoneVerificationCodeRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # For demo purposes, accept "123456" as valid code
    # In production, verify against stored code
    if request.verification_code == "123456":
        user.phone_verified = True
        db.commit()
        return {"message": "Phone number verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")
