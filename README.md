# starcharts

Search real astronomical history for dates matching a textual sky
description — a *janam patri* (birth chart), an epic verse describing
planetary omens, or any other claim of the form "the sky looked like
this." Corrects for precession, ayanamsha, and calendar conversion
explicitly, and reports a ranked list of candidates with their match
quality rather than a single answer.

**Live demo:** [Cosmic Timeline](https://rahulbhargavain.github.io/starcharts/cosmic_timeline/)
— the sidereal sky and the rise and fall of civilizations, 3500 BCE to
today ([all demos](https://rahulbhargavain.github.io/starcharts/)).

## What it does

1. **Ephemeris + ayanamsha** — real planetary positions for any date
   (including deep BCE history), converted from tropical to sidereal
   longitude under a configurable ayanamsha (Lahiri by default).
2. **Calendar layer** — tithi, amanta lunar month, nakshatra, all with
   tolerance-aware matching for how uncertain a claim should be treated.
3. **Search engine** — coarse-to-fine constraint search across
   multi-millennium ranges (ordered slowest-to-fastest graha), fast
   enough to sweep ~8,400 years in low single-digit seconds.
4. **Reporting** — full chart, per-constraint match detail, and
   cross-ayanamsha sensitivity for every candidate, so a result comes
   with the information needed to judge how much to trust it.
5. **Visualization** — a North-Indian kundali SVG renderer and an
   interactive HTML explorer built on real search output.
6. **Cosmic timeline** ([live](https://rahulbhargavain.github.io/starcharts/cosmic_timeline/),
   source in `demo/cosmic_timeline/`) — a playable sidereal
   sky (Earth-centred wheel, Sun-centred orbits, or a tilted isometric
   view) next to a world map of civilizations rising and falling,
   3500 BCE to today. Static files, no build step; planet positions are
   computed in the browser (within ~0.5° of the Swiss Ephemeris, see
   `tests/test_cosmic_timeline_astro.py`). Serve it with
   `python -m http.server --directory demo` and open
   `/cosmic_timeline/` to run it locally.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Dates outside ~3002 BCE–3003 CE need the real Swiss Ephemeris data
files (not checked into the repo — see `ephe/README.md`):

```bash
bash ephe/download.sh
```

With a regular (non-editable) install, set `STARCHARTS_EPHE_DIR` to
wherever the data files live; `download.sh` uses the same variable.

Run the tests with `pytest` (and lint with `ruff check .`). Tests that
need the data files are skipped, not failed, when the files are absent.

## Example

```python
from datetime import datetime, timezone
from starcharts import compute_chart, render_kundali_svg

chart = compute_chart(datetime(2024, 1, 1, tzinfo=timezone.utc))
svg = render_kundali_svg(chart, title="2024-01-01 (Lahiri)")
```

See `src/starcharts/texts/` for worked examples applying the full
pipeline to real textual sources (the Ramayana's Bala Kanda birth
description, the Mahabharata's war-omen verses), each citation-checked
against Sanskrit critical editions rather than paraphrased from
secondary sources.

## On what this project does and doesn't claim

This tool tests the astronomical viability and internal consistency of
a textual sky description — it does not produce an objective, singular
date. A rashi-level (sign-level) match alone is rarely unique: real sky
configurations recur on cycles of years to millennia, so a search
returns a ranked candidate list, not an answer. `WORKPLAN.md` documents
the full methodology, every caveat, and the results (including several
negative ones) from applying this to real historical dating questions.

## License

AGPL-3.0-or-later (see `LICENSE`). This follows from the license of the
core dependency, [pyswisseph](https://pypi.org/project/pyswisseph/)
(Swiss Ephemeris, AGPL/dual-licensed by Astrodienst).
