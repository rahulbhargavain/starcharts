"""Ephemeris access: real planetary positions at a point in time.

Defaults to the Swiss Ephemeris Moshier analytical model (SEFLG_MOSEPH),
which needs no external data files but is only valid for ~3002 BCE to
~3003 CE (swisseph enforces this and raises swisseph.Error outside it).

For dates outside that range, this module automatically falls back to
the full Swiss Ephemeris data files (SEFLG_SWIEPH) in EPHE_DIR
(<project root>/ephe). Those files must be downloaded separately -- they
aren't checked into the repo (see ephe/README.md) -- and only cover
whatever span has actually been fetched. Reaching further back in time
just means downloading more files of the same kind (see ephe/README.md
for the naming convention and a ready-made download script).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import swisseph as swe

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha

EPHE_DIR = Path(__file__).resolve().parent.parent.parent / "ephe"
swe.set_ephe_path(str(EPHE_DIR))


@dataclass(frozen=True)
class Position:
    tropical_longitude: float
    sidereal_longitude: float
    ayanamsha: float
    speed_deg_per_day: float
    retrograde: bool
    ephemeris_model: str  # "moshier" or "swieph" -- which one actually computed this


def to_julian_day_ut(dt: datetime, proleptic_julian_calendar: bool = False) -> float:
    """Convert a UTC datetime to a Julian day number (UT).

    dt must be timezone-aware UTC, or naive and already assumed UTC. Only
    usable for 1-9999 CE: Python's datetime cannot represent BCE years at
    all. For anything before 1 CE, use to_julian_day_ut_astro() instead,
    which takes an astronomical (signed) year number directly.

    Use proleptic_julian_calendar=True for dates that should be read against
    the Julian (not Gregorian) calendar convention.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return to_julian_day_ut_astro(
        dt.year, dt.month, dt.day, hour, proleptic_julian_calendar
    )


def to_julian_day_ut_astro(
    year: int,
    month: int,
    day: int,
    hour: float = 0.0,
    proleptic_julian_calendar: bool = False,
) -> float:
    """Convert an astronomical (signed) year/month/day/hour to Julian day (UT).

    Astronomical year numbering has no year zero gap: year 0 = 1 BCE,
    year -1 = 2 BCE, year -3101 = 3102 BCE, and so on. This is the entry
    point for any date before 1 CE, since Python's datetime cannot hold
    those years.
    """
    cal_flag = swe.JUL_CAL if proleptic_julian_calendar else swe.GREG_CAL
    whole_hour = int(hour)
    minutes_float = (hour - whole_hour) * 60.0
    whole_minute = int(minutes_float)
    seconds = (minutes_float - whole_minute) * 60.0
    _, jd_ut = swe.utc_to_jd(
        year, month, day, whole_hour, whole_minute, seconds, cal_flag
    )
    return jd_ut


def _calc(jd_ut: float, body: int, flags: int):
    return swe.calc_ut(jd_ut, body, flags)


def sidereal_longitude_and_speed(
    jd_ut: float, body: int, ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA
) -> tuple[float, float]:
    """Just the sidereal longitude and its speed -- the same values
    graha_position() returns, with the same Moshier-then-data-files
    fallback, from one ephemeris call instead of three. For hot loops such
    as the search engine's constraint scans."""
    swe.set_sid_mode(ayanamsha.value)
    try:
        xx, _ = _calc(jd_ut, body, swe.FLG_MOSEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL)
    except swe.Error:
        xx, _ = _calc(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL)
    return xx[0], xx[3]


def graha_position(
    jd_ut: float,
    body: int,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    use_moshier: bool = True,
) -> Position:
    """Compute a graha's tropical + sidereal longitude at a given Julian day.

    use_moshier=True (default): use the fast, file-free Moshier model, but
    if jd_ut falls outside its valid range, automatically retry with the
    full Swiss Ephemeris data files (SEFLG_SWIEPH) instead of raising.
    use_moshier=False: force SEFLG_SWIEPH (requires the relevant data
    files to be present in EPHE_DIR for jd_ut's era).
    """
    swe.set_sid_mode(ayanamsha.value)
    model = "moshier" if use_moshier else "swieph"
    base_flag = swe.FLG_MOSEPH if use_moshier else swe.FLG_SWIEPH

    try:
        tropical_xx, _ = _calc(jd_ut, body, base_flag | swe.FLG_SPEED)
        sidereal_xx, _ = _calc(jd_ut, body, base_flag | swe.FLG_SPEED | swe.FLG_SIDEREAL)
    except swe.Error:
        if not use_moshier:
            raise
        model = "swieph"
        tropical_xx, _ = _calc(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
        sidereal_xx, _ = _calc(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL)

    speed = sidereal_xx[3]
    ayanamsha_value = swe.get_ayanamsa_ut(jd_ut)

    return Position(
        tropical_longitude=tropical_xx[0],
        sidereal_longitude=sidereal_xx[0],
        ayanamsha=ayanamsha_value,
        speed_deg_per_day=speed,
        retrograde=speed < 0,
        ephemeris_model=model,
    )
