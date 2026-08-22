"""pytest configuration for deckgl-marimo.

Two opt-in groups are skipped by default (CI runs plain ``pytest``):

* perf watchdog tests (``tests/perf_watchdog/``, marked ``perf``) spawn a
  marimo kernel and assert timing ratios — enable with ``--run-perf`` or
  ``DECKGL_RUN_PERF=1``;
* live-server tests (``tests/e2e/``, marked ``e2e``) talk to a real WFS —
  enable with ``--run-e2e`` or ``DECKGL_RUN_E2E=1``.
"""

from __future__ import annotations

import os

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-perf",
        action="store_true",
        default=False,
        help="run the perf watchdog tests (tests/perf_watchdog, marker 'perf'); equivalent to DECKGL_RUN_PERF=1",
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="run live-server tests (tests/e2e, marker 'e2e'); equivalent to DECKGL_RUN_E2E=1",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "perf: kernel-side performance watchdog; skipped unless --run-perf / DECKGL_RUN_PERF=1",
    )
    config.addinivalue_line(
        "markers",
        "e2e: live-server tests; skipped unless --run-e2e / DECKGL_RUN_E2E=1",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_perf = config.getoption("--run-perf") or os.environ.get("DECKGL_RUN_PERF") == "1"
    run_e2e = config.getoption("--run-e2e") or os.environ.get("DECKGL_RUN_E2E") == "1"
    skip_perf = pytest.mark.skip(reason="perf watchdog is opt-in: pass --run-perf (or set DECKGL_RUN_PERF=1)")
    skip_e2e = pytest.mark.skip(reason="live-server tests are opt-in: pass --run-e2e (or set DECKGL_RUN_E2E=1)")
    for item in items:
        if "perf" in item.keywords and not run_perf:
            item.add_marker(skip_perf)
        if "e2e" in item.keywords and not run_e2e:
            item.add_marker(skip_e2e)
