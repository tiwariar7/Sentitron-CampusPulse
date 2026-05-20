from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
import os
from datetime import datetime, timedelta

def get_ist_time():
    # Indian Standard Time (IST) is UTC + 5 hours 30 minutes
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

# Use SQLite as fallback if DATABASE_URL is not set and postgres isn't running
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./campuspulse.db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # admin, moderator, user, guest
    department = Column(String, nullable=True) # CSE, Hostel, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_ist_time)

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String, index=True, unique=True)
    timestamp = Column(DateTime, default=get_ist_time)
    source = Column(String)
    department = Column(String)
    category = Column(String)
    subcategory = Column(String)
    complaint_text = Column(String)
    sentiment_score = Column(Float)
    urgency_level = Column(Integer)
    escalation_flag = Column(String)
    resolved = Column(String)
    duplicate_group_id = Column(String, index=True)
    toxicity_score = Column(Float)
    anonymous = Column(String)
    response_delay_hours = Column(String)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    reported_by = relationship("User", foreign_keys=[reported_by_id])

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    message = Column(String)
    severity = Column(String, index=True) # INFO, WARNING, HIGH, CRITICAL
    category = Column(String, index=True) 
    lifecycle_state = Column(String, default="CREATED", index=True) # CREATED, ACKNOWLEDGED, RESOLVED, DISMISSED
    timestamp = Column(DateTime, default=get_ist_time)
    ai_recommendations = Column(Text) # JSON string of recommendations
    related_entity_id = Column(String) # For linking to a cluster or incident

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text) # JSON string
    description = Column(String)
    last_updated = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)
    updated_by = Column(String)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_ist_time)
    administrator_identity = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)
    modified_parameters = Column(Text) # JSON string
    previous_values = Column(Text) # JSON string
    updated_values = Column(Text) # JSON string

    user = relationship("User", foreign_keys=[user_id])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
