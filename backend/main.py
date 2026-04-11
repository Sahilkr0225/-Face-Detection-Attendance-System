from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import init_db
from backend.services.recognition_service import load_embeddings_to_memory
from backend.routes.auth_routes import router as auth_router
from backend.routes.enrollment_routes import router as enrollment_router
from backend.routes.recognition_routes import router as recognition_router 
from backend.routes.teacher_route import router as teacher_router
# FIX 1: Changed 'StaticFile' to 'StaticFiles'
from fastapi.staticfiles import StaticFiles 

# ─────────────────────────────────────────
# Lifespan — DB initialize karo
# ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    load_embeddings_to_memory()  # ← Embeddings memory mein load karo
    print("[APP] Server started successfully!")
    yield

# ─────────────────────────────────────────
# App Initialize
# ─────────────────────────────────────────
app = FastAPI(
    title="AI Face Recognition Attendance System",
    description="70 students ke liye AI based attendance system",
    version="1.0.0",
    lifespan=lifespan
)

# ─────────────────────────────────────────
# CORS
# ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Routes Register
# ─────────────────────────────────────────
app.include_router(auth_router)
app.include_router(enrollment_router)
app.include_router(recognition_router)
app.include_router(teacher_router)

# FIX 2: Move the mount AFTER 'app' is defined
# Also, usually you mount static files to a path like "/static" or at the end
# Inside backend/main.py
app.mount("/", StaticFiles(directory="backend/frontend", html=True), name="frontend")

# ─────────────────────────────────────────
# Test Route
# ─────────────────────────────────────────
@app.get("/health") # Changed to /health because mount "/" might conflict
async def root():
    return {"message": "Attendance System API is running! 🚀"}