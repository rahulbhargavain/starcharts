# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

starcharts searches real astronomical history for dates matching a textual sky description (a janam patri, an epic verse) and reports ranked candidates with their match quality. `WORKPLAN.md` holds the current findings, the method's caveats, and a research log — read its "Where things stand" and "What a result can and can't tell you" sections before changing search behaviour or reported results.

## Commands

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
bash ephe/download.sh              # Swiss Ephemeris data files for dates before ~3000 BCE
pytest                             # ~35 s with data files; data-dependent tests skip without them
pytest tests/test_engine_brute_force.py   # the engine-vs-brute-force checks (~25 s)
ruff check .
```

`STARCHARTS_EPHE_DIR` overrides where the data files are read from (needed for a non-editable install); `download.sh` honours it too.

## Architecture (`src/starcharts/`)

- **Ephemeris**: `ephemeris.py` (pyswisseph; Moshier for ~3002 BCE–3003 CE, data files beyond), `nodes.py` (Rahu/Ketu, mean node).
- **Coordinates**: `ayanamsha.py`, `rashi.py`, `arcs.py` (arc membership, signed margins, Gaussian scores).
- **Calendar**: `panchanga.py` (tithi), `masa.py` (amanta month, adhika/kshaya), `calendar.py` (text date → Julian days), `search.py` (root-finding).
- **Search**: `constraints.py` (typed constraints: hard `is_satisfied` for pruning, `score` for ranking, `margin` for safe stepping), `motion.py` (speed/acceleration bounds per body), `engine.py` (bound-proven stepping, then a 15-minute refinement pass, then scoring).
- **Reporting**: `report.py`, `chart.py`, `visualize.py` (North-Indian kundali SVG).
- **Texts**: `texts/ramayana.py`, `texts/mahabharata.py` — worked constraint sets with their Sanskrit citation checks in the docstrings.

## Conventions that matter

- **swisseph state is per thread** (it's built with thread-local storage). Route every swisseph computation through `ephemeris.ensure_thread_ready()` (the `_calc` helper does) so the data-file path is set in the calling thread, and set the sidereal mode immediately before each sidereal computation.
- **Years**: the core API takes astronomical years (0 = 1 BCE); `datetime` can't represent BCE. Calendar dates are proleptic Gregorian unless a function says otherwise.
- **Every prunable constraint's `margin() >= 0` must equal `is_satisfied()`**, and its `motion_bounds` must really bound how fast the margin changes — the engine skips ahead based on them. `tests/test_engine_brute_force.py` checks both; extend it when adding a constraint type or a body.
- **Validate calendar code against published Panchangs**, not just shape tests — several real bugs were only caught that way (see WORKPLAN.md, "Verification").
- **Tests needing the data files** are marked `@pytest.mark.ephe_data` (see `tests/conftest.py`) so they skip cleanly without them.
- **Report findings with their tolerance.** Distinguish exact matches (score > 0.99) from within-tolerance ones, and keep superseded results marked as such in WORKPLAN.md rather than deleting them.
