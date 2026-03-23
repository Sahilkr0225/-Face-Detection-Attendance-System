import asyncio
import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.database.db import SessionLocal
from backend.config import (
    MID_SCAN_COUNT_MIN,
    MID_SCAN_COUNT_MAX,
    ENTRY_WINDOW_MINUTES,
    EXIT_WINDOW_MINUTES
)


# ─────────────────────────────────────────
# Global State
# ─────────────────────────────────────────
current_class_id = None
is_session_active = False


# ─────────────────────────────────────────
# Trigger Scan
# ─────────────────────────────────────────

async def trigger_scan(class_id: str, scan_type: str):
    """
    Ek scan trigger karo:
    1. Camera se frame lo
    2. Faces recognize karo
    3. Attendance update karo
    """
    from backend.services.camera_service import camera_service
    from backend.services.recognition_service import recognize_all_faces
    from backend.services.attendance_service import process_scan_results
    from backend.database.models import ScanLog

    print(f"\n[SCAN] {scan_type} scan triggered at {datetime.now(timezone.utc)}")

    db: Session = SessionLocal()

    try:
        # Frame capture karo
        frame = camera_service.capture_frame()

        # Faces recognize karo
        detected_students = recognize_all_faces(frame)

        # Attendance update karo
        result = process_scan_results(
            db=db,
            class_id=class_id,
            scan_type=scan_type,
            detected_students=detected_students
        )

        # Scan log save karo
        scan_log = ScanLog(
            class_id=class_id,
            scan_type=scan_type,
            students_detected=len(detected_students)
        )
        db.add(scan_log)
        db.commit()

        print(f"[SCAN] {scan_type} complete! "
              f"Detected: {result['detected']}, "
              f"Alerts: {len(result['alerts'])}")

        # Alerts print karo
        for alert in result["alerts"]:
            print(f"[ALERT] {alert['student_name']} "
                  f"({alert['roll_no']}) — "
                  f"{alert['strikes']} strikes!")

    except Exception as e:
        print(f"[ERROR] Scan failed: {e}")

    finally:
        db.close()


# ─────────────────────────────────────────
# Random Mid Scans Schedule
# ─────────────────────────────────────────

async def schedule_mid_scans(class_id: str, duration_minutes: int):
    """
    Class ke beech mein 2-3 random mid scans karo
    """
    num_scans = random.randint(MID_SCAN_COUNT_MIN, MID_SCAN_COUNT_MAX)

    # Available time window
    available_start = ENTRY_WINDOW_MINUTES
    available_end = duration_minutes - EXIT_WINDOW_MINUTES

    # Random times nikalo
    scan_times = sorted(random.sample(
        range(available_start, available_end),
        num_scans
    ))

    print(f"[SCHEDULER] Mid scans scheduled at minutes: {scan_times}")

    last_time = ENTRY_WINDOW_MINUTES
    for scan_minute in scan_times:
        if not is_session_active:
            break

        wait_seconds = (scan_minute - last_time) * 60
        await asyncio.sleep(wait_seconds)

        if is_session_active:
            await trigger_scan(class_id, "MID")

        last_time = scan_minute


# ─────────────────────────────────────────
# Main Class Session
# ─────────────────────────────────────────

async def run_class_session(class_id: str, duration_minutes: int = 60):
    """
    Poora class session manage karo:
    Entry → Mid Scans → Exit
    """
    global current_class_id, is_session_active

    current_class_id = class_id
    is_session_active = True

    print(f"\n[SCHEDULER] Class session started! Duration: {duration_minutes} min")

    # Step 1 — Entry Scan (turant)
    await trigger_scan(class_id, "ENTRY")

    # Step 2 — Mid Scans (random times pe)
    mid_scan_task = asyncio.create_task(
        schedule_mid_scans(class_id, duration_minutes)
    )

    # Step 3 — Exit Scan (last 10 min mein)
    exit_wait = (duration_minutes - EXIT_WINDOW_MINUTES) * 60
    await asyncio.sleep(exit_wait)

    # Mid scans khatam karo
    mid_scan_task.cancel()

    if is_session_active:
        await trigger_scan(class_id, "EXIT")

    is_session_active = False
    print(f"[SCHEDULER] Class session complete!")


# ─────────────────────────────────────────
# Stop Session
# ─────────────────────────────────────────

def stop_session():
    """Session force stop karo"""
    global is_session_active
    is_session_active = False
    print("[SCHEDULER] Session stopped!")