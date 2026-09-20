"""Sidereal longitude -> rashi (sign) / nakshatra (lunar mansion) lookup."""

from dataclasses import dataclass

from starcharts.arcs import arc_matches, arc_score
from starcharts.constants import (
    NAKSHATRA_ARC_DEGREES,
    NAKSHATRAS,
    PADA_ARC_DEGREES,
    RASHI_ARC_DEGREES,
    RASHIS,
)


@dataclass(frozen=True)
class RashiPlacement:
    index: int
    name: str
    degree_in_rashi: float


@dataclass(frozen=True)
class NakshatraPlacement:
    index: int
    name: str
    pada: int
    degree_in_nakshatra: float


def _normalize_degrees(longitude: float) -> float:
    return longitude % 360.0


def to_rashi(sidereal_longitude: float) -> RashiPlacement:
    longitude = _normalize_degrees(sidereal_longitude)
    index = int(longitude // RASHI_ARC_DEGREES)
    degree_in_rashi = longitude - index * RASHI_ARC_DEGREES
    return RashiPlacement(index=index, name=RASHIS[index], degree_in_rashi=degree_in_rashi)


def rashi_matches(
    sidereal_longitude: float, rashi_index: int, tolerance_degrees: float = 0.0
) -> bool:
    """Does sidereal_longitude fall within rashi_index's arc, padded by
    tolerance_degrees on each side? See WORKPLAN.md on why old dates need
    non-zero tolerance rather than an exact boundary cutoff."""
    arc_start = rashi_index * RASHI_ARC_DEGREES
    return arc_matches(_normalize_degrees(sidereal_longitude), arc_start, RASHI_ARC_DEGREES, tolerance_degrees)


def rashi_score(
    sidereal_longitude: float, rashi_index: int, tolerance_degrees: float = 0.0
) -> float:
    """1.0 inside the arc, decaying (Gaussian, sigma=tolerance_degrees)
    outside it. For ranking candidates, not for hard filtering."""
    arc_start = rashi_index * RASHI_ARC_DEGREES
    return arc_score(_normalize_degrees(sidereal_longitude), arc_start, RASHI_ARC_DEGREES, tolerance_degrees)


def nakshatra_matches(
    sidereal_longitude: float, nakshatra_index: int, tolerance_degrees: float = 0.0
) -> bool:
    """Does sidereal_longitude fall within nakshatra_index's arc, padded by
    tolerance_degrees on each side?

    Padding matters for old dates: ayanamsha extrapolation error and lunar
    position uncertainty both grow going back in time, so an exact
    boundary cutoff overstates precision that far back. See WORKPLAN.md.
    """
    arc_start = nakshatra_index * NAKSHATRA_ARC_DEGREES
    return arc_matches(
        _normalize_degrees(sidereal_longitude), arc_start, NAKSHATRA_ARC_DEGREES, tolerance_degrees
    )


def nakshatra_score(
    sidereal_longitude: float, nakshatra_index: int, tolerance_degrees: float = 0.0
) -> float:
    """1.0 inside the arc, decaying (Gaussian, sigma=tolerance_degrees)
    outside it. For ranking candidates, not for hard filtering."""
    arc_start = nakshatra_index * NAKSHATRA_ARC_DEGREES
    return arc_score(
        _normalize_degrees(sidereal_longitude), arc_start, NAKSHATRA_ARC_DEGREES, tolerance_degrees
    )


def to_nakshatra(sidereal_longitude: float) -> NakshatraPlacement:
    longitude = _normalize_degrees(sidereal_longitude)
    index = int(longitude // NAKSHATRA_ARC_DEGREES)
    degree_in_nakshatra = longitude - index * NAKSHATRA_ARC_DEGREES
    pada = int(degree_in_nakshatra // PADA_ARC_DEGREES) + 1
    return NakshatraPlacement(
        index=index,
        name=NAKSHATRAS[index],
        pada=pada,
        degree_in_nakshatra=degree_in_nakshatra,
    )
