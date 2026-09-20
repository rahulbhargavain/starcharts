from datetime import datetime, timezone

import pytest

from starcharts.chart import compute_chart
from starcharts.constraints import (
    NakshatraConstraint,
    RashiConstraint,
    RetrogradeConstraint,
    TithiConstraint,
)
from starcharts.engine import CandidateMatch, SearchProfile, cluster_into_epochs, search
from starcharts.ephemeris import to_julian_day_ut
from starcharts.panchanga import tithi_at


def _constraints_from_known_chart(dt, tithi_tolerance=0.5, rashi_tolerance=0.0):
    chart = compute_chart(dt)
    jd = to_julian_day_ut(dt)
    tithi = tithi_at(jd)
    constraints = [
        RashiConstraint(graha, placement.rashi.index, tolerance_degrees=rashi_tolerance)
        for graha, placement in chart.items()
    ]
    constraints.append(TithiConstraint(tithi.number, tolerance_degrees=tithi_tolerance))
    return chart, jd, constraints


def test_search_recovers_a_known_date_within_its_own_year():
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    _chart, true_jd, constraints = _constraints_from_known_chart(dt)

    profile = SearchProfile(
        start_astronomical_year=2024,
        end_astronomical_year=2024,
        constraints=tuple(constraints),
    )
    matches = search(profile)

    assert matches, "expected at least one surviving candidate"
    best = matches[0]
    assert best.score > 0.99
    assert abs(best.jd_ut - true_jd) < 1.0


def test_search_returns_no_candidates_for_an_impossible_constraint():
    # Force a Jupiter rashi that it provably does not occupy in this
    # narrow one-year window, with zero tolerance -- the coarse stage
    # should prune everything and return an empty list rather than
    # scanning all the way to the fine stages.
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    chart = compute_chart(dt)
    wrong_rashi = (chart["Guru"].rashi.index + 6) % 12  # opposite sign, never true here
    profile = SearchProfile(
        start_astronomical_year=2024,
        end_astronomical_year=2024,
        constraints=(RashiConstraint("Guru", wrong_rashi, tolerance_degrees=0.0),),
    )
    assert search(profile) == []


def test_search_with_nakshatra_and_retrograde_constraints_does_not_crash():
    dt = datetime(2024, 6, 1, tzinfo=timezone.utc)
    chart = compute_chart(dt)
    moon = chart["Chandra"]
    shani = chart["Shani"]
    profile = SearchProfile(
        start_astronomical_year=2024,
        end_astronomical_year=2024,
        constraints=(
            RashiConstraint("Shani", shani.rashi.index, tolerance_degrees=1.0),
            NakshatraConstraint("Chandra", moon.nakshatra.index, tolerance_degrees=2.0),
            RetrogradeConstraint("Shani", retrograde=shani.position.retrograde),
        ),
    )
    matches = search(profile)
    assert matches
    assert matches[0].score > 0.0


def test_cluster_into_epochs_groups_nearby_matches_and_drops_low_scores():
    matches = [
        CandidateMatch(100.0, 1.0, ()),
        CandidateMatch(100.2, 1.0, ()),
        CandidateMatch(100.4, 0.5, ()),  # below default threshold, dropped
        CandidateMatch(500.0, 1.0, ()),  # far away, separate epoch
    ]
    epochs = cluster_into_epochs(matches, gap_days=1.0)
    assert len(epochs) == 2
    assert len(epochs[0]) == 2
    assert len(epochs[1]) == 1


def test_constraint_validation_rejects_bad_values():
    with pytest.raises(ValueError):
        RashiConstraint("NotAGraha", 0)
    with pytest.raises(ValueError):
        RashiConstraint("Surya", 12)
    with pytest.raises(ValueError):
        NakshatraConstraint("Surya", 27)
    with pytest.raises(ValueError):
        TithiConstraint(31)
