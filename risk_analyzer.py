from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

from translations import localization_service, TranslationResult


class RiskLevel(str, Enum):
    """Enumeration of ADAS risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertColor(str, Enum):
    """Enumeration of cockpit alert indicator colors."""
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"


@dataclass(frozen=True)
class HazardContext:
    """Encapsulates perception inputs for risk evaluation."""
    pothole_count: int = 0
    confidences: List[float] = field(default_factory=list)
    person_count: int = 0
    vehicle_count: int = 0
    animal_count: int = 0
    danger_score: int = 0
    terrain: Optional[Dict[str, Any]] = None
    animals: List[Dict[str, Any]] = field(default_factory=list)
    language: str = "English"

    @property
    def avg_confidence(self) -> float:
        return (sum(self.confidences) / len(self.confidences)) if self.confidences else 0.0

    @property
    def is_dry_grass(self) -> bool:
        return bool(self.terrain and self.terrain.get("surface_status") == "Dry Grass Present")

    @property
    def snakes(self) -> List[str]:
        return [
            a.get("label", "") for a in self.animals
            if any(k in a.get("label", "").lower() for k in ("snake", "cobra", "viper", "mamba", "python"))
        ]

    @property
    def predators(self) -> List[str]:
        pred_set = {"Lion", "Tiger", "Leopard", "Cheetah", "Jaguar", "Lioness / Wildlife", "Elephant"}
        return [a.get("label", "") for a in self.animals if a.get("label", "") in pred_set]


@dataclass
class RiskAssessmentResult:
    """Encapsulates the output of risk analysis."""
    risk_level: str
    message: str
    instruction: str
    alert_color: str
    msg_key: str
    translation: TranslationResult

    def __iter__(self):
        """Allows tuple unpacking: risk, msg, inst, color = analyzer.analyze(...)"""
        yield self.risk_level
        yield self.message
        yield self.instruction
        yield self.alert_color


class AbstractRiskRule(ABC):
    """Abstract Strategy interface for evaluating hazard risk."""

    @abstractmethod
    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        """
        Evaluates context and returns (risk_level, color, message, msg_key) if matched.
        """
        pass


class WildlifeDangerRule(AbstractRiskRule):
    """Evaluates apex predators and venomous snakes."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        snakes = ctx.snakes
        predators = ctx.predators

        if snakes and predators:
            snake_str = ", ".join(sorted(set(snakes)))
            pred_str = ", ".join(sorted(set(predators)))
            return (
                RiskLevel.CRITICAL.value,
                AlertColor.RED.value,
                f"Extreme Wildlife Danger: {pred_str} and venomous {snake_str} detected on savanna.",
                "CRITICAL_SNAKE_PREDATOR"
            )

        if snakes:
            snake_str = ", ".join(sorted(set(snakes)))
            if ctx.is_dry_grass:
                return (
                    RiskLevel.CRITICAL.value,
                    AlertColor.RED.value,
                    f"Venomous Reptile Alert: {snake_str} detected on dry grass savanna.",
                    "CRITICAL_SNAKE_GRASS"
                )
            return (
                RiskLevel.CRITICAL.value,
                AlertColor.RED.value,
                f"Reptile Hazard: {snake_str} detected on roadway.",
                "CRITICAL_SNAKE_ROAD"
            )

        if predators:
            pred_str = ", ".join(sorted(set(predators)))
            if ctx.is_dry_grass:
                return (
                    RiskLevel.CRITICAL.value,
                    AlertColor.RED.value,
                    f"Savanna Wildlife Alert: {pred_str} detected on dry grass terrain.",
                    "CRITICAL_PREDATOR_SAVANNA"
                )
            return (
                RiskLevel.CRITICAL.value,
                AlertColor.RED.value,
                f"Dangerous Wildlife Alert: {pred_str} detected in driving path.",
                "CRITICAL_PREDATOR_ROAD"
            )

        return None


class CriticalObstacleRule(AbstractRiskRule):
    """Evaluates imminent collision danger or deep obstacle proximity."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.danger_score >= 80 or (ctx.pothole_count >= 2 and ctx.person_count >= 1):
            return (
                RiskLevel.CRITICAL.value,
                AlertColor.RED.value,
                "Critical hazard: Immediate obstacle or deep pothole close to vehicle.",
                "CRITICAL_BRAKE_SLOW"
            )
        return None


class PedestrianPotholeRule(AbstractRiskRule):
    """Evaluates dual pedestrian and pothole co-occurrence."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.person_count > 0 and ctx.pothole_count > 0:
            return (
                RiskLevel.HIGH.value,
                AlertColor.RED.value,
                f"Multiple hazards detected: {ctx.pothole_count} pothole(s) and {ctx.person_count} pedestrian(s).",
                "PERSON_AND_POTHOLE"
            )
        return None


class PedestrianSafetyRule(AbstractRiskRule):
    """Evaluates vulnerable road users / pedestrians."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.person_count > 0:
            risk = RiskLevel.HIGH.value if ctx.person_count >= 2 else RiskLevel.MEDIUM.value
            color = AlertColor.ORANGE.value if risk == RiskLevel.MEDIUM.value else AlertColor.RED.value
            return (
                risk,
                color,
                f"Pedestrian warning: {ctx.person_count} person(s) detected near roadway.",
                "PEDESTRIAN_AHEAD"
            )
        return None


class LivestockAnimalRule(AbstractRiskRule):
    """Evaluates domestic animals and livestock on road."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.animal_count > 0:
            if ctx.is_dry_grass:
                return (
                    RiskLevel.MEDIUM.value,
                    AlertColor.ORANGE.value,
                    f"Wildlife in vicinity: {ctx.animal_count} animal(s) on dry grass savanna terrain.",
                    "ANIMAL_SAVANNA"
                )
            return (
                RiskLevel.MEDIUM.value,
                AlertColor.ORANGE.value,
                f"Animal on roadway: {ctx.animal_count} animal(s) detected.",
                "ANIMAL_ROAD"
            )
        return None


class SeverePotholeClusterRule(AbstractRiskRule):
    """Evaluates major road damage and crater clusters."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.pothole_count >= 3 or ctx.avg_confidence >= 0.70 or ctx.danger_score >= 60:
            return (
                RiskLevel.HIGH.value,
                AlertColor.RED.value,
                f"Severe road damage: {ctx.pothole_count} significant pothole(s) detected.",
                "DEEP_POTHOLES"
            )
        return None


class ModeratePotholeRule(AbstractRiskRule):
    """Evaluates moderate surface ruts."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.pothole_count >= 1:
            return (
                RiskLevel.MEDIUM.value,
                AlertColor.ORANGE.value,
                f"Road roughness warning: {ctx.pothole_count} pothole(s) detected.",
                "POTHOLE_NEARBY"
            )
        return None


class TrafficRule(AbstractRiskRule):
    """Evaluates forward vehicle density."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.vehicle_count >= 3:
            return (
                RiskLevel.LOW.value,
                AlertColor.ORANGE.value,
                f"Dense traffic ahead: {ctx.vehicle_count} vehicles detected.",
                "TRAFFIC_AHEAD"
            )
        return None


class DryGrassTerrainRule(AbstractRiskRule):
    """Evaluates off-road dry grass presence."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        if ctx.is_dry_grass:
            return (
                RiskLevel.LOW.value,
                AlertColor.ORANGE.value,
                "Off-road terrain: Dry grass surface detected. No roadway potholes.",
                "DRY_GRASS_TERRAIN"
            )
        return None


class ClearPathRule(AbstractRiskRule):
    """Default rule when route is unobstructed."""

    def evaluate(self, ctx: HazardContext) -> Optional[Tuple[str, str, str, str]]:
        return (
            RiskLevel.LOW.value,
            AlertColor.GREEN.value,
            "Path is clear. No immediate roadway hazards detected.",
            "PATH_CLEAR"
        )


class RiskAnalyzer:
    """
    Object-Oriented Intelligent Risk Assessment Engine.
    Uses Strategy / Chain of Responsibility pattern for polymorphic risk evaluation.
    """

    def __init__(self, rules: Optional[List[AbstractRiskRule]] = None):
        self._rules = rules or [
            WildlifeDangerRule(),
            CriticalObstacleRule(),
            PedestrianPotholeRule(),
            PedestrianSafetyRule(),
            LivestockAnimalRule(),
            SeverePotholeClusterRule(),
            ModeratePotholeRule(),
            TrafficRule(),
            DryGrassTerrainRule(),
            ClearPathRule()
        ]
        self.last_translation: Dict[str, Any] = {}

    def analyze(
        self,
        pothole_count: int = 0,
        confidences: Optional[List[float]] = None,
        person_count: int = 0,
        vehicle_count: int = 0,
        animal_count: int = 0,
        danger_score: int = 0,
        terrain: Optional[Dict[str, Any]] = None,
        animals: Optional[List[Dict[str, Any]]] = None,
        language: str = "English"
    ) -> RiskAssessmentResult:
        """
        Executes polymorphic rule evaluation and translates driver instructions.
        """
        ctx = HazardContext(
            pothole_count=pothole_count,
            confidences=confidences or [],
            person_count=person_count,
            vehicle_count=vehicle_count,
            animal_count=animal_count,
            danger_score=danger_score,
            terrain=terrain,
            animals=animals or [],
            language=language
        )

        risk_level = RiskLevel.LOW.value
        alert_color = AlertColor.GREEN.value
        message = "Path is clear."
        msg_key = "PATH_CLEAR"

        # Chain of Responsibility evaluation
        for rule in self._rules:
            res = rule.evaluate(ctx)
            if res is not None:
                risk_level, alert_color, message, msg_key = res
                break

        # Localization via LocalizationService
        trans_res = localization_service.translate(msg_key, language=language)
        self.last_translation = {
            "text": trans_res.text,
            "speech_browser": trans_res.speech_browser,
            "speech_system": trans_res.speech_system,
            "locale": trans_res.locale,
        }

        return RiskAssessmentResult(
            risk_level=risk_level,
            message=message,
            instruction=trans_res.text,
            alert_color=alert_color,
            msg_key=msg_key,
            translation=trans_res
        )