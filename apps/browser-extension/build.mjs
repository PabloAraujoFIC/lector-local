import { build as viteBuild } from "vite";
import { build } from "esbuild";
import { readFile, writeFile, rm, cp, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL(".", import.meta.url));
const read = async (path) =>
  JSON.parse(await readFile(new URL(path, import.meta.url), "utf8"));
const config = await read("../../core/reader_core/distribution.json");
const { version } = await read("../../package.json");
const channel = process.env.LECTOR_CHANNEL ?? "production";
if (!["production", "development"].includes(channel))
  throw new Error("Unknown distribution channel");
await rm(root + "dist", { recursive: true, force: true });
await viteBuild({
  root,
  build: {
    outDir: "dist/common",
    sourcemap: false,
    rollupOptions: { input: root + "popup.html" },
  },
});
await build({
  entryPoints: [root + "src/background.ts", root + "src/content.ts"],
  bundle: true,
  outdir: root + "dist/common",
  format: "iife",
  target: "es2022",
  minify: true,
  sourcemap: false,
  define: { __NATIVE_HOST__: JSON.stringify(config.nativeHost) },
});
const base = await read("manifests/base.json");
for (const browser of ["chromium", "firefox"]) {
  const directory = root + "dist/" + browser;
  await mkdir(directory, { recursive: true });
  await cp(root + "dist/common", directory, { recursive: true });
  await cp(root + "icons", directory + "/icons", { recursive: true });
  const manifest = {
    ...base,
    ...(await read("manifests/" + browser + ".json")),
    version,
  };
  if (browser === "firefox")
    manifest.browser_specific_settings.gecko.id = config.firefoxId;
  if (browser === "chromium" && channel === "development")
    manifest.key = config.development.chromiumKey;
  await writeFile(
    directory + "/manifest.json",
    JSON.stringify(manifest, null, 2) + "\n",
  );
}
