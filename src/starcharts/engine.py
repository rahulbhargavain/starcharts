"""Constraint search across a multi-millennium date range.

The core problem: given several graha/tithi constraints, find every
Julian day in a huge range where they all hold, without checking every
day one at a time.

Each prunable constraint reports a signed margin -- how far its value is
from the match boundary, >= 0 exactly when it's satisfied -- and bounds on
how fast that margin can change (motion.py). From one sample the engine
therefore knows how long the constraint is guaranteed to stay on its
current side of the boundary, and steps exactly that far: huge steps when
a slow graha is far from its arc, small ones only near a boundary. A
stretch is discarded only when the bounds prove the constraint fails
throughout it, so no match can be stepped over, however short it is or
however briefly several constraints overlap. Where the bounds can't
certify a stretch of at least MIN_STEP_DAYS, that stretch is kept rather
than dropped; a second pass at REFINE_STEP_DAYS (15 minutes) then trims
the surviving windows, so they run at most that far past a true boundary.

Constraints are scanned slowest-first (constraints.SCAN_ORDER): the
first is scanned over the whole range, each later one only inside what
earlier ones left, so the result is the intersection. Surviving windows
are then sampled every FINE_STEP_DAYS (plus each window's midpoint, so a
window shorter than one step is still sampled inside) and ranked by the
constraints' continuous scores.

This replaced fixed per-stage step sizes (200 days for Shani/Guru, 20 for
Mangala/nodes, 5 for Surya/Shukra/Budha) chosen from the mean time a
graha spends in a whole rashi. Those steps were longer than many
satisfying windows -- a Guru nakshatra transit or retrograde spell, or the
overlap of two constraints -- and silently missed real matches (e.g. 2 of
3 Bhishma Parva epochs and 3 of 14 Udyoga Parva epochs across
5400 BCE - 3000 CE). tests/test_engine_brute_force.py checks the engine
against dense brute-force scans.

Constraints without a margin() (e.g. AscendantConstraint, which moves too
fast for date-level scanning) don't prune; they're only scored.
"""

from dataclasses import dataclass

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.constraints import Constraint
from starcharts.ephemeris import to_julian_day_ut_astro
from starcharts.motion import safe_duration

FINE_STEP_DAYS = 0.25  # scoring resolution inside surviving windows
MIN_STEP_DAYS = FINE_STEP_DAYS  # boundaries unresolved below this are kept as possible matches
REFINE_STEP_DAYS = 1.0 / 96.0  # 15 minutes: second pass over the (small) surviving windows


@dataclass(frozen=True)
class SearchProfile:
    start_astronomical_year: int
    end_astronomical_year: int
    constraints: tuple[Constraint, ...]
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA


@dataclass(frozen=True)
class CandidateMatch:
    jd_ut: float
    score: float
    per_constraint_scores: tuple[float, ...]


def _is_prunable(constraint: Constraint) -> bool:
    return hasattr(constraint, "margin")


def _possible_windows(
    windows: list[tuple[float, float]],
    constraint: Constraint,
    ayanamsha: Ayanamsha,
    min_step: float = MIN_STEP_DAYS,
) -> list[tuple[float, float]]:
    """The parts of `windows` where `constraint` may be satisfied: every
    instant it is satisfied is inside the result. Each sample certifies a
    stretch as possibly-satisfied or definitely-not via motion.safe_duration
    and the scan resumes where that stretch ends."""
    bounds = constraint.motion_bounds
    slack = constraint.margin_slack
    kept: list[tuple[float, float]] = []
    for window_start, window_end in windows:
        jd = window_start
        while jd <= window_end:
            margin, rate = constraint.margin(jd, ayanamsha)
            if margin + slack >= 0.0:
                # Possibly satisfied until the margin could drop below -slack.
                step = max(safe_duration(margin + slack, rate, bounds), min_step)
                kept.append((jd, min(jd + step, window_end)))
            else:
                # Definitely not satisfied until the margin could climb to -slack.
                step = safe_duration(-(margin + slack), rate, bounds)
                if step < min_step:
                    step = min_step
                    kept.append((jd, min(jd + step, window_end)))
            jd += step
    return _merge_overlapping(kept)


def _merge_overlapping(windows: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not windows:
        return []
    windows = sorted(windows)
    merged = [windows[0]]
    for start, end in windows[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def search(profile: SearchProfile) -> list[CandidateMatch]:
    """Search profile.constraints across the given astronomical-year
    range, returning every surviving candidate ranked by combined score
    (highest first)."""
    jd_start = to_julian_day_ut_astro(profile.start_astronomical_year, 1, 1)
    jd_end = to_julian_day_ut_astro(profile.end_astronomical_year, 12, 31)
    windows = [(jd_start, jd_end)]

    prunable = sorted((c for c in profile.constraints if _is_prunable(c)), key=lambda c: c.scan_key)
    # Coarse pass over the whole range, then a 15-minute pass over what
    # survives, so each window's midpoint lands inside overlaps as short as
    # ~half an hour (the Moon moves ~0.5 deg/hour, so tight lunar
    # constraints can overlap only briefly) instead of up to a step away.
    for min_step in (MIN_STEP_DAYS, REFINE_STEP_DAYS):
        for constraint in prunable:
            windows = _possible_windows(windows, constraint, profile.ayanamsha, min_step)
            if not windows:
                return []

    return _score_candidates(windows, profile, FINE_STEP_DAYS)


def cluster_into_epochs(
    matches: list[CandidateMatch], gap_days: float = 60.0, score_threshold: float = 0.99
) -> list[list[CandidateMatch]]:
    """Group high-scoring matches into distinct epochs -- consecutive
    matches within gap_days of each other are the same underlying
    astronomical event (the same window sampled repeatedly at the
    engine's finest resolution), not separate occurrences. Reusable
    version of clustering logic that had been hand-rolled repeatedly
    across this project's Mahabharata/Ramayana analysis scripts."""
    survivors = sorted((m for m in matches if m.score >= score_threshold), key=lambda m: m.jd_ut)
    epochs: list[list[CandidateMatch]] = []
    for m in survivors:
        if epochs and m.jd_ut - epochs[-1][-1].jd_ut <= gap_days:
            epochs[-1].append(m)
        else:
            epochs.append([m])
    return epochs


def _sample_times(windows: list[tuple[float, float]], step_days: float) -> list[float]:
    """Every step_days across each window, padded by one step on each side
    so ranking sees the approach to each boundary, plus each window's
    midpoint so even a window shorter than one step is sampled inside."""
    times: set[float] = set()
    for window_start, window_end in windows:
        jd = window_start - step_days
        while jd <= window_end + step_days:
            times.add(jd)
            jd += step_days
        times.add((window_start + window_end) / 2.0)
    return sorted(times)


def _score_candidates(
    windows: list[tuple[float, float]], profile: SearchProfile, step_days: float
) -> list[CandidateMatch]:
    candidates: list[CandidateMatch] = []
    for jd in _sample_times(windows, step_days):
        per_constraint = tuple(c.score(jd, profile.ayanamsha) for c in profile.constraints)
        combined = min(per_constraint) if per_constraint else 0.0
        candidates.append(CandidateMatch(jd, combined, per_constraint))
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
