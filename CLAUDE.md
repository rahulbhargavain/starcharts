# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This is a fresh Python project scaffold with no application code yet. The package lives at `src/starcharts/` (src-layout) with tests in `tests/`.

## Commands

```bash
# create and activate a virtualenv
python -m venv .venv
.venv/Scripts/activate

# install the package in editable mode
pip install -e .

# run tests (once a test runner dependency like pytest is added)
pytest
```

## Architecture

No architecture yet — `src/starcharts/__init__.py` is empty. Update this file as real modules, entry points, and test conventions are established.
