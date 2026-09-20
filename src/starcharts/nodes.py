"""Rahu/Ketu (the Moon's lunar nodes) -- deliberately excluded from the
seven physical grahas in constants.py (they're computed geometric
points, not bodies), but several Mahabharata omen verses name them
specifically, so they need their own small module rather than forcing
them into GRAHAS.

Uses the mean node (SE_MEAN_NODE); Ketu is always exactly 180 degrees
from Rahu by definition, so it's derived rather than separately queried.
"""

from dataclasses import dataclass

import swisseph as swe

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.ephemeris import Position, graha_position

RAHU_BODY = swe.MEAN_NODE
NODE_NAMES = ("Rahu", "Ketu")


def rahu_position(jd_ut: float, ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA) -> Position:
    return graha_position(jd_ut, RAHU_BODY, ayanamsha=ayanamsha)


def ketu_position(jd_ut: float, ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA) -> Position:
    rahu = rahu_position(jd_ut, ayanamsha)
    return Position(
        tropical_longitude=(rahu.tropical_longitude + 180.0) % 360.0,
        sidereal_longitude=(rahu.sidereal_longitude + 180.0) % 360.0,
        ayanamsha=rahu.ayanamsha,
        speed_deg_per_day=rahu.speed_deg_per_day,
        retrograde=rahu.retrograde,
        ephemeris_model=rahu.ephemeris_model,
    )


def node_position(jd_ut: float, node: str, ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA) -> Position:
    if node == "Rahu":
        return rahu_position(jd_ut, ayanamsha)
    if node == "Ketu":
        return ketu_position(jd_ut, ayanamsha)
    raise ValueError(f"node must be one of {NODE_NAMES}, got {node!r}")
