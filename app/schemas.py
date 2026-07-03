from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime
    class Config:
        from_attributes = True

class CertificateCreate(BaseModel):
    student_name: str
    student_email: EmailStr
    achievement: str
    organization_name: str
    event_name: str

class CertificateResponse(BaseModel):
    id: int
    certificate_id: str
    student_name: str
    student_email: str
    achievement: str
    organization_name: str
    event_name: str
    certificate_code: str
    qr_code_path: Optional[str]
    certificate_file_path: Optional[str]
    issued_date: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
