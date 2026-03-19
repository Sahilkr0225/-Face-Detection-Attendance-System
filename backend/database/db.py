from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency — har request ke liye DB session do
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Saari tables create karo (agar exist nahi karti)
    """
    # Direct import — no circular issue
    from backend.database.models import Teacher, Student, Class, Attendance, ScanLog, AttendanceOverride  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("[DB] Database initialized successfully!")