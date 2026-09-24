"""Shared test configuration.

Tests marked `ephe_data` need the Swiss Ephemeris data files (dates
outside Moshier's ~3002 BCE-3003 CE range). They are skipped, not failed,
when the files aren't in starcharts.ephemeris.EPHE_DIR -- run
ephe/download.sh, or set STARCHARTS_EPHE_DIR to where the files are.
"""

import pytest

from starcharts.ephemeris import EPHE_DIR


def have_ephe_data_files() -> bool:
    return any(EPHE_DIR.glob("*.se1"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "ephe_data: needs the Swiss Ephemeris data files (run ephe/download.sh)"
    )


def pytest_collection_modifyitems(config, items):
    if have_ephe_data_files():
        return
    skip = pytest.mark.skip(
        reason=f"Swiss Ephemeris data files not found in {EPHE_DIR} "
        "(run ephe/download.sh or set STARCHARTS_EPHE_DIR)"
    )
    for item in items:
        if "ephe_data" in item.keywords:
            item.add_marker(skip)
