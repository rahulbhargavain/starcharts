"""Coarse-to-fine constraint search across a multi-millennium date range.

The core problem: given several graha/tithi constraints, find every
Julian day in a huge range where they all hold, without checking every
day one at a time. The trick is ordering constraints from slowest-moving
to fastest and scanning at a step size safe for the *current* stage's
slowest constrained graha -- each stage only has to survive not skipping
past a satisfying window, not pin down the exact day. Only the final stage
scans at high resolution, and only within windows that already survived
every coarser filter.

Stage grouping and step sizes intentionally follow the mean time a graha
spends per rashi (30 degrees), halved for safety margin so a scan can't
step clean over a satisfying window:
    Shani (Saturn)  ~897 days/rashi  -> coarse stage,  200-day steps
    Guru (Jupiter)  ~361 days/rashi  -> coarse stage shares the 200-day step
    Mangala (Mars)  ~57 days/rashi   -> mars stage,      20-day steps
    Surya/Shukra/Budha (Sun/Venus/Mercury, treated alike for this coarse
                    purpose despite Venus/Mercury's retrograde loops)
                    ~30 days/rashi   -> fine stage,        5-day steps
    Chandra (Moon)  ~2.25 days/rashi -> moon stage,      0.25-day steps
    Rahu/Ketu (nodes) ~251 days/nakshatra -> mars stage's 20-day step is
                    comfortably safe for these too (18.6-year node cycle)
Tithi and retrograde constraints are cheap to check at any resolution and
are folded into the moon stage (tithi changes about once a day, same
order as the Moon's rashi-transit rate).
"""

from dataclasses import dataclass

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.constraints import (
    Constraint,
    NakshatraConstraint,
    NodeNakshatraConstraint,
    RashiConstraint,
    RetrogradeConstraint,
    TithiConstraint,
)
from starcharts.ephemeris import to_julian_day_ut_astro

# (stage_name, step_days, grahas/nodes checked at this stage)
_STAGES: tuple[tuple[str, float, tuple[str, ...]], ...] = (
    ("coarse", 200.0, ("Shani", "Guru")),
    ("mars", 20.0, ("Mangala", "Rahu", "Ketu")),
    ("fine", 5.0, ("Surya", "Shukra", "Budha")),
    ("moon", 0.25, ("Chandra",)),
)


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


def _graha_of(constraint: Constraint) -> str | None:
    if isinstance(constraint, (RashiConstraint, NakshatraConstraint, RetrogradeConstraint)):
        return constraint.graha
    if isinstance(constraint, NodeNakshatraConstraint):
        return constraint.node
    return None


def _scan_windows(
    windows: list[tuple[float, float]],
    step_days: float,
    stage_constraints: list[Constraint],
    ayanamsha: Ayanamsha,
) -> list[tuple[float, float]]:
    """Step through each window at step_days, keep the sub-ranges where
    every stage constraint is satisfied, padded by one step on each side
    so the next (finer) stage doesn't start exactly on a boundary."""
    survivors: list[tuple[float, float]] = []
    for window_start, window_end in windows:
        hit_start: float | None = None
        jd = window_start
        while jd <= window_end:
            satisfied = all(c.is_satisfied(jd, ayanamsha) for c in stage_constraints)
            if satisfied and hit_start is None:
                hit_start = jd
            elif not satisfied and hit_start is not None:
                survivors.append((hit_start - step_days, jd + step_days))
                hit_start = None
            jd += step_days
        if hit_start is not None:
            survivors.append((hit_start - step_days, window_end + step_days))
    return survivors


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

    for _stage_name, step_days, grahas in _STAGES:
        stage_constraints = [c for c in profile.constraints if _graha_of(c) in grahas]
        if not stage_constraints:
            continue
        windows = _merge_overlapping(
            _scan_windows(windows, step_days, stage_constraints, profile.ayanamsha)
        )
        if not windows:
            return []

    # Tithi constraints ride along with the finest (moon) resolution scan.
    finest_step_days = _STAGES[-1][1]
    tithi_constraints = [c for c in profile.constraints if isinstance(c, TithiConstraint)]
    if tithi_constraints:
        windows = _merge_overlapping(
            _scan_windows(windows, finest_step_days, tithi_constraints, profile.ayanamsha)
        )
        if not windows:
            return []

    return _score_candidates(windows, profile, finest_step_days)


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


def _score_candidates(
    windows: list[tuple[float, float]], profile: SearchProfile, step_days: float
) -> list[CandidateMatch]:
    candidates: list[CandidateMatch] = []
    for window_start, window_end in windows:
        jd = window_start
        while jd <= window_end:
            per_constraint = tuple(
                c.score(jd, profile.ayanamsha) for c in profile.constraints
            )
            combined = min(per_constraint) if per_constraint else 0.0
            candidates.append(CandidateMatch(jd, combined, per_constraint))
            jd += step_days
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
