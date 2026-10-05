import { build as viteBuild } from "vite";
import { build } from "esbuild";
import { copyFile, mkdir, cp } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL(".", import.meta.url));
await viteBuild({
  root,
  build: {
    outDir: "dist/common",
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
});
for (const browser of ["chromium", "firefox"]) {
  await mkdir(root + "dist/" + browser, { recursive: true });
  await cp(root + "dist/common", root + "dist/" + browser, { recursive: true });
  await copyFile(
    root + "manifests/" + browser + ".json",
    root + "dist/" + browser + "/manifest.json",
  );
}
