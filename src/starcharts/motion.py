"""Speed limits for everything the search engine scans, and the safe-step
rule built on them.

The engine can only sample a constraint at discrete instants. To skip
ahead without stepping over a match, it needs to know how long a sampled
value is guaranteed to stay on its side of a boundary. For a quantity
whose rate (degrees/day) is currently v, off by at most rate_error, and
changing by at most max_rate_change per day, it moves at most
    (|v| + rate_error) * s + max_rate_change * s**2 / 2
in s days, and never more than max_rate * s. safe_duration() inverts that:
the longest s for which the quantity cannot cover a given distance.

The bounds below are the observed maxima over 5300 BCE - 2940 CE (Moshier
in range, Swiss Ephemeris data files outside it), sampled every 0.25 day
(0.125 for the Moon), with at least ~30% headroom:

    body      max|rate|  max|rate change|  rate error (reported vs actual)
    Surya       1.025       0.0007            0.00001
    Chandra    15.40        0.517             0.0003
    Mangala     0.792       0.0151            0.0025
    Budha       2.204       0.198             0.0043
    Guru        0.243       0.0035            0.0101
    Shukra      1.264       0.043             0.0015
    Shani       0.134       0.0057            0.0113
    mean node   0.053       ~0                ~0
    elongation 14.40        0.517             (Moon's)

"Rate error" is how far Swiss Ephemeris' reported speed can sit from the
actual change in position: it jumps at internal segment boundaries (by up
to ~0.025 deg/day between consecutive days for Guru/Shani). That is
covered by rate_error -- added to the sampled rate for position margins,
and as margin slack (2x, both ends of a step) for the speed itself in
RetrogradeConstraint -- so max_rate_change only has to bound the physical
motion.
tests/test_engine_brute_force.py re-checks these bounds against the
ephemeris and checks the engine against dense brute-force scans.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MotionBounds:
    max_rate: float  # |d value / dt|, units/day
    max_rate_change: float  # |d rate / dt|, units/day^2
    rate_error: float  # max |reported rate - actual rate|, units/day


GRAHA_MOTION: dict[str, MotionBounds] = {
    "Surya": MotionBounds(1.1, 0.002, 0.001),
    "Chandra": MotionBounds(16.5, 0.8, 0.005),
    "Mangala": MotionBounds(0.9, 0.03, 0.01),
    "Budha": MotionBounds(2.5, 0.3, 0.02),
    "Guru": MotionBounds(0.3, 0.01, 0.03),
    "Shukra": MotionBounds(1.4, 0.07, 0.01),
    "Shani": MotionBounds(0.2, 0.01, 0.03),
}
NODE_MOTION = MotionBounds(0.07, 0.001, 0.001)
ELONGATION_MOTION = MotionBounds(16.5, 0.8, 0.006)


def safe_duration(distance: float, rate: float | None, bounds: MotionBounds) -> float:
    """Longest time (days) in which the quantity cannot move `distance`.

    rate=None means the current rate is unknown: only the max_rate cap is
    used. Returns 0 for a non-positive distance."""
    if distance <= 0.0:
        return 0.0
    capped = distance / bounds.max_rate
    if rate is None:
        return capped
    v = abs(rate) + bounds.rate_error
    a = bounds.max_rate_change
    # Positive root of v*s + a*s^2/2 = distance, in the cancellation-free form.
    kinematic = 2.0 * distance / (v + math.sqrt(v * v + 2.0 * a * distance)) if a > 0 else distance / v
    return max(capped, kinematic)
