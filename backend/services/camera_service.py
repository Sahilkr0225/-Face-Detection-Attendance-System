import cv2
import numpy as np
from backend.config import CAMERA_INDEX


# ─────────────────────────────────────────
# Camera Service
# ─────────────────────────────────────────

class CameraService:
    def __init__(self):
        self.cap = None
        self.is_running = False

    def start(self):
        """Camera start karo"""
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise Exception("Camera nahi khul raha! Connection check karo.")
        self.is_running = True
        print("[CAMERA] Camera started!")

    def capture_frame(self) -> np.ndarray:
        """Ek frame capture karo"""
        if not self.cap or not self.is_running:
            raise Exception("Camera start nahi hai!")

        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Frame capture failed!")

        return frame

    def stop(self):
        """Camera band karo"""
        if self.cap:
            self.cap.release()
        self.is_running = False
        print("[CAMERA] Camera stopped!")

    def is_camera_available(self) -> bool:
        """Camera available hai ya nahi check karo"""
        test = cv2.VideoCapture(CAMERA_INDEX)
        available = test.isOpened()
        test.release()
        return available


# ─────────────────────────────────────────
# Global Instance
# ─────────────────────────────────────────
camera_service = CameraService()