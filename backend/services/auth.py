from datetime import datetime, timedelta
from typing import Optional, List
import os
import bcrypt
import jwt
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from services.db import get_db, User

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "campuspulse-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.PyJWTError:
        return None

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> User:
    # 1. Try JWT Auth
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if user is None:
            # Check by email
            result = await db.execute(select(User).where(User.email == username))
            user = result.scalars().first()
            
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    # 2. Fallback to mock headers (for backward compatibility with existing tests/chaos scripts)
    if x_user_role or x_user_id:
        email = x_user_id or "mock@sentitron.ai"
        # Extract username from email
        username = email.split("@")[0] if "@" in email else email
        role = x_user_role or "user"
        
        # Check if the user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            
        if not user:
            # Map test roles appropriately
            mapped_role = "user"
            if role in ["Super Admin", "Analytics Admin"]:
                mapped_role = "admin"
            elif role in ["Department Admin", "Moderator/Manager", "Moderator"]:
                mapped_role = "moderator"
            elif role in ["Monitoring Viewer", "Guest"]:
                mapped_role = "guest"
                
            # Create a mock user on the fly so DB constraints pass
            user = User(
                username=username,
                email=email,
                hashed_password=hash_password("mockpassword"),
                role=mapped_role,
                department="General"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_optional_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> Optional[User]:
    try:
        return await get_current_user(db, authorization, x_user_role, x_user_id)
    except HTTPException:
        return None

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Role '{current_user.role}' not authorized"
            )
        return current_user
