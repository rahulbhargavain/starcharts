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
from starcharts.ephemeris import graha_position
from starcharts.nodes import NODE_NAMES, node_position
from starcharts.panchanga import tithi_matches, tithi_score
from starcharts.rashi import (
    nakshatra_matches,
    nakshatra_score,
    rashi_matches,
    rashi_score,
)


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
        position = graha_position(jd_ut, GRAHAS[self.graha], ayanamsha=ayanamsha)
        return rashi_matches(position.sidereal_longitude, self.rashi_index, self.tolerance_degrees)

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        position = graha_position(jd_ut, GRAHAS[self.graha], ayanamsha=ayanamsha)
        return rashi_score(position.sidereal_longitude, self.rashi_index, self.tolerance_degrees)


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
        position = graha_position(jd_ut, GRAHAS[self.graha], ayanamsha=ayanamsha)
        return nakshatra_matches(
            position.sidereal_longitude, self.nakshatra_index, self.tolerance_degrees
        )

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        position = graha_position(jd_ut, GRAHAS[self.graha], ayanamsha=ayanamsha)
        return nakshatra_score(
            position.sidereal_longitude, self.nakshatra_index, self.tolerance_degrees
        )


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

    def score(self, jd_ut: float, ayanamsha: Ayanamsha) -> float:
        return tithi_score(jd_ut, self.tithi_number, self.tolerance_degrees)


@dataclass(frozen=True)
class RetrogradeConstraint:
    graha: str
    retrograde: bool = True

    def __post_init__(self) -> None:
        _validate_graha(self.graha)

    def is_satisfied(self, jd_ut: float, ayanamsha: Ayanamsha) -> bool:
        position = graha_position(jd_ut, GRAHAS[self.graha], ayanamsha=ayanamsha)
        return position.retrograde == self.retrograde

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
