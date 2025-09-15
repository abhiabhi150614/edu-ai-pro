from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    is_google_authenticated: bool
    google_name: Optional[str] = None
    google_picture: Optional[str] = None
    phone_number: Optional[str] = None
    phone_verified: bool = False
    created_at: datetime

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str

class GoogleUserInfo(BaseModel):
    google_id: str
    email: str
    name: str
    picture: str

class PhoneVerificationRequest(BaseModel):
    phone_number: str

class PhoneVerificationCodeRequest(BaseModel):
    phone_number: str
    verification_code: str
