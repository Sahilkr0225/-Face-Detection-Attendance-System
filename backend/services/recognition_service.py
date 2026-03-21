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
    """
    Server start hote hi embeddings
    memory mein load karo — fast access ke liye
    """
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
        print("[RECOGNITION] No embeddings found — start enrolling students!")


def reload_embeddings():
    """
    Naya student enroll hone ke baad
    embeddings reload karo
    """
    load_embeddings_to_memory()


# ─────────────────────────────────────────
# Single Face Recognize
# ─────────────────────────────────────────

def recognize_face(frame) -> tuple:
    """
    Ek frame mein ek face recognize karo
    Returns: (student_id, result, confidence)
    """
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Face detect karo
    faces = app.get(frame)

    if not faces:
        return None, "No face detected", 0.0

    if not known_encodings:
        return None, "No students enrolled yet!", 0.0

    # Query embedding
    query_embedding = faces[0].embedding.reshape(1, -1)

    # Known embeddings matrix
    known_matrix = np.array(known_encodings)

    # Cosine similarity — ek saath saare students se compare
    scores = cosine_similarity(query_embedding, known_matrix)[0]

    best_idx = np.argmax(scores)
    best_score = float(scores[best_idx])

    # Confidence system
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
    """
    Ek frame mein saare faces recognize karo
    Classroom scan ke liye — 70 students ek saath!
    Returns: list of {student_id, result, confidence, bbox}
    """
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Saare faces detect karo
    faces = app.get(frame)

    if not faces:
        return []

    if not known_encodings:
        return []

    # Saare detected faces ke embeddings
    query_embeddings = np.array([face.embedding for face in faces])

    # Known embeddings matrix
    known_matrix = np.array(known_encodings)

    # Matrix cosine similarity — ek saath saare!
    similarity_matrix = cosine_similarity(query_embeddings, known_matrix)
    # Shape: (detected_faces, known_students)

    results = []
    for i, scores in enumerate(similarity_matrix):
        best_idx = np.argmax(scores)
        best_score = float(scores[best_idx])

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