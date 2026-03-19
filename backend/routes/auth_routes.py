from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.services.auth_service import (
    authenticate_teacher,
    register_teacher,
    create_access_token
)
from backend.middleware.auth_middleware import get_current_teacher
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ─────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    teacher_name: str


# ─────────────────────────────────────────
# Login
# ─────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Teacher login kare — JWT token milega
    """
    teacher = authenticate_teacher(db, form_data.username, form_data.password)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": teacher.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "teacher_name": teacher.name
    }


# ─────────────────────────────────────────
# Register
# ─────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Naya teacher register karo
    """
    teacher = register_teacher(
        db=db,
        name=request.name,
        email=request.email,
        password=request.password
    )

    return {
        "message": "Teacher registered successfully!",
        "teacher_id": teacher.id,
        "name": teacher.name
    }


# ─────────────────────────────────────────
# Me (Current Teacher Info)
# ─────────────────────────────────────────
@router.get("/me")
async def me(teacher=Depends(get_current_teacher)):
    """
    Current logged-in teacher ki info
    """
    return {
        "id": teacher.id,
        "name": teacher.name,
        "email": teacher.email
    }