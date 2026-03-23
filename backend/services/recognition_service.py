import cv2
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.config import (
    EMBEDDINGS_PATH,
    SIMILARITY_THRESHOLD,
    CONFIRMED_THRESHOLD
)


# ─────────────────────────────────────────
# Global — Embeddings Memory Mein Load
# ─────────────────────────────────────────
known_ids = []
known_encodings = []


def load_embeddings_to_memory():
    """Server start hote hi embeddings memory mein load karo"""
    global known_ids, known_encodings

    try:
        with open(EMBEDDINGS_PATH, "rb") as f:
            data = pickle.load(f)
        known_ids = data["ids"]
        known_encodings = data["encodings"]
        print(f"[RECOGNITION] {len(known_ids)} students loaded!")
    except FileNotFoundError:
        known_ids = []
        known_encodings = []
        print("[RECOGNITION] No embeddings found!")


def reload_embeddings():
    """Naya student enroll hone ke baad reload karo"""
    load_embeddings_to_memory()


# ─────────────────────────────────────────
# Liveness Detection
# ─────────────────────────────────────────

def is_real_face(frame, bbox) -> bool:
    """
    Simple liveness detection:
    1. Texture check — real skin has texture
    2. Color distribution check
    """
    x1, y1, x2, y2 = [int(b) for b in bbox]
    face_region = frame[y1:y2, x1:x2]

    if face_region.size == 0:
        return False

    # Check 1: Texture Analysis
    gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
    texture_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    if texture_score < 60:
        print(f"[LIVENESS] Failed texture check! Score: {texture_score}")
        return False

    # Check 2: Color Distribution
    b, g, r = cv2.split(face_region)
    b_std = float(np.std(b))
    g_std = float(np.std(g))
    r_std = float(np.std(r))
    avg_std = (b_std + g_std + r_std) / 3

    if avg_std < 15:
        print(f"[LIVENESS] Failed color check! Avg std: {avg_std}")
        return False

    print(f"[LIVENESS] Real face! Texture: {texture_score:.1f}, Color: {avg_std:.1f}")
    return True


# ─────────────────────────────────────────
# Single Face Recognize
# ─────────────────────────────────────────

def recognize_face(frame) -> tuple:
    """Ek frame mein ek face recognize karo"""
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))

    faces = app.get(frame)

    if not faces:
        return None, "No face detected", 0.0

    if not known_encodings:
        return None, "No students enrolled yet!", 0.0

    # Liveness check
    if not is_real_face(frame, faces[0].bbox):
        return None, "Spoof detected! Real face required.", 0.0

    query_embedding = faces[0].embedding.reshape(1, -1)
    known_matrix = np.array(known_encodings)
    scores = cosine_similarity(query_embedding, known_matrix)[0]

    best_idx = np.argmax(scores)
    best_score = float(scores[best_idx])

    if best_score >= CONFIRMED_THRESHOLD:
        status = "CONFIRMED"
        student_id = known_ids[best_idx]
        result = f"Present - {status} (score: {round(best_score, 2)})"
    elif best_score >= SIMILARITY_THRESHOLD:
        status = "UNCERTAIN"
        student_id = known_ids[best_idx]
        result = f"Uncertain - Verify manually (score: {round(best_score, 2)})"
    else:
        status = "UNKNOWN"
        student_id = None
        result = f"Unknown face (score: {round(best_score, 2)})"

    return student_id, result, best_score


# ─────────────────────────────────────────
# Multiple Faces — Full Classroom Scan
# ─────────────────────────────────────────

def recognize_all_faces(frame) -> list:
    """Ek frame mein saare faces recognize karo"""
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))

    faces = app.get(frame)

    if not faces:
        return []

    if not known_encodings:
        return []

    query_embeddings = np.array([face.embedding for face in faces])
    known_matrix = np.array(known_encodings)
    similarity_matrix = cosine_similarity(query_embeddings, known_matrix)

    results = []
    for i, scores in enumerate(similarity_matrix):
        best_idx = np.argmax(scores)
        best_score = float(scores[best_idx])

        # Liveness check
        if not is_real_face(frame, faces[i].bbox):
            results.append({
                "student_id": None,
                "status": "SPOOF",
                "confidence": 0.0,
                "bbox": faces[i].bbox.tolist()
            })
            continue

        if best_score >= CONFIRMED_THRESHOLD:
            results.append({
                "student_id": known_ids[best_idx],
                "status": "CONFIRMED",
                "confidence": round(best_score, 2),
                "bbox": faces[i].bbox.tolist()
            })
        elif best_score >= SIMILARITY_THRESHOLD:
            results.append({
                "student_id": known_ids[best_idx],
                "status": "UNCERTAIN",
                "confidence": round(best_score, 2),
                "bbox": faces[i].bbox.tolist()
            })
        else:
            results.append({
                "student_id": None,
                "status": "UNKNOWN",
                "confidence": round(best_score, 2),
                "bbox": faces[i].bbox.tolist()
            })

    return results