import { chromium } from "playwright";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
const root = process.cwd();
const home = await mkdtemp(path.join(tmpdir(), "lector-chromium-"));
const data = path.join(home, "data");
const extension = path.join(root, "apps/browser-extension/dist/chromium");
const logs = [];
let context;
const send = (page, command, payload = {}) =>
  page.evaluate(
    async ({ command, payload }) =>
      chrome.runtime.sendMessage({
        kind: "request",
        request: {
          protocol_version: 1,
          type: "command",
          id: crypto.randomUUID(),
          command,
          payload,
        },
      }),
    { command, payload },
  );
try {
  context = await chromium.launchPersistentContext(path.join(home, "profile"), {
    channel: "chromium",
    headless: true,
    viewport: { width: 1280, height: 800 },
    env: {
      ...process.env,
      HOME: home,
      XDG_CONFIG_HOME: path.join(home, ".config"),
      LECTOR_DATA_DIR: data,
    },
    args: [
      "--no-sandbox",
      `--disable-extensions-except=${extension}`,
      `--load-extension=${extension}`,
    ],
  });
  const worker =
    context.serviceWorkers()[0] ??
    (await context.waitForEvent("serviceworker"));
  const id = new URL(worker.url()).host;
  const page = await context.newPage();
  page.on("pageerror", (error) => logs.push(error.message));
  await page.goto(`chrome-extension://${id}/popup.html`);
  const missing = await send(page, "state");
  if (missing.success !== false) throw new Error("Missing host not detected");
  const host = path.join(home, "lector-host");
  await writeFile(
    host,
    `#!/bin/sh\nexport LECTOR_DATA_DIR='${data}'\nexec '${root}/artifacts/core/lector-core/lector-core' native-host 2>> '${root}/artifacts/validation/logs/chromium-host.log'\n`,
    { mode: 0o755 },
  );
  for (const directory of [
    path.join(home, "profile", "NativeMessagingHosts"),
    ...["google-chrome", "chromium", "google-chrome-for-testing"].map(
      (folder) => path.join(home, ".config", folder, "NativeMessagingHosts"),
    ),
  ]) {
    await mkdir(directory, { recursive: true });
    await writeFile(
      path.join(directory, "org.lector.local.json"),
      JSON.stringify({
        name: "org.lector.local",
        description: "Lector Local smoke",
        path: host,
        type: "stdio",
        allowed_origins: [`chrome-extension://${id}/`],
      }),
    );
  }
  await page.waitForTimeout(1000);
  const connected = await send(page, "state");
  if (!connected.success) throw new Error(JSON.stringify(connected));
  const updated = await send(page, "settings", { values: { speed: 1.15 } });
  if (updated.payload.settings.speed !== 1.15)
    throw new Error("Settings did not roundtrip");
  await page.reload();
  await page.waitForTimeout(1000);
  await mkdir(path.join(root, "store/chrome/screenshots"), { recursive: true });
  await page.screenshot({
    path: path.join(
      root,
      "store/chrome/screenshots/popup-connected-1280x800.png",
    ),
  });
  const article = await context.newPage();
  await article.goto("https://es.wikipedia.org/wiki/Lectura", {
    waitUntil: "domcontentloaded",
  });
  if (!(await article.locator("body").innerText()).includes("Lectura"))
    throw new Error("Wikipedia content missing");
  if (logs.length) throw new Error(logs.join("\n"));
  const report = {
    browser: await context.browser().version(),
    extensionId: id,
    result: "passed",
    checks: [
      "production extension loaded",
      "missing host error",
      "real Native Messaging to packaged runtime",
      "settings roundtrip",
      "popup rendered without page errors",
      "Wikipedia loaded in real browser",
    ],
    limitations: [
      "activeTab article action requires user gesture; Wikipedia extraction is additionally tested in jsdom and Zen",
    ],
  };
  await mkdir(path.join(root, "artifacts/validation"), { recursive: true });
  await writeFile(
    path.join(root, "artifacts/validation/chromium.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(JSON.stringify(report));
} finally {
  if (context) await context.close();
  try {
    const endpoint = JSON.parse(
      await readFile(path.join(data, "endpoint.json"), "utf8"),
    );
    process.kill(endpoint.pid, "SIGTERM");
  } catch {}
  await rm(home, { recursive: true, force: true });
}
