"""Krishna's birth (Janmashtami) and a couple of the Mahabharata war's
planetary-omen verses, encoded as search constraints.

CONFIDENCE NOTE (read before trusting either constraint set below):
Krishna's birth details are consistently repeated across Puranic sources
(Vishnu Purana, Bhagavata Purana, Harivamsa) with LOWER textual variance
than Rama's Bala Kanda verses on the calendar/nakshatra particulars, but
they carry far LESS astronomical detail -- there's no five-planet
exaltation story here, just a tithi + nakshatra + time-of-day, and it
has NOT been checked against a Sanskrit source the way the war-omen
verses below now have been. The war "omen" verses (Udyoga/Bhishma Parva)
are the opposite: richer in planetary detail, and as of 2026-09-20 both
`war_omen_profile_bhishma_parva` and `war_omen_profile_udyoga_parva`
have been checked shloka-by-shloka against Sanskrit critical/reader
editions (GRETIL for Bhishma Parva, a Devanagari reader edition for
Udyoga Parva) -- see the detailed per-verse notes below. That checking
process caught real errors in the first (English-translation-only)
version of this module twice over, which is the whole reason it's worth
doing rather than trusting a paraphrase.

KRISHNA'S BIRTH, paraphrased: born at midnight, on the eighth tithi
(Ashtami) of the dark half (Krishna paksha), with the Moon in Rohini
nakshatra. The month is usually given as Bhadrapada, though some
traditions say Shravana -- this project encodes Bhadrapada as the
default and flags the ambiguity rather than picking silently. Sun in
Simha is a commonly added detail (roughly consistent with Bhadrapada
month in the sidereal solar calendar) but is corroborating, not from the
core birth story itself.

WHY THIS WON'T PICK A YEAR BY ITSELF: unlike Rama's five-exalted-planet
conjunction (rare enough to recur only once every few millennia), Rohini
+ Ashtami + Krishna-paksha + midnight is a purely calendar-cyclical
combination -- tithi and nakshatra both cycle every lunar month, so this
configuration recurs roughly once a YEAR, not once a millennium. Expect
one candidate per year across the whole searched range, not a short
list. Pinning an actual year needs either additional distinguishing
detail (which this project doesn't have a confident source for yet) or
cross-reference to a separately-dated event, most plausibly the
Mahabharata war itself (traditionally ~89-90 years after Krishna's
birth) via its own, richer verses.

MAHABHARATA WAR OMENS -- citation-checked against the actual Sanskrit
critical edition (2026-09-19, via GRETIL's Bhismaparvan text,
mbh_06_u.htm), not just an English translation. This REPLACES an
earlier version of this module built from English-translation sources,
which got two things wrong: (1) it treated "Mars wheeleth towards
Magha" as having no retrograde component, when the Sanskrit
(06,003.013c: "maghāsu aṅgārakaḥ vakraḥ, śravaṇe ca bṛhaspatiḥ" -- "in
Magha, Mars is retrograde; and in Shravana, Jupiter") makes
Mars-retrograde-in-Magha and Jupiter-in-Shravana one unified statement,
not two separately-optional details; (2) it required a Ketu-Jyeshtha
and Rahu-Chitra/Swati placement SIMULTANEOUSLY, which is geometrically
close to impossible -- Rahu and Ketu are always exactly 180 degrees
apart, but Jyeshtha and Chitra/Swati are only ~53 degrees apart, so
requiring both at once (as the old code did) was asking for something
that can basically never happen. That fully explains why that variant
always scored 0 -- it wasn't underpowered, it was constructed wrong.

**Bhishma Parva 06,003 (Vyasa's narration to Dhritarashtra -- the
user's "Bhishma Parva 2-3" citation), verified shloka by shloka**:
- 06,003.013c-d: "maghāsu aṅgārakaḥ vakraḥ, śravaṇe ca bṛhaspatiḥ" --
  Mars RETROGRADE in Magha, and Jupiter in Shravana, as one clause.
- Shani afflicting Rohini (separately attested, already correctly
  encoded from the start).
- 06,003.015: "śyāmo grahaḥ ... ākramya jyeṣṭhām tiṣṭhati" -- "the dark
  planet ... having entered Jyeshtha, stands there." "Dark/śyāma" as a
  node epithet is ambiguous between Rahu and Ketu across different
  texts (unlike the earlier English-derived reading, which confidently
  called this "Ketu" -- that confidence wasn't warranted). Encoded
  generically as "a node" (checks Rahu OR Ketu, whichever is closer)
  rather than committing to one.
- 06,003.011c: "śveto grahas ... citrām samatikramya tiṣṭhati" -- "a
  white planet ... having crossed over Chitra, stands there" -- the
  OTHER node, at a DIFFERENT nakshatra. Given the 180-degree Rahu/Ketu
  relationship, this is almost certainly describing a different moment
  within the same extended omen narration, not the same instant as the
  Jyeshtha placement -- consistent with the omens describing a run-up
  period of months, not one frozen instant. NOT required simultaneously
  with the Jyeshtha node placement; not encoded as a joint constraint.
- 06,003.017a: "vakrānuvakraṃ kṛtvā ca śravaṇe pāvakaprabhaḥ" -- "having
  made retrograde-then-direct-then-retrograde motion [a full retrograde
  loop], the fire-bright one [Mars, by its traditional color epithet]
  in Shravana" -- a SECOND, later Mars detail: Mars completing a full
  retrograde loop specifically at Shravana (not Magha). Encoded
  separately as war_omen_profile_bhishma_parva_mars_circuitous_variant,
  since it's textually a different moment than 013c's Mars-in-Magha.
- "Such strange eclipses, both lunar and solar, forebode a great
  slaughter" -- the eclipse-pair detail; see the caveat below.

**Udyoga Parva 5.141 (Karna's speech to Krishna -- the user's "ch.
141-143" citation), now ALSO Sanskrit-verified (2026-09-20), via a
Devanagari reader edition (rikamrit.com) since GRETIL's own Udyoga
Parva page was too large for a single targeted fetch to reach adhyaya
141 (it only rendered through ~adhyaya 22 before hitting the fetch
tool's own processing limit)**:
- 5.141.7: "prājāpatyaṃ hi nakṣatraṃ ... śanaiścaraḥ pīḍayati" -- Saturn
  afflicts the "Prajapatya" nakshatra. Prajapati/Brahma is Rohini's
  presiding deity in the standard nakshatra-deity list, so this is the
  same Shani-Rohini claim as Bhishma Parva, independently confirmed.
- 5.141.8: "kṛtvā ca aṅgārakaḥ vakraṃ jyeṣṭhāyāṃ madhusūdana, anurādhāṃ
  prārthayate" -- "Mars, having gone retrograde IN Jyeshtha, O
  Madhusudana, now approaches/seeks Anuradha." This is ONE continuous
  event, not an ambiguous choice between two nakshatras as the earlier
  (pre-Sanskrit-check) secondary-source summary made it sound: Mars is
  retrograde, positioned in Jyeshtha, and moving toward Anuradha
  *because* retrograde motion runs backward through the zodiac and
  Anuradha (nakshatra 16) precedes Jyeshtha (17) in normal order --
  the direction is exactly consistent with real retrograde motion. This
  CORRECTS the previous encoding of this module, which had Mars-at-
  Jyeshtha right but was missing the retrograde requirement entirely.
- 5.141.9: "citrāṃ pīḍayate grahaḥ" -- "a planet afflicts Chitra." The
  planet is genuinely unnamed in this verse itself (not a translation
  gap on my part) -- not encoded, same as before, but now confirmed
  the earlier "Mahapat" identification was some kind of secondary-
  source or OCR artifact, not a real name in the primary text.
- 5.141.10: "rāhur arkam upaiṣyati" -- "Rahu approaches the sun" --
  confirmed real, still not encoded (no orb given).

Both `war_omen_profile_bhishma_parva` and `war_omen_profile_udyoga_parva`
are now Sanskrit-verified to the same standard.

EclIPSE-PAIR CAVEAT: checked the "two eclipses ~13 days apart" claim
against real syzygy geometry (eclipses.py) before encoding it as a
constraint here, and it turned out NOT to be a useful discriminator:
the minimum possible gap between a solar and lunar eclipse in the same
eclipse season is ~13.9 days (never exactly 13, in any era checked), and
such pairs occur about 2.9 times per year on average -- i.e. nearly
every year in history has one. So this detail is NOT included as a
SearchProfile constraint; it's checked separately with
has_close_eclipse_pair() as a sanity/context annotation only, not as a
filter that meaningfully narrows anything.
"""

from starcharts.ascendant import ascendant_position, local_midnight_jd_ut
from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.constraints import (
    EitherNodeNakshatraConstraint,
    NakshatraConstraint,
    RashiConstraint,
    RetrogradeConstraint,
    TithiConstraint,
)
from starcharts.eclipses import find_close_eclipse_pairs
from starcharts.engine import SearchProfile
from starcharts.ephemeris import to_julian_day_ut_astro
from starcharts.rashi import rashi_matches

MATHURA_LATITUDE = 27.4924
MATHURA_LONGITUDE = 77.6737

_SIMHA = 4
_VRISHABHA = 1
_ROHINI_NAKSHATRA = 3
_MAGHA_NAKSHATRA = 9
_JYESHTHA_NAKSHATRA = 17
_SHRAVANA_NAKSHATRA = 21
_ASHTAMI_KRISHNA_PAKSHA_TITHI = 23  # 15 (Shukla count) + 8


def krishna_birth_profile(
    start_astronomical_year: int,
    end_astronomical_year: int,
    tolerance_degrees: float = 1.5,
    include_surya_simha: bool = True,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
) -> SearchProfile:
    """Rohini nakshatra (Moon) + Ashtami Krishna-paksha tithi, optionally
    with Sun in Simha as corroborating (not core-story) detail. Expect
    roughly one candidate per year -- see module docstring."""
    constraints = [
        NakshatraConstraint("Chandra", _ROHINI_NAKSHATRA, tolerance_degrees),
        TithiConstraint(_ASHTAMI_KRISHNA_PAKSHA_TITHI, tolerance_degrees),
    ]
    if include_surya_simha:
        constraints.append(RashiConstraint("Surya", _SIMHA, tolerance_degrees))
    return SearchProfile(start_astronomical_year, end_astronomical_year, tuple(constraints), ayanamsha)


def lagna_matches_vrishabha_at_midnight(
    astronomical_year: int,
    month: int,
    day: int,
    tolerance_degrees: float = 1.5,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    proleptic_julian_calendar: bool = False,
) -> tuple[bool, float]:
    """Some (later, less universally attested than Rama's Karka lagna)
    traditions add a Vrishabha lagna at Krishna's birth. Checked at local
    midnight in Mathura, same pattern as ramayana.lagna_matches_at_noon."""
    jd_midnight = local_midnight_jd_ut(
        astronomical_year, month, day, MATHURA_LONGITUDE, proleptic_julian_calendar
    )
    position = ascendant_position(jd_midnight, MATHURA_LATITUDE, MATHURA_LONGITUDE, ayanamsha)
    matches = rashi_matches(position.sidereal_longitude, _VRISHABHA, tolerance_degrees)
    return matches, position.sidereal_longitude


def war_omen_profile_bhishma_parva(
    start_astronomical_year: int,
    end_astronomical_year: int,
    tolerance_degrees: float = 2.0,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    include_node_at_jyeshtha: bool = True,
) -> SearchProfile:
    """Bhishma Parva 06,003.013 reading, Sanskrit-verified -- see module
    docstring. Shani near Rohini, Mangala RETROGRADE at Magha, Guru at
    Shravana (013c-d is one unified clause: retrograde is not optional
    here), and (if include_node_at_jyeshtha) a node (Rahu or Ketu,
    whichever fits -- see docstring) near Jyeshtha per 06,003.015. Does
    NOT also require a node near Chitra (06,003.011c) simultaneously --
    that's a different node, and geometrically can't coincide with the
    Jyeshtha placement for the same Rahu/Ketu pair; almost certainly a
    separate moment in the same extended omen narration."""
    constraints = [
        NakshatraConstraint("Shani", _ROHINI_NAKSHATRA, tolerance_degrees),
        NakshatraConstraint("Mangala", _MAGHA_NAKSHATRA, tolerance_degrees),
        RetrogradeConstraint("Mangala", retrograde=True),
        NakshatraConstraint("Guru", _SHRAVANA_NAKSHATRA, tolerance_degrees),
    ]
    if include_node_at_jyeshtha:
        constraints.append(EitherNodeNakshatraConstraint(_JYESHTHA_NAKSHATRA, tolerance_degrees))
    return SearchProfile(start_astronomical_year, end_astronomical_year, tuple(constraints), ayanamsha)


def war_omen_profile_bhishma_parva_mars_circuitous_variant(
    start_astronomical_year: int,
    end_astronomical_year: int,
    tolerance_degrees: float = 2.0,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
) -> SearchProfile:
    """Sanskrit-verified (2026-09-19) against GRETIL's Bhismaparvan text,
    06,003.017a: "vakrānuvakraṃ kṛtvā ca śravaṇe pāvakaprabhaḥ" -- "having
    made a full retrograde loop [direct-retrograde-direct], the
    fire-bright one [Mars, by its traditional color epithet] in
    Shravana." A textually DIFFERENT moment than 013c's Mars-retrograde-
    at-Magha (encoded in war_omen_profile_bhishma_parva) -- this is Mars
    completing a retrograde loop later, specifically at Shravana, which
    is also where 013c already placed Jupiter. Encoded as Shani-Rohini +
    Mangala-Shravana (retrograde) + Guru-Shravana, as its own variant
    rather than merged into the Magha reading."""
    constraints = (
        NakshatraConstraint("Shani", _ROHINI_NAKSHATRA, tolerance_degrees),
        NakshatraConstraint("Mangala", _SHRAVANA_NAKSHATRA, tolerance_degrees),
        RetrogradeConstraint("Mangala", retrograde=True),
        NakshatraConstraint("Guru", _SHRAVANA_NAKSHATRA, tolerance_degrees),
    )
    return SearchProfile(start_astronomical_year, end_astronomical_year, constraints, ayanamsha)


def war_omen_profile_udyoga_parva(
    start_astronomical_year: int,
    end_astronomical_year: int,
    tolerance_degrees: float = 2.0,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
) -> SearchProfile:
    """Sanskrit-verified (2026-09-20) against Mahabharata 5.141.7-8.
    Shani afflicting the "Prajapatya" nakshatra (Rohini's Vedic deity --
    same claim as Bhishma Parva, independently confirmed), and Mangala
    RETROGRADE in Jyeshtha (5.141.8: "kṛtvā ca aṅgārakaḥ vakraṃ
    jyeṣṭhāyāṃ" -- the retrograde requirement was missing from the
    previous version of this function; verse 8 also has Mars then
    approaching Anuradha as a consequence of that retrograde motion,
    not encoded as a separate simultaneous placement since it's the
    same single continuous event). Does not include the unnamed-planet-
    at-Chitra (5.141.9) or Rahu-near-Sun (5.141.10) details -- both
    real in the source but not specific enough to encode as constraints."""
    constraints = (
        NakshatraConstraint("Shani", _ROHINI_NAKSHATRA, tolerance_degrees),
        NakshatraConstraint("Mangala", _JYESHTHA_NAKSHATRA, tolerance_degrees),
        RetrogradeConstraint("Mangala", retrograde=True),
    )
    return SearchProfile(start_astronomical_year, end_astronomical_year, constraints, ayanamsha)


def has_close_eclipse_pair(
    astronomical_year: int,
    window_years: float = 1.0,
    min_gap_days: float = 13.0,
    max_gap_days: float = 15.6,
) -> bool:
    """Context annotation, NOT a discriminating filter -- see the
    module's eclipse-pair caveat. True for almost any year, since such
    pairs occur ~2.9 times/year on average in every era checked."""
    jd_start = to_julian_day_ut_astro(astronomical_year, 1, 1)
    jd_end = to_julian_day_ut_astro(astronomical_year + int(window_years) + 1, 1, 1)
    return len(find_close_eclipse_pairs(jd_start, jd_end, min_gap_days, max_gap_days)) > 0
