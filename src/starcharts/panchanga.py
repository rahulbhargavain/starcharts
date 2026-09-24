"""Tithi (lunar day): the Moon-Sun angular separation, in 12-degree steps.

Tithi is ayanamsha-independent: it's a difference of two longitudes, so
whatever precession offset applies to the Moon applies equally to the Sun
and cancels out. This module works in tropical longitude throughout for
that reason -- it would give the identical result in sidereal.
"""

from dataclasses import dataclass

import swisseph as swe

from starcharts.arcs import arc_margin, arc_matches, arc_score

TITHI_ARC_DEGREES = 12.0
_PAKSHA_TITHI_COUNT = 15


@dataclass(frozen=True)
class Tithi:
    number: int  # 1-30, 1 = Shukla Pratipada, 16 = Krishna Pratipada
    paksha: str  # "Shukla" (waxing) or "Krishna" (waning)
    tithi_in_paksha: int  # 1-15
    degrees_into_tithi: float


def _tropical_longitude_and_speed(jd_ut: float, body: int) -> tuple[float, float]:
    """Same Moshier-first, Swiss-Ephemeris-data-file-fallback behaviour
    as ephemeris.graha_position -- see that module's docstring."""
    try:
        xx, _ = swe.calc_ut(jd_ut, body, swe.FLG_MOSEPH | swe.FLG_SPEED)
    except swe.Error:
        xx, _ = swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return xx[0], xx[3]


def tropical_longitude(jd_ut: float, body: int) -> float:
    return _tropical_longitude_and_speed(jd_ut, body)[0]


def moon_sun_elongation(jd_ut: float) -> float:
    """Moon longitude minus Sun longitude, normalized to [0, 360)."""
    moon = tropical_longitude(jd_ut, swe.MOON)
    sun = tropical_longitude(jd_ut, swe.SUN)
    return (moon - sun) % 360.0


def tithi_at(jd_ut: float) -> Tithi:
    elongation = moon_sun_elongation(jd_ut)
    number = int(elongation // TITHI_ARC_DEGREES) + 1
    degrees_into_tithi = elongation - (number - 1) * TITHI_ARC_DEGREES
    if number <= _PAKSHA_TITHI_COUNT:
        paksha = "Shukla"
        tithi_in_paksha = number
    else:
        paksha = "Krishna"
        tithi_in_paksha = number - _PAKSHA_TITHI_COUNT
    return Tithi(
        number=number,
        paksha=paksha,
        tithi_in_paksha=tithi_in_paksha,
        degrees_into_tithi=degrees_into_tithi,
    )


def tithi_matches(jd_ut: float, tithi_number: int, tolerance_degrees: float = 0.0) -> bool:
    """Does jd_ut fall within tithi_number's 12-degree arc, padded by
    tolerance_degrees on each side?

    The padding matters past ~1500 BCE: lunar secular acceleration and
    Delta-T uncertainty can shift the Moon's true position by multiple
    degrees at those timescales, so treating a tithi boundary as an exact
    boolean cutoff overstates precision. See WORKPLAN.md.
    """
    elongation = moon_sun_elongation(jd_ut)
    arc_start = (tithi_number - 1) * TITHI_ARC_DEGREES
    return arc_matches(elongation, arc_start, TITHI_ARC_DEGREES, tolerance_degrees)


def tithi_margin(jd_ut: float, tithi_number: int, tolerance_degrees: float = 0.0) -> tuple[float, float]:
    """(signed degrees of elongation to the padded tithi arc's edge, the
    elongation's rate in degrees/day). margin >= 0 iff tithi_matches."""
    moon, moon_speed = _tropical_longitude_and_speed(jd_ut, swe.MOON)
    sun, sun_speed = _tropical_longitude_and_speed(jd_ut, swe.SUN)
    arc_start = (tithi_number - 1) * TITHI_ARC_DEGREES
    margin = arc_margin((moon - sun) % 360.0, arc_start, TITHI_ARC_DEGREES, tolerance_degrees)
    return margin, moon_speed - sun_speed


def tithi_score(jd_ut: float, tithi_number: int, tolerance_degrees: float = 0.0) -> float:
    """1.0 inside the tithi's arc, decaying (Gaussian, sigma=
    tolerance_degrees) outside it. For ranking candidates, not filtering."""
    elongation = moon_sun_elongation(jd_ut)
    arc_start = (tithi_number - 1) * TITHI_ARC_DEGREES
    return arc_score(elongation, arc_start, TITHI_ARC_DEGREES, tolerance_degrees)


def tithi_number_for(paksha: str, tithi_in_paksha: int) -> int:
    """Inverse of Tithi.paksha/tithi_in_paksha -> the 1-30 tithi number."""
    if not 1 <= tithi_in_paksha <= _PAKSHA_TITHI_COUNT:
        raise ValueError("tithi_in_paksha must be 1-15")
    if paksha == "Shukla":
        return tithi_in_paksha
    if paksha == "Krishna":
        return _PAKSHA_TITHI_COUNT + tithi_in_paksha
    raise ValueError("paksha must be 'Shukla' or 'Krishna'")
