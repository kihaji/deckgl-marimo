# Makefile for deckgl-marimo
#
# Usage:
#   make            - Build the JS bundle into src/deckgl_marimo/static/
#   make watch      - Rebuild the bundle on JS source changes (dev loop)
#   make clean      - Remove build artifacts
#   make test       - Run the Python test suite
#   make test-js    - Run the vitest JS suite
#   make quality    - ruff (lint) + pyright (types)
#   make check-versions [VERSION=x.y.z] - Verify all version sources agree
#   make release VERSION=x.y.z - Verify clean tree + versions and tag
#   make docs-serve - Serve docs locally at http://127.0.0.1:8000
#   make docs-build - Build docs with strict mode
#

.PHONY: all build watch clean test test-js quality check-git check-version check-versions release docs-serve docs-build

all: build

# Build the production (minified) JS bundle
build:
	@echo "Building JS bundle..."
	cd js && npm run build
	@echo "Build complete: src/deckgl_marimo/static/deckgl-marimo.bundle.js"

# Rebuild on change — pair with `uv sync` (editable install) for the dev loop
watch:
	cd js && npm run watch

clean:
	@echo "Cleaning build artifacts..."
	rm -f src/deckgl_marimo/static/deckgl-marimo.bundle.js
	rm -f src/deckgl_marimo/static/deckgl-marimo.bundle.css
	rm -rf dist/
	@echo "Clean complete"

# Python test suite
test:
	uv run pytest

# JS unit tests
test-js:
	cd js && npm test

# Run code quality checks: ruff (lint) + pyright (types)
quality:
	@echo "Running ruff linter..."
	uv run ruff check .
	@echo "Running pyright type checker..."
	uv run npx pyright
	@echo ""
	@echo "Quality check complete."

# Check if git working directory is clean
check-git:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Working directory has uncommitted changes:"; \
		git status --short; \
		echo ""; \
		echo "Please commit or stash changes before releasing."; \
		exit 1; \
	fi
	@echo "Git working directory is clean"

# Check that VERSION is provided
check-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required"; \
		echo "Usage: make release VERSION=x.y.z"; \
		exit 1; \
	fi
	@echo "Release version: $(VERSION)"

# Check that all version sources agree (and match VERSION when provided)
check-versions:
	uv run python scripts/check_versions.py $(VERSION)

# Release target - verify clean tree + version consistency and tag
# Use scripts/release.py to bump + verify + commit first, or bump by hand.
release: check-version check-git check-versions
	@echo ""
	@echo "Creating git tag v$(VERSION)..."
	git tag -a "v$(VERSION)" -m "Release v$(VERSION)"
	@echo ""
	@echo "=========================================="
	@echo "Release v$(VERSION) prepared successfully!"
	@echo "=========================================="
	@echo ""
	@echo "To publish:"
	@echo "  git push && git push --tags"
	@echo "  then create a GitHub Release from the tag (publishing triggers on Release published)"
	@echo ""

# Serve documentation locally
docs-serve:
	uv run --extra docs mkdocs serve

# Build documentation with strict mode (catches broken links/warnings)
docs-build:
	uv run --extra docs mkdocs build --strict
