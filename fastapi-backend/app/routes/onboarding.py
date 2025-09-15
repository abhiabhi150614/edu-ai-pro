from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.onboarding import OnboardingData, OnboardingResponse
from app.database.db import get_db
from app.models.user import User
from app.models.onboarding import Onboarding
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()
router = APIRouter()

@router.post("/onboarding")
def save_onboarding(data: OnboardingData, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        user_id = decode_token(token)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete existing onboarding data if it exists
        existing = db.query(Onboarding).filter(Onboarding.user_id == user.id).first()
        if existing:
            db.delete(existing)
            db.commit()

        # Create new onboarding data
        new_onboarding = Onboarding(
            user_id=user.id,
            name=data.name,
            grade=data.grade,
            career_goals=data.career_goals,
            current_skills=data.current_skills,
            time_commitment=data.time_commitment
        )
        
        db.add(new_onboarding)
        db.commit()
        db.refresh(new_onboarding)
        
        return {"message": "Onboarding data saved successfully"}
        
    except Exception as e:
        print(f"Onboarding save error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save onboarding data: {str(e)}")

@router.get("/onboarding")
def get_onboarding(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        user_id = decode_token(token)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
        
        if not onboarding:
            raise HTTPException(status_code=404, detail="Onboarding data not found")
            
        return {
            "id": onboarding.id,
            "user_id": onboarding.user_id,
            "name": onboarding.name,
            "grade": onboarding.grade,
            "career_goals": onboarding.career_goals or [],
            "current_skills": onboarding.current_skills or [],
            "time_commitment": onboarding.time_commitment
        }
        
    except Exception as e:
        print(f"Onboarding get error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get onboarding data: {str(e)}")
