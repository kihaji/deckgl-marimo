#!/usr/bin/env python3
"""Create a release: bump version, verify, commit, and tag.

Usage:
    python scripts/release.py 0.7.0
    python scripts/release.py 0.7.0 --dry-run  # Preview without making changes

The JS bundle itself is NOT committed (it is gitignored and built at wheel-build
time by hatch_build.py); the build step here just verifies the bundle compiles.
"""
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from check_versions import check  # noqa: E402

# js/package.json and js/package-lock.json are bumped via `npm version`
# (the source of truth); these follow.
FILES_TO_UPDATE = [
    ("pyproject.toml", r'version = "[^"]+"', 'version = "{version}"'),
]


def run(cmd: str, dry_run: bool = False, cwd: Path | None = None) -> bool:
    """Run a shell command."""
    print(f"  → {cmd}")
    if dry_run:
        return True
    result = subprocess.run(cmd, shell=True, cwd=cwd or PROJECT_ROOT)
    return result.returncode == 0


def bump_version(new_version: str, dry_run: bool = False) -> bool:
    """Update version in all configuration files."""
    print(f"\n📝 Bumping version to {new_version}")

    if not run(
        f"npm version {new_version} --no-git-tag-version --allow-same-version",
        dry_run,
        cwd=PROJECT_ROOT / "js",
    ):
        print("❌ Error: npm version failed")
        return False

    for filepath, pattern, replacement in FILES_TO_UPDATE:
        full_path = PROJECT_ROOT / filepath
        if not full_path.exists():
            print(f"  ⚠ Warning: {filepath} not found, skipping")
            continue

        content = full_path.read_text()
        new_content = re.sub(pattern, replacement.format(version=new_version), content, count=1)

        if content == new_content:
            print(f"  ⚠ Warning: No version found in {filepath}")
        else:
            if not dry_run:
                full_path.write_text(new_content)
            print(f"  ✓ Updated {filepath}")

    # uv.lock records the project's own version; CI gates on `uv lock --check`
    if not run("uv lock", dry_run):
        print("❌ Error: uv lock failed")
        return False

    return True


def release(version: str, dry_run: bool = False) -> None:
    """Execute the full release workflow."""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print(f"❌ Error: Invalid version format '{version}'. Expected format: X.Y.Z")
        sys.exit(1)

    tag = f"v{version}"

    print(f"\n🚀 Creating release {tag}")
    if dry_run:
        print("   (DRY RUN - no changes will be made)\n")

    if not bump_version(version, dry_run):
        sys.exit(1)

    # Verify the bundle compiles (output is gitignored, not committed)
    print("\n📦 Building JavaScript bundle (verification only)")
    if not run("npm run build", dry_run, cwd=PROJECT_ROOT / "js"):
        print("❌ Error: npm build failed")
        sys.exit(1)

    print("\n🔍 Verifying version consistency")
    if not dry_run and not check(expected=version):
        print("❌ Error: version sources disagree — aborting before commit/tag")
        sys.exit(1)

    print("\n📝 Committing changes")
    if not run("git add -A", dry_run):
        sys.exit(1)
    if not run(f'git commit -m "Release {tag}"', dry_run):
        print("❌ Error: git commit failed (maybe no changes?)")
        sys.exit(1)

    print("\n🏷️  Creating tag")
    if not run(f"git tag {tag}", dry_run):
        print("❌ Error: git tag failed (tag may already exist)")
        sys.exit(1)

    print(f"\n✅ Release {tag} created successfully!")
    print("\n📤 To publish, run:")
    print("   git push && git push --tags")
    print("\n   Then create a GitHub Release from the tag — publishing to PyPI")
    print("   triggers on the Release being published.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/release.py <version> [--dry-run]")
        print("Example: python scripts/release.py 0.7.0")
        sys.exit(1)

    version = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    release(version, dry_run)
