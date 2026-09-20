"""Lagna (ascendant) computation -- the one placement that needs a
birth location, not just a date.

Every graha placement so far is geocentric: it depends only on the
instant, not on where on Earth you're standing. The ascendant is
different -- it's where the ecliptic crosses the local eastern horizon,
so it depends on geographic latitude/longitude too, and it cycles through
all 12 rashis roughly once per sidereal day (~2 hours/rashi, much faster
than any graha). That means it can't be folded into engine.py's
coarse-to-fine date-level search the way graha rashi/tithi constraints
are: see WORKPLAN.md's "lagna and other location/time-of-day
constraints" note for how this is meant to be used instead (checked at a
specific local time on an already-found candidate date, not scanned).
"""

from dataclasses import dataclass

import swisseph as swe

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.ephemeris import to_julian_day_ut_astro


@dataclass(frozen=True)
class AscendantPosition:
    tropical_longitude: float
    sidereal_longitude: float
    ephemeris_model: str  # "moshier" or "swieph"


def ascendant_position(
    jd_ut: float,
    latitude: float,
    longitude: float,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    house_system: bytes = b"P",
    use_moshier: bool = True,
) -> AscendantPosition:
    """Ascendant (Lagna) longitude at jd_ut for an observer at the given
    geographic latitude/longitude (degrees, north/east positive).

    Same auto-fallback behaviour as ephemeris.graha_position: tries the
    file-free Moshier model first (default), and falls back to the full
    Swiss Ephemeris data files if jd_ut is outside Moshier's range.
    """
    swe.set_sid_mode(ayanamsha.value)
    model = "moshier" if use_moshier else "swieph"
    base_flag = swe.FLG_MOSEPH if use_moshier else swe.FLG_SWIEPH
    try:
        _cusps, ascmc_tropical = swe.houses_ex(jd_ut, latitude, longitude, house_system, base_flag)
        _cusps_s, ascmc_sidereal = swe.houses_ex(
            jd_ut, latitude, longitude, house_system, base_flag | swe.FLG_SIDEREAL
        )
    except swe.Error:
        if not use_moshier:
            raise
        model = "swieph"
        _cusps, ascmc_tropical = swe.houses_ex(jd_ut, latitude, longitude, house_system, swe.FLG_SWIEPH)
        _cusps_s, ascmc_sidereal = swe.houses_ex(
            jd_ut, latitude, longitude, house_system, swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        )
    return AscendantPosition(
        tropical_longitude=ascmc_tropical[0],
        sidereal_longitude=ascmc_sidereal[0],
        ephemeris_model=model,
    )


def local_time_jd_ut(
    year: int,
    month: int,
    day: int,
    local_hour: float,
    longitude: float,
    proleptic_julian_calendar: bool = False,
) -> float:
    """Julian day (UT) of a given local mean-solar hour (0-24) on this
    calendar date, at the given geographic longitude (mean-solar
    approximation -- ignores the equation of time, which shifts true
    solar time by at most ~16 minutes, negligible next to how slowly a
    rashi-level lagna check needs to resolve)."""
    jd_midnight = to_julian_day_ut_astro(
        year, month, day, 0.0, proleptic_julian_calendar=proleptic_julian_calendar
    )
    universal_hour = local_hour - longitude / 15.0
    return jd_midnight + universal_hour / 24.0


def local_noon_jd_ut(
    year: int,
    month: int,
    day: int,
    longitude: float,
    proleptic_julian_calendar: bool = False,
) -> float:
    """Julian day (UT) of local apparent noon on this date. See
    local_time_jd_ut for the general form and its caveats."""
    return local_time_jd_ut(year, month, day, 12.0, longitude, proleptic_julian_calendar)


def local_midnight_jd_ut(
    year: int,
    month: int,
    day: int,
    longitude: float,
    proleptic_julian_calendar: bool = False,
) -> float:
    """Julian day (UT) of local midnight AT THE END of this calendar date
    (i.e. the midnight between this date and the next), matching how
    "born at midnight on tithi X" is traditionally meant. See
    local_time_jd_ut for the general form and its caveats."""
    return local_time_jd_ut(year, month, day, 24.0, longitude, proleptic_julian_calendar)
