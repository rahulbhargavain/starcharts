# starcharts — Workplan

## Purpose

Given a set of "planet was in this zodiac arc" constraints (a Vedic *janam patri* /
textual sky description), search backward through history for candidate dates
when the real sky matched — correcting for precession, ayanamsha, calendar
conversion, and ephemeris accuracy. Long-term goal: apply this to the
Ramayana/Mahabharata planetary descriptions for Ram and Krishna, while being
honest about the method's actual resolving power.

## Architecture (5 layers)

1. **Ephemeris layer** — real planetary positions over time.
   - Backbone: JPL DE431 (~13,000 BCE–17,000 CE) via `skyfield` or
     `astropy` + `jplephem`.
   - Seven grahas = Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
     (naked-eye only; no Rahu/Ketu here — those are computed nodes, relevant
     later for eclipse constraints).
   - Flag growing uncertainty in lunar position the further back in time
     (secular acceleration); ΔT matters for weekday/eclipse timing, not for
     rashi-level resolution.

2. **Coordinate layer** — tropical → sidereal.
   - `sidereal_longitude = tropical_longitude - ayanamsha(date)`.
   - Use a real precession model (IAU 2006 / Vondrák), not a flat rate —
     precession rate itself drifts over a ~25,772-year cycle.
   - Ayanamsha must be a configurable parameter (Lahiri, Krishnamurti, Raman,
     Fagan-Bradley, ...) — different choices produce materially different
     answer-dates. Never hardcode one.

3. **Calendar layer** — text date (tithi, nakshatra, masa, paksha, era,
   sometimes weekday/ayana) → candidate Julian Day(s).
   - Needs a luni-solar reconstruction module, including intercalary
     (adhika) month handling, which itself varies by tradition/era and can
     be multi-valued.

4. **Search layer** — constraint satisfaction across millennia.
   - Coarse pass: use slow planets (Jupiter ~1 rashi/yr, Saturn ~2.5 yr/rashi)
     to prune the candidate era by orders of magnitude.
   - Refine: day-by-day within surviving windows using Moon + tithi +
     nakshatra (tithi ties Moon to Sun, making this the sharpest filter).
   - Apply rare discriminators last (retrograde/vakri mentions, eclipses) —
     these often collapse a candidate set to near-unique.
   - Output is a **ranked candidate list with confidence/uniqueness scores**,
     not a single date — sky configurations recur on multiple timescales.

5. **Reporting layer** — for each candidate: proleptic Gregorian date,
   sidereal positions of all 7 grahas, which constraints matched exactly vs
   approximately, and sensitivity analysis across ayanamsha choices.

## Build order

1. Ephemeris + ayanamsha + tropical→sidereal rashi conversion (core module).
2. Validate against a modern, known Panchang/chart before trusting anything
   on ancient dates.
3. Luni-solar calendar reconstruction (tithi/nakshatra/masa → JD).
4. Constraint search engine (coarse-to-fine, as above).
5. Apply to Ram/Krishna janam patri data — report as a candidate list with
   explicit caveats, not a single confident year.

## Known caveats to keep surfacing in output (not just this doc)

- Rashi-only (sign-level, 12-way) constraints are weak — cycles repeat across
  a multi-millennium search window, so rashi-only matches are rarely unique.
  Nakshatra-level (27-way) or tithi-tied constraints are what actually narrow
  things down.
- Existing scholarly attempts at this exact problem (Ramayana/Mahabharata
  dating) disagree by *thousands of years* depending on verse selection,
  translation of ambiguous rashi/nakshatra names, and ayanamsha choice — that
  spread is itself the finding, not a bug to engineer away.
- Circulating janam patris for Ram/Krishna are themselves later
  reconstructions built to match epic verses under someone's assumed
  ayanamsha/calendar — running them through this system mostly tests that
  reconstruction's internal consistency, not an independent astronomical
  measurement.

## Implementation notes (learned while scaffolding)

- Using **pyswisseph** (Swiss Ephemeris Python bindings), not raw JPL DE431 —
  it's the de facto standard in existing Vedic astrology software, has
  every ayanamsha built in, and needs no huge kernel download for the
  default (Moshier) model.
- Moshier's own valid range is only **~3002 BCE to ~3003 CE** (enforced by
  swisseph itself, raises `swisseph.Error` outside it) — this already
  excludes the traditional Kali Yuga epoch (3102 BCE). Anything older
  needs the full Swiss Ephemeris data files or JPL DE431 swapped in.
- Python's `datetime` cannot represent BCE years at all (min year is 1 CE),
  so the core API takes astronomical (signed) year numbers directly for
  anything before 1 CE (year 0 = 1 BCE, year -3101 = 3102 BCE) rather than
  routing through `datetime`.
- Default ayanamsha is Lahiri (India's civil/Panchang standard), but it's
  a swappable enum end-to-end — every chart function takes it as a
  parameter, never hardcoded. Also added the "true" star-anchored modes
  (`TRUE_CITRA`, `TRUE_REVATI`, `TRUE_MULA`, `TRUE_PUSHYA`) — see the
  ayanamsha caveat below.
- **Real correctness bug caught by manual cross-check, not by any test I'd
  already written**: the amanta masa name must come from the rashi the Sun
  transits *into* during that lunar month (the sankranti falling inside
  it), not the rashi it starts in. Naming by the start rashi silently gave
  "Phalguna" for the lunar month that was actually Chaitra (containing
  2024's Ugadi/Chaitra Shukla Pratipada, 2024-04-09) — off by one month,
  the kind of error that would corrupt every downstream search. Fixed in
  `masa.py`; the 2024-04-09 case is now a locked-in regression test.
  Lesson: structural/shape tests ("is this a valid rashi index") don't
  catch semantic bugs like this — only checking against a real published
  Panchang does. Validate any future calendar-adjacent code the same way.

## MIT-licensing alternatives considered (not adopted yet)

Checked two suggested alternatives to `pyswisseph` (whose underlying Swiss
Ephemeris is AGPL/dual-licensed) against actual PyPI metadata rather than
assumption:

- **libephemeris** — `AGPL-3.0-only`. Same restrictive license family;
  doesn't solve an MIT-licensing goal at all.
- **openephem** — genuinely `MIT`-licensed, built on `skyfield` + JPL
  kernels, already has a `vedic` module with `ayanamsa='lahiri'` support.
  Real, functional project. The catch: its default kernel (DE440) only
  covers 1550–2650 CE; reaching multi-millennium BCE dates needs DE441
  (a multi-GB download), unlike `pyswisseph`'s zero-download Moshier model.

**Decision**: stay on `pyswisseph` while this is research use for one
person. Revisit `openephem` + DE441 if/when this needs to be redistributed
to others under an MIT-compatible license.

## External audit notes (2026-09-19, via Gemini, evaluated point by point)

An external review flagged several real issues. Assessed each rather than
accepting wholesale:

- **Ayanamsha extrapolation beyond ~1000 BCE is unphysical** — legitimate.
  `swe.set_sid_mode`'s standard ayanamshas (Lahiri, Raman, Krishnamurti,
  Fagan-Bradley) are polynomial/linear-rate fits calibrated for the last
  few centuries; extrapolating them over millennia can drift multiple
  degrees. Mitigation already partly in place: the ayanamsha enum now
  includes swisseph's "true" star-anchored modes (`TRUE_CITRA`,
  `TRUE_REVATI`, `TRUE_MULA`, `TRUE_PUSHYA`), which track a real fixed
  star's measured position instead. **Action**: prefer a `TRUE_*` mode,
  not `LAHIRI`, for any search reaching past ~1000 BCE, and say so in
  reported output.
- **ΔT / lunar secular acceleration makes strict tithi/nakshatra boundaries
  overconfident past ~1500 BCE** — legitimate, and already partly
  addressed: `tithi_matches()` and `nakshatra_matches()` (this session's
  calendar-layer work) take a `tolerance_degrees` padding parameter instead
  of a hard boolean cutoff, precisely so the future search layer can widen
  the margin for older candidates rather than silently overstating
  precision.
- **Swiss Ephemeris file cutoffs (claimed: 5401 BCE–5402 CE for the `se1`/
  `sem`/`se2` data files) vs. JPL DE431/441** — the specific number is
  *unverified* here (not the same as the Moshier bound we did verify
  empirically: ~3002 BCE–3003 CE). Don't repeat that exact figure as fact
  without checking Astrodienst's own documentation first. The underlying
  point stands regardless: if a search ever needs to reach past what the
  installed SE data files (or Moshier) cover, `openephem`/JPL DE441 is the
  already-identified fallback (see above).
- **Calendar-layer inversion ("don't do text→JD forward calendar parsing;
  screen the ephemeris first, check tithi/nakshatra at candidate JDs, treat
  masa/paksha naming as corroborating only")** — correct, but for a more
  specific reason than "it's underdetermined": the *modern* amanta
  intercalation rule (masa named by the sankranti falling inside a lunar
  month; adhika = no sankranti inside) is itself a post-~500 CE
  (Siddhantic-era) convention. Pre-Aryabhata calendars (e.g. Vedanga
  Jyotisha's 5-year yuga cycle) intercalated on a different, mean-motion
  schedule. So a masa/paksha name reconstructed for a pre-500 CE candidate
  date may not mean what the ancient text-keeper meant by that name — this
  is now the explicit module-level caveat in `calendar.py` and `masa.py`.
  Tithi and nakshatra stay reliable much further back because they're
  direct angular measurements with no calendar-rule ambiguity, which is why
  `calendar.py` treats them as primary and masa/paksha as secondary,
  best-effort corroboration.
- **Refined coarse-to-fine search pipeline (Saturn/Jupiter monthly pass →
  Mars/nodes → Sun/Venus/Mercury daily → Moon sub-day, with Gaussian-decay
  scoring at boundaries)** — good, concrete design for the not-yet-built
  search layer (layer 4). Adopt this ordering when building it; the
  `tolerance_degrees` params already added to `tithi_matches`/
  `nakshatra_matches` are the hook a Gaussian-decay scorer would sit on top
  of, rather than the hard boolean cutoff they currently default to.
- The suggested typed `ArcConstraint`/`SearchProfile` data model (Graha
  enum, min/max sidereal longitude with wraparound, tolerance_deg,
  ayanamsha_system, tithi_index) is a reasonable shape for layer 4's public
  API — worth adopting close to as-proposed when that layer is built,
  rather than stringly-typed constraints.

## Status

Ephemeris + ayanamsha core (layer 1-2), calendar layer (layer 3, tithi/
masa/nakshatra with tolerance-aware matching), and the constraint search
engine (layer 4) are built and tested (22/22 passing) in `src/starcharts/`:

- `arcs.py` — shared degree-arc membership + Gaussian-decay scoring, used
  by rashi/nakshatra/tithi matching and by the engine's ranking.
- `constraints.py` — typed `RashiConstraint`/`NakshatraConstraint`/
  `TithiConstraint`/`RetrogradeConstraint`, each with `is_satisfied`
  (hard boolean, for pruning) and `score` (continuous, for ranking).
- `engine.py` — coarse-to-fine search: stages ordered slowest-to-fastest
  graha (Shani/Guru -> Mangala -> Surya/Shukra/Budha -> Chandra+tithi),
  each stage scanning at a fixed step size. (Those fixed steps turned out
  NOT to be safe -- see "Search engine could step over matches" at the
  end of this file; the engine now steps by proven speed bounds instead.)
  Verified against a known chart (recovers 2024-01-01
  from a full 2000-year and a ~6000-year search in well under a second)
  and against a deliberately impossible constraint (correctly returns no
  candidates without scanning to the fine stages).

A North-Indian diamond kundali SVG visualizer (`visualize.py`) and an
interactive HTML demo (`demo/graha_recurrence_map.html`, published at
https://claude.ai/artifact/CxrkHimfjCaBk2GQRsK7Rx) also exist. The demo
uses real `engine.search()` output (not synthetic data): every 1700-2300
CE date where Shani+Guru sit in 2024-01-01's rashi pair and the tithi
matches too, which visibly clusters into three ~59-60-year-apart eras --
a live demonstration of the "cycles repeat, output is a candidate list"
point this project keeps insisting on.

The reporting layer (layer 5) is also built and tested (27/27 passing):

- `report.py` — `generate_report`/`generate_reports` turn a raw
  `CandidateMatch` into a `CandidateReport`: proleptic BCE/CE date +
  weekday, the full 7-graha chart (not just the constrained grahas),
  tithi/masa, per-constraint match detail (`exact` vs `within tolerance`
  vs `NOT satisfied` -- exact is tested by re-running the same constraint
  with tolerance forced to 0), and a cross-ayanamsha sensitivity table
  (Lahiri/Raman/Krishnamurti/Fagan-Bradley/True Citra by default).
  `format_report_text` renders one as human-readable plain text.
- Sanity-checked against the known 2024-01-01 chart: all 5 default
  ayanamshas happened to agree on every rashi for that date even though
  their offsets differ by up to ~2.3 degrees, because no graha sits near
  a 30-degree boundary that day -- a real, concrete illustration of
  exactly when ayanamsha choice matters (boundary cases) and when it
  doesn't. Worth re-checking this on any actual Ram/Krishna candidate,
  since those are far more likely to straddle a boundary given the much
  larger ayanamsha drift that far back.

All five planned layers now exist.

## Ramayana Bala Kanda: first real constraint set (2026-09-19)

Encoded the traditionally-cited sky description of Rama's birth (Bala
Kanda, ~Sarga 18, ~verses 8-10 -- numbering/wording varies by edition,
content paraphrased in `texts/ramayana.py`'s docstring, not quoted
verbatim from any one translation): five grahas each in their sign of
exaltation (Surya-Mesha, Mangala-Makara, Shani-Tula, Guru-Karka,
Shukra-Meena), Moon in its own sign (Karka) and Punarvasu nakshatra,
Chaitra Shukla Navami tithi, and Karka lagna.

**Real gap this closed**: the engine had no ascendant/lagna support at
all. Lagna depends on birth *location* (unlike every graha, which is
geocentric) and moves ~2h/rashi -- far too fast for layer 4's date-level
coarse-to-fine scan. New `ascendant.py` + `constraints.AscendantConstraint`
handle it, but deliberately *outside* `engine.search()`'s staging:
checked once, at local noon in Ayodhya (the traditional birth time), on
whichever dates the graha/tithi search already found -- see both
modules' docstrings. This is the pattern to reuse for any other
location/time-of-day-specific textual detail (a named muhurta, an
eclipse visible from a specific place).

**Result**: searched the full ~3002 BCE-3003 CE Moshier range. At the
tolerance the other constraints have been using (1.5 degrees), nothing
survives with a nonzero combined score. Cross-checked with an independent
brute-force scan (bypassing engine.py's staging entirely, 15-day steps
across all 6000 years) to rule out a staging bug: the best any instant
achieves is 6 of 8 constraints exactly satisfied, with the remaining two
(Shukra's rashi and the tithi) sitting at essentially zero and not
improving within +/-45 days of that point -- not a near-miss, a genuine
non-match. Progressively widening tolerance to 3/5/8 degrees (well past
what any of this project's other searches have used) still only reaches
combined scores of 0.013/0.407/0.704 at best. **This configuration does
not occur anywhere in the ~3000 BCE-3000 CE range**, at any tolerance
worth calling a match.

That's consistent with -- though it doesn't prove -- the traditional
placement of this configuration around 5114 BCE (Pushkar Bhatnagar's
planetarium-based figure), which is outside the Moshier range entirely.
**This result cannot currently be checked either way**: not "the
tradition is wrong," not "the tradition is confirmed" -- just "our
current ephemeris can't reach far enough back to test it." The
already-tracked ephemeris swap (openephem + JPL DE441, see the
MIT-licensing section above) is the concrete next step if actually
testing ~5114 BCE matters enough to justify that download.

**Correction (2026-09-19)**: the line above ("Lagna=Karka is weak
corroboration") was wrong for this specific case, caught via external
review and verified by direct computation. At local noon the Sun sits
at the Midheaven by definition; at Ayodhya's latitude the Ascendant runs
~93-95 degrees ahead of the Midheaven (not exactly 90, but close). So
once Surya-in-Mesha already holds at noon, Karka-lagna follows from it
almost automatically at this latitude -- it is NOT independent evidence
on top of the Surya constraint, and treating it as corroboration
double-counts one piece of information as two. See the correction note
in `texts/ramayana.py`'s module docstring.

The same review also worked through the verse's lunar geometry (Surya
Mesha + Chandra Karka/Punarvasu + Chaitra Shukla Navami) by hand and
concluded these are mutually exclusive by 16-31 degrees -- which would
explain the zero matches on its own. Checked this against the actual
computed data: it rests on a nakshatra-boundary error -- using Ardra's
span (66.67-80.0 degrees) for Punarvasu, when Punarvasu is actually
80.0-93.33 degrees (confirmed against `constants.py` and standard
tables; Ardra is the nakshatra immediately before it). With
the correct boundary the real gap is ~2.67 degrees, not 16-31 -- and a
real computed near-miss (1042 CE, from the earlier brute-force scan)
shows Surya-Mesha and Chandra-Punarvasu holding *simultaneously* with
scores of 1.0/1.0 each, directly contradicting "mutually exclusive."
What actually fails at that instant is the tithi. So: a real but narrow
lunar-geometry tension exists (confirmed), it is not the 16-31 degree
"structural gulf" claimed, and it is not what's driving the zero-match
result across the full search -- widening tolerance to 8 degrees (far
more than needed to bridge 2.67 degrees) still only reaches combined
score 0.70, meaning the actual bottleneck across history is the
independent five-slow-planet conjunction (Mangala/Shani/Guru/Shukra
rarely aligning simultaneously), not the lunar geometry.

## Ephemeris extended to ~5400 BCE (2026-09-19)

Downloaded the real Swiss Ephemeris data files (not Moshier) covering
~5400-2400 BCE: `seplm30/36/42/48/54.se1` + `semom` equivalents from the
public Swiss Ephemeris GitHub repo, into `ephe/` (binary, gitignored;
`ephe/download.sh` fetches them, `ephe/README.md` explains the naming
convention and how to reach further back). Total download: ~9.5MB, not
the multi-GB DE441 the `openephem` path would have needed.

`ephemeris.graha_position`, `panchanga.tropical_longitude`, and
`ascendant.ascendant_position` all now try Moshier first (fast, no
files) and **automatically fall back** to the real data files
(`SEFLG_SWIEPH`) on `swisseph.Error`, rather than requiring the caller to
know which model a given date needs. `Position`/`AscendantPosition` both
gained an `ephemeris_model` field ("moshier" or "swieph") so any report
can show which one actually computed a given placement -- this matters
because Moshier is an analytical approximation and the real data files
are not, and that distinction is worth surfacing, not hiding.

**Reran the Bala Kanda search (previous section) across the now-real
~5400 BCE-3000 CE range: still nothing above ~0 combined score at 1.5
degree tolerance.** A direct spot-check at the specific date commonly
attributed to Bhatnagar (10 January 5114 BCE) also didn't match well
under Lahiri ayanamsha -- but I'm flagging real uncertainty here rather
than treating that as a refutation: I don't have high confidence in
exactly which calendar convention (Julian vs. proleptic Gregorian),
ayanamsha, or software defaults Bhatnagar's original analysis used, and
a single spot-check is much weaker evidence than the systematic
range search. The systematic search's negative result stands on its
own regardless of that spot-check's ambiguity: the six-constraint
configuration this project encoded from the verse does not occur
anywhere in ~5400 BCE-3000 CE, at any tolerance up to 8 degrees (per the
earlier tolerance-widening test). That's a real, checkable finding, not
proof the tradition is wrong -- it could equally mean the verse's
"exalted" language was never meant as an exact simultaneous rashi-level
conjunction, or that further-back dates (or a different ayanamsha
assumption) would find it. Both remain open.

## Testing the "Surya may not be one of the five" hypothesis (2026-09-19)

External review raised a genuinely testable point I can't verify
independently (a claim about the root shloka's exact wording and which
five grahas it names) but could act on regardless: added
`require_surya_exalted=False` to `bala_kanda_birth_profile`, dropping
just the Surya-in-Mesha constraint and keeping everything else.

**Result: exactly one match across the entire ~5400 BCE-3000 CE range,
5 January 4498 BCE, combined score 1.000 on all 7 remaining
constraints** (Mangala-Makara, Shani-Tula, Guru-Karka, Shukra-Meena,
Chandra-Karka, Chandra-Punarvasu, Chaitra Shukla Navami all exact). That
rarity (one hit in 8400 years) is itself informative -- it's not a
trivially common configuration.

But it doesn't hold up as *the* candidate:
- **Fails the Karka-lagna check outright.** Verified this isn't an
  hour-of-day artifact by checking both the matched instant (local
  ~05:30) and true local noon: Ascendant is 329.6 degrees (Meena) and
  85.8 degrees (Mithuna) respectively -- nowhere near Karka (90-120)
  either way. Surya sits in Meena here, not Mesha, so the Surya-at-noon
  to Karka-lagna coupling documented above doesn't apply and nothing
  else pulls the Ascendant there.
- **Ayanamsha-fragile at this depth.** Lahiri/Raman/Krishnamurti/True
  Citra roughly agree (offsets 292.8-294.4 degrees), but Fagan-Bradley
  disagrees enough to flip 2 of 7 placements (Chandra to Mithuna,
  Shukra to Kumbha) -- a concrete instance of the ayanamsha-extrapolation
  caveat from the earlier external audit: 6800 years from any
  ayanamsha's calibration epoch is far enough that which precession
  model you trust starts changing the answer.
- **Doesn't match the popularly-cited ~5114 BCE either.**

Net assessment: a genuine, rare, worth-recording candidate under the
"Surya not required" reading, but not one to present as an answer --
it fails an independent detail from the same verse (Lagna) and isn't
robust to ayanamsha choice. Recorded here rather than discarded, in
case it's useful context for whoever resolves the underlying textual
question about which five grahas the verse actually names.

## Krishna/Mahabharata: first constraint sets (2026-09-19)

`texts/mahabharata.py` -- two separate profiles, with explicitly
different confidence levels attached (see the module docstring for the
full reasoning):

- `krishna_birth_profile`: Rohini nakshatra + Ashtami Krishna-paksha
  tithi (+ optional Sun-in-Simha corroboration). Textually well-attested
  across Puranic sources, but thin astronomically -- no multi-planet
  story like Rama's. **Quantified the "this can't pin a year alone"
  caveat rather than just asserting it**: searched -3000 to +3000 (6000
  years) at 0.5-degree tolerance and got **12,019 high-scoring
  candidates** -- roughly one per year, exactly as expected for a
  purely calendar-cyclical (not rare-conjunction) combination. Pinning
  an actual year needs either more distinguishing detail or
  cross-reference to the war (traditionally ~89-90 years after Krishna's
  birth).
- `war_omen_profile`: Saturn near/afflicting Rohini nakshatra + Mars
  retrograde, from commonly-repeated secondary-source descriptions of
  the war's planetary omens (Udyoga/Bhishma Parva). **Explicitly lower
  confidence than every other constraint set in this project** -- more
  textual variance across editions, and weaker recollection confidence
  on my part re: exact planet-nakshatra pairings. Flagged as a rough
  first pass to refine against an actual citation, not a trustworthy
  encoding yet. Searched the same 6000-year range at 2-degree tolerance:
  **154 distinct epochs** (~one every 39 years on average, driven mostly
  by Saturn's ~29.5-year cycle through Rohini's narrow nakshatra arc,
  modulated by whether Mars happens to be retrograde) -- far more
  selective than the birth-alone search, but still nowhere near unique
  on its own.

Also added `ascendant.local_midnight_jd_ut` (generalizing
`local_noon_jd_ut` into `local_time_jd_ut`) since Krishna's birth is
traditionally at midnight, not noon, and a Mathura-based
`lagna_matches_vrishabha_at_midnight` check analogous to Rama's Karka
one -- flagged as even less universally attested across traditions than
Rama's lagna claim.

## Eclipse-pair claim checked against real syzygy geometry (2026-09-19)

Added `eclipses.py`, using swisseph's own eclipse-finding routines
(`sol_eclipse_when_glob`/`lun_eclipse_when`) rather than a hand-rolled
node-elongation approximation -- this is the one detail in this project
that genuinely needs real syzygy/node geometry, not a sign-level
rashi/nakshatra check.

**Checked the "two eclipses ~13 days apart" claim before encoding it as
a constraint, and it turned out not to be useful as one**: the minimum
possible gap between a solar and lunar eclipse in the same eclipse
season is ~13.9 days -- a literal 13 never occurs, in any era checked
(modern or ~3200 BCE). And such pairs occur ~2.9 times per year on
average, in every era -- essentially every year in history has one.
So `has_close_eclipse_pair()` exists as a context annotation, not a
SearchProfile constraint: it would add close to zero discriminating
power if used as a filter, and treating it as a strong signal (as
popular secondary sources sometimes do) overstates what the astronomy
actually supports.

## War-omen constraint sets built and tested against the 4 commonly-
## debated candidate years (2026-09-19)

Built `war_omen_profile` (Shani near/in Rohini nakshatra + Mangala
retrograde, already existing) and a second, independently-guessed
`war_omen_profile_lingering_variant` (Guru retrograde near Jyeshtha +
Mangala retrograde near Anuradha -- a different reading of the
"lingering near Vishakha/Jyeshtha" detail). Both remain explicitly
LOW CONFIDENCE per the module docstring -- neither is verified against
a primary-source citation.

Tested both, plus the (non-discriminating) eclipse-pair check, against
+/-3-year windows around the four candidate years the user named:

| Candidate year | Shani-Rohini + Mangala-retro | Lingering variant | Eclipse pair present |
|---|---|---|---|
| 3137 BCE (traditional/Aihole) | 0.000 | 0.000 | True (non-discriminating) |
| **3067 BCE (Achar)** | **1.000** | 0.000 | True (non-discriminating) |
| **2449 BCE** | **1.000** (at 2448 BCE) | 0.000 | True (non-discriminating) |
| 1478 BCE | 0.451 (Shani close but outside tolerance; Mangala retrograde confirmed) | 0.000 | True (non-discriminating) |

The two perfect-score hits are tightly localized, not spread across the
whole 6-year search window: 3067 BCE matches on 1-5 April of that exact
year; 2448 BCE matches on 12-17 June. Given the base rate for this
constraint combination is ~154 distinct epochs across 6000 years (~one
every 39 years, established earlier), two independent hits landing
right on two of four externally-proposed candidate years is a genuinely
notable (though not remotely conclusive) result -- it's the kind of
corroboration worth recording, not proof, since the underlying omen
encoding is still unverified against a primary source and the
lingering-variant guess found nothing at any of the four.

## War-omen verses citation-checked against primary sources (2026-09-19)

Used WebSearch/WebFetch to check the previous guessed encoding against
the actual public-domain Kisari Mohan Ganguli translation (cross-checked
two independently-OCR'd copies against each other, since one had heavy
scan corruption). **The earlier guesses were wrong** and have been
replaced in `texts/mahabharata.py`:

- Confirmed correct: Shani (Saturn) near/afflicting Rohini nakshatra.
- Wrong, now corrected: Guru was guessed near Vishakha/Jyeshtha; the
  Bhishma Parva text actually says Guru approaches **Shravana**, and
  Mangala (not Guru) approaches **Magha**. Jyeshtha in that passage
  belongs to **Ketu**, not Guru or Mangala as guessed.
- New capability added because of this: `nodes.py` + `NodeNakshatraConstraint`
  for Rahu/Ketu (mean lunar node; Ketu = Rahu + 180 degrees exactly).
  These were deliberately excluded from the seven physical grahas in
  `constants.py`, correctly, but several omen verses name them
  specifically, so they needed their own small module rather than
  forcing them into GRAHAS. Folded into `engine.py`'s "mars" stage
  (20-day step; safe for the node's ~251-day-per-nakshatra dwell).

**Real, load-bearing finding: the omen catalogue itself varies by
speaker/parva, not just by my transcription error.** Bhishma Parva
(Vyasa's narration) and Udyoga Parva (Karna's speech) give DIFFERENT
specifics for where Mars is headed (Magha vs. Anuradha/Jyeshtha) while
agreeing on Shani-Rohini. That's textually real (expected for an
oral-tradition epic compiled over time), not something to force into
one merged profile -- hence two separate functions,
`war_omen_profile_bhishma_parva` and `war_omen_profile_udyoga_parva`,
with different confidence levels (Bhishma Parva verified against the
primary translation directly; Udyoga Parva still resting on
secondary-source summaries).

**Results against the four candidate years (+/-3 year windows):**

| Candidate | Bhishma Parva (Shani-Rohini + Mangala-Magha + Guru-Shravana) | Udyoga Parva (Shani-Rohini + Mangala-Jyeshtha) |
|---|---|---|
| 3137 BCE | 0.000 | 0.000 |
| **3067 BCE (Achar)** | 0.000 | **1.000** (23 Jun - 14 Jul, -3066) |
| 2449 BCE | 0.000 | 0.026 |
| **1478 BCE** | 0.000 | **1.000** (26 Aug - 14 Sep, -1475, i.e. 1476 BCE) |

The Bhishma Parva profile (three simultaneous slow-planet nakshatra
placements) is much more restrictive and found nothing within +/-3
years of any of the four -- would need a systematic wide-range search
to find where it DOES occur, not yet done. The Udyoga Parva profile (two
constraints, no retrograde requirement) hit two of the four cleanly.

**But that result doesn't survive adding Mars retrograde.** The Bhishma
Parva text's "wheeleth towards" phrasing doesn't explicitly say
retrograde for the Mars-Magha detail (a separate passage describes Mars
"wheeling circuitously" near Shravana instead -- itself attributed to a
different planet than the Guru-Shravana reading above, more textual
tangle). Checked anyway: adding a Mars-retrograde requirement to the
Udyoga Parva profile drops the 8400-year hit count from 159 epochs to
just **11, spaced with striking regularity ~442 years apart** -- and
NEITHER 3067 BCE nor 1478 BCE is among them (nearest are 5070 BCE and
857 BCE). So which of these two readings is right hinges on a real,
unresolved textual question (is retrograde motion actually implied by
"wheeleth towards," or is that reading too strict) -- flagging this
honestly rather than reporting only the flattering version.

## Bhishma Parva profile: wide-range search (2026-09-19)

Ran the full ~8400-year sweep (previously only checked in narrow
+/-3-year windows around the four candidate years):

**Without the Rahu/Ketu constraints** (Shani-Rohini + Mangala-Magha +
Guru-Shravana only): just **6 distinct epochs** in ~8400 years --
markedly rarer than the Udyoga Parva profile's 159, as expected for a
3-way vs. 2-way simultaneous slow-planet conjunction. None land near
any of the four candidate years:

| Epoch | Nearest candidate year | Gap |
|---|---|---|
| 5394-5393 BCE | -- | -- |
| 4540-4539 BCE | -- | -- |
| 3449-3448 BCE | 3137 BCE / 3067 BCE | ~310-380 years |
| 1800-1799 BCE | 1478 BCE | ~321 years |
| 946-945 BCE | -- | -- |
| 151-150 BCE | -- | -- |

**With the Rahu/Ketu constraints added**: zero matches anywhere in the
full range, including at all 6 epochs above. Checked this isn't hiding
a bug by inspecting per-constraint scores at each of the 6 epochs
directly: Shani/Mangala/Guru all score 0.95-1.0 as expected, but Ketu
scores a flat 0.0 at every single one (not a near-miss), while Rahu
comes close once (0.861 at 1799 BCE) and is near-zero elsewhere. Given
this is now a 4th independent, faster-moving body's narrow arc stacked
on an already-rare 3-way conjunction, a 0-for-6 hit rate is not
statistically surprising on its own (expected hits under independence
is well under 1) -- this null result doesn't confirm or rule out the
Ketu/Rahu detail, it's just an underpowered check given only 6 samples
to test it against.

Net picture: neither Bhishma Parva reading (with or without nodes)
lands near any of the four externally-proposed candidate years, in
contrast to the Udyoga Parva profile's two clean hits (3067 BCE, 1478
BCE) reported earlier -- itself caveated by the unresolved
Mars-retrograde question. The two primary-source readings of this
project's own encoding point in different directions, which is an
honest state to be in given the source material's own internal
variance, not a bug to resolve by picking the more flattering one.

## Mars-retrograde question resolved against the primary source (2026-09-19)

Could not reach an actual Sanskrit critical edition through the tools
available here -- Wikisource's API returned only page metadata, GRETIL
wasn't reachable via search, sacred-texts.com 403'd, mahabharataonline's
guessed URL 404'd. Fell back to a second English-translation source
(archive.org's scan of the same Ganguli translation) and searched it
specifically for retrograde/circuitous language around every Mars
reference, rather than assuming the earlier passage was exhaustive.

**This resolved the question, but not the way the previous ambiguity
assumed.** The primary-source English distinguishes TWO separate Mars
statements, not one ambiguous one:
- "Mars wheeleth towards Magha" -- plain directional language, no
  retrograde/circuitous wording. This is what `war_omen_profile_bhishma_parva`
  already encodes, and it turns out to be textually faithful as written.
- A DIFFERENT verse: "the red-bodied Mars ... wheeling circuitously,
  stayeth in a line with ... Sravana, over-ridden by Vrihaspati
  [Jupiter]" -- THIS is where the retrograde-like language actually
  lives, and it places Mars together with Jupiter near **Shravana**,
  not Magha.

So the previous session's test (bolting a bare Mars-retrograde
requirement onto the Udyoga Parva Jyeshtha reading) was testing a
hybrid that doesn't correspond to any single verse's actual claim. The
real third reading this reveals -- Shani-Rohini + Mangala-Shravana +
Mangala-retrograde + Guru-Shravana (Mars and Jupiter conjunct near
Shravana, Mars circuitous) -- is now `war_omen_profile_bhishma_parva_mars_circuitous_variant`.

**Result**: this is the rarest constraint set in the entire project --
just **1 epoch in ~8400 years (882 CE)** -- and it lands nowhere near
any of the four candidate years (nearest, 3137 BCE, is off by over
4000 years). Combined with the earlier findings, the honest overall
picture across all three Bhishma-Parva-family readings and the one
Udyoga Parva reading:

| Reading | Epochs in ~8400 yrs | Hits among the 4 candidates |
|---|---|---|
| Bhishma: Shani-Rohini + Mangala-Magha + Guru-Shravana | 6 | 0 |
| Bhishma: + Rahu/Ketu | 0 | 0 (underpowered, not a refutation) |
| Bhishma: Mars-circuitous variant (this session) | 1 | 0 |
| Udyoga: Shani-Rohini + Mangala-Jyeshtha (no retrograde) | 159 | 2 (3067 BCE, 1478 BCE) |

Every reading that's actually textually grounded in a specific verse's
exact wording misses all four candidates. The only reading that hits
two of them is also the loosest one (2 constraints, no retrograde) --
which is the expected direction for a false-positive-prone constraint,
not reassuring. That's the most defensible summary this project can
currently give: the primary-source omen verses, read carefully and
separately rather than merged into one convenient composite, don't
corroborate any of the four popularly-debated Mahabharata-war years.

## Reached the actual Sanskrit critical edition via GRETIL (2026-09-19)

GRETIL (gretil.sub.uni-goettingen.de) hosts the Mahabharata critical
edition text directly -- `mbh_06_u.htm` for Bhismaparvan. Reached it
this time (the earlier attempt didn't try GRETIL directly, only
secondary sources). Checked shloka-by-shloka rather than requesting
bulk text (the fetch tool declined a large verbatim block on fair-use
grounds, reasonably, for a scholarly resource marked "for reference
only" -- worked within that by asking narrow, targeted questions
instead).

**This overturned the previous session's conclusion, not confirmed it.**
06,003.013c-d reads: "maghāsu aṅgārakaḥ vakraḥ, śravaṇe ca bṛhaspatiḥ"
-- "in Magha, Mars is RETROGRADE; and in Shravana, Jupiter." That's one
unified clause. The earlier English-translation-only reading ("Mars
wheeleth towards Magha," treated as non-retrograde, with the retrograde
language assumed to belong to a separate Mars-near-Shravana verse) was
wrong: retrograde was already attached to the Magha placement in the
Sanskrit; the English translation just didn't preserve that clearly.
Fixed in `war_omen_profile_bhishma_parva`, which now requires Mangala
retrograde as part of the core reading, not a separate variant.

**A second error caught in the same pass**: 06,003.015 identifies the
node at Jyeshtha as "śyāmo grahaḥ" (the DARK planet), not the "white
planet" the earlier English-derived reading called Ketu. Color epithets
for Rahu/Ketu vary across texts and I don't have grounds to confidently
pick one over the other from this alone, so this is now
`EitherNodeNakshatraConstraint` (new, in `constraints.py`) -- checks
Rahu OR Ketu, whichever fits, rather than committing to Ketu specifically.

**A third, purely geometric error this also caught**: the previous
`include_nodes=True` variant required a node at Jyeshtha AND a node at
Chitra/Swati SIMULTANEOUSLY. Rahu and Ketu are always exactly 180
degrees apart; Jyeshtha and Chitra/Swati are only ~53 degrees apart.
Requiring both at once for the same Rahu/Ketu pair is asking for
something close to geometrically impossible -- which is why that
variant always scored 0. It wasn't underpowered, as guessed at the
time; it was constructed wrong. 06,003.011c's Chitra-node reference is
now understood as a different moment in the same extended omen
narration (consistent with the omens describing a months-long run-up,
not one instant), not a simultaneous requirement, and isn't encoded as
a joint constraint with the Jyeshtha placement.

**06,003.017a confirmed as a genuinely separate verse**: "vakrānuvakraṃ
kṛtvā ca śravaṇe pāvakaprabhaḥ" -- "having made a full retrograde loop,
the fire-bright one [Mars] in Shravana." This is
`war_omen_profile_bhishma_parva_mars_circuitous_variant`, and it really
is textually distinct from 013c (Mars at Magha) -- confirmed, not
merely inferred from an ambiguous English rendering.

**Recomputed results with the corrected encoding:**

| Reading | Epochs in ~8400 yrs | Hits among the 4 candidates |
|---|---|---|
| Bhishma 013c-d: Shani-Rohini + Mangala-Magha-RETROGRADE + Guru-Shravana | 1 (3449-3448 BCE) | 0 |
| + Jyeshtha node (Rahu or Ketu) | 0 | 0 (underpowered, 1 sample) |
| Bhishma 017a: Mars full retrograde loop + Jupiter, at Shravana | 1 (882 CE) | 0 |
| Udyoga (still English-summary-only, NOT Sanskrit-verified): Shani-Rohini + Mangala-Jyeshtha, no retrograde | 159 | 2 (3067 BCE, 1478 BCE) |

The picture is now sharper, not different in conclusion: every reading
that has been checked against the actual Sanskrit is rarer than
previously thought (1 epoch, not 6) and still misses all four
candidates. The only reading that hits two of them remains the one
that's (a) the loosest (no retrograde, 2 constraints) and (b) still
unverified against the Sanskrit -- exactly the profile most likely to
produce a false positive, and the one this session didn't get to check
at the primary-source level.

## Udyoga Parva verified against Sanskrit (2026-09-20)

GRETIL's own Udyoga Parva page (`mbh_05_u.htm`) was too large for the
fetch tool to reach adhyaya 141 in one targeted query (it only rendered
through ~adhyaya 22 before hitting the tool's own processing limit).
Found a Devanagari verse-level reader (rikamrit.com) instead and
verified 5.141.7-10 directly.

**This caught the same class of error as the Bhishma Parva check --
retrograde was missing, not the nakshatra**:
- 5.141.7: "prājāpatyaṃ hi nakṣatraṃ ... śanaiścaraḥ pīḍayati" -- Saturn
  afflicts the "Prajapatya" nakshatra. Prajapati/Brahma is Rohini's
  Vedic presiding deity, so this independently confirms the Shani-Rohini
  claim from a completely different parva/speaker.
- 5.141.8: "kṛtvā ca aṅgārakaḥ vakraṃ jyeṣṭhāyāṃ madhusūdana, anurādhāṃ
  prārthayate" -- "Mars, having gone RETROGRADE in Jyeshtha, now
  approaches Anuradha." One continuous event, not an ambiguous choice
  between two nakshatras: retrograde motion runs backward through the
  zodiac, and Anuradha (nakshatra 16) precedes Jyeshtha (17) in normal
  order, so "retrograde in Jyeshtha, heading toward Anuradha" is
  internally consistent astronomy, not two competing readings. The
  previous version of `war_omen_profile_udyoga_parva` had the nakshatra
  right (Jyeshtha) but was missing the retrograde requirement entirely
  -- exactly the same category of omission as the Bhishma Parva fix.
- 5.141.9: "citrāṃ pīḍayate grahaḥ" -- "a planet afflicts Chitra," planet
  genuinely unnamed in the verse itself. Confirms the earlier "Mahapat"
  identification from a secondary source was some kind of artifact, not
  a real name in the primary text. Still not encoded (nothing to encode).
- 5.141.10: "rāhur arkam upaiṣyati" -- Rahu approaches the sun, real and
  confirmed, still not encoded (no orb given).

**Recomputed with the retrograde requirement added**: drops from the
previous (wrong) 159 loose epochs across ~8400 years down to **11**,
spaced with striking regularity ~442 years apart -- and this is now the
textually-correct number, not the speculative "what if retrograde is
required" side-check from two sessions ago (which happened to land on
this same figure by coincidence, before the Sanskrit confirmed it was
the right question to ask). None of the 11 land within 300 years of any
of the four candidate years; nearest are ~5070 BCE and ~857 BCE.

## Final picture: all four textually-grounded readings checked, none corroborate any candidate year

| Reading | Sanskrit-verified? | Epochs in ~8400 yrs | Hits among the 4 candidates |
|---|---|---|---|
| Bhishma 013c-d: Shani-Rohini + Mangala-Magha-retrograde + Guru-Shravana | Yes | 1 | 0 |
| Bhishma 017a: Mars full retrograde loop + Jupiter, at Shravana | Yes | 1 | 0 |
| Udyoga 5.141.7-8: Shani-Rohini + Mangala-Jyeshtha-retrograde | Yes | 11 | 0 |

Every reading that exists in the primary Sanskrit text, checked
carefully rather than paraphrased, misses all four popularly-debated
Mahabharata-war years by hundreds to thousands of years. The readings
that used to "hit" (the pre-Sanskrit-check versions of both profiles)
did so specifically because they were missing a retrograde requirement
the Sanskrit turns out to require in both cases -- a real, repeatable
pattern of English-translation paraphrases dropping a technical
astrological term ("vakra") that changes the answer, not a coincidence.

This is the most defensible conclusion this project can currently
reach on the Mahabharata dating question: the omen verses, read
carefully against the actual Sanskrit, do not corroborate 3137 BCE,
3067 BCE, 2449 BCE, or 1478 BCE. That doesn't rule out some other year
this project hasn't checked, and it doesn't resolve whether the verses
were ever meant as precise simultaneous astronomy rather than
traditional/rhetorical omen-cataloguing -- but within its own terms,
the search has been run honestly and the answer is negative across the
board.

## Widened beyond the four candidates (2026-09-20)

Two genuinely different ways to widen the search, both run across the
full ~8400-year range rather than narrow windows around external
hypotheses:

**1. Where does each strict, Sanskrit-verified reading actually occur,
full stop?** (Not "does it hit year X" but "here is its complete
epoch list.") Already had these from the citation-check sessions, laid
out together for the first time:
- Bhishma 013c-d (Mars retrograde at Magha): **only 3449-3448 BCE**,
  once in the entire range.
- Bhishma 017a (Mars retrograde loop at Shravana): **only 882 CE**,
  once in the entire range.
- Udyoga 5.141.7-8 (Mars retrograde at Jyeshtha): 11 epochs, listed in
  the table above, ~442 years apart.

Cross-checked whether any of these ever land near each other (since the
text presents them as describing one extended run-up to one war, they
might be expected to cluster even though they're different specific
events): closest approach across all three pairwise comparisons is
**882 CE vs. 912 CE -- only 30 years apart** (Bhishma's Shravana loop
vs. one of Udyoga's Jyeshtha epochs). Every other cross-reading pairing
is 1600+ years apart. Checked whether 30 years is actually meaningful:
with 11 Jyeshtha epochs scattered across 8400 years and one fixed
Shravana-loop epoch, the chance of at least one Jyeshtha epoch landing
within 30 years by pure chance is roughly 7-8% -- not below any
reasonable significance bar. Worth noting, not worth building on.

**2. What if the search is widened by OR-ing across the textual
variants instead of picking one?** Since different verses genuinely
name different Mars targets (Magha, Shravana, Jyeshtha, and Udyoga's
own "approaching Anuradha"), tried the more permissive version: find
every Shani-Rohini epoch (466 of them -- Saturn transits Rohini every
~29.5 years, with 2-3 sub-windows per pass from retrograde loops), then
check whether Mars was retrograde in ANY of {Magha, Shravana, Jyeshtha,
Anuradha} within +/-3 years of each one.

**Result: 387 of 466 Shani-Rohini epochs (83%) have a qualifying Mars
match nearby.** This is the important finding from this round, and it's
a methodological one rather than a dating one: loosening the match
criteria this way doesn't narrow anything -- it makes the combined
condition nearly always true, because Mars retrogrades roughly every 26
months for ~2-2.5 months each time, and 4 of 27 nakshatras (~15% of the
sky) count as a hit, so within any 6-year window there's a high chance
some retrograde loop lands somewhere in the accepted set. This is
exactly why the STRICT single-verse readings (1, 1, and 11 epochs) are
the only versions of this analysis worth taking seriously: they're
informative precisely because they're strict. OR-ing across textual
variants to be "more inclusive" destroys the thing that made the
individual verses worth checking in the first place.

Added `engine.cluster_into_epochs()` as a proper reusable utility for
the epoch-clustering logic that had been hand-rolled inline across
several analysis scripts this session (find candidates, cluster
consecutive high scorers within a gap threshold into one "epoch") --
worth having in the library now that it's been needed repeatedly.

**Bottom line after widening**: the astronomy doesn't converge on a
year nobody has proposed, and it doesn't retroactively support any of
the four popularly-debated ones either. The honest state of this
sub-project is that the Mahabharata's own omen catalogue, read
carefully, is real, checkable astronomy that happens rarely -- and none
of the popular dating proposals line up with when it actually happens.

## Search engine could step over matches -- fixed, results re-checked (2026-09-24)

A review found that `engine.search()`'s fixed stage steps (200 days for
Shani/Guru, 20 for Mangala/nodes, 5 for Surya/Shukra/Budha) were sized
from the mean time a graha spends in a whole rashi, not from how briefly
a constraint -- or an overlap of several -- can actually hold. Anything
shorter than a step could be stepped over. Checked against dense
brute-force scans with identical constraints:

| Profile | Old engine | Brute force |
|---|---|---|
| Guru in Shravana, 0-3000 CE | 190 spells | 376 |
| Guru retrograde, 2000-2100 | 35 spells | 92 |
| Shani-Rohini + Guru-Shravana, 250 BCE-0 | 0 spells | 3 |
| Udyoga 5.141.7-8, within 2 deg tolerance | 11 epochs | 14 |

**Fix**: each constraint now reports a signed margin to its match boundary
plus bounds on how fast that margin can change (`motion.py`, measured
over 5300 BCE-2940 CE with headroom), and the engine steps exactly as far
as those bounds prove the constraint can't change state. Nothing shorter
than a step can be missed any more, including brief overlaps. It is also
no slower: ~1.3-1.5 s for the full ~8400-year Mahabharata profiles.
`tests/test_engine_brute_force.py` re-checks the bounds against the
ephemeris and the engine against brute-force scans (fixed miss patterns
plus randomized profiles).

**What changes in the conclusions above**:
- The *perfect* matches (every constraint inside its arc, score > 0.99)
  are unchanged: Bhishma 013c-d still 1 epoch (3449 BCE), the Shravana
  loop still 1 (882 CE), Udyoga still 11. The old engine never missed
  these; the tests pinning them still pass as written.
- *Within the 2-degree tolerance*, Udyoga gains three epochs the old
  engine missed: **4628, 1946 and 1299 BCE**. 1299 BCE is **179 years
  from the 1478 BCE candidate** -- closer than any Udyoga epoch known
  before (621 years). Still not within the ~100-year margin the tests
  use, so the "misses all four candidates" statements hold.
- Bhishma 013c-d's two within-tolerance epochs, 2536 BCE (87 years from
  the 2449 BCE candidate) and 2768 CE, were already found by the old
  engine; an earlier comparison that suggested otherwise was comparing
  perfect-match counts against within-tolerance counts.

Anything else run through the old engine with Guru/Shani nakshatra or
retrograde constraints, or with brief multi-constraint overlaps, is
worth re-running.

## Calendar and labelling fixes (2026-09-24)

Three more bugs from the same review, each now pinned by tests in
`tests/test_calendar_and_labels.py`:

- **Adhika months were named after the previous month.** An adhika month
  (no sankranti) takes the name of the regular month that *follows* it.
  The old code gave e.g. "Adhika Ashadha" for 2023's Jul 18 - Aug 16
  month, which published Panchangs call Adhika Shravana; 2015, 2018,
  2020 and 2026 were all off by one the same way. `masa.py` also now
  flags **kshaya** months (two sankrantis; 1963, 1983 and 2123 in
  1900-2200) with both month names, since conventions differ on which
  one the combined month carries, and `find_calendar_dates` matches
  either.
- **`find_tithi_jd_near` often landed in the previous tithi** (205 of
  400 random trials): it targeted the tithi's exact starting boundary,
  and the root-finder's tolerance left the result just short of it. It
  now targets the middle of the tithi's arc (0 misses in 3000 trials).
- **The ephemeris model could be mislabelled.** swisseph silently
  substitutes its Moshier model when no data file covers the date, and
  reports that only in its return flags, which were discarded -- so
  `graha_position(..., use_moshier=False)` said "swieph" for CE dates
  (no CE data files are downloaded) and CE-era eclipses were described as
  data-file based. `Position.ephemeris_model` and the new
  `Eclipse.ephemeris_model` now come from the returned flags.
