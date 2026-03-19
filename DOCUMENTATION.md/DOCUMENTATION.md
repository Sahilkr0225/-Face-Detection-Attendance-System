# AI Face Recognition Attendance System
> 70 Students ke liye AI based Attendance System with Hybrid Verification

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [File Structure](#3-file-structure)
4. [System Architecture](#4-system-architecture)
5. [Database Design](#5-database-design)
6. [Attendance Logic Flowchart](#6-attendance-logic-flowchart)
7. [API Endpoints](#7-api-endpoints)
8. [Setup Instructions](#8-setup-instructions)
9. [Progress Tracker](#9-progress-tracker)

---

## 1. Project Overview

### Problem Statement
Traditional attendance systems allow students to:
- Mark attendance and leave early
- Use proxy attendance
- Exploit single-scan biometric systems

### Proposed Solution
An AI-based Face Recognition Attendance System that:
- Verifies continuous student presence throughout the class
- Uses a **Hybrid Scanning Model** — Entry + Random Mid Scans + Exit
- Prevents proxy attendance using face embeddings
- Gives teacher full control with manual override

### Key Features
- Real-time face detection using **RetinaFace**
- Face recognition using **Cosine Similarity**
- Hybrid attendance verification (Entry + Mid + Exit scans)
- Strike-based absence system
- Teacher dashboard with manual override
- Complete audit trail of all overrides
- Privacy-first — only embeddings stored, no raw images

---

## 2. Tech Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| Backend | FastAPI (Python) | Fast, modern, async support |
| Face Detection | RetinaFace (InsightFace) | Accurate, production-grade |
| Face Recognition | Cosine Similarity (sklearn) | Perfect for 70 students |
| Embeddings Storage | Pickle file | Simple, fast, no setup needed |
| Database | SQLite + SQLAlchemy | Zero setup, file-based |
| Camera | OpenCV (USB Webcam) | Simple USB integration |
| Scheduler | APScheduler | Automatic scan scheduling |
| Authentication | JWT (python-jose) | Secure teacher login |
| Frontend | HTML + TailwindCSS + Vanilla JS | Lightweight, no framework needed |

---

## 3. File Structure

```
Face-Detection-Attendance/
│
├── backend/
│   ├── __init__.py
│   ├── main.py                      ← FastAPI entry point
│   ├── config.py                    ← All project settings
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                    ← SQLite connection + session
│   │   └── models.py                ← All database tables
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── camera_service.py        ← USB webcam handling
│   │   ├── recognition_service.py   ← Face detect + match
│   │   ├── attendance_service.py    ← Attendance logic + strikes
│   │   └── scheduler_service.py    ← Auto scan scheduling
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py           ← Teacher login/logout
│   │   ├── enrollment_routes.py     ← Student enrollment
│   │   ├── attendance_routes.py     ← Attendance CRUD
│   │   └── teacher_routes.py        ← Dashboard + override
│   │
│   └── middleware/
│       ├── __init__.py
│       └── auth_middleware.py       ← JWT verification
│
├── frontend/
│   ├── index.html                   ← Login page
│   ├── dashboard.html               ← Teacher dashboard
│   └── enrollment.html              ← Student enrollment page
│
├── student_faces/                   ← Enrollment images stored here
├── embeddings.pkl                   ← Auto generated on enrollment
├── attendance.db                    ← Auto generated on startup
├── requirements.txt                 ← All dependencies
└── .env                             ← Secret keys (never commit!)
```

---

## 4. System Architecture

```
📷 USB Webcam
(Classroom mein rakha, laptop se USB connected)
        |
        | Raw Video Frames
        ↓
💻 Teacher ka Laptop
(Classroom mein, server yahan run hoga)
        |
        |── OpenCV          → Frames capture karo
        |── RetinaFace      → Faces detect karo
        |── Cosine Similarity → Students pehchano
        |── APScheduler     → Auto scans trigger karo
        |── SQLite          → Attendance save karo
        |
        ↓
🌐 Teacher Dashboard (Browser)
localhost:8000
        |
        |── Class start/end
        |── Live attendance view
        |── Manual scan trigger
        |── Override attendance
        └── Download reports
```

### Request Flow
```
Browser Request
      ↓
FastAPI Router
      ↓
JWT Middleware (auth check)
      ↓
Route Handler
      ↓
Service Layer (business logic)
      ↓
Database (SQLite)
      ↓
Response
```

---

## 5. Database Design

### Tables Overview

```
┌─────────────┐         ┌──────────────┐
│  teachers   │         │   students   │
├─────────────┤         ├──────────────┤
│ id (PK)     │         │ id (PK)      │
│ name        │         │ name         │
│ email       │         │ roll_no      │
│ password    │         │ photo_path   │
│ created_at  │         │ enrolled_at  │
└──────┬──────┘         └──────┬───────┘
       │                       │
       │         ┌─────────────┘
       │         │
┌──────▼─────────▼──────────────────────┐
│              classes                   │
├───────────────────────────────────────┤
│ id (PK)                               │
│ subject                               │
│ teacher_id (FK → teachers)            │
│ date                                  │
│ start_time                            │
│ end_time                              │
│ duration_minutes                      │
│ status (ONGOING / COMPLETED)          │
└──────────────────┬────────────────────┘
                   │
       ┌───────────┴────────────┐
       │                        │
┌──────▼──────────┐   ┌────────▼────────────┐
│   attendance    │   │      scan_logs       │
├─────────────────┤   ├──────────────────────┤
│ id (PK)         │   │ id (PK)              │
│ student_id (FK) │   │ class_id (FK)        │
│ class_id (FK)   │   │ scan_type            │
│ status          │   │ (ENTRY/MID/EXIT/     │
│ confidence_score│   │  MANUAL)             │
│ strike_count    │   │ triggered_at         │
│ final_marked_at │   │ students_detected    │
└────────┬────────┘   └──────────────────────┘
         │
┌────────▼────────────┐
│  attendance_overrides│
├─────────────────────┤
│ id (PK)             │
│ attendance_id (FK)  │
│ teacher_id (FK)     │
│ old_status          │
│ new_status          │
│ reason              │
│ overridden_at       │
└─────────────────────┘
```

### Table Details

#### Teachers
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key, auto generated |
| name | String | Teacher ka naam |
| email | String | Unique, login ke liye |
| password | String | Bcrypt hashed |
| created_at | DateTime | Account creation time |

#### Students
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key, auto generated |
| name | String | Student ka naam |
| roll_no | String | Unique roll number |
| photo_path | String | Enrollment image path |
| enrolled_at | DateTime | Enrollment time |

#### Classes
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key |
| subject | String | Subject name |
| teacher_id | FK | Teacher reference |
| date | String | Class date (YYYY-MM-DD) |
| start_time | DateTime | Class start time |
| end_time | DateTime | Class end time |
| duration_minutes | Integer | Default 60 min |
| status | Enum | ONGOING / COMPLETED |

#### Attendance
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key |
| student_id | FK | Student reference |
| class_id | FK | Class reference |
| status | Enum | PRESENT / ABSENT / UNCERTAIN |
| confidence_score | Float | Best match score (0-1) |
| strike_count | Integer | Missed scans count |
| final_marked_at | DateTime | When finalized |

#### Scan Logs
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key |
| class_id | FK | Class reference |
| scan_type | Enum | ENTRY/MID/EXIT/MANUAL |
| triggered_at | DateTime | Scan time |
| students_detected | Integer | Count of detected students |

#### Attendance Overrides
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key |
| attendance_id | FK | Attendance reference |
| teacher_id | FK | Teacher who overrode |
| old_status | String | Previous status |
| new_status | String | Updated status |
| reason | String | Teacher ka reason |
| overridden_at | DateTime | Override time |

---

## 6. Attendance Logic Flowchart

```
Teacher "Start Class" dabaye
              ↓
    ┌─────────────────────┐
    │   Camera ON         │
    │   Scheduler START   │
    └────────┬────────────┘
             ↓
    ┌─────────────────────┐
    │   ENTRY SCAN        │
    │   (Class shuru)     │
    └────────┬────────────┘
             ↓
    Har student check karo
    ┌────────┴────────────┐
    │                     │
  Mila ✅            Nahi Mila ❌
    │                     │
strike = 0          strike + 1
    │                     │
    └────────┬────────────┘
             ↓
    ┌─────────────────────┐
    │  RANDOM MID SCANS   │
    │  (2-3 baar random)  │
    └────────┬────────────┘
             ↓
    Har student check karo
    ┌────────┴────────────┐
    │                     │
  Mila ✅            Nahi Mila ❌
    │                     │
strike reset         strike + 1
    │                     │
    │              Strike >= 2?
    │              ┌──────┴──────┐
    │              │ YES         │ NO
    │         Teacher Alert   Continue
    │              │
    └──────────────┘
             ↓
    ┌─────────────────────┐
    │    EXIT SCAN        │
    │  (Class khatam)     │
    └────────┬────────────┘
             ↓
    Final Decision:
    ┌──────────────────────────┐
    │ Score >= 0.75 → PRESENT  │
    │ Score >= 0.50 → UNCERTAIN│
    │ Score < 0.50  → ABSENT   │
    └──────────────────────────┘
             ↓
    ┌─────────────────────┐
    │  CLASS COMPLETED    │
    │  Camera OFF         │
    │  Report Generate    │
    └─────────────────────┘
```

### Confidence Score System
| Score | Status | Action |
|-------|--------|--------|
| >= 0.75 | PRESENT | Direct mark present |
| >= 0.50 | UNCERTAIN | Teacher se verify karo |
| < 0.50 | ABSENT | Mark absent |

### Strike System
| Strikes | Action |
|---------|--------|
| 0-1 | Safe — grace period |
| 2+ | Mark ABSENT + Teacher alert |

---

## 7. API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Teacher login |
| POST | /auth/logout | Teacher logout |

### Enrollment
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /enrollment/student | Naya student add |
| GET | /enrollment/students | Saare students list |
| DELETE | /enrollment/student/{id} | Student remove |
| POST | /enrollment/capture | Camera se photo lo |

### Classes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /teacher/class/start | Class shuru karo |
| POST | /teacher/class/end | Class khatam karo |
| GET | /teacher/classes | Saari classes list |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attendance/{class_id} | Class ki attendance |
| GET | /attendance/student/{id} | Student ki history |
| POST | /attendance/override | Manual override |
| POST | /teacher/scan/manual | Manual scan trigger |

### Recognition
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /recognition/recognize | Face recognize karo |

---

## 8. Setup Instructions

### Step 1 — Project Setup
```powershell
# D drive mein jaao
cd D:\

# Folder banao
mkdir Face-Detection-Attendance
cd Face-Detection-Attendance

# Virtual environment
python -m venv venv
venv\Scripts\activate

# Folders banao
New-Item -ItemType Directory -Path backend/database, backend/services, backend/routes, backend/middleware, frontend, student_faces

# Init files banao
New-Item backend/__init__.py
New-Item backend/database/__init__.py
New-Item backend/services/__init__.py
New-Item backend/routes/__init__.py
New-Item backend/middleware/__init__.py
```

### Step 2 — Dependencies Install
```powershell
pip install -r requirements.txt
```

### Step 3 — Server Run
```powershell
uvicorn backend.main:app --reload
```

### Step 4 — Test
```
Browser mein kholo: http://localhost:8000
Swagger UI: http://localhost:8000/docs
```

---

## 9. Progress Tracker

### Completed ✅
- [x] Project structure setup
- [x] Virtual environment
- [x] Dependencies install (requirements.txt)
- [x] config.py — All settings
- [x] db.py — SQLite connection
- [x] models.py — All 5 tables
- [x] main.py — FastAPI server
- [x] Server running successfully

### In Progress 🔄
- [ ] auth_routes.py — Teacher login/logout
- [ ] auth_middleware.py — JWT verification

### Pending ⏳
- [ ] enrollment_routes.py — Student enrollment
- [ ] recognition_service.py — Face detection + matching
- [ ] camera_service.py — USB webcam
- [ ] attendance_service.py — Strike system
- [ ] scheduler_service.py — Auto scans
- [ ] attendance_routes.py — Attendance CRUD
- [ ] teacher_routes.py — Dashboard + override
- [ ] Frontend — Login, Dashboard, Enrollment pages
- [ ] Testing with real students

---

*Documentation last updated: Project Phase 1 Complete*
*Next: Auth System (Teacher Login/Logout)*
