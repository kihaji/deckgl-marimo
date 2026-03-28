import { build, context } from "esbuild";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const watching = process.argv.includes("--watch");

const config = {
  entryPoints: [resolve(__dirname, "src/index.js")],
  bundle: true,
  minify: !watching,
  format: "esm",
  outfile: resolve(
    __dirname,
    "../src/deckgl_marimo/static/deckgl-marimo.bundle.js"
  ),
  external: [],
  loader: {
    ".css": "text",
  },
  define: {
    "process.env.NODE_ENV": '"production"',
  },
  logLevel: "info",
};

if (watching) {
  const ctx = await context(config);
  await ctx.watch();
  console.log("Watching for changes...");
} else {
  await build(config);
}
