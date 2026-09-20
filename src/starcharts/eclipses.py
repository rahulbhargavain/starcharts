"""Eclipse finding, for the Mahabharata's "two eclipses close together"
claim -- this needs real syzygy/node geometry (via swisseph's own
eclipse-finding routines), not a sign-level rashi/nakshatra approximation
the rest of this project uses. An eclipse depends on the Moon's ecliptic
*latitude* at syzygy (how close the New/Full Moon falls to a lunar node),
which none of the rashi/nakshatra/tithi machinery elsewhere in this
project touches at all.

Uses SEFLG_SWIEPH directly (not the Moshier auto-fallback pattern used
elsewhere) because eclipse timing needs the real ephemeris; Moshier's
approximation is not precise enough for this and swisseph's eclipse
functions are documented against the real data files. Requires the
files in EPHE_DIR to cover whatever era is being searched.
"""

from dataclasses import dataclass

import swisseph as swe

from starcharts.ephemeris import EPHE_DIR  # noqa: F401 (ensures ephe path is set)


@dataclass(frozen=True)
class Eclipse:
    jd_max: float
    kind: str  # "solar" or "lunar"


def _next_solar_eclipse(jd_ut: float) -> Eclipse:
    _res, tret = swe.sol_eclipse_when_glob(jd_ut, swe.FLG_SWIEPH, 0, False)
    return Eclipse(jd_max=tret[0], kind="solar")


def _next_lunar_eclipse(jd_ut: float) -> Eclipse:
    _res, tret = swe.lun_eclipse_when(jd_ut, swe.FLG_SWIEPH, 0, False)
    return Eclipse(jd_max=tret[0], kind="lunar")


def find_eclipses_in_range(jd_start: float, jd_end: float) -> list[Eclipse]:
    """Every solar and lunar eclipse (by time of maximum) in [jd_start,
    jd_end], merged and sorted chronologically."""
    eclipses: list[Eclipse] = []
    for finder in (_next_solar_eclipse, _next_lunar_eclipse):
        jd = jd_start
        while jd < jd_end:
            eclipse = finder(jd)
            if eclipse.jd_max >= jd_end:
                break
            eclipses.append(eclipse)
            jd = eclipse.jd_max + 1.0  # step past it to find the next one
    eclipses.sort(key=lambda e: e.jd_max)
    return eclipses


@dataclass(frozen=True)
class EclipsePair:
    first: Eclipse
    second: Eclipse
    gap_days: float


def find_close_eclipse_pairs(
    jd_start: float,
    jd_end: float,
    min_gap_days: float = 12.0,
    max_gap_days: float = 15.0,
) -> list[EclipsePair]:
    """Consecutive eclipse pairs (almost always one solar + one lunar,
    since that's what falls in an ~half-synodic-month gap) whose gap
    falls in [min_gap_days, max_gap_days].

    The traditional claim ("two eclipses within ~13 days") is notably
    SHORTER than the normal ~14.77-day half-synodic-month spacing
    between a solar and lunar eclipse in the same eclipse season --
    that's what makes it a distinctive, checkable detail rather than a
    routine occurrence. Default bounds are widened slightly around 13
    (12-15) to absorb tithi-vs-solar-day counting ambiguity in how the
    verse's "13" was meant, not because the astronomy itself is fuzzy.
    """
    eclipses = find_eclipses_in_range(jd_start, jd_end)
    pairs = []
    for a, b in zip(eclipses, eclipses[1:]):
        gap = b.jd_max - a.jd_max
        if min_gap_days <= gap <= max_gap_days:
            pairs.append(EclipsePair(first=a, second=b, gap_days=gap))
    return pairs
