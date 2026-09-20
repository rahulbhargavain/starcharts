"""Generic degree-arc membership and fuzzy-boundary scoring.

Shared by rashi, nakshatra, and tithi matching (all three are "does this
angle fall in this arc, padded by some tolerance" checks), and by the
search engine's ranking, which needs a continuous score rather than a
hard boolean.
"""

import math


def signed_gap_to_center(longitude: float, arc_start: float, arc_width: float) -> float:
    """Shortest signed angular gap from longitude to the arc's center."""
    center = arc_start + arc_width / 2.0
    return (longitude - center + 180.0) % 360.0 - 180.0


def arc_matches(
    longitude: float, arc_start: float, arc_width: float, tolerance_degrees: float = 0.0
) -> bool:
    """Does longitude fall within [arc_start, arc_start + arc_width],
    padded by tolerance_degrees on each side?"""
    gap = signed_gap_to_center(longitude, arc_start, arc_width)
    return abs(gap) <= arc_width / 2.0 + tolerance_degrees


def arc_score(
    longitude: float, arc_start: float, arc_width: float, tolerance_degrees: float = 0.0
) -> float:
    """1.0 anywhere inside the arc; decays as a Gaussian (sigma =
    tolerance_degrees) once outside it, reaching ~0 well past the padded
    boundary. Used for ranking candidates, not for hard filtering."""
    gap = abs(signed_gap_to_center(longitude, arc_start, arc_width))
    half_width = arc_width / 2.0
    if gap <= half_width:
        return 1.0
    excess = gap - half_width
    sigma = max(tolerance_degrees, 1e-6)
    return math.exp(-0.5 * (excess / sigma) ** 2)
