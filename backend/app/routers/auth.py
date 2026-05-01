from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import register, login

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await register(user_data, db)


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login(login_data, db)
