from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileUpdate,
    PasswordChange,
    PreferencesResponse,
    Token,
)
from ..services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

PREFERENCE_DEFAULTS: dict[str, bool] = {
    "task_completed": True,
    "task_failed": True,
    "agent_offline": False,
    "weekly_summary": True,
}


def _preference_response(stored: dict) -> PreferencesResponse:
    merged = {
        key: bool(stored.get(key, default))
        for key, default in PREFERENCE_DEFAULTS.items()
    }
    return PreferencesResponse(**merged)


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.username is None and body.email is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    if body.email is not None and (
        db.query(User)
        .filter(User.email == str(body.email), User.id != current_user.id)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Email already registered")

    if body.username is not None and (
        db.query(User)
        .filter(User.username == body.username, User.id != current_user.id)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Username already taken")

    if body.username is not None:
        current_user.username = body.username
    if body.email is not None:
        current_user.email = str(body.email)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="New password must be at least 8 characters"
        )

    current_user.hashed_password = get_password_hash(body.new_password)
    db.commit()
    return {"message": "Password updated"}


@router.get("/preferences", response_model=PreferencesResponse)
def get_preferences(current_user: User = Depends(get_current_user)):
    return _preference_response(current_user.preferences or {})


@router.put("/preferences", response_model=PreferencesResponse)
def update_preferences(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unknown = set(body) - set(PREFERENCE_DEFAULTS)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preference keys: {', '.join(sorted(unknown))}",
        )
    non_bool = [key for key, value in body.items() if not isinstance(value, bool)]
    if non_bool:
        raise HTTPException(
            status_code=400,
            detail=f"Preference values must be boolean: {', '.join(sorted(non_bool))}",
        )

    stored = {**(current_user.preferences or {}), **body}
    current_user.preferences = stored
    db.commit()
    db.refresh(current_user)
    return _preference_response(stored)
