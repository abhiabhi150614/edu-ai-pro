from pydantic import BaseModel

class PhoneVerificationRequest(BaseModel):
    phone_number: str

class PhoneVerificationCodeRequest(BaseModel):
    phone_number: str
    verification_code: str 