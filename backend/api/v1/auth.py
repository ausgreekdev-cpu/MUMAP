from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..deps import get_current_user, get_user_repo
from ...schemas.user import UserCreate, UserLogin, UserResponse, Token
from ...services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from ...config import settings
from ...repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    request: Request,
    user_repo: UserRepository = Depends(get_user_repo),
):
    existing_email = user_repo.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = user_repo.get_by_username(user_data.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = user_repo.create({
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
    })

    logger.info(f"User registered: {user.username} (ID: {user.id})")
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    user_repo: UserRepository = Depends(get_user_repo),
):
    user = user_repo.get_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    logger.info(f"User logged in: {user.username} (ID: {user.id})")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/token", response_model=Token)
async def login_with_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repo),
):
    user = user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/dev-login", response_model=Token)
async def dev_login(
    user_repo: UserRepository = Depends(get_user_repo),
):
    from ...config import settings
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Dev login disabled in production")

    dev_email = "dev@mumap.local"
    dev_username = "developer"
    dev_password = "dev123456"

    user = user_repo.get_by_email(dev_email)
    if not user:
        user = user_repo.create({
            "email": dev_email,
            "username": dev_username,
            "hashed_password": get_password_hash(dev_password),
            "role": "admin",
        })
        logger.info(f"Dev user created: {dev_username} (ID: {user.id})")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }
