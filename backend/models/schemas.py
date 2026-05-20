from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field("user", description="user, moderator, admin, guest")
    department: Optional[str] = Field(None, description="Department assignment like CSE, Hostel")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse

class ComplaintBase(BaseModel):
    complaint_id: str = Field(..., description="Unique identifier like CMP-XXXX")
    source: str = Field(..., description="Source like WhatsApp, Email")
    department: str = Field(..., description="Department like CSE")
    category: str = Field(..., description="Main category")
    subcategory: str = Field(..., description="Subcategory")
    complaint_text: str = Field(..., description="The actual text")
    sentiment_score: float = Field(0.0)
    urgency_level: int = Field(1)
    escalation_flag: str = Field("false")
    resolved: str = Field("false")
    duplicate_group_id: str = Field("")
    toxicity_score: float = Field(0.0)
    anonymous: str = Field("false")
    response_delay_hours: str = Field("")
    reported_by_id: Optional[int] = Field(None)

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintResponse(ComplaintBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
