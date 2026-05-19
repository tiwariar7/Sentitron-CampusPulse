from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ComplaintBase(BaseModel):
    student_id: str = Field(..., description="Anonymized student identifier")
    category: Optional[str] = Field(None, description="Category of the complaint, e.g., Academic, Infrastructure")
    content: str = Field(..., description="The raw text of the complaint")
    source: str = Field(..., description="Where the complaint originated from (e.g., WhatsApp, WebForm)")

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintResponse(ComplaintBase):
    id: int
    timestamp: datetime
    status: str
    
    class Config:
        from_attributes = True
