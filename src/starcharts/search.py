"""Root-finding for exact panchanga moments (new moon, tithi boundaries).

Moon-Sun elongation increases at a fairly steady ~12.19 deg/day (the mean
synodic rate), so a fixed-point iteration using that mean rate converges in
a handful of steps even though the Moon's true angular speed varies.
"""

from starcharts.panchanga import moon_sun_elongation

SYNODIC_MONTH_DAYS = 29.530588
_MEAN_ELONGATION_RATE_DEG_PER_DAY = 360.0 / SYNODIC_MONTH_DAYS


def _signed_gap(elongation: float, target: float) -> float:
    """Shortest signed angular gap elongation -> target, in (-180, 180]."""
    gap = (target - elongation) % 360.0
    if gap > 180.0:
        gap -= 360.0
    return gap


def find_elongation_crossing(
    jd_guess: float,
    target_degrees: float,
    max_iterations: int = 40,
    tolerance_degrees: float = 1e-6,
) -> float:
    """Find the Julian day nearest jd_guess where Moon-Sun elongation equals
    target_degrees (mod 360)."""
    jd = jd_guess
    for _ in range(max_iterations):
        current = moon_sun_elongation(jd)
        gap = _signed_gap(current, target_degrees)
        if abs(gap) < tolerance_degrees:
            return jd
        jd += gap / _MEAN_ELONGATION_RATE_DEG_PER_DAY
    return jd
