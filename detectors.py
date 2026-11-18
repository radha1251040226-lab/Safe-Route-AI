import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

import cv2
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from ultralytics import YOLO

# ============================================================
# MODEL WEIGHT PATHS CONFIGURATION
# ============================================================
FINE_GRAINED_POTHOLE_WEIGHTS = r"runs\detect\pothole_detection-4\weights\best.pt"
CLUSTER_POTHOLE_WEIGHTS = r"runs\detect\runs\detect\pothole_detection_new\weights\best.pt"
DEFAULT_POTHOLE_WEIGHTS = FINE_GRAINED_POTHOLE_WEIGHTS if os.path.exists(FINE_GRAINED_POTHOLE_WEIGHTS) else CLUSTER_POTHOLE_WEIGHTS

DEFAULT_PERSON_WEIGHTS = r"dataset_multi\runs\detect\person_detection\weights\best.pt"
DEFAULT_VEHICLE_WEIGHTS = r"runs\detect\vehicle_detection-2\weights\best.pt"
DEFAULT_GENERAL_WEIGHTS = "yolo11n.pt"
RESNET_WEIGHTS = r"C:\Users\radha daulat shinde\.cache\torch\hub\checkpoints\resnet18-f37072fd.pth"


# ============================================================
# DOMAIN DATA TRANSFER OBJECTS (OOP ENCAPSULATION)
# ============================================================

@dataclass
class BoundingBox:
    """Encapsulates spatial coordinates, intersection, and containment logic."""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0

    def as_list(self) -> List[int]:
        return [self.x1, self.y1, self.x2, self.y2]

    def contains_point(self, px: float, py: float) -> bool:
        return (self.x1 <= px <= self.x2) and (self.y1 <= py <= self.y2)

    def intersection_area(self, other: "BoundingBox") -> int:
        ix1 = max(self.x1, other.x1)
        iy1 = max(self.y1, other.y1)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)
        if ix2 > ix1 and iy2 > iy1:
            return (ix2 - ix1) * (iy2 - iy1)
        return 0

    def iou(self, other: "BoundingBox") -> float:
        ia = self.intersection_area(other)
        if ia == 0:
            return 0.0
        union = self.area + other.area - ia
        return ia / max(union, 1)

    def overlaps_obstacle(self, other: "BoundingBox", threshold: float = 0.10) -> bool:
        """Determines if candidate overlaps an obstacle center or exceeds area threshold."""
        cx, cy = self.center
        ocx, ocy = other.center
        if other.contains_point(cx, cy) or self.contains_point(ocx, ocy):
            return True
        ia = self.intersection_area(other)
        if ia > 0:
            if (ia / max(self.area, 1) > threshold) or (ia / max(other.area, 1) > threshold):
                return True
        return False


@dataclass
class DetectedHazard:
    """Encapsulates an identified roadway hazard item."""
    label: str
    confidence: float
    bbox: List[int]
    area_ratio: float = 0.0
    severity: str = "Low"
    display_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "label": self.label,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "area_ratio": self.area_ratio,
        }
        if self.severity:
            d["severity"] = self.severity
        if self.display_name:
            d["display_name"] = self.display_name
        return d


# ============================================================
# ABSTRACT DETECTOR BASE CLASS (OOP ABSTRACTION)
# ============================================================

class AbstractHazardDetector(ABC):
    """Abstract Base Class for all vision detection engines."""

    @abstractmethod
    def detect(self, *args, **kwargs) -> Any:
        """Executes perception inference."""
        pass


class HUDOverlayRenderer:
    """Encapsulates visual telemetry rendering on OpenCV matrices."""

    @staticmethod
    def draw_box(img: np.ndarray, bbox: List[int], label_text: str, color: Tuple[int, int, int], thickness: int = 2) -> None:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        tag_y1 = max(0, y1 - th - 8)
        tag_y2 = y1
        tag_x2 = min(img.shape[1], x1 + tw + 10)
        cv2.rectangle(img, (x1, tag_y1), (tag_x2, tag_y2), color, -1)
        cv2.putText(
            img,
            label_text,
            (x1 + 4, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

    @staticmethod
    def draw_surface_badge(img: np.ndarray, surface_status: str) -> None:
        hud_surface_text = f"SURFACE: {surface_status.upper()}"
        (st_w, st_h), _ = cv2.getTextSize(hud_surface_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(img, (8, 8), (st_w + 22, st_h + 20), (20, 20, 20), -1)
        badge_border_color = (0, 215, 255) if surface_status == "Dry Grass Present" else (100, 200, 100)
        cv2.rectangle(img, (8, 8), (st_w + 22, st_h + 20), badge_border_color, 1)
        cv2.putText(
            img,
            hud_surface_text,
            (15, st_h + 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )


# ============================================================
# CONCRETE DETECTOR ENGINES (OOP INHERITANCE & ENCAPSULATION)
# ============================================================

class TerrainAnalyzer(AbstractHazardDetector):
    """Encapsulates surface texture, HSV ground analysis, and savanna classification."""

    SAVANNA_SPECIES = {
        "Lion", "Giraffe", "Elephant", "Antelope / Hartebeest",
        "Antelope / Gazelle", "Antelope / Impala", "Zebra", "Cheetah",
        "Leopard", "Lioness / Wildlife", "Hyena", "Buffalo"
    }

    def detect(self, cv_img: np.ndarray, animals: Optional[List[Dict[str, Any]]] = None, vehicles: Optional[List[Dict[str, Any]]] = None, people: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return self.classify_terrain(cv_img, animals=animals, vehicles=vehicles, people=people)

    @classmethod
    def classify_terrain(cls, cv_img: np.ndarray, animals=None, vehicles=None, people=None) -> Dict[str, Any]:
        animals = animals or []
        vehicles = vehicles or []
        people = people or []

        height, width = cv_img.shape[:2]
        ground = cv_img[int(height * 0.45):, :]
        if ground.size == 0:
            ground = cv_img

        gray = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(ground, cv2.COLOR_BGR2HSV)

        # 1. Golden dry grass: Hue [11, 32], Saturation [45, 255], Value [105, 255]
        gold_grass = cv2.inRange(hsv, (11, 45, 105), (32, 255, 255))
        gold_pct = float(np.count_nonzero(gold_grass) / max(ground.shape[0] * ground.shape[1], 1))

        # 2. Mud / earthen dirt: Hue [8, 32], Saturation [35, 255], Value [20, 105]
        mud = cv2.inRange(hsv, (8, 35, 20), (32, 255, 105))
        mud_pct = float(np.count_nonzero(mud) / max(ground.shape[0] * ground.shape[1], 1))

        # 3. Paved gray asphalt: low saturation (< 45), medium value [25, 175]
        gray_road = cv2.inRange(hsv, (0, 0, 25), (180, 45, 175))
        gray_pct = float(np.count_nonzero(gray_road) / max(ground.shape[0] * ground.shape[1], 1))

        # 4. Green vegetation: Hue [35, 85], Saturation [35, 255]
        green_veg = cv2.inRange(hsv, (35, 35, 40), (85, 255, 255))
        green_pct = float(np.count_nonzero(green_veg) / max(ground.shape[0] * ground.shape[1], 1))

        # 5. Roughness variance
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        has_savanna_wildlife = any(
            a.get("label") in cls.SAVANNA_SPECIES or "snake" in a.get("label", "").lower() or "cobra" in a.get("label", "").lower()
            for a in animals
        )

        if has_savanna_wildlife or (gold_pct >= 0.40 and lap_var > 400 and len(vehicles) == 0):
            return {
                "type": "Dry Grass / Savanna Grassland",
                "surface_status": "Dry Grass Present",
                "icon": "🌾",
                "is_offroad": True,
                "gold_ratio": gold_pct,
                "description": "Dry grass savanna terrain detected. Wild animal habitat."
            }
        elif green_pct >= 0.35:
            return {
                "type": "Green Meadow / Grassland",
                "surface_status": "Green Grass Present",
                "icon": "🌱",
                "is_offroad": True,
                "gold_ratio": 0.0,
                "description": "Vegetated unpaved meadow terrain."
            }
        elif gray_pct >= 0.35 or (len(vehicles) > 0 and gold_pct < 0.40):
            return {
                "type": "Paved Asphalt Road",
                "surface_status": "Paved Asphalt",
                "icon": "🛣️",
                "is_offroad": False,
                "gold_ratio": gold_pct,
                "description": "Standard paved asphalt roadway surface."
            }
        elif mud_pct >= 0.35:
            return {
                "type": "Unpaved Dirt Road",
                "surface_status": "Unpaved Dirt Road",
                "icon": "🚜",
                "is_offroad": True,
                "gold_ratio": gold_pct,
                "description": "Unpaved earthen roadway surface."
            }
        else:
            return {
                "type": "Mixed Road / Off-Road",
                "surface_status": "General Surface",
                "icon": "🛣️",
                "is_offroad": False,
                "gold_ratio": gold_pct,
                "description": "Roadway / mixed terrain."
            }


class ObstacleDetectionEngine(AbstractHazardDetector):
    """
    Encapsulates YOLO general obstacle detection and ResNet-18 secondary classifier
    for fine-grained bovine and wildlife identification.
    """

    ANIMAL_CLASSES = {
        "bird", "cat", "dog", "horse", "sheep",
        "cow", "elephant", "bear", "zebra", "giraffe"
    }

    VEHICLE_CLASSES = {
        "car", "motorcycle", "bus", "truck", "bicycle", "ambulance"
    }

    WILDLIFE_MAPPING = {
        "lion": "Lion",
        "tiger": "Tiger",
        "cheetah": "Cheetah",
        "leopard": "Leopard",
        "jaguar": "Jaguar",
        "African elephant": "Elephant",
        "Indian elephant": "Elephant",
        "tusker": "Elephant",
        "hyena": "Hyena",
        "zebra": "Zebra",
        "giraffe": "Giraffe",
        "gazelle": "Antelope / Gazelle",
        "hartebeest": "Antelope / Hartebeest",
        "impala": "Antelope / Impala",
        "bison": "Bison / Bull",
        "ox": "Cow / Bull (Cattle)",
        "water buffalo": "Water Buffalo (Cattle)",
        "Arabian camel": "Lioness / Wildlife",
        "bighorn": "Wildlife",
        "wild boar": "Wild Boar",
        "thunder snake": "Snake (Thunder Snake)",
        "ringneck snake": "Snake (Ringneck Snake)",
        "hognose snake": "Snake (Hognose Snake)",
        "green snake": "Snake (Green Snake)",
        "king snake": "Snake (King Snake)",
        "garter snake": "Snake (Garter Snake)",
        "water snake": "Snake (Water Snake)",
        "vine snake": "Snake (Vine Snake)",
        "night snake": "Snake (Night Snake)",
        "boa constrictor": "Snake (Boa Constrictor)",
        "rock python": "Snake (Python)",
        "Indian cobra": "Snake (Cobra)",
        "green mamba": "Snake (Mamba)",
        "sea snake": "Snake (Sea Snake)",
        "horned viper": "Snake (Horned Viper)",
        "sidewinder": "Snake (Sidewinder)"
    }

    SNAKE_CLASSES = {
        "thunder snake", "ringneck snake", "hognose snake", "green snake",
        "king snake", "garter snake", "water snake", "vine snake",
        "night snake", "boa constrictor", "rock python", "Indian cobra",
        "green mamba", "sea snake", "horned viper", "sidewinder"
    }

    def __init__(self, general_weights: str = DEFAULT_GENERAL_WEIGHTS, resnet_weights: str = RESNET_WEIGHTS):
        self._general_model = YOLO(general_weights) if os.path.exists(general_weights) else YOLO("yolov8n.pt")
        self._animal_classifier = None
        self._animal_preprocess = None
        self._imagenet_categories = None

        if os.path.exists(resnet_weights):
            try:
                clf = models.resnet18()
                clf.load_state_dict(torch.load(resnet_weights, weights_only=True))
                clf.eval()
                self._animal_classifier = clf
                self._animal_preprocess = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ])
                from torchvision.models import ResNet18_Weights
                self._imagenet_categories = ResNet18_Weights.DEFAULT.meta['categories']
            except Exception as e:
                print("ResNet18 animal refiner initialization note:", e)

    def detect(
        self,
        cv_img: np.ndarray,
        pil_img: Image.Image,
        conf_objects: float = 0.25,
        detect_people: bool = True,
        detect_vehicles: bool = True,
        detect_animals: bool = True
    ) -> Dict[str, Any]:
        height, width = cv_img.shape[:2]
        frame_area = max(height * width, 1)

        people: List[Dict[str, Any]] = []
        vehicles: List[Dict[str, Any]] = []
        raw_animals: List[Dict[str, Any]] = []
        raw_obstacle_boxes: List[List[int]] = []
        danger_score = 0

        # Baseline threshold to ensure obstacles are tracked even if UI slider is high
        internal_conf = min(conf_objects, 0.18)

        g_res = self._general_model.predict(cv_img, conf=internal_conf, verbose=False)
        if g_res and len(g_res) > 0:
            names = g_res[0].names
            for box in g_res[0].boxes:
                cls_id = int(box.cls[0])
                label = names.get(cls_id, "").lower()
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                b_area = (x2 - x1) * (y2 - y1)
                area_ratio = b_area / frame_area

                if label in {"person"} or label in self.VEHICLE_CLASSES or label in self.ANIMAL_CLASSES:
                    raw_obstacle_boxes.append([x1, y1, x2, y2])

                # Pedestrians
                if detect_people and label == "person" and conf >= conf_objects:
                    danger_score = max(danger_score, 75 if area_ratio > 0.08 else 45)
                    people.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": conf,
                        "area_ratio": area_ratio,
                        "label": "Pedestrian"
                    })

                # Vehicles
                elif detect_vehicles and label in self.VEHICLE_CLASSES and conf >= conf_objects:
                    vehicles.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": conf,
                        "area_ratio": area_ratio,
                        "label": label.capitalize()
                    })

                # Livestock & Animals with perception floor 0.22
                elif detect_animals and (label in self.ANIMAL_CLASSES or label in {"tie", "baseball bat", "banana", "sports ball"}) and conf >= min(conf_objects, 0.22):
                    final_label = "Cow (Cattle)" if label == "cow" else label.capitalize()
                    display_name = f"Animal ({final_label})"
                    refined_conf = conf

                    # Two-stage classification via ResNet18
                    if self._animal_classifier is not None:
                        try:
                            pad_x = int((x2 - x1) * 0.05)
                            pad_y = int((y2 - y1) * 0.05)
                            crop = pil_img.crop((max(0, x1 - pad_x), max(0, y1 - pad_y), min(width, x2 + pad_x), min(height, y2 + pad_y)))
                            t_inp = self._animal_preprocess(crop).unsqueeze(0)
                            with torch.no_grad():
                                logits = self._animal_classifier(t_inp)
                            probs = torch.nn.functional.softmax(logits[0], dim=0)
                            top_p, top_id = torch.topk(probs, 1)
                            pred_class = self._imagenet_categories[top_id[0]]
                            pred_prob = float(top_p[0])

                            if pred_class in self.WILDLIFE_MAPPING and pred_prob >= 0.15:
                                final_label = self.WILDLIFE_MAPPING[pred_class]
                                refined_conf = max(conf, pred_prob)
                                if pred_class in self.SNAKE_CLASSES:
                                    display_name = f"{final_label} (Venomous Reptile)"
                                elif "cattle" in final_label.lower() or "cow" in final_label.lower() or "buffalo" in final_label.lower():
                                    display_name = f"{final_label} (Livestock)"
                                else:
                                    display_name = f"{final_label} (Wildlife)"
                        except Exception:
                            pass

                    raw_animals.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": refined_conf,
                        "area_ratio": area_ratio,
                        "label": final_label,
                        "display_name": display_name
                    })

        return {
            "people": people,
            "vehicles": vehicles,
            "raw_animals": raw_animals,
            "raw_obstacle_boxes": raw_obstacle_boxes,
            "danger_score": danger_score
        }

    def scan_savanna_reptiles(self, pil_img: Image.Image, frame_area: int) -> List[Dict[str, Any]]:
        """Patched scanner for reptiles on dry savanna grassland."""
        if self._animal_classifier is None:
            return []
        width, height = pil_img.size
        snakes_found = []
        try:
            scale = min(1.0, 640.0 / max(width, height))
            sw, sh = int(width * scale), int(height * scale)
            sim = pil_img.resize((sw, sh))
            g_top = int(sh * 0.35)
            patch_sz = 160
            step = 90
            p_crops, p_boxes = [], []
            for py in range(g_top, sh - 30, step):
                for px in range(0, sw - 30, step):
                    px2 = min(sw, px + patch_sz)
                    py2 = min(sh, py + patch_sz)
                    crop = sim.crop((px, py, px2, py2))
                    p_crops.append(self._animal_preprocess(crop))
                    p_boxes.append([int(px / scale), int(py / scale), int(px2 / scale), int(py2 / scale)])
                    if len(p_crops) >= 32:
                        break
                if len(p_crops) >= 32:
                    break

            if p_crops:
                t_batch = torch.stack(p_crops)
                with torch.no_grad():
                    logits = self._animal_classifier(t_batch)
                probs = torch.nn.functional.softmax(logits, dim=1)
                for i, p_box in enumerate(p_boxes):
                    top_p, top_id = torch.topk(probs[i], 1)
                    p_cat = self._imagenet_categories[top_id[0]]
                    p_prob = float(top_p[0])
                    if p_cat in self.SNAKE_CLASSES and p_prob >= 0.30:
                        s_label = self.WILDLIFE_MAPPING.get(p_cat, "Snake")
                        snakes_found.append({
                            "bbox": p_box,
                            "confidence": p_prob,
                            "area_ratio": (p_box[2] - p_box[0]) * (p_box[3] - p_box[1]) / frame_area,
                            "label": s_label,
                            "display_name": f"{s_label} (Savanna Reptile)"
                        })
        except Exception:
            pass
        return snakes_found


class SpatialSafetyBarrier:
    """Enforces spatial obstacle rejection to prevent false potholes on animals/people/vehicles."""

    @staticmethod
    def is_pothole_spatially_valid(
        candidate_bbox: BoundingBox,
        obstacle_boxes: List[BoundingBox],
        frame_height: int,
        is_savanna_terrain: bool,
        confidence: float
    ) -> bool:
        # Safety Filter 1: A pothole cannot be in the sky, wall, or ceiling
        if candidate_bbox.y2 < frame_height * 0.20:
            return False

        # Safety Filter 2: Suppress low-confidence hallucinations on open savanna grass
        if is_savanna_terrain and confidence < 0.85:
            return False

        # Safety Filter 3: A pothole cannot overlap with any detected obstacle
        for obs in obstacle_boxes:
            if candidate_bbox.overlaps_obstacle(obs, threshold=0.10):
                return False

        return True


class PotholeDetectionEngine(AbstractHazardDetector):
    """
    Encapsulates dual-head YOLO crater detection, multi-scale TTA,
    and NMS/IoU containment fusion.
    """

    def __init__(self, primary_weights: str = DEFAULT_POTHOLE_WEIGHTS, secondary_weights: Optional[str] = None):
        self._primary_model = YOLO(primary_weights) if os.path.exists(primary_weights) else None
        alt_weights = secondary_weights or (
            CLUSTER_POTHOLE_WEIGHTS if primary_weights != CLUSTER_POTHOLE_WEIGHTS else FINE_GRAINED_POTHOLE_WEIGHTS
        )
        self._secondary_model = YOLO(alt_weights) if os.path.exists(alt_weights) else None

    @property
    def is_ready(self) -> bool:
        return self._primary_model is not None

    def detect(
        self,
        cv_img: np.ndarray,
        conf_pothole: float = 0.20,
        augment: bool = True,
        obstacle_boxes: Optional[List[BoundingBox]] = None,
        is_savanna_terrain: bool = False
    ) -> List[Dict[str, Any]]:
        if not self.is_ready:
            return []

        height, width = cv_img.shape[:2]
        frame_area = max(height * width, 1)
        raw_cutoff = min(conf_pothole, 0.18)
        obstacle_boxes = obstacle_boxes or []

        all_boxes = []
        p_res1 = self._primary_model.predict(cv_img, conf=raw_cutoff, augment=augment, verbose=False)
        if p_res1 and len(p_res1) > 0:
            all_boxes.extend(p_res1[0].boxes)

        if self._secondary_model is not None:
            p_res2 = self._secondary_model.predict(cv_img, conf=raw_cutoff, augment=False, verbose=False)
            if p_res2 and len(p_res2) > 0:
                all_boxes.extend(p_res2[0].boxes)

        raw_candidates = []
        for box in all_boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cand_bbox = BoundingBox(x1, y1, x2, y2)

            if not SpatialSafetyBarrier.is_pothole_spatially_valid(
                cand_bbox, obstacle_boxes, height, is_savanna_terrain, conf
            ):
                continue

            raw_candidates.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": conf,
                "cand_bbox": cand_bbox,
                "area": cand_bbox.area
            })

        # Sort descending by confidence and fuse with NMS IoU + containment
        raw_candidates.sort(key=lambda x: x["confidence"], reverse=True)
        final_potholes: List[Dict[str, Any]] = []

        for item in raw_candidates:
            conf = item["confidence"]
            if conf < conf_pothole:
                continue

            b1 = item["cand_bbox"]
            keep = True
            for accepted in final_potholes:
                b2 = accepted["_bbox_obj"]
                ia = b1.intersection_area(b2)
                if ia > 0:
                    iou = ia / max(b1.area + b2.area - ia, 1)
                    if iou > 0.40 or ia / min(b1.area, b2.area) > 0.75:
                        keep = False
                        break

            if not keep:
                continue

            area_ratio = b1.area / frame_area
            if area_ratio > 0.10 or conf >= 0.60:
                severity = "High"
            elif area_ratio > 0.04 or conf >= 0.30:
                severity = "Medium"
            else:
                severity = "Low"

            final_potholes.append({
                "bbox": b1.as_list(),
                "confidence": conf,
                "area_ratio": area_ratio,
                "severity": severity,
                "label": "Pothole",
                "_bbox_obj": b1
            })

        return final_potholes


# ============================================================
# FACADE PIPELINE (OOP COMPOSITION & UNIFIED INTERFACE)
# ============================================================

class MultiHazardDetector:
    """
    Unified Multi-Hazard Perception Pipeline.
    Coordinates TerrainAnalyzer, ObstacleDetectionEngine, PotholeDetectionEngine,
    and HUDOverlayRenderer via Composition.
    """

    ANIMAL_CLASSES = ObstacleDetectionEngine.ANIMAL_CLASSES
    VEHICLE_CLASSES = ObstacleDetectionEngine.VEHICLE_CLASSES
    WILDLIFE_MAPPING = ObstacleDetectionEngine.WILDLIFE_MAPPING
    SNAKE_CLASSES = ObstacleDetectionEngine.SNAKE_CLASSES

    def __init__(
        self,
        pothole_weights: str = DEFAULT_POTHOLE_WEIGHTS,
        general_weights: str = DEFAULT_GENERAL_WEIGHTS,
        person_weights: str = DEFAULT_PERSON_WEIGHTS
    ):
        self.pothole_engine = PotholeDetectionEngine(primary_weights=pothole_weights)
        self.obstacle_engine = ObstacleDetectionEngine(general_weights=general_weights)
        self.terrain_analyzer = TerrainAnalyzer()
        self.renderer = HUDOverlayRenderer()

        # Backward compatibility properties
        self.pothole_model = self.pothole_engine._primary_model
        self.pothole_model_secondary = self.pothole_engine._secondary_model
        self.general_model = self.obstacle_engine._general_model
        self.animal_classifier = self.obstacle_engine._animal_classifier

    def detect_all(
        self,
        image_input,
        conf_pothole: float = 0.25,
        conf_objects: float = 0.30,
        detect_potholes: bool = True,
        detect_people: bool = True,
        detect_vehicles: bool = True,
        detect_animals: bool = True,
        augment_potholes: bool = True
    ) -> Dict[str, Any]:
        """
        Executes unified multi-hazard perception inference.
        """
        if isinstance(image_input, str):
            cv_img = cv2.imread(image_input)
            if cv_img is None:
                raise ValueError(f"Could not load image from {image_input}")
            pil_img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            cv_img = image_input.copy()
            if len(cv_img.shape) == 2:
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2BGR)
            pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        else:
            raise TypeError("Unsupported image input format.")

        height, width = cv_img.shape[:2]
        frame_area = max(height * width, 1)
        annotated_bgr = cv_img.copy()

        # Step 1: Obstacle Perception
        obs_res = self.obstacle_engine.detect(
            cv_img, pil_img,
            conf_objects=conf_objects,
            detect_people=detect_people,
            detect_vehicles=detect_vehicles,
            detect_animals=detect_animals
        )
        people = obs_res["people"]
        vehicles = obs_res["vehicles"]
        raw_animals = obs_res["raw_animals"]
        raw_obstacle_boxes = obs_res["raw_obstacle_boxes"]
        danger_score = obs_res["danger_score"]

        # Step 2: Terrain Classification
        terrain = self.terrain_analyzer.detect(cv_img, animals=raw_animals, vehicles=vehicles, people=people)

        # Ground Reptile Scanner for Savanna
        is_savanna = (terrain.get("surface_status") == "Dry Grass Present") or (terrain.get("gold_ratio", 0) >= 0.35 and len(raw_animals) > 0)
        if detect_animals and is_savanna:
            reptiles = self.obstacle_engine.scan_savanna_reptiles(pil_img, frame_area)
            raw_animals.extend(reptiles)

        # Animal NMS deduplication
        animals: List[Dict[str, Any]] = []
        raw_animals.sort(key=lambda x: x["confidence"], reverse=True)
        for item in raw_animals:
            box_a = item["bbox"]
            keep = True
            for accepted in animals:
                box_b = accepted["bbox"]
                inter_w = max(0, min(box_a[2], box_b[2]) - max(box_a[0], box_b[0]))
                inter_h = max(0, min(box_a[3], box_b[3]) - max(box_a[1], box_b[1]))
                ia = inter_w * inter_h
                if ia > 0:
                    aa = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
                    ab = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
                    if ia / max(aa + ab - ia, 1) > 0.35:
                        keep = False
                        break
            if keep:
                animals.append(item)

        # Render Obstacle Annotations
        for p in people:
            self.renderer.draw_box(annotated_bgr, p["bbox"], f"PERSON {p['confidence']:.1%}", (255, 105, 0))
        for v in vehicles:
            self.renderer.draw_box(annotated_bgr, v["bbox"], f"{v['label'].upper()} {v['confidence']:.1%}", (255, 191, 0))
        for a in animals:
            lbl = a["label"]
            cnf = a["confidence"]
            if "snake" in lbl.lower() or "cobra" in lbl.lower() or "viper" in lbl.lower():
                danger_score = max(danger_score, 95)
                box_color = (0, 0, 255)
                tag = f"DANGER: {lbl.upper()} {cnf:.1%}"
            elif lbl in {"Lion", "Tiger", "Leopard", "Cheetah", "Jaguar", "Lioness / Wildlife", "Elephant"}:
                danger_score = max(danger_score, 90)
                box_color = (0, 0, 235)
                tag = f"DANGER: {lbl.upper()} {cnf:.1%}"
            else:
                danger_score = max(danger_score, 60)
                box_color = (180, 50, 200)
                tag = f"{lbl.upper()} {cnf:.1%}"
            self.renderer.draw_box(annotated_bgr, a["bbox"], tag, box_color)

        # Step 3: Pothole Perception with Spatial Consistency
        potholes: List[Dict[str, Any]] = []
        max_area_ratio = 0.0

        if detect_potholes and self.pothole_engine.is_ready:
            # Build obstacle barrier list from both detected UI objects and raw baseline boxes
            obstacle_bboxes: List[BoundingBox] = []
            for o in (people + animals + vehicles):
                b = o["bbox"]
                obstacle_bboxes.append(BoundingBox(b[0], b[1], b[2], b[3]))
            for rb in raw_obstacle_boxes:
                obstacle_bboxes.append(BoundingBox(rb[0], rb[1], rb[2], rb[3]))

            is_savanna_terrain = (
                terrain["surface_status"] == "Dry Grass Present"
                and (
                    any(a.get("label") in TerrainAnalyzer.SAVANNA_SPECIES or "snake" in a.get("label", "").lower() for a in animals)
                    or terrain.get("gold_ratio", 0) > 0.60
                )
            )

            potholes_res = self.pothole_engine.detect(
                cv_img,
                conf_pothole=conf_pothole,
                augment=augment_potholes,
                obstacle_boxes=obstacle_bboxes,
                is_savanna_terrain=is_savanna_terrain
            )

            for p in potholes_res:
                ar = p["area_ratio"]
                cnf = p["confidence"]
                if ar > max_area_ratio:
                    max_area_ratio = ar

                if p["severity"] == "High":
                    danger_score = max(danger_score, 85)
                    color = (0, 0, 235)
                elif p["severity"] == "Medium":
                    danger_score = max(danger_score, 55)
                    color = (0, 140, 255)
                else:
                    danger_score = max(danger_score, 30)
                    color = (0, 200, 200)

                clean_p = {k: v for k, v in p.items() if not k.startswith("_")}
                potholes.append(clean_p)
                self.renderer.draw_box(annotated_bgr, p["bbox"], f"POTHOLE {cnf:.1%}", color)

        # Step 4: Render Surface Badge
        self.renderer.draw_surface_badge(annotated_bgr, terrain["surface_status"])
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

        return {
            "annotated_image": annotated_rgb,
            "potholes": potholes,
            "people": people,
            "vehicles": vehicles,
            "animals": animals,
            "terrain": terrain,
            "danger_score": danger_score,
            "max_area_ratio": max_area_ratio,
            "summary": {
                "potholes": len(potholes),
                "people": len(people),
                "vehicles": len(vehicles),
                "animals": len(animals),
                "total_hazards": len(potholes) + len(people) + len(vehicles) + len(animals),
                "terrain_type": terrain["type"],
                "surface_status": terrain["surface_status"]
            }
        }

    @staticmethod
    def classify_terrain(cv_img, animals=None, vehicles=None, people=None):
        """Static facade to TerrainAnalyzer."""
        return TerrainAnalyzer.classify_terrain(cv_img, animals=animals, vehicles=vehicles, people=people)


# Legacy Detector Aliases for Backward Compatibility
class Detector:
    """Legacy base detector wrapper."""
    def __init__(self, model_path, detector_name="Generic Detector"):
        self.model_path = model_path
        self.detector_name = detector_name
        self.model = YOLO(model_path)

    def detect(self, source, confidence=0.25):
        return self.model.predict(source=source, conf=confidence, verbose=False)


class PotholeDetector(Detector):
    def __init__(self, model_path=None):
        path = model_path if model_path and os.path.exists(model_path) else DEFAULT_POTHOLE_WEIGHTS
        super().__init__(path, "Pothole Detector")


class PersonDetector(Detector):
    def __init__(self, model_path=None):
        path = model_path if model_path and os.path.exists(model_path) else (
            DEFAULT_PERSON_WEIGHTS if os.path.exists(DEFAULT_PERSON_WEIGHTS) else DEFAULT_GENERAL_WEIGHTS
        )
        super().__init__(path, "Person Detector")