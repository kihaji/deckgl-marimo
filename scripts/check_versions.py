#!/usr/bin/env python3
"""Verify the package version agrees across all files that declare it.

Usage:
    python scripts/check_versions.py            # fail if any source disagrees
    python scripts/check_versions.py 0.7.0      # additionally fail if the agreed version != 0.7.0

Stdlib-only so it can run in CI before any dependencies are installed.
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def collect_versions() -> dict[str, str]:
    """Return {source: version} for every file that declares the package version."""
    versions = {}

    match = re.search(r'^version = "([^"]+)"', (PROJECT_ROOT / "pyproject.toml").read_text(), re.MULTILINE)
    versions["pyproject.toml"] = match.group(1) if match else "<not found>"

    versions["js/package.json"] = json.loads((PROJECT_ROOT / "js" / "package.json").read_text()).get("version", "<not found>")

    lock = json.loads((PROJECT_ROOT / "js" / "package-lock.json").read_text())
    versions["js/package-lock.json"] = lock.get("version", "<not found>")
    versions['js/package-lock.json packages[""]'] = lock.get("packages", {}).get("", {}).get("version", "<not found>")

    match = re.search(r'^name = "deckgl-marimo"\nversion = "([^"]+)"', (PROJECT_ROOT / "uv.lock").read_text(), re.MULTILINE)
    versions["uv.lock"] = match.group(1) if match else "<not found>"

    return versions


def check(expected: str | None = None) -> bool:
    """Print all version sources and return True when they agree (and match `expected`, if given)."""
    versions = collect_versions()
    width = max(len(source) for source in versions)
    for source, version in versions.items():
        print(f"  {source:<{width}}  {version}")

    distinct = set(versions.values())
    if len(distinct) != 1:
        print(f"\n❌ Version mismatch: found {sorted(distinct)}")
        return False

    agreed = distinct.pop()
    if expected is not None and agreed != expected:
        print(f"\n❌ Files say {agreed} but expected {expected}")
        return False

    print(f"\n✅ All sources agree on {agreed}" + (f" (matches expected {expected})" if expected else ""))
    return True


if __name__ == "__main__":
    expected = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(0 if check(expected) else 1)
