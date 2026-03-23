from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.database.models import (
    Attendance, Class, Student,
    AttendanceStatus, ClassStatus
)
from backend.config import STRIKE_LIMIT, CONFIRMED_THRESHOLD, SIMILARITY_THRESHOLD


# ─────────────────────────────────────────
# In-Memory Strike Tracker
# ─────────────────────────────────────────
attendance_strikes = {}   # {student_id: strike_count}
confirmed_present = set() # {student_id} — jo confirm present hain


# ─────────────────────────────────────────
# Class Start
# ─────────────────────────────────────────

def start_class_session(db: Session, subject: str, teacher_id: str, duration_minutes: int = 8) -> Class:
    """
    Naya class session start karo
    """
    global attendance_strikes, confirmed_present

    # Trackers reset karo
    attendance_strikes = {}
    confirmed_present = set()

    # Class DB mein save karo
    new_class = Class(
        subject=subject,
        teacher_id=teacher_id,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        start_time=datetime.now(timezone.utc),
        duration_minutes=duration_minutes,
        status=ClassStatus.ONGOING
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    # Saare students ke liye UNCERTAIN attendance banao
    students = db.query(Student).all()
    for student in students:
        attendance = Attendance(
            student_id=student.id,
            class_id=new_class.id,
            status=AttendanceStatus.UNCERTAIN,
            strike_count=0
        )
        db.add(attendance)
    db.commit()

    print(f"[CLASS] Session started: {subject} | {len(students)} students")
    return new_class


# ─────────────────────────────────────────
# Process Scan Results
# ─────────────────────────────────────────

def process_scan_results(
    db: Session,
    class_id: str,
    scan_type: str,
    detected_students: list
) -> dict:
    """
    Scan results process karo aur attendance update karo
    detected_students = [{"student_id": "...", "status": "CONFIRMED", "confidence": 0.79}]
    """
    detected_ids = {
        s["student_id"]
        for s in detected_students
        if s["student_id"] is not None
    }

    # Saare students ki attendance lo
    attendances = db.query(Attendance).filter(
        Attendance.class_id == class_id
    ).all()

    updated = 0
    alerts = []

    for att in attendances:
        student_id = att.student_id

        if student_id in confirmed_present:
            continue  # Already confirmed — skip

        if student_id in detected_ids:
            # Student mila — strike reset
            att.strike_count = 0
            attendance_strikes[student_id] = 0

            # Confidence score update
            detected = next(
                (s for s in detected_students if s["student_id"] == student_id),
                None
            )
            if detected:
                att.confidence_score = detected["confidence"]

            # Exit scan pe PRESENT mark karo
            if scan_type == "EXIT":
                att.status = AttendanceStatus.PRESENT
                att.final_marked_at = datetime.now(timezone.utc)
                confirmed_present.add(student_id)

        else:
            # Student nahi mila — strike add karo
            current_strikes = attendance_strikes.get(student_id, 0) + 1
            attendance_strikes[student_id] = current_strikes
            att.strike_count = current_strikes

            # Strike limit cross ho gayi?
            if current_strikes >= STRIKE_LIMIT:
                att.status = AttendanceStatus.ABSENT
                att.final_marked_at = datetime.now(timezone.utc)

                # Teacher ko alert
                student = db.query(Student).filter(
                    Student.id == student_id
                ).first()
                if student:
                    alerts.append({
                        "student_name": student.name,
                        "roll_no": student.roll_no,
                        "strikes": current_strikes
                    })

        updated += 1

    db.commit()
    print(f"[ATTENDANCE] {scan_type} scan processed. "
          f"Detected: {len(detected_ids)}, Updated: {updated}")

    return {
        "scan_type": scan_type,
        "detected": len(detected_ids),
        "alerts": alerts
    }


# ─────────────────────────────────────────
# Class End
# ─────────────────────────────────────────

def end_class_session(db: Session, class_id: str) -> dict:
    """
    Class khatam karo — final attendance mark karo
    """
    # Class status update karo
    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_:
        raise ValueError("Class nahi mili!")

    class_.status = ClassStatus.COMPLETED
    class_.end_time = datetime.now(timezone.utc)

    # Jo students abhi bhi UNCERTAIN hain unhe ABSENT mark karo
    uncertain = db.query(Attendance).filter(
        Attendance.class_id == class_id,
        Attendance.status == AttendanceStatus.UNCERTAIN
    ).all()

    for att in uncertain:
        att.status = AttendanceStatus.ABSENT
        att.final_marked_at = datetime.now(timezone.utc)

    db.commit()

    # Final report
    present = db.query(Attendance).filter(
        Attendance.class_id == class_id,
        Attendance.status == AttendanceStatus.PRESENT
    ).count()

    absent = db.query(Attendance).filter(
        Attendance.class_id == class_id,
        Attendance.status == AttendanceStatus.ABSENT
    ).count()

    print(f"[CLASS] Session ended! Present: {present}, Absent: {absent}")

    return {
        "class_id": class_id,
        "subject": class_.subject,
        "present": present,
        "absent": absent,
        "total": present + absent
    }


# ─────────────────────────────────────────
# Get Attendance Report
# ─────────────────────────────────────────

def get_attendance_report(db: Session, class_id: str) -> list:
    """Class ki attendance report lo"""
    attendances = db.query(Attendance).filter(
        Attendance.class_id == class_id
    ).all()

    report = []
    for att in attendances:
        student = db.query(Student).filter(
            Student.id == att.student_id
        ).first()
        if student:
            report.append({
                "student_name": student.name,
                "roll_no": student.roll_no,
                "status": att.status,
                "confidence": att.confidence_score,
                "strikes": att.strike_count
            })

    return report


# ─────────────────────────────────────────
# Manual Override
# ─────────────────────────────────────────

def override_attendance(
    db: Session,
    attendance_id: str,
    teacher_id: str,
    new_status: str,
    reason: str = None
) -> bool:
    """Teacher manually attendance change kare"""
    from backend.database.models import AttendanceOverride

    att = db.query(Attendance).filter(
        Attendance.id == attendance_id
    ).first()

    if not att:
        return False

    # Override record banao
    override = AttendanceOverride(
        attendance_id=att.id,
        teacher_id=teacher_id,
        old_status=att.status,
        new_status=new_status,
        reason=reason,
    )
    db.add(override)

    # Attendance update karo
    att.status = new_status
    att.final_marked_at = datetime.now(timezone.utc)

    db.commit()
    print(f"[OVERRIDE] Attendance {attendance_id} changed to {new_status}")
    return True