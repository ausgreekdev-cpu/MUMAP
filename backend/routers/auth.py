from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import APIKey, User
from ..schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileUpdate,
    PasswordChange,
    PreferencesResponse,
    APIKeyCreate,
    APIKeyCreated,
    APIKeyResponse,
    Token,
)
from ..services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    generate_api_key,
)
from ..services.audit import get_audit_logger, request_context
from ..config import get_settings
from ..utils import utcnow

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

PREFERENCE_DEFAULTS: dict[str, bool] = {
    "task_completed": True,
    "task_failed": True,
    "agent_offline": False,
    "weekly_summary": True,
}

API_KEY_SCOPES = {
    "agents:read",
    "agents:write",
    "tasks:read",
    "tasks:write",
    "usage:read",
}


def _preference_response(stored: dict) -> PreferencesResponse:
    merged = {
        key: bool(stored.get(key, default))
        for key, default in PREFERENCE_DEFAULTS.items()
    }
    return PreferencesResponse(**merged)


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
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
    db.flush()
    get_audit_logger(db).log(
        action="CREATE",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        new_values={"email": user.email, "username": user.username},
        **request_context(request),
    )
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    audit = get_audit_logger(db)
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        audit.log(
            action="LOGIN",
            resource_type="user",
            resource_id=user.id if user else None,
            user_id=user.id if user else None,
            success=False,
            error_message="Invalid email or password",
            **request_context(request),
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    audit.log(action="LOGIN", resource_type="user", user_id=user.id, **request_context(request))
    db.commit()

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
    request: Request,
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

    old_values = {"username": current_user.username, "email": current_user.email}
    if body.username is not None:
        current_user.username = body.username
    if body.email is not None:
        current_user.email = str(body.email)

    get_audit_logger(db).log(
        action="UPDATE",
        resource_type="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        old_values=old_values,
        new_values={"username": current_user.username, "email": current_user.email},
        **request_context(request),
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
def change_password(
    body: PasswordChange,
    request: Request,
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
    get_audit_logger(db).log(
        action="UPDATE",
        resource_type="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        new_values={"field": "password"},
        **request_context(request),
    )
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


@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(APIKey)
        .filter(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
        .all()
    )


@router.post("/api-keys", response_model=APIKeyCreated, status_code=201)
def create_api_key(
    body: APIKeyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unknown = set(body.scopes) - API_KEY_SCOPES
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scopes: {', '.join(sorted(unknown))}",
        )
    if body.expires_at is not None and body.expires_at <= utcnow():
        raise HTTPException(status_code=400, detail="expires_at must be in the future")

    plaintext, key_hash, prefix = generate_api_key()
    api_key = APIKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=key_hash,
        prefix=prefix,
        scopes=body.scopes,
        expires_at=body.expires_at,
    )
    db.add(api_key)
    db.flush()
    get_audit_logger(db).log(
        action="CREATE",
        resource_type="api_key",
        resource_id=api_key.id,
        user_id=current_user.id,
        new_values={"name": api_key.name, "prefix": prefix},
        **request_context(request),
    )
    db.commit()
    db.refresh(api_key)

    response = APIKeyCreated(
        **APIKeyResponse.model_validate(api_key).model_dump(), key=plaintext
    )
    return response


@router.delete("/api-keys/{key_id}")
def delete_api_key(
    key_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == current_user.id)
        .first()
    )
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")

    old_values = {"name": api_key.name, "prefix": api_key.prefix}
    db.delete(api_key)
    get_audit_logger(db).log(
        action="DELETE",
        resource_type="api_key",
        resource_id=key_id,
        user_id=current_user.id,
        old_values=old_values,
        **request_context(request),
    )
    db.commit()
    return {"message": "API key revoked"}
