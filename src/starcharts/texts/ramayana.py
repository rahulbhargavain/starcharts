"""Valmiki Ramayana, Bala Kanda, Sarga 18 -- the verses describing the
sky at Rama's birth, encoded as search constraints.

TEXT CAVEAT: the verse numbering (commonly cited as approximately Sarga
18, verses 8-10) and exact wording both vary across editions (e.g. the
Baroda critical edition vs. the widely circulated Gita Press text) and
across translators. What follows is a paraphrase of content that is
consistent across the versions surveyed, not a verbatim quotation of any
single edition or translation -- treat the *substance* as reasonably
well attested and the precise verse numbers as approximate.

Paraphrased content: Rama was born on the ninth day (Navami) of the
bright half (Shukla paksha) of the month of Chaitra, with the Moon in
Punarvasu nakshatra. At that moment, five grahas were each in their sign
of exaltation -- Surya in Mesha, Mangala in Makara, Shani in Tula, Guru
in Karka, and Shukra in Meena -- while the Moon was in its own sign,
Karka, and the ascendant (Lagna) was also Karka.

CONSTRAINT-SET NOTES (see WORKPLAN.md for the fuller discussion):
- This is six simultaneous graha-rashi constraints plus a Moon nakshatra,
  a tithi, and a Lagna -- an extremely tight conjunction. That tightness
  is exactly why this configuration gets used for dating attempts: it is
  rare enough that if it's found at all, it's a strong candidate. It's
  also why an empty result in a given search range isn't surprising on
  its own.
- The Moshier ephemeris model covers only ~3002 BCE to ~3003 CE; the
  full Swiss Ephemeris data files in ephe/ extend real coverage further
  back (see ephemeris.py). A search that comes up empty within whatever
  range is currently reachable neither confirms nor refutes a
  traditionally-cited date outside that range.
- Masa (Chaitra) is corroborating evidence only, not a hard filter --
  see calendar.py's module caveat on pre-500 CE intercalation anachronism.
- Lagna is checked separately from the graha/tithi search, at local noon
  in Ayodhya (the traditional time of birth), because the ascendant
  moves far too fast (~2h/rashi) for engine.py's date-level coarse-to-fine
  scan -- see ascendant.py's module docstring. It is NOT part of the
  SearchProfile this module builds; check it with lagna_matches_at_noon()
  on whatever candidate dates the graha/tithi search returns.
- Lagna is not independent evidence once Surya-in-Mesha already holds:
  at local noon the Sun sits at the Midheaven by definition, and at
  Ayodhya's latitude the Ascendant runs roughly 93-95 degrees ahead of
  the Midheaven (by direct computation, not the flat 90 degrees a
  simplified model would assume). So whenever Surya-in-Mesha holds at
  noon, Karka-lagna follows from it almost automatically at this
  latitude. Still worth checking -- it can fail near Mesha's far edge,
  since the true MC-Asc offset isn't exactly 90 degrees -- but it adds
  little discriminating power on top of the Surya constraint alone.
"""

from starcharts.ascendant import ascendant_position, local_noon_jd_ut
from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.constraints import NakshatraConstraint, RashiConstraint, TithiConstraint
from starcharts.engine import SearchProfile
from starcharts.rashi import rashi_matches

AYODHYA_LATITUDE = 26.8
AYODHYA_LONGITUDE = 82.2

# Rashi indices (0=Mesha .. 11=Meena), per the exaltation/own-sign claims above.
_MESHA, _KARKA, _TULA, _MAKARA, _MEENA = 0, 3, 6, 9, 11
_PUNARVASU_NAKSHATRA = 6
_CHAITRA_SHUKLA_NAVAMI_TITHI = 9


def bala_kanda_birth_profile(
    start_astronomical_year: int,
    end_astronomical_year: int,
    tolerance_degrees: float = 1.5,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    require_surya_exalted: bool = True,
) -> SearchProfile:
    """Build the SearchProfile for the graha-rashi constraints, the
    Moon's Punarvasu nakshatra, and the Chaitra Shukla Navami tithi.
    Does NOT include the Lagna=Karka claim -- check that separately with
    lagna_matches_at_noon() on whatever this returns. tolerance_degrees
    applies to every rashi/nakshatra constraint; widen it to surface
    near-misses as ranked (lower-scoring) candidates instead of nothing.

    require_surya_exalted=False drops the Surya-in-Mesha constraint. The
    root shloka's exact wording on which five grahas are meant is an open
    textual question, unverified against a primary source -- if Surya
    isn't one of the intended five, this constraint is an interpretive
    addition rather than part of the verse itself, and dropping it is
    worth testing on its own merits regardless of how that resolves.
    """
    constraints = [
        RashiConstraint("Mangala", _MAKARA, tolerance_degrees),
        RashiConstraint("Shani", _TULA, tolerance_degrees),
        RashiConstraint("Guru", _KARKA, tolerance_degrees),
        RashiConstraint("Shukra", _MEENA, tolerance_degrees),
        RashiConstraint("Chandra", _KARKA, tolerance_degrees),
        NakshatraConstraint("Chandra", _PUNARVASU_NAKSHATRA, tolerance_degrees),
        TithiConstraint(_CHAITRA_SHUKLA_NAVAMI_TITHI, tolerance_degrees),
    ]
    if require_surya_exalted:
        constraints.insert(0, RashiConstraint("Surya", _MESHA, tolerance_degrees))
    return SearchProfile(start_astronomical_year, end_astronomical_year, tuple(constraints), ayanamsha)


def lagna_matches_at_noon(
    astronomical_year: int,
    month: int,
    day: int,
    tolerance_degrees: float = 1.5,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    proleptic_julian_calendar: bool = False,
) -> tuple[bool, float]:
    """Does the Karka-lagna claim hold at local noon in Ayodhya on this
    date? Returns (matches, sidereal_ascendant_longitude)."""
    jd_noon = local_noon_jd_ut(
        astronomical_year, month, day, AYODHYA_LONGITUDE, proleptic_julian_calendar
    )
    position = ascendant_position(jd_noon, AYODHYA_LATITUDE, AYODHYA_LONGITUDE, ayanamsha)
    matches = rashi_matches(position.sidereal_longitude, _KARKA, tolerance_degrees)
    return matches, position.sidereal_longitude
