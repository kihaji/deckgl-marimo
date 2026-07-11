"""Hatchling build hook: build the JS bundle inside `uv build` / `python -m build`.

The 2.65 MB esbuild bundle is no longer git-tracked — wheels are self-building.
Requires Node 20+ and npm on PATH when building wheels (PyPI users install
prebuilt wheels and never need Node).

Skip rules:
- sdist builds never run npm (the sdist ships JS sources, not the bundle)
- editable installs (`uv sync`, `pip install -e .`) build only when the bundle
  is missing, so day-to-day syncs stay fast
- DECKGL_MARIMO_SKIP_JS_BUILD=1 skips unconditionally (escape hatch for CI
  stages that build the bundle themselves)
"""
import os
import shutil
import subprocess

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

BUNDLE_JS = os.path.join("src", "deckgl_marimo", "static", "deckgl-marimo.bundle.js")
BUNDLE_CSS = os.path.join("src", "deckgl_marimo", "static", "deckgl-marimo.bundle.css")
JS_DIR = "js"


class JSBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        if self.target_name == "sdist":
            return
        bundle_path = os.path.join(self.root, BUNDLE_JS)
        css_path = os.path.join(self.root, BUNDLE_CSS)
        if os.environ.get("DECKGL_MARIMO_SKIP_JS_BUILD"):
            return
        # hatchling signals editable installs via `version` ('standard' | 'editable')
        if version == "editable" and os.path.exists(bundle_path):
            return

        npm = shutil.which("npm")
        if npm is None:
            if os.path.exists(bundle_path) and os.path.exists(css_path):
                return  # pre-built bundle present; ship it as-is
            raise RuntimeError(
                "Building deckgl-marimo from source requires Node.js 20+ and npm to "
                "compile the deck.gl bundle (cd js && npm ci && npm run build). "
                "Install Node or install a prebuilt wheel from PyPI instead."
            )
        js_dir = os.path.join(self.root, JS_DIR)
        subprocess.run([npm, "ci"], cwd=js_dir, check=True)
        subprocess.run([npm, "run", "build"], cwd=js_dir, check=True)
        for path, rel in ((bundle_path, BUNDLE_JS), (css_path, BUNDLE_CSS)):
            if not os.path.exists(path):
                raise RuntimeError(f"JS build completed but {rel} was not produced")
