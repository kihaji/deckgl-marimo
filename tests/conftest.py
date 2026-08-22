"""pytest configuration for deckgl-marimo.

Perf watchdog tests (``tests/perf_watchdog/``, marked ``perf``) are opt-in:
they spawn a marimo kernel and assert timing ratios, so they are skipped unless
``--run-perf`` is passed or ``DECKGL_RUN_PERF=1`` is set. CI runs plain
``pytest`` and therefore never executes them.
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


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "perf: kernel-side performance watchdog; skipped unless --run-perf / DECKGL_RUN_PERF=1",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-perf") or os.environ.get("DECKGL_RUN_PERF") == "1":
        return
    skip = pytest.mark.skip(reason="perf watchdog is opt-in: pass --run-perf (or set DECKGL_RUN_PERF=1)")
    for item in items:
        if "perf" in item.keywords:
            item.add_marker(skip)
