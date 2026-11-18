import os
from ultralytics import YOLO

DEFAULT_MODEL_PATH = r"runs\detect\pothole_detection-4\weights\best.pt"


class PotholeDetector:

    def __init__(self, model_path=None):
        path = model_path if model_path and os.path.exists(model_path) else DEFAULT_MODEL_PATH
        self.model = YOLO(path)

    def detect(self, image_path, confidence=0.10):
        results = self.model.predict(
            source=image_path,
            conf=confidence,
            save=False,
            verbose=False
        )

        return results

    def get_pothole_count(self, results):
        if not results or len(results) == 0:
            return 0
        return len(results[0].boxes)

    def get_confidences(self, results):
        if not results or len(results) == 0:
            return []
        return [
            float(box.conf[0])
            for box in results[0].boxes
        ]