from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from services.db import get_db, User
from models.schemas import UserCreate, UserResponse, UserUpdate, LoginRequest, TokenResponse
from services.auth import hash_password, verify_password, create_access_token, get_current_user, RoleChecker

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if username exists
    username_stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(username_stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    email_stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(email_stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Map roles to strictly validated system roles
    role = user_data.role
    if role not in ["admin", "moderator", "user", "guest"]:
        role = "user"

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=role,
        department=user_data.department
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user by username or email
    stmt = select(User).where((User.username == login_data.username) | (User.email == login_data.username))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Admin-only: list all users
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(RoleChecker(["admin"]))
):
    stmt = select(User).order_by(User.id)
    result = await db.execute(stmt)
    return result.scalars().all()

# Admin-only: update user details/role
@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(RoleChecker(["admin"]))
):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = updates.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "role" and value not in ["admin", "moderator", "user", "guest"]:
            continue
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user
