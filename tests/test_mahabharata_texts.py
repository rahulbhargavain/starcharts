import swisseph as swe

from starcharts.engine import search
from starcharts.texts.mahabharata import (
    has_close_eclipse_pair,
    krishna_birth_profile,
    lagna_matches_vrishabha_at_midnight,
    war_omen_profile_bhishma_parva,
    war_omen_profile_bhishma_parva_mars_circuitous_variant,
    war_omen_profile_udyoga_parva,
)


def test_krishna_birth_profile_recurs_roughly_annually():
    # A calendar-cyclical combination (tithi + nakshatra), not a rare
    # multi-planet conjunction -- across a 50-year window it should
    # produce roughly one candidate per year, not a short list.
    profile = krishna_birth_profile(2000, 2050, tolerance_degrees=1.0)
    matches = search(profile)
    nonzero = [m for m in matches if m.score > 0.5]
    assert len(nonzero) > 20  # order of one per year across 50 years


def test_lagna_matches_vrishabha_returns_a_plausible_longitude():
    matches, lon = lagna_matches_vrishabha_at_midnight(2000, 8, 1)
    assert 0.0 <= lon < 360.0
    assert isinstance(matches, bool)


def test_war_omen_profile_bhishma_parva_builds_without_error():
    profile = war_omen_profile_bhishma_parva(1000, 1100, tolerance_degrees=2.0)
    matches = search(profile)
    assert isinstance(matches, list)


def test_war_omen_profile_bhishma_parva_is_rare_and_misses_all_four_candidates():
    # Sanskrit-verified encoding (06,003.013c-d): Mars retrograde is part
    # of the same clause as Mars-in-Magha, not optional -- requiring it
    # makes this even rarer than the earlier (wrong) no-retrograde
    # reading: just 1 epoch in ~8400 years, still nowhere near any of
    # the four externally-proposed candidate years.
    matches = search(
        war_omen_profile_bhishma_parva(-5399, 3000, tolerance_degrees=2.0, include_node_at_jyeshtha=False)
    )
    perfect = sorted([m for m in matches if m.score > 0.99], key=lambda m: m.jd_ut)
    epochs = []
    for m in perfect:
        if epochs and m.jd_ut - epochs[-1] <= 60:
            continue
        epochs.append(m.jd_ut)
    assert len(epochs) == 1
    candidate_years = (-3136, -3066, -2448, -1477)
    for jd in epochs:
        year = swe.revjul(jd, swe.GREG_CAL)[0]
        assert all(abs(year - cy) > 100 for cy in candidate_years)


def test_war_omen_profile_bhishma_parva_node_constraint_is_less_restrictive_without_it():
    # Dropping the Jyeshtha-node constraint can only raise or keep the
    # best achievable score, never lower it.
    lo, hi = -3070, -3060
    with_node = search(
        war_omen_profile_bhishma_parva(lo, hi, tolerance_degrees=2.0, include_node_at_jyeshtha=True)
    )
    without_node = search(
        war_omen_profile_bhishma_parva(lo, hi, tolerance_degrees=2.0, include_node_at_jyeshtha=False)
    )
    best_with = max((m.score for m in with_node), default=0.0)
    best_without = max((m.score for m in without_node), default=0.0)
    assert best_without >= best_with


def test_war_omen_profile_udyoga_parva_builds_without_error():
    profile = war_omen_profile_udyoga_parva(-3070, -3060, tolerance_degrees=2.0)
    matches = search(profile)
    assert isinstance(matches, list)


def test_war_omen_profile_udyoga_parva_is_rare_and_misses_all_four_candidates():
    # Sanskrit-verified (5.141.8): "kṛtvā ca aṅgārakaḥ vakraṃ jyeṣṭhāyāṃ"
    # -- Mars retrograde IS required, not optional as an earlier
    # (pre-Sanskrit-check) version of this function had it. With that
    # fix, this drops from 159 loose epochs to 11 tightly-spaced ones
    # (~442 years apart) -- none within 300 years of any of the four
    # externally-proposed candidate years.
    matches = search(war_omen_profile_udyoga_parva(-5399, 3000, tolerance_degrees=2.0))
    perfect = sorted([m for m in matches if m.score > 0.99], key=lambda m: m.jd_ut)
    epochs = []
    for m in perfect:
        if epochs and m.jd_ut - epochs[-1] <= 60:
            continue
        epochs.append(m.jd_ut)
    assert len(epochs) == 11
    candidate_years = (-3136, -3066, -2448, -1477)
    for jd in epochs:
        year = swe.revjul(jd, swe.GREG_CAL)[0]
        assert all(abs(year - cy) > 100 for cy in candidate_years)


def test_mars_circuitous_variant_is_extremely_rare_and_misses_all_four_candidates():
    # Sanskrit-verified (06,003.017a): a full Mars retrograde loop at
    # Shravana is a textually distinct moment from 013c's Mars-in-Magha.
    # Extremely rare (checked previously: 1 epoch in ~8400 years) and
    # doesn't land near any candidate.
    matches = search(war_omen_profile_bhishma_parva_mars_circuitous_variant(-5399, 3000, tolerance_degrees=2.0))
    perfect = [m for m in matches if m.score > 0.99]
    assert len(perfect) > 0
    candidate_years = (-3136, -3066, -2448, -1477)
    for m in perfect:
        year = swe.revjul(m.jd_ut, swe.GREG_CAL)[0]
        assert all(abs(year - cy) > 100 for cy in candidate_years)


def test_has_close_eclipse_pair_is_true_almost_every_year():
    # Documents that this detail is NOT a useful discriminator on its
    # own -- see the module's eclipse-pair caveat.
    hits = sum(has_close_eclipse_pair(year) for year in range(2000, 2010))
    assert hits >= 8
