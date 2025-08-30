import secrets
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy  # Changed import
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request
import uuid

from app.models.user import User
from app.models.database import get_db
from app.config import settings

# Generate secure secret key if not provided
SECRET_KEY = getattr(settings, 'SECRET_KEY', None) or secrets.token_urlsafe(32)

# User database adapter
class UserDatabase(SQLAlchemyUserDatabase[User, uuid.UUID]):
    pass

# User manager
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield UserDatabase(session, User)

async def get_user_manager(user_db: UserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# Authentication configuration - CHANGED TO BEARER TRANSPORT
bearer_transport = BearerTransport(tokenUrl="/api/auth/jwt/login") # Changed from CookieTransport

# JWT Strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=SECRET_KEY,
        lifetime_seconds=3600 * 24 * 7,  # 7 days
    )

# Authentication Backend - UPDATED
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,  # Changed to bearer transport
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Auth dependencies
current_active_user = fastapi_users.current_user(active=True)
current_user = fastapi_users.current_user()
optional_current_user = fastapi_users.current_user(optional=True)

# User schemas for registration/response
from fastapi_users import schemas
from pydantic import EmailStr, Field
from typing import Optional

class UserRead(schemas.BaseUser[uuid.UUID]):
    id: uuid.UUID
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None