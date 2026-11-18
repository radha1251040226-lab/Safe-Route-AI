from ultralytics import YOLO
import cv2
import pyttsx3
import time
import os

# ============================================================
# SafeRouteAI - Final Video Demo
# ============================================================

POTHOLE_MODEL = r"runs\detect\pothole_detection-4\weights\best.pt"
POTHOLE_MODEL_SECONDARY = r"runs\detect\runs\detect\pothole_detection_new\weights\best.pt"
VIDEO_FILE = "road_video.mp4"

# Load models
pothole_model = YOLO(POTHOLE_MODEL)
pothole_model_secondary = YOLO(POTHOLE_MODEL_SECONDARY) if os.path.exists(POTHOLE_MODEL_SECONDARY) else None
object_model = YOLO("yolo11n.pt")

# Voice engine
from alert_manager import AlertManager
alert_manager = AlertManager()

last_warning = ""
last_voice_time = 0
VOICE_DELAY = 3.5

# Object categories
animals = {
    "bird", "cat", "dog", "horse", "sheep",
    "cow", "elephant", "bear", "zebra", "giraffe"
}

vehicles = {
    "car", "motorcycle", "bus", "truck", "bicycle"
}


def speak_warning(message):
    global last_warning, last_voice_time

    current_time = time.time()

    if (
        message != last_warning
        or current_time - last_voice_time >= VOICE_DELAY
    ):
        alert_manager.speak(message, interrupt=True)
        last_warning = message
        last_voice_time = current_time



# Check video
if not os.path.exists(VIDEO_FILE):
    print("ERROR: road_video.mp4 not found.")
    print("Put your road video inside SafeRouteAI.")
    exit()

cap = cv2.VideoCapture(VIDEO_FILE)

if not cap.isOpened():
    print("ERROR: Could not open road_video.mp4")
    exit()

print("======================================")
print("       SafeRouteAI Final Demo")
print("======================================")
print("Press Q to stop.")
print("======================================")


while True:

    ret, frame = cap.read()

    if not ret:
        print("Video finished.")
        break

    frame_height, frame_width = frame.shape[:2]
    frame_area = frame_width * frame_height

    warning = "ROAD CLEAR"
    warning_color = (0, 255, 0)
    danger_score = 0

    # ========================================================
    # POTHOLE DETECTION
    # ========================================================

    raw_boxes = []
    p_res1 = pothole_model(frame, conf=0.20, verbose=False)
    for r in p_res1:
        for box in r.boxes:
            raw_boxes.append((map(int, box.xyxy[0]), float(box.conf[0])))

    if pothole_model_secondary is not None:
        p_res2 = pothole_model_secondary(frame, conf=0.20, verbose=False)
        for r in p_res2:
            for box in r.boxes:
                raw_boxes.append((map(int, box.xyxy[0]), float(box.conf[0])))

    # Sort descending and deduplicate overlapping boxes
    raw_boxes.sort(key=lambda x: x[1], reverse=True)
    fused_potholes = []
    for (coords, confidence) in raw_boxes:
        x1, y1, x2, y2 = coords
        if y2 < frame_height * 0.20:
            continue
        overlap = False
        for (fx1, fy1, fx2, fy2, f_conf) in fused_potholes:
            ix1, iy1 = max(x1, fx1), max(y1, fy1)
            ix2, iy2 = min(x2, fx2), min(y2, fy2)
            if ix2 > ix1 and iy2 > iy1:
                inter = (ix2 - ix1) * (iy2 - iy1)
                a1 = (x2 - x1) * (y2 - y1)
                a2 = (fx2 - fx1) * (fy2 - fy1)
                iou = inter / max(a1 + a2 - inter, 1)
                if iou > 0.40 or inter / min(a1, a2) > 0.75:
                    overlap = True
                    break
        if not overlap:
            fused_potholes.append((x1, y1, x2, y2, confidence))

    for (x1, y1, x2, y2, confidence) in fused_potholes:
        area = (x2 - x1) * (y2 - y1)
        area_ratio = area / frame_area

        if area_ratio > 0.15 or confidence >= 0.70:
            current_warning = "DANGER! POTHOLE VERY CLOSE - STOP"
            current_score = 100
            current_color = (0, 0, 255)
        elif area_ratio > 0.07 or confidence >= 0.40:
            current_warning = "POTHOLE AHEAD - SLOW DOWN"
            current_score = 70
            current_color = (0, 140, 255)
        else:
            current_warning = "POTHOLE AHEAD - BE CAREFUL"
            current_score = 40
            current_color = (0, 255, 255)

        if current_score > danger_score:
            warning = current_warning
            warning_color = current_color
            danger_score = current_score

        cv2.rectangle(frame, (x1, y1), (x2, y2), current_color, 2)
        cv2.putText(
            frame,
            f"POTHOLE {confidence:.1%}",
            (x1, max(y1 - 10, 25)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            current_color,
            2
        )

    # ========================================================
    # ANIMAL / PERSON / VEHICLE DETECTION
    # ========================================================

    object_results = object_model(
        frame,
        conf=0.35,
        verbose=False
    )

    for result in object_results:

        for box in result.boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            name = object_model.names[class_id]

            if (
                name not in animals
                and name not in vehicles
                and name != "person"
            ):
                continue

            area = (x2 - x1) * (y2 - y1)
            area_ratio = area / frame_area

            # -----------------------------------------------
            # ANIMAL
            # -----------------------------------------------

            if name in animals:

                if area_ratio > 0.15:

                    current_warning = (
                        f"STOP! {name} VERY CLOSE"
                    )

                    current_score = 100
                    current_color = (0, 0, 255)

                elif area_ratio > 0.07:

                    current_warning = (
                        f"{name} AHEAD - SLOW DOWN"
                    )

                    current_score = 70
                    current_color = (0, 140, 255)

                else:

                    current_warning = (
                        f"{name} AHEAD - BE CAREFUL"
                    )

                    current_score = 40
                    current_color = (0, 255, 255)

            # -----------------------------------------------
            # PERSON
            # -----------------------------------------------

            elif name == "person":

                if area_ratio > 0.15:

                    current_warning = (
                        "STOP! PERSON VERY CLOSE"
                    )

                    current_score = 100
                    current_color = (0, 0, 255)

                else:

                    current_warning = (
                        "PERSON AHEAD - SLOW DOWN"
                    )

                    current_score = 70
                    current_color = (0, 140, 255)

            # -----------------------------------------------
            # VEHICLE
            # -----------------------------------------------

            else:

                if area_ratio > 0.15:

                    current_warning = (
                        "DANGER! VEHICLE VERY CLOSE"
                    )

                    current_score = 100
                    current_color = (0, 0, 255)

                elif area_ratio > 0.07:

                    current_warning = (
                        "VEHICLE AHEAD - SLOW DOWN"
                    )

                    current_score = 70
                    current_color = (0, 140, 255)

                else:

                    current_warning = (
                        "VEHICLE AHEAD - MAINTAIN DISTANCE"
                    )

                    current_score = 40
                    current_color = (0, 255, 255)

            # Update strongest warning
            if current_score > danger_score:

                warning = current_warning
                warning_color = current_color
                danger_score = current_score

            # Draw object
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                current_color,
                3
            )

            cv2.putText(
                frame,
                f"{name} {confidence:.2f}",
                (x1, max(y1 - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                current_color,
                2
            )

    # ========================================================
    # DISPLAY WARNING
    # ========================================================

    cv2.rectangle(
        frame,
        (0, 0),
        (frame_width, 75),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        warning,
        (20, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        warning_color,
        3
    )

    # ========================================================
    # VOICE
    # ========================================================

    speak_warning(warning)

    # ========================================================
    # PROJECT NAME
    # ========================================================

    cv2.putText(
        frame,
        "SafeRouteAI - Intelligent Road Safety",
        (15, frame_height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "SafeRouteAI - Final Demo",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()

print("SafeRouteAI demo finished.")