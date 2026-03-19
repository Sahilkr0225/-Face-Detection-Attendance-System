from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.database.models import Teacher
from backend.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_MIN

# ─────────────────────────────────────────
# Password Hashing Setup
# ─────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Plain password ko hash karo"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Plain password ko hash se compare karo"""
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────
# JWT Token
# ─────────────────────────────────────────
def create_access_token(data: dict) -> str:
    """JWT token banao"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MIN)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """JWT token decode karo — agar invalid ho toh None return karo"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ─────────────────────────────────────────
# Teacher Auth
# ─────────────────────────────────────────
def authenticate_teacher(db: Session, email: str, password: str) -> Teacher | None:
    """
    Email aur password se teacher verify karo
    Sahi hone pe Teacher object return karo, warna None
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        return None

    if not verify_password(password, teacher.password):
        return None

    return teacher


def register_teacher(db: Session, name: str, email: str, password: str) -> Teacher:
    """
    Naya teacher register karo
    """
    hashed = hash_password(password)
    teacher = Teacher(
        name=name,
        email=email,
        password=hashed
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher