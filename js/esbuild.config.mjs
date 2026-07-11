import { build, context } from "esbuild";
import { copyFileSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const watching = process.argv.includes("--watch");

const staticDir = resolve(__dirname, "../src/deckgl_marimo/static");

const config = {
  entryPoints: [resolve(__dirname, "src/index.js")],
  bundle: true,
  minify: !watching,
  format: "esm",
  outfile: resolve(staticDir, "deckgl-marimo.bundle.js"),
  external: [],
  loader: {
    ".css": "text",
  },
  define: {
    "process.env.NODE_ENV": '"production"',
  },
  logLevel: "info",
};

// widget.css is hand-written widget chrome (container border, dark-mode
// controls); MapLibre's CSS is inlined into the JS bundle via the "text"
// loader above. Copy it alongside the JS bundle so `static/` is entirely
// a build product.
function copyWidgetCss() {
  mkdirSync(staticDir, { recursive: true });
  copyFileSync(
    resolve(__dirname, "src/widget.css"),
    resolve(staticDir, "deckgl-marimo.bundle.css")
  );
}

if (watching) {
  const ctx = await context(config);
  copyWidgetCss();
  await ctx.watch();
  console.log("Watching for changes...");
} else {
  await build(config);
  copyWidgetCss();
}
