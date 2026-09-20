"""High-level chart computation: all seven grahas at a point in time."""

from dataclasses import dataclass
from datetime import datetime

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.constants import GRAHAS
from starcharts.ephemeris import (
    Position,
    graha_position,
    to_julian_day_ut,
    to_julian_day_ut_astro,
)
from starcharts.rashi import NakshatraPlacement, RashiPlacement, to_nakshatra, to_rashi


@dataclass(frozen=True)
class GrahaPlacement:
    graha: str
    position: Position
    rashi: RashiPlacement
    nakshatra: NakshatraPlacement


def compute_chart_at_jd(
    jd_ut: float,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    use_moshier: bool = True,
) -> dict[str, GrahaPlacement]:
    """Compute sidereal rashi/nakshatra placements for all seven grahas."""
    chart: dict[str, GrahaPlacement] = {}
    for graha_name, body_id in GRAHAS.items():
        position = graha_position(
            jd_ut, body_id, ayanamsha=ayanamsha, use_moshier=use_moshier
        )
        chart[graha_name] = GrahaPlacement(
            graha=graha_name,
            position=position,
            rashi=to_rashi(position.sidereal_longitude),
            nakshatra=to_nakshatra(position.sidereal_longitude),
        )
    return chart


def compute_chart(
    dt_utc: datetime,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    use_moshier: bool = True,
    proleptic_julian_calendar: bool = False,
) -> dict[str, GrahaPlacement]:
    """Compute a chart for a CE date (1-9999) given as a Python datetime."""
    jd_ut = to_julian_day_ut(dt_utc, proleptic_julian_calendar=proleptic_julian_calendar)
    return compute_chart_at_jd(jd_ut, ayanamsha=ayanamsha, use_moshier=use_moshier)


def compute_chart_astro(
    year: int,
    month: int,
    day: int,
    hour: float = 0.0,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    use_moshier: bool = True,
    proleptic_julian_calendar: bool = False,
) -> dict[str, GrahaPlacement]:
    """Compute a chart for any date, including BCE, via astronomical year
    numbering (year 0 = 1 BCE, year -3101 = 3102 BCE, etc.)."""
    jd_ut = to_julian_day_ut_astro(
        year, month, day, hour, proleptic_julian_calendar=proleptic_julian_calendar
    )
    return compute_chart_at_jd(jd_ut, ayanamsha=ayanamsha, use_moshier=use_moshier)
