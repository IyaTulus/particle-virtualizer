from pathlib import Path
from urllib.request import urlretrieve

import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).resolve().parent.parent / "hand_landmarker.task"

HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)

GESTURE_MAP = {
    # (0, 1, 0, 0, 0): "POINTING",
    # (1, 1, 1, 1, 1): "OPEN HAND",
    # Map common letter gestures (user-provided mapping)
    (0, 0, 0, 0, 0): "A (FIST)",
    (0, 1, 1, 1, 1): "B",
    (1, 1, 0, 0, 0): "L",
    (1, 0, 0, 0, 1): "Y",
    (0, 0, 0, 0, 1): "I",
    # # Thumb up
    # (1, 0, 0, 0, 0): "THUMB UP",
    # (0, 0, 0, 1, 0): "THUMB DOWN",
    # (0, 1, 1, 0, 0): "PEACE",
    # (0, 1, 1, 1, 0): "OK",
}


def _is_thumb_open(
    hand_landmarks, hand_label: str | None = None, mirrored: bool = True
) -> bool:
    """Return whether the thumb is open, compensating for handedness and mirroring."""
    thumb_tip_x = hand_landmarks[4].x
    thumb_ip_x = hand_landmarks[3].x

    # On mirrored/selfie frames, the x-axis is flipped relative to the physical hand.
    if hand_label == "Left":
        return thumb_tip_x > thumb_ip_x if mirrored else thumb_tip_x < thumb_ip_x

    if hand_label == "Right":
        return thumb_tip_x < thumb_ip_x if mirrored else thumb_tip_x > thumb_ip_x

    # Fallback when handedness is unavailable.
    return thumb_tip_x > thumb_ip_x if mirrored else thumb_tip_x < thumb_ip_x


def ensure_model() -> None:
    if MODEL_PATH.exists():
        return

    print("Mengunduh model Hand Landmarker...")
    urlretrieve(MODEL_URL, MODEL_PATH)


def create_hand_landmarker():
    ensure_model()
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.HandLandmarker.create_from_options(options)


def open_camera(max_index: int = 5):
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"Menggunakan kamera index {index}")
            return cap
        cap.release()

    return None


def draw_hand(frame, landmarks, show_coordinates: bool = False) -> None:
    height, width, _ = frame.shape
    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))

        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)

        # if show_coordinates:
        #     cv2.putText(
        #         frame,
        #         f"{x}, {y}",
        #         (x + 8, y - 8),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.5,
        #         (0, 0, 255),
        #         2,
        #     )

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (0, 255, 0), 2)


def get_finger_state(
    hand_landmarks, hand_label: str | None = None, mirrored: bool = True
):
    finger = []

    finger.append(1 if _is_thumb_open(hand_landmarks, hand_label, mirrored) else 0)

    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    for tip, pip in zip(tips, pips):
        if hand_landmarks[tip].y < hand_landmarks[pip].y:
            finger.append(1)
        else:
            finger.append(0)

    return finger


def classify_gesture(finger_states) -> str:
    return GESTURE_MAP.get(tuple(finger_states), "UNKNOWN")


def draw_label(frame, text: str, origin: tuple[int, int]) -> None:
    cv2.putText(
        frame,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2,
    )
