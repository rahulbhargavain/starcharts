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

import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import swisseph as swe

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha


def _default_ephe_dir() -> Path:
    """STARCHARTS_EPHE_DIR if set; otherwise the repo's own ephe/ directory.
    The repo-relative path only exists for a source checkout or an editable
    install -- a regular `pip install` puts this module in site-packages,
    so set STARCHARTS_EPHE_DIR to wherever ephe/download.sh put the files."""
    override = os.environ.get("STARCHARTS_EPHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent.parent / "ephe"


EPHE_DIR = _default_ephe_dir()

# swisseph is built with thread-local storage: its settings (data-file
# path, sidereal mode) are per thread. Setting the path once at import
# only covers the importing thread -- any other thread would look in
# swisseph's default path and fail on every date needing the data files.
# So every computation goes through ensure_thread_ready() first. (The
# sidereal mode needs no such care: it is set right before each use, and
# being per-thread, another thread can't change it in between.)
_thread_state = threading.local()


def ensure_thread_ready() -> None:
    """Point this thread's swisseph at EPHE_DIR (once per thread)."""
    if getattr(_thread_state, "ephe_dir", None) != EPHE_DIR:
        swe.set_ephe_path(str(EPHE_DIR))
        _thread_state.ephe_dir = EPHE_DIR


ensure_thread_ready()


@dataclass(frozen=True)
class Position:
    tropical_longitude: float
    sidereal_longitude: float
    ayanamsha: float
    speed_deg_per_day: float
    retrograde: bool
    ephemeris_model: str  # "moshier"/"swieph"/"jpl" -- read from swisseph's return flags


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
    ensure_thread_ready()
    return swe.calc_ut(jd_ut, body, flags)


def model_from_flags(return_flags: int) -> str:
    """Which ephemeris actually produced a swisseph result, from the flags
    it returns. swisseph silently substitutes Moshier when the requested
    data files don't cover the date, so the requested model is not proof."""
    if return_flags & swe.FLG_JPLEPH:
        return "jpl"
    if return_flags & swe.FLG_SWIEPH:
        return "swieph"
    if return_flags & swe.FLG_MOSEPH:
        return "moshier"
    return "unknown"


def sidereal_longitude_and_speed(
    jd_ut: float, body: int, ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA
) -> tuple[float, float]:
    """Just the sidereal longitude and its speed -- the same values
    graha_position() returns, with the same Moshier-then-data-files
    fallback, from one ephemeris call instead of three. For hot loops such
    as the search engine's constraint scans. Cached: a profile often
    constrains the same graha twice (e.g. Mangala's nakshatra and its
    retrograde motion) at the same instant."""
    return _sidereal_cached(jd_ut, body, ayanamsha)


@lru_cache(maxsize=16384)
def _sidereal_cached(jd_ut: float, body: int, ayanamsha: Ayanamsha) -> tuple[float, float]:
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
    use_moshier=False: request SEFLG_SWIEPH. If EPHE_DIR has no data file
    for jd_ut's era, swisseph silently uses Moshier instead (when jd_ut is
    in Moshier's range) -- Position.ephemeris_model reports the model that
    was actually used, read from swisseph's return flags.
    """
    base_flag = swe.FLG_MOSEPH if use_moshier else swe.FLG_SWIEPH
    swe.set_sid_mode(ayanamsha.value)
    try:
        tropical_xx, _ = _calc(jd_ut, body, base_flag | swe.FLG_SPEED)
        sidereal_xx, flags = _calc(jd_ut, body, base_flag | swe.FLG_SPEED | swe.FLG_SIDEREAL)
    except swe.Error:
        if not use_moshier:
            raise
        tropical_xx, _ = _calc(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
        sidereal_xx, flags = _calc(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL)
    ayanamsha_value = swe.get_ayanamsa_ut(jd_ut)
    model = model_from_flags(flags)
    speed = sidereal_xx[3]

    return Position(
        tropical_longitude=tropical_xx[0],
        sidereal_longitude=sidereal_xx[0],
        ayanamsha=ayanamsha_value,
        speed_deg_per_day=speed,
        retrograde=speed < 0,
        ephemeris_model=model,
    )
