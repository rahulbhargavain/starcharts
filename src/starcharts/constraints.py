"""Typed constraints for the sky-configuration search engine (layer 4).

Each constraint answers two questions at a given Julian day: is_satisfied
(a hard boolean, used to prune candidate windows cheaply during search) and
score (a continuous 0-1 value with Gaussian decay past the tolerance-padded
boundary, used only for ranking survivors -- never for pruning, since a
decayed-but-nonzero score would otherwise leak nearly every candidate
through every stage).
"""

from dataclasses import dataclass

from starcharts.ascendant import ascendant_position
from starcharts.ayanamsha import Ayanamsha
from starcharts.constants import GRAHAS
from starcharts.ephemeris import sidereal_longitude_and_speed
from starcharts.motion import ELONGATION_MOTION, GRAHA_MOTION, NODE_MOTION, MotionBounds
from starcharts.nodes import NODE_NAMES, node_position, node_sidereal_longitude_and_speed
from starcharts.panchanga import tithi_margin, tithi_matches, tithi_score
from starcharts.rashi import (
    nakshatra_margin,
    nakshatra_matches,
    nakshatra_score,
    rashi_margin,
    rashi_matches,
    rashi_score,
)

# Prunable constraints also expose margin() -> (signed distance to the
# match boundary, its current rate or None), >= 0 exactly when
# is_satisfied(), plus the MotionBounds that bound how fast that margin can
# change and a margin_slack covering errors in the reported values. The
# engine uses these to skip ahead without stepping over a match -- see
# motion.py and engine.py.
#
# Scan order for the engine: slowest-changing first, so the cheapest,
# widest steps prune the range before faster bodies are scanned.
SCAN_ORDER: dict[str, int] = {
    "node": 0, "Shani": 1, "Guru": 2, "Mangala": 3, "Surya": 4,
    "Shukra": 5, "Budha": 6, "Chandra": 7, "tithi": 8,
}
POSITION_SLACK_DEGREES = 1e-4  # covers tiny position jumps between ephemeris segments


def _validate_graha(graha: str) -> None:
    if graha not in GRAHAS:
        raise ValueError(f"unknown graha {graha!r}; must be one of {sorted(GRAHAS)}")


@dataclass(frozen=True)
class RashiConstraint:
    graha: str
    rashi_index: int
    tolerance_degrees: float = 0.0

    def __post_init__(self) -> None:
        _validate_graha(self.graha)
        if not 0 <= self.rashi_index <= 11:
            raise ValueError("rashi_index must be 0-11")

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        longitude, _speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return rashi_matches(longitude, self.rashi_index, self.tolerance_degrees)

    def margin(self, jd_ut: float, ayanamsha: Ayanamsha) -> tuple[float, float | None]:
        longitude, speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return rashi_margin(longitude, self.rashi_index, self.tolerance_degrees), speed

    @property
    def motion_bounds(self) -> MotionBounds:
        return GRAHA_MOTION[self.graha]

    margin_slack = POSITION_SLACK_DEGREES

    @property
    def scan_key(self) -> int:
        return SCAN_ORDER[self.graha]

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        longitude, _speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return rashi_score(longitude, self.rashi_index, self.tolerance_degrees)


@dataclass(frozen=True)
class NakshatraConstraint:
    graha: str
    nakshatra_index: int
    tolerance_degrees: float = 0.0

    def __post_init__(self) -> None:
        _validate_graha(self.graha)
        if not 0 <= self.nakshatra_index <= 26:
            raise ValueError("nakshatra_index must be 0-26")

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        longitude, _speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return nakshatra_matches(longitude, self.nakshatra_index, self.tolerance_degrees)

    def margin(self, jd_ut: float, ayanamsha: Ayanamsha) -> tuple[float, float | None]:
        longitude, speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return nakshatra_margin(longitude, self.nakshatra_index, self.tolerance_degrees), speed

    @property
    def motion_bounds(self) -> MotionBounds:
        return GRAHA_MOTION[self.graha]

    margin_slack = POSITION_SLACK_DEGREES

    @property
    def scan_key(self) -> int:
        return SCAN_ORDER[self.graha]

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        longitude, _speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return nakshatra_score(longitude, self.nakshatra_index, self.tolerance_degrees)


@dataclass(frozen=True)
class TithiConstraint:
    tithi_number: int  # 1-30
    tolerance_degrees: float = 0.0

    def __post_init__(self) -> None:
        if not 1 <= self.tithi_number <= 30:
            raise ValueError("tithi_number must be 1-30")

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        # Tithi is ayanamsha-independent; the parameter is accepted only so
        # every constraint shares the same call signature.
        return tithi_matches(jd_ut, self.tithi_number, self.tolerance_degrees)

    def margin(self, jd_ut: float, ayanamsha: Ayanamsha) -> tuple[float, float | None]:
        return tithi_margin(jd_ut, self.tithi_number, self.tolerance_degrees)

    motion_bounds = ELONGATION_MOTION
    margin_slack = POSITION_SLACK_DEGREES
    scan_key = SCAN_ORDER["tithi"]

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        return tithi_score(jd_ut, self.tithi_number, self.tolerance_degrees)


@dataclass(frozen=True)
class RetrogradeConstraint:
    graha: str
    retrograde: bool = True

    def __post_init__(self) -> None:
        _validate_graha(self.graha)

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        _longitude, speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return (speed < 0) == self.retrograde

    def margin(self, jd_ut: float, ayanamsha: Ayanamsha) -> tuple[float, float | None]:
        # The margin is the speed itself (deg/day), signed so that >= 0
        # means satisfied; its own rate (the acceleration) isn't reported.
        _longitude, speed = sidereal_longitude_and_speed(jd_ut, GRAHAS[self.graha], ayanamsha)
        return (-speed if self.retrograde else speed), None

    @property
    def motion_bounds(self) -> MotionBounds:
        # The speed changes by at most the graha's max_rate_change per day.
        return MotionBounds(GRAHA_MOTION[self.graha].max_rate_change, 0.0, 0.0)

    @property
    def margin_slack(self) -> float:
        # Reported speed can be off by rate_error at both ends of a step.
        return 2.0 * GRAHA_MOTION[self.graha].rate_error

    @property
    def scan_key(self) -> int:
        return SCAN_ORDER[self.graha]

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        return 1.0 if self.is_satisfied(jd_ut, ayanamsha) else 0.0


@dataclass(frozen=True)
class AscendantConstraint:
    """Lagna in a given rashi at jd_ut, for an observer at latitude/
    longitude. NOT fed into engine.search()'s coarse-to-fine staging --
    the ascendant moves too fast (~2h/rashi) for that date-level scan.
    Meant to be checked at one specific, deliberately chosen instant
    (e.g. ascendant.local_noon_jd_ut(...) on an already-found candidate
    date) -- see ascendant.py's module docstring."""

    latitude: float
    longitude: float
    rashi_index: int
    tolerance_degrees: float = 0.0
    house_system: bytes = b"P"

    def __post_init__(self) -> None:
        if not 0 <= self.rashi_index <= 11:
            raise ValueError("rashi_index must be 0-11")

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        position = ascendant_position(
            jd_ut, self.latitude, self.longitude, ayanamsha, self.house_system
        )
        return rashi_matches(position.sidereal_longitude, self.rashi_index, self.tolerance_degrees)

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        position = ascendant_position(
            jd_ut, self.latitude, self.longitude, ayanamsha, self.house_system
        )
        return rashi_score(position.sidereal_longitude, self.rashi_index, self.tolerance_degrees)


@dataclass(frozen=True)
class NodeNakshatraConstraint:
    """Rahu or Ketu (lunar node) in a given nakshatra -- see nodes.py.
    Several Mahabharata omen verses name these specifically."""

    node: str  # "Rahu" or "Ketu"
    nakshatra_index: int
    tolerance_degrees: float = 0.0

    def __post_init__(self) -> None:
        if self.node not in NODE_NAMES:
            raise ValueError(f"node must be one of {NODE_NAMES}, got {self.node!r}")
        if not 0 <= self.nakshatra_index <= 26:
            raise ValueError("nakshatra_index must be 0-26")

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        position = node_position(jd_ut, self.node, ayanamsha)
        return nakshatra_matches(
            position.sidereal_longitude, self.nakshatra_index, self.tolerance_degrees
        )

    def margin(self, jd_ut: float, ayanamsha: Ayanamsha) -> tuple[float, float | None]:
        longitude, speed = node_sidereal_longitude_and_speed(jd_ut, self.node, ayanamsha)
        return nakshatra_margin(longitude, self.nakshatra_index, self.tolerance_degrees), speed

    motion_bounds = NODE_MOTION
    margin_slack = POSITION_SLACK_DEGREES
    scan_key = SCAN_ORDER["node"]

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        position = node_position(jd_ut, self.node, ayanamsha)
        return nakshatra_score(
            position.sidereal_longitude, self.nakshatra_index, self.tolerance_degrees
        )


@dataclass(frozen=True)
class EitherNodeNakshatraConstraint:
    """Rahu OR Ketu in the given nakshatra, whichever fits better --
    for verses where a node's color/epithet doesn't reliably identify
    which one is meant (see texts/mahabharata.py's citation notes)."""

    nakshatra_index: int
    tolerance_degrees: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.nakshatra_index <= 26:
            raise ValueError("nakshatra_index must be 0-26")

    def _candidates(self) -> tuple[NodeNakshatraConstraint, NodeNakshatraConstraint]:
        return (
            NodeNakshatraConstraint("Rahu", self.nakshatra_index, self.tolerance_degrees),
            NodeNakshatraConstraint("Ketu", self.nakshatra_index, self.tolerance_degrees),
        )

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        return any(c.is_satisfied(jd_ut, ayanamsha) for c in self._candidates())

    def margin(self, jd_ut: float, ayanamsha: Ayanamsha) -> tuple[float, float | None]:
        # Rahu and Ketu move at the same speed, so the better of the two
        # margins changes no faster than either one.
        return max(c.margin(jd_ut, ayanamsha) for c in self._candidates())

    motion_bounds = NODE_MOTION
    margin_slack = POSITION_SLACK_DEGREES
    scan_key = SCAN_ORDER["node"]

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        return max(c.score(jd_ut, ayanamsha) for c in self._candidates())


Constraint = (
    RashiConstraint
    | NakshatraConstraint
    | TithiConstraint
    | RetrogradeConstraint
    | AscendantConstraint
    | NodeNakshatraConstraint
    | EitherNodeNakshatraConstraint
)
