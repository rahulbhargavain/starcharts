# starcharts — workplan and findings

starcharts searches real astronomical history for dates when the sky matched
a textual description: a *janam patri* (birth chart), an epic verse listing
planetary omens, or any claim of the form "the sky looked like this". It
corrects for precession, ayanamsha and calendar conversion explicitly, and
reports ranked candidates with their match quality rather than a single
answer.

This document leads with the current state and findings, then the method's
limits, how the system is built and verified, and open questions. The dated
research log at the end records how each result was reached, including the
readings and results that later turned out to be wrong.

Years are given historically (BCE/CE) unless marked *astronomical*
(year 0 = 1 BCE, year −3101 = 3102 BCE), which is what the code uses.
Calendar dates are proleptic Gregorian.

## Where things stand (2026-09-24)

- **All five layers are built and tested**: ephemeris, ayanamsha
  conversion, luni-solar calendar, constraint search, and reporting, plus
  an SVG kundali renderer and an interactive demo. 118 tests pass (with the
  ephemeris data files downloaded; see `ephe/README.md`), and CI runs them
  with and without the data files.
- **The search engine is checked against brute force.** It can no longer
  step over a short match (see *Verification*). Every result below was
  re-run on the fixed engine on 2026-09-24.
- **Mahabharata war omens**: all three readings that exist in the Sanskrit
  text occur rarely, and none of them occurs within 100 years of the four
  popularly debated war years (3137, 3067, 2449 and 1478 BCE).
- **Ramayana (Rama's birth)**: the configuration never occurs exactly in
  5400 BCE–3000 CE. Its closest approach, missing by 4.6° at worst, is
  10 January of astronomical year −5114 (just after midnight, Ayodhya local
  time), which lines up with the traditionally cited "10 January 5114 BCE".
  The miss doesn't depend on ΔT or the lunar tidal acceleration.

## Findings

### Mahabharata war omens

Three readings survive a shloka-by-shloka check against the Sanskrit
(GRETIL's critical edition for Bhishma Parva, a Devanagari reader edition
for Udyoga Parva). Searched over 5400 BCE–3000 CE at the project's standard
2° tolerance. An *exact* epoch has every constraint inside its arc (score
> 0.99); a *within-tolerance* epoch meets them only with the 2° padding.
Matches less than 60 days apart count as one epoch.

| Reading | Exact epochs | Also within tolerance | Closest to a candidate year |
|---|---|---|---|
| Bhishma 6.3.13c-d: Shani in Rohini, Mangala **retrograde** in Magha, Guru in Shravana | 1: 3449 BCE | 2536 BCE, 2768 CE | 2536 BCE, 87 years from 2449 BCE (within tolerance only); exact: 312 years |
| … plus a node (Rahu or Ketu) in Jyeshtha (6.3.15) | 0 | 0 | — |
| Bhishma 6.3.17a: Mangala completes a retrograde loop in Shravana, with Guru and Shani as above | 1: 882 CE | — | 2359 years |
| Udyoga 5.141.7-8: Shani afflicts Rohini ("Prajapatya"), Mangala goes **retrograde** in Jyeshtha | 11: 5070, 857, 415 BCE; 28, 470, 912, 1117, 1559, 2001, 2443, 2885 CE | 4628, 1946, 1299 BCE | 1299 BCE, 179 years from 1478 BCE (within tolerance only); exact: 621 years |

**Conclusion.** Read carefully against the Sanskrit, the omen verses do not
corroborate 3137, 3067, 2449 or 1478 BCE. That doesn't rule out a year this
project hasn't considered. It also doesn't settle whether the verses were
ever meant as one precise, simultaneous sky rather than a traditional
catalogue of omens. But within its own terms the search is negative across
the board.

Two patterns matter for anyone repeating this:
- **English paraphrases drop "vakra" (retrograde).** The versions that used
  to hit candidate years (Udyoga hit 3067 and 1478 BCE) did so only because
  their English-derived encodings lacked a retrograde requirement the
  Sanskrit states. Adding it removed both hits.
- **Loosening makes the search uninformative, not more inclusive.** Accepting
  Mangala retrograde in *any* of the four nakshatras the verses name
  (Magha, Shravana, Jyeshtha, Anuradha) within ±3 years of each Shani-in-
  Rohini epoch matches 358 of 525 such epochs (68%). Mars retrogrades every
  ~26 months, and four nakshatras cover ~15% of the sky, so the combined
  condition is nearly always true. The strict single-verse readings are
  informative precisely because they are strict.

**Do the readings cluster?** The text presents them as one run-up to one
war, so a real match might show several readings close together. The
closest pair across readings is 882 CE (Bhishma 17a) and 912 CE (Udyoga),
30 years apart. With 11–14 Udyoga epochs spread over 8400 years, at least
one falls within 30 years of a fixed date about 7–10% of the time by
chance. Worth noting, not worth building on. Every other cross-reading pair
is at least 117 years apart.

**Other Mahabharata details:**
- **Krishna's birth** (Rohini nakshatra, Krishna-paksha Ashtami, Sun in
  Simha) recurs about once a year: ~5,500 distinct dates in 3000 BCE–
  3000 CE at 0.5° tolerance. It is calendar-cyclical, not a rare
  conjunction, and cannot pick a year alone.
- **"Two eclipses close together"** is not a useful constraint. The
  shortest solar-to-lunar eclipse gap in one season is ~13.9 days (a literal
  13 never occurs, in any era checked), and such pairs happen ~2.9 times a
  year in every era. `has_close_eclipse_pair()` exists as an annotation, not
  a filter.
- 5.141.9 ("a planet afflicts Chitra") names no planet, and 5.141.10 ("Rahu
  approaches the Sun") gives no orb, so neither is encoded. Bhishma 6.3.11c
  (a node across Chitra) can't hold at the same instant as the Jyeshtha
  node, since Rahu and Ketu are always 180° apart, so it's read as a
  different moment in the run-up.

### Ramayana: Rama's birth (Bala Kanda, ~Sarga 18)

Encoded: five grahas exalted (Surya in Mesha, Mangala in Makara, Shani in
Tula, Guru in Karka, Shukra in Meena), Chandra in Karka and Punarvasu,
Chaitra Shukla Navami, and Karka lagna (checked separately at local noon in
Ayodhya).

- **No exact match anywhere in 5400 BCE–3000 CE**, at 1.5° or 3°
  tolerance.
- **The closest approach is 10 January, astronomical year −5114**
  (5115 BCE), at about 00:32 Ayodhya local mean time (9 January ~19:00 UT)
  with Swiss Ephemeris' default ΔT. Five of the six sign placements hold
  exactly. Shani is 1.4° short of Tula, and the Moon's nakshatra and the
  tithi each miss by about 4.6°. The best instant misses by 4.6° at
  worst, so it appears once the tolerance reaches 5°. Karka lagna holds at
  local noon. Seven or eight of eight ayanamsha choices keep every
  constraint within 8°.
- **This lines up with the traditionally cited date**, "10 January
  5114 BCE" (Pushkar Bhatnagar's planetarium-based figure). The same date
  one year later (astronomical −5113, which is 5114 BCE in historical
  numbering) fits badly. The cited year therefore most likely uses
  astronomical numbering, as planetarium software does. That should be
  confirmed against the original source.
- **ΔT and the Moon's tidal acceleration don't close the gap.** Re-run
  with ΔT (43.3 h by default at this date) shifted by ±3, ±6, ±12 and
  ±24 hours, and with the lunar tidal acceleration anywhere from −22 to
  −28″/cy² (bracketing DE200 through DE431), the worst miss stays at
  4.61° every time. ΔT only moves *when*, in civil time, the geometry
  occurs: the best instant drifts from 9 January midday (ΔT +12 h) to
  10 January midday (ΔT −12 h), and stays within 9 Jan 21:46 – 10 Jan
  05:21 across the tidal-acceleration range. Karka lagna at noon holds in
  every case.
- **At the traditional birth time, local noon**, the fit is worse: with
  default ΔT the worst miss at noon on 10 January is 11.3° (the Moon has
  not yet reached Punarvasu). It comes back to ~4.9° only if ΔT is about
  12 hours smaller than the default.
- **How to read it.** This is a near-fit, not a match at the tolerances used
  elsewhere in this project, and the usual lunar-uncertainty argument
  doesn't rescue it. The geometric miss is insensitive to ΔT and tidal
  acceleration, and the tithi miss (a Moon-minus-Sun angle) is
  independent of ayanamsha too. What remains open is whether the verse
  intends this level of precision. It is the closest the sky comes in
  8,400 years, and much closer than this document previously reported
  (see the 2026-09-24 log entries).
- **At 8° tolerance** four epochs appear: 5115, 4498 and 3644 BCE and
  2810 CE. 5115 BCE is the closest fit.
- **If Surya is not among the five** (an external suggestion about which
  grahas the verse names; the wording wasn't verified here), the remaining
  seven constraints hold exactly on **5 January 4498 BCE** and nowhere else.
  One more date, 4262 BCE, fits within 1.5°. The 4498 BCE date fails the
  Karka-lagna check (the Ascendant at noon is ~86°, in Mithuna), and
  Fagan-Bradley ayanamsha flips two of its seven placements. It is recorded,
  not presented as an answer.
- **Karka lagna is not independent evidence.** At local noon the Sun is at
  the Midheaven, and at Ayodhya's latitude the Ascendant runs ~93–95° ahead
  of it. So Surya in Mesha at noon almost forces Karka lagna.

## What a result can and can't tell you

- **Rashi-only constraints are weak.** Sign-level (12-way) placements recur
  constantly across millennia. Nakshatra-level (27-way) and tithi constraints
  are what narrow a search.
- **Ayanamsha extrapolation drifts.** Lahiri, Raman, Krishnamurti and
  Fagan-Bradley are fits calibrated on recent centuries, and they can drift
  by degrees over millennia. Prefer the star-anchored `TRUE_*` modes past
  ~1000 BCE. Every report includes a cross-ayanamsha sensitivity table,
  because boundary cases flip.
- **The Moon's position loses precision with age.** ΔT and lunar secular
  acceleration make exact tithi and nakshatra boundaries overconfident past
  ~1500 BCE. That's why every constraint takes a `tolerance_degrees`, and
  why *exact* and *within-tolerance* results are reported separately.
- **Masa names are modern.** The amanta rule used here (a month is named by
  the sankranti inside it; an adhika month by the month that follows it) is
  a post-~500 CE Siddhantic convention. Earlier calendars intercalated
  differently (e.g. the Vedanga Jyotisha 5-year yuga). Before ~500 CE, a
  masa name is corroboration, never a filter. Tithi and nakshatra are direct
  angular measurements and stay reliable much further back.
- **Scholarly dating attempts disagree by thousands of years**, depending on
  verse selection, translation and ayanamsha. That spread is itself a
  finding, not a bug to engineer away.
- **Circulating janam patris are reconstructions.** Running one through
  this system mostly tests its internal consistency, not the sky.
- **A negative result is bounded by the ephemeris range.** Positions reach
  ~5400 BCE (see below). Nothing here speaks to earlier dates.

## How it works

| Layer | Modules | Notes |
|---|---|---|
| Ephemeris | `ephemeris.py`, `nodes.py` | pyswisseph. Moshier model (no files) for ~3002 BCE–3003 CE; Swiss Ephemeris data files for ~5400–2400 BCE, via `ephe/download.sh` (~9.5 MB). Each `Position` records which model actually computed it, read from swisseph's return flags. Rahu/Ketu use the mean node. |
| Coordinates | `ayanamsha.py`, `rashi.py`, `arcs.py` | Tropical → sidereal under a configurable ayanamsha (Lahiri default; all common modes plus `TRUE_*`). Rashi and nakshatra arcs with tolerance padding. |
| Calendar | `panchanga.py`, `masa.py`, `calendar.py`, `search.py` | Tithi, amanta masa (adhika and kshaya months handled), and text date → candidate Julian days. Root-finding for exact new moons and tithi moments. |
| Search | `constraints.py`, `motion.py`, `engine.py` | Typed constraints (rashi, nakshatra, tithi, retrograde, node, either-node, ascendant). Each has a hard `is_satisfied` for pruning and a Gaussian `score` for ranking. |
| Reporting | `report.py`, `chart.py`, `visualize.py` | Full 7-graha chart, per-constraint exact / within-tolerance / not-satisfied detail, cross-ayanamsha sensitivity, North-Indian kundali SVG. |
| Texts | `texts/ramayana.py`, `texts/mahabharata.py` | Worked constraint sets, with the citation checks in their docstrings. |

**The search engine** (`engine.py`). Each prunable constraint reports a
signed *margin*: how far its value is from the match boundary, ≥ 0 exactly
when it is satisfied. `motion.py` bounds how fast each margin can change:
each body's maximum speed, maximum acceleration, and the error in
swisseph's reported speed. From one sample, the engine can therefore prove
how long a constraint stays on its current side of the boundary, and it
steps exactly that far. The steps are huge when a slow graha is far from
its arc and small only near a boundary.

Constraints are scanned slowest first and their results intersected. A
15-minute second pass then trims the surviving windows. The windows are
sampled every 6 hours plus each midpoint, and the samples are ranked by
score. The full ~8400-year Mahabharata profiles take ~1.5 s. The ascendant
moves too fast for date-level scanning, so it is checked separately at a
chosen time of day (e.g. local noon) on dates the search finds.

## Verification

Checks against independent sources, not only shape tests:
- **Published calendars**: Chaitra 2024 (Ugadi, 9 April), and the adhika
  months of 2015, 2018, 2020, 2023 and 2026.
- **Brute force**: `tests/test_engine_brute_force.py` compares the engine
  with dense scans (1 day down to 30 minutes) on each pattern that used to
  fail and on 30 randomized profiles. It re-checks the `motion.py` bounds
  against the ephemeris. It also pins the full-range Udyoga and Bhishma
  epoch lists, each verified once against a 1-day scan of all 8400 years
  (~2.5 minutes each).
- **Model labels**: checked against swisseph's own return flags.

Correctness bugs found and fixed, most found by checking against something
external rather than by shape tests:
- **Masa named by the rashi at the month's start** instead of the sankranti
  inside it (2026-09-19). This gave "Phalguna" for 2024's Chaitra.
- **The engine stepped over short matches** (2026-09-24). Fixed steps of
  200, 20 and 5 days were sized from time-per-rashi, not from how briefly a
  constraint or an overlap of constraints holds. Against brute force it
  found 190 of 376 Guru-in-Shravana spells (0–3000 CE), 0 of 37 Guru
  retrograde spells (2000–2040), 0 of 3 Shani-Rohini + Guru-Shravana
  overlaps (250 BCE–0), and 11 of 14 within-tolerance Udyoga epochs. Exact
  Mahabharata results were unaffected.
- **Surviving windows sampled too sparsely** (2026-09-24). Overlaps of a few
  hours could be reported as near-misses. This hid the 5115 BCE Bala Kanda
  fit at 5°.
- **Adhika months named after the previous month** instead of the following
  one (2026-09-24), in all five years checked.
- **`find_tithi_jd_near` landed in the previous tithi** about half the time
  (2026-09-24), because it targeted the tithi's exact start.
- **Ephemeris model mislabelled** (2026-09-24). swisseph silently uses
  Moshier where no data file covers the date, so CE-era "swieph" positions
  and eclipses were really Moshier.
- **Worker threads couldn't reach the data files** (2026-09-24). swisseph
  keeps its settings per thread, and the data-file path was set only in
  the importing thread, so any computation before ~3000 BCE failed in
  another thread. The path is now set per thread. (The review's concern,
  a race on the global sidereal mode, turned out not to apply: the mode is
  per-thread too.)

## Decisions

- **pyswisseph, not raw JPL DE431/441.** It is the de facto standard in Vedic
  astrology software, has every ayanamsha built in, and needs no large
  download for the Moshier range. The Swiss Ephemeris is AGPL, and so is
  this project. `openephem` (MIT, skyfield + JPL kernels) is the
  alternative if a permissive license is ever needed. Its default DE440
  kernel covers only 1550–2650 CE, though, and multi-millennium BCE work
  would need DE441 (several GB). `libephemeris` is AGPL too.
- **BCE dates bypass `datetime`**, which can't represent them. The core API
  takes astronomical year numbers directly.
- **Tithi and nakshatra are primary; masa and paksha corroborate** (see
  above). Text dates are handled by screening the ephemeris first and then
  checking calendar details at candidate dates, not by forward calendar
  parsing.
- **Scores rank; hard checks prune.** A decayed-but-nonzero score would
  otherwise let almost every candidate through every stage.
- **Each verse is its own profile.** Readings from different parvas and
  speakers genuinely differ; merging them into one convenient composite
  would hide that.

## Open questions and next steps

- **Bala Kanda near-fit**:
  - check which calendar and year numbering Bhatnagar used;
  - check whether the published ΔT uncertainty at ~5100 BCE allows the
    ~12-hour shift that would put the best fit at local noon (the
    geometric miss itself is ΔT-independent; see *Findings*);
  - settle the verse wording (whether Surya is among the five exalted
    grahas).
- **Udyoga 1299 BCE** (within tolerance, 179 years from 1478 BCE): inspect
  which constraint needs the tolerance and by how much.
- **Earlier than ~5400 BCE**: download more `seplm*/semom*` files (see
  `ephe/README.md`).
- **Krishna's birth** needs an independent discriminator, most plausibly
  the war (traditionally ~89–90 years later).
- **Parallel searches**: now safe with threads (see *Verification*), but
  each search still runs single-threaded; splitting a long range across a
  process or thread pool is the obvious speed-up if one is needed.

## Research log

Condensed and chronological. Superseded results are kept, and marked, so
the path to each current finding stays checkable.

**2026-09-19 — scaffolding and first searches**
- Built the ephemeris, ayanamsha and calendar layers. A manual check against
  a published Panchang caught the masa start-rashi bug (see *Verification*).
  Lesson: calendar code needs checking against real published data.
- An external audit (via Gemini) was assessed point by point. Accepted:
  ayanamsha extrapolation risk (added the `TRUE_*` modes), overconfident
  lunar boundaries (added tolerances), screening the ephemeris before
  calendar parsing, the slowest-to-fastest search order, and typed
  constraints. Flagged as unverified: its claimed data-file date range.
- Built the coarse-to-fine engine and the reporting layer. At 2024-01-01
  all five default ayanamshas agreed on every rashi because no graha sat
  near a boundary. That is a concrete example of when ayanamsha choice
  does and doesn't matter.
- **Bala Kanda**: no match at 1.5° anywhere in the then-reachable
  ~3000 BCE–3000 CE. Added lagna support (`ascendant.py`). Two corrections
  the same day:
  - Karka lagna is implied by Surya in Mesha at noon, so it isn't extra
    evidence.
  - An external claim that the lunar constraints were mutually exclusive
    by 16–31° rested on using Ardra's span for Punarvasu. The real tension
    is ~2.7°, and 1042 CE has Surya in Mesha and Chandra in Punarvasu at
    once.
  - *Superseded:* "best scores 0.013 / 0.407 / 0.704 at 3° / 5° / 8°;
    doesn't occur at any tolerance up to 8°". Those came from the old
    engine; see 2026-09-24.
- **Extended the ephemeris to ~5400 BCE** with the Swiss Ephemeris data
  files, with automatic fallback from Moshier. Still no Bala Kanda match at
  1.5°. A spot check at "10 January 5114 BCE" fit badly. In hindsight it
  probably tested astronomical −5113; see 2026-09-24.
- **"Surya may not be one of the five"**: one exact match, 5 January
  4498 BCE. It fails the lagna check and is ayanamsha-fragile (see
  *Findings*).
- **Krishna and Mahabharata first sets.** Krishna's birth recurs yearly. A
  first, secondary-source war-omen profile (Shani in Rohini + Mangala
  retrograde) gave ~154 epochs in 6000 years. The eclipse-pair claim was
  checked and found non-discriminating.
- **Candidate-year tests (superseded).** Guessed encodings seemed to hit
  3067 and 2449 BCE. A citation check against Ganguli's English
  translation then showed the guesses were wrong: Guru is in Shravana,
  Mangala heads to Magha, and the Jyeshtha body is a node. `nodes.py` was
  added. Bhishma and Udyoga give genuinely different specifics.
  English-only Udyoga (no retrograde) hit 3067 and 1478 BCE. Bhishma
  without retrograde had 6 epochs, none near a candidate.
- **Reached the Sanskrit (GRETIL, Bhismaparvan).** This overturned the
  English reading:
  - 6.3.13c-d makes Mangala retrograde in Magha, in one clause with Guru
    in Shravana.
  - 6.3.15's node is "śyāma" (dark), so it could be Rahu or Ketu. This led
    to `EitherNodeNakshatraConstraint`.
  - The earlier "node at Jyeshtha and at Chitra simultaneously" variant
    was geometrically near-impossible, not underpowered.
  - 6.3.17a (Mars's full retrograde loop at Shravana) is a separate
    verse.
  - Bhishma dropped to 1 epoch (3449 BCE).

**2026-09-20 — Udyoga verified; widening**
- **Udyoga 5.141.7-10 in Devanagari.** "Prajapatya" (the nakshatra of
  Rohini's deity) confirms Shani in Rohini independently. 5.141.8 makes
  Mangala *retrograde* in Jyeshtha, heading back toward Anuradha, which is
  consistent astronomy. With retrograde required, Udyoga dropped from 159
  loose epochs to 11 (~442 years apart), and its candidate-year hits
  vanished.
- **Widened the search beyond the four candidate years**: complete epoch
  lists for every reading, the 882/912 CE proximity check, and the
  "OR the variants" test, which showed loosening destroys informativeness.
  Added `engine.cluster_into_epochs()`. *Superseded counts:* 466
  Shani-Rohini epochs, 83% with a nearby Mars match (old engine; now 525
  and 68%).

**2026-09-24 — engine and calendar fixes; every result re-run**
- **The engine stepped over short matches** (see *Verification*). Replaced
  the fixed steps with bound-proven steps (`motion.py`) and added
  brute-force regression tests.
  - Exact Mahabharata results were unchanged.
  - Udyoga gained three within-tolerance epochs: 4628, 1946 and 1299 BCE.
  - An external review had read "1 vs 3 Bhishma epochs" as a miss. It was
    comparing exact counts with within-tolerance counts; the old engine
    had found 2536 BCE.
- **Fixed** adhika naming, kshaya months (now flagged; they occur in 1963,
  1983 and 2123 within 1900–2200), the `find_tithi_jd_near` off-by-one, and
  ephemeris-model labels.
- **Re-ran every result** in this document on the fixed engine. That
  turned up the sampling gap (fixed with the 15-minute refinement pass)
  and changed the Bala Kanda picture. The closest fit, 9 January of
  astronomical −5114, was previously missed entirely. It misses by 4.65° at
  worst, so it appears at 5° tolerance, not only at 8°, and it lines up
  with the traditional "10 January 5114 BCE".
- **Closed the remaining review items**: a `STARCHARTS_EPHE_DIR` override
  for non-editable installs, per-thread swisseph setup (see
  *Verification*), results clipped to the requested range, single-call
  cached ephemeris lookups for scoring, SVG title escaping, CI (lint, and
  tests with and without the data files), and tests that skip cleanly
  without the data files.
- **Re-ran the Bala Kanda fit under ΔT and tidal-acceleration variants.**
  The 4.61° worst miss is unchanged by either; only the date and hour of
  the best fit move. With default ΔT it is 10 January (Ayodhya local
  time), not 9 January as first written (that was UT). Corrected the
  earlier suggestion that ΔT uncertainty might close the gap: it can't.
