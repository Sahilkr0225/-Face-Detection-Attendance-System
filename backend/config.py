import os

# ─────────────────────────────────────────
# Face Recognition Settings
# ─────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.50   # is se kam → Unknown
CONFIRMED_THRESHOLD  = 0.75   # is se zyada → Confirmed Present
ENROLLMENT_PHOTOS    = 5      # enrollment mein kitni photos leni hain

# ─────────────────────────────────────────
# Attendance Logic Settings
# ─────────────────────────────────────────
STRIKE_LIMIT             = 2   # kitne strikes pe absent mark karo
ENTRY_WINDOW_MINUTES     = 10  # class shuru ke baad kitne min tak entry scan
EXIT_WINDOW_MINUTES      = 10  # class khatam hone se pehle kitne min
MID_SCAN_COUNT_MIN       = 2   # minimum random mid scans
MID_SCAN_COUNT_MAX       = 3   # maximum random mid scans

# ─────────────────────────────────────────
# Camera Settings
# ─────────────────────────────────────────
CAMERA_INDEX = 0               # USB webcam index (0 = default)

# ─────────────────────────────────────────
# JWT Auth Settings
# ─────────────────────────────────────────
SECRET_KEY       = "change-this-to-a-strong-secret-key"
ALGORITHM        = "HS256"
TOKEN_EXPIRE_MIN = 60 * 8      # 8 hours

# ─────────────────────────────────────────
# Paths
# ─────────────────────────────────────────
STUDENT_FACES_DIR = "student_faces"
EMBEDDINGS_PATH   = "embeddings.pkl"
DATABASE_URL      = "sqlite:///./attendance.db"