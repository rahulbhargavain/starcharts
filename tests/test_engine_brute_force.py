"""Brute-force regression tests for engine.search().

The engine skips ahead using the speed bounds in motion.py instead of
checking every instant. These tests check that the skipping never loses a
match: (1) the bounds themselves hold against the ephemeris, and (2) on
fixed and randomized profiles, every spell a dense brute-force scan finds
is also found by the engine.

A "spell" is a run of satisfied instants: consecutive satisfied samples
closer than SPELL_GAP_DAYS apart belong to the same spell.
"""

import random
from pathlib import Path

import pytest

from starcharts.ayanamsha import DEFAULT_AYANAMSHA
from starcharts.constants import GRAHAS
from starcharts.constraints import (
    EitherNodeNakshatraConstraint,
    NakshatraConstraint,
    NodeNakshatraConstraint,
    RashiConstraint,
    RetrogradeConstraint,
    TithiConstraint,
)
from starcharts.engine import SearchProfile, search
from starcharts.ephemeris import sidereal_longitude_and_speed, to_julian_day_ut_astro
from starcharts.motion import ELONGATION_MOTION, GRAHA_MOTION, NODE_MOTION
from starcharts.nodes import RAHU_BODY
from starcharts.panchanga import _tropical_longitude_and_speed

import swisseph as swe

SPELL_GAP_DAYS = 2.0
EPHE_DIR = Path(__file__).resolve().parent.parent / "ephe"
needs_data_files = pytest.mark.skipif(
    not any(EPHE_DIR.glob("*.se1")),
    reason="Swiss Ephemeris data files not downloaded (run ephe/download.sh)",
)


# --- helpers -----------------------------------------------------------------

def _satisfied(profile, jd):
    return all(c.is_satisfied(jd, profile.ayanamsha) for c in profile.constraints)


def _spells(jds, gap=SPELL_GAP_DAYS):
    spells = []
    for jd in sorted(jds):
        if spells and jd - spells[-1][1] <= gap:
            spells[-1][1] = jd
        else:
            spells.append([jd, jd])
    return spells


def _brute_force_spells(profile, step_days):
    """Every step_days across the range. Uses margin() >= 0, which is
    is_satisfied() from one ephemeris call instead of three --
    test_margin_sign_matches_is_satisfied checks the two agree."""
    order = sorted(profile.constraints, key=lambda c: c.scan_key)
    jd = to_julian_day_ut_astro(profile.start_astronomical_year, 1, 1)
    end = to_julian_day_ut_astro(profile.end_astronomical_year, 12, 31)
    hits = []
    while jd <= end:
        if all(c.margin(jd, profile.ayanamsha)[0] >= 0.0 for c in order):
            hits.append(jd)
        jd += step_days
    return _spells(hits)


def _engine_spells(profile):
    return _spells([m.jd_ut for m in search(profile) if _satisfied(profile, m.jd_ut)])


def _assert_engine_finds_every_brute_force_spell(profile, step_days):
    brute = _brute_force_spells(profile, step_days)
    engine = _engine_spells(profile)
    missed = [
        (swe.revjul(start), swe.revjul(end))
        for start, end in brute
        if not any(e_start - step_days <= end and start <= e_end + step_days for e_start, e_end in engine)
    ]
    assert not missed, f"engine missed {len(missed)} of {len(brute)} brute-force spells, e.g. {missed[:3]}"
    return brute, engine


# --- 1. the motion bounds hold ------------------------------------------------

_BOUND_ERAS = (-2900, -1500, 0, 1500, 2800)  # Moshier range: no data files needed


def _check_position_bounds(sample, bounds, rng, n=400):
    for _ in range(n):
        jd = swe.julday(rng.choice(_BOUND_ERAS), 1, 1) + rng.uniform(0, 100 * 365.25)
        s = rng.choice((0.25, 1.0, 5.0, 20.0, 60.0)) * rng.uniform(0.5, 1.0)
        lon0, v0 = sample(jd)
        lon1, v1 = sample(jd + s)
        moved = abs((lon1 - lon0 + 180.0) % 360.0 - 180.0)
        limit = min(
            bounds.max_rate * s,
            (abs(v0) + bounds.rate_error) * s + bounds.max_rate_change * s * s / 2.0,
        )
        assert moved <= limit + 1e-9, (jd, s, moved, limit)
        assert abs(v1 - v0) <= bounds.max_rate_change * s + 2 * bounds.rate_error + 1e-12, (jd, s, v0, v1)


@pytest.mark.parametrize("graha", sorted(GRAHAS))
def test_graha_motion_bounds_hold(graha):
    rng = random.Random(graha)
    body = GRAHAS[graha]
    _check_position_bounds(
        lambda jd: sidereal_longitude_and_speed(jd, body, DEFAULT_AYANAMSHA), GRAHA_MOTION[graha], rng
    )


def test_node_motion_bounds_hold():
    _check_position_bounds(
        lambda jd: sidereal_longitude_and_speed(jd, RAHU_BODY, DEFAULT_AYANAMSHA), NODE_MOTION, random.Random(0)
    )


def test_elongation_motion_bounds_hold():
    def elongation(jd):
        moon, moon_speed = _tropical_longitude_and_speed(jd, swe.MOON)
        sun, sun_speed = _tropical_longitude_and_speed(jd, swe.SUN)
        return (moon - sun) % 360.0, moon_speed - sun_speed

    _check_position_bounds(elongation, ELONGATION_MOTION, random.Random(1))


@pytest.mark.parametrize("graha", ["Guru", "Shani"])
@needs_data_files
def test_slow_graha_bounds_hold_outside_moshier_range(graha):
    """Beyond ~3000 BCE positions come from the data files, whose reported
    speed jumps at segment boundaries -- rate_error has to cover that."""
    rng = random.Random(graha + "-deep")
    body = GRAHAS[graha]
    bounds = GRAHA_MOTION[graha]
    for _ in range(300):
        jd = swe.julday(-5300, 1, 1) + rng.uniform(0, 2200 * 365.25)
        s = rng.uniform(0.5, 30.0)
        lon0, v0 = sidereal_longitude_and_speed(jd, body, DEFAULT_AYANAMSHA)
        lon1, v1 = sidereal_longitude_and_speed(jd + s, body, DEFAULT_AYANAMSHA)
        moved = abs((lon1 - lon0 + 180.0) % 360.0 - 180.0)
        assert moved <= (abs(v0) + bounds.rate_error) * s + bounds.max_rate_change * s * s / 2.0 + 1e-9
        assert abs(v1 - v0) <= bounds.max_rate_change * s + 2 * bounds.rate_error


def test_margin_sign_matches_is_satisfied():
    """margin() >= 0 must mean exactly is_satisfied() for every prunable
    constraint type -- the engine prunes on one and callers check the other."""
    rng = random.Random(7)
    for _ in range(3000):
        constraint = rng.choice((
            RashiConstraint(rng.choice(sorted(GRAHAS)), rng.randrange(12), rng.choice((0.0, 2.0))),
            NakshatraConstraint(rng.choice(sorted(GRAHAS)), rng.randrange(27), rng.choice((0.0, 2.0))),
            TithiConstraint(rng.randint(1, 30), rng.choice((0.0, 2.0))),
            RetrogradeConstraint(rng.choice(("Mangala", "Budha", "Guru", "Shukra", "Shani")), rng.random() < 0.5),
            NodeNakshatraConstraint(rng.choice(("Rahu", "Ketu")), rng.randrange(27), 1.0),
            EitherNodeNakshatraConstraint(rng.randrange(27), 1.0),
        ))
        jd = swe.julday(rng.randrange(-2900, 2900), 1, 1) + rng.uniform(0, 365.25)
        assert (constraint.margin(jd, DEFAULT_AYANAMSHA)[0] >= 0.0) == constraint.is_satisfied(jd, DEFAULT_AYANAMSHA)


# --- 2. engine vs brute force: the miss patterns the old fixed steps had ------

# expected_spells: brute-force count; the old fixed-step engine's count in comments.
@pytest.mark.parametrize(
    "name, profile, step_days, expected_spells",
    [
        # Guru crosses a 13.3-degree nakshatra in ~160 days on average,
        # shorter than the old 200-day coarse step. Old engine: 13.
        ("Guru nakshatra", SearchProfile(0, 200, (NakshatraConstraint("Guru", 21),)), 1.0, 26),
        # Guru retrograde spells (~120 days) vs the old 200-day step. Old
        # engine: 0 here (35 of 92 over 2000-2100).
        ("Guru retrograde", SearchProfile(2000, 2040, (RetrogradeConstraint("Guru"),)), 2.0, 37),
        # Two slow constraints that each hold for months but overlap only
        # briefly. Old engine: 0.
        (
            "Shani+Guru overlap",
            SearchProfile(-250, 0, (NakshatraConstraint("Shani", 3), NakshatraConstraint("Guru", 21))),
            1.0,
            3,
        ),
        # Budha's retrograde dip back into the previous rashi. Old engine: 8.
        (
            "Budha retrograde re-entry",
            SearchProfile(1990, 2010, (RashiConstraint("Budha", 5), RetrogradeConstraint("Budha"))),
            0.25,
            9,
        ),
        # Fast constraints together: the overlap can last only hours. Old engine: 4.
        (
            "Chandra nakshatra + tithi",
            SearchProfile(2020, 2023, (NakshatraConstraint("Chandra", 3), TithiConstraint(8))),
            0.05,
            4,
        ),
        # Old engine: 9 -- but only because EitherNode never pruned anything.
        (
            "node + Mangala retrograde",
            SearchProfile(
                1500, 1700, (EitherNodeNakshatraConstraint(17, 1.0), RetrogradeConstraint("Mangala"))
            ),
            1.0,
            9,
        ),
    ],
)
def test_engine_matches_brute_force_on_known_miss_patterns(name, profile, step_days, expected_spells):
    brute, engine = _assert_engine_finds_every_brute_force_spell(profile, step_days)
    assert len(brute) == expected_spells, name
    assert len(engine) == expected_spells, name


# --- 3. engine vs brute force: randomized profiles ----------------------------

_SLOW = ("Shani", "Guru", "Mangala")
_MEDIUM = ("Surya", "Shukra", "Budha")


def _random_constraint(rng, pool):
    kind = rng.choice(("rashi", "nakshatra", "retrograde", "node"))
    graha = rng.choice(pool)
    tol = rng.choice((0.0, 0.5, 2.0))
    if kind == "rashi":
        return RashiConstraint(graha, rng.randrange(12), tol)
    if kind == "nakshatra":
        return NakshatraConstraint(graha, rng.randrange(27), tol)
    if kind == "retrograde" and graha != "Surya":
        return RetrogradeConstraint(graha, rng.random() < 0.7)
    return NodeNakshatraConstraint(rng.choice(("Rahu", "Ketu")), rng.randrange(27), tol)


@pytest.mark.parametrize("seed", range(12))
def test_engine_matches_brute_force_on_random_slow_profiles(seed):
    rng = random.Random(seed)
    start = rng.randrange(-2900, 2700)
    constraints = tuple(_random_constraint(rng, _SLOW) for _ in range(rng.randint(1, 3)))
    profile = SearchProfile(start, start + rng.randint(40, 120), constraints)
    brute, engine = _assert_engine_finds_every_brute_force_spell(profile, step_days=1.0)
    assert len(engine) >= len(brute)


@pytest.mark.parametrize("seed", range(12))
def test_engine_matches_brute_force_on_random_fast_profiles(seed):
    rng = random.Random(1000 + seed)
    start = rng.randrange(-2900, 2900)
    constraints = [_random_constraint(rng, _MEDIUM)]
    if rng.random() < 0.5:
        constraints.append(NakshatraConstraint("Chandra", rng.randrange(27), rng.choice((0.0, 2.0))))
    if rng.random() < 0.5:
        constraints.append(TithiConstraint(rng.randint(1, 30), rng.choice((0.0, 2.0))))
    profile = SearchProfile(start, start + rng.randint(1, 4), tuple(constraints))
    brute, engine = _assert_engine_finds_every_brute_force_spell(profile, step_days=0.05)
    assert len(engine) >= len(brute)


# --- 4. full-range results verified once against a 1-day brute-force scan ----

def _epoch_years(profile):
    """Start years of within-tolerance epochs (spells <= 60 days apart merged)."""
    return [
        swe.revjul(start)[0]
        for start, _end in _spells(
            [m.jd_ut for m in search(profile) if _satisfied(profile, m.jd_ut)], gap=60.0
        )
    ]


@needs_data_files
def test_udyoga_parva_within_tolerance_epochs_match_brute_force():
    """A 1-day brute-force scan of 5400 BCE - 3000 CE (~2.5 minutes, too
    slow to rerun here) finds these 14 epochs; the old fixed-step engine
    found only 11, missing 4628, 1946 and 1299 BCE."""
    from starcharts.texts.mahabharata import war_omen_profile_udyoga_parva

    assert _epoch_years(war_omen_profile_udyoga_parva(-5399, 3000, tolerance_degrees=2.0)) == [
        -5069, -4627, -1945, -1298, -856, -414, 28, 470, 912, 1117, 1559, 2001, 2443, 2885,
    ]


@needs_data_files
def test_bhishma_parva_within_tolerance_epochs_match_brute_force():
    from starcharts.texts.mahabharata import war_omen_profile_bhishma_parva

    profile = war_omen_profile_bhishma_parva(-5399, 3000, tolerance_degrees=2.0, include_node_at_jyeshtha=False)
    assert _epoch_years(profile) == [-3448, -2535, 2768]
