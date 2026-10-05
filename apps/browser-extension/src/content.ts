import browser from "webextension-polyfill";
import { extractArticle, extractFrom } from "./extraction";

// Prevent duplicated listeners when activeTab scripts are injected repeatedly.
const marker = "data-lector-local-active";
if (!document.documentElement.hasAttribute(marker)) {
  document.documentElement.setAttribute(marker, "");
  let selecting = false;
  let floating = false;
  let paragraphId: number | null = null;
  let readingElements: (HTMLElement | null)[] = [];
  const mapReading = (text: string) => {
    const candidates = Array.from(
      document.querySelectorAll("h1,h2,h3,h4,p,li,blockquote"),
    );
    const clean = (value: string) => value.replace(/\s+/g, " ").trim();
    let cursor = 0;
    readingElements = text
      .split("\n\n")
      .filter((value) => value.trim())
      .map((value) => {
        const found = candidates.findIndex(
          (element, index) =>
            index >= cursor &&
            clean(element.textContent ?? "") === clean(value),
        );
        if (found < 0) return null;
        cursor = found + 1;
        return candidates[found] as HTMLElement;
      });
  };
  let highlighted: HTMLElement | null = null;
  let originalOutline = "";
  let outlinePriority = "";
  const button = document.createElement("button");
  button.textContent = "🔊";
  button.setAttribute("aria-label", "Leer selección con Lector Local");
  Object.assign(button.style, {
    position: "fixed",
    zIndex: "2147483647",
    border: "1px solid #6c8a4c",
    borderRadius: "50%",
    width: "38px",
    height: "38px",
    background: "#c0db96",
    cursor: "pointer",
    display: "none",
  });
  document.addEventListener(
    "click",
    (event) => {
      if (
        !selecting ||
        !event.isTrusted ||
        !(event.target instanceof Element) ||
        event.target === button
      )
        return;
      event.preventDefault();
      event.stopPropagation();
      selecting = false;
      document.body.style.cursor = "";
      try {
        const value = extractFrom(document, event.target);
        mapReading(value.text);
        void browser.runtime.sendMessage({ kind: "speak", ...value });
      } catch (error) {
        window.alert((error as Error).message);
      }
    },
    true,
  );
  document.addEventListener("mouseup", (event) => {
    if (!floating || !event.isTrusted) return;
    const selection = window.getSelection()?.toString().trim();
    if (selection) {
      if (!button.isConnected) document.body.append(button);
      button.style.display = "block";
      button.style.left =
        Math.min(event.clientX + 10, window.innerWidth - 50) + "px";
      button.style.top = Math.max(5, event.clientY - 48) + "px";
    } else button.style.display = "none";
  });
  button.addEventListener("mousedown", (event) => event.preventDefault());
  button.addEventListener("click", (event) => {
    if (!event.isTrusted) return;
    const text = window.getSelection()?.toString();
    if (text) {
      mapReading(text);
      void browser.runtime.sendMessage({
        kind: "speak",
        text: text.slice(0, 200_000),
        title: document.title,
      });
    }
    button.style.display = "none";
  });
  browser.runtime.onMessage.addListener((message: unknown) => {
    if (!message || typeof message !== "object") return undefined;
    const msg = message as {
      kind: string;
      floating?: boolean;
      paragraph_id?: number | null;
      autoscroll?: boolean;
    };
    if (msg.kind === "article") {
      try {
        const value = extractArticle(document);
        mapReading(value.text);
        return Promise.resolve(value);
      } catch (error) {
        return Promise.resolve({ error: (error as Error).message });
      }
    }
    if (msg.kind === "from") {
      selecting = true;
      document.body.style.cursor = "crosshair";
      return Promise.resolve({ ok: true });
    }
    if (msg.kind === "selection") {
      const text = window.getSelection()?.toString() ?? "";
      mapReading(text);
      return Promise.resolve({ text, title: document.title });
    }
    if (msg.kind === "preferences") {
      floating = !!msg.floating;
      return Promise.resolve({ ok: true });
    }
    if (msg.kind === "highlight" && msg.paragraph_id !== paragraphId) {
      paragraphId = msg.paragraph_id ?? null;
      if (highlighted) {
        highlighted.style.setProperty(
          "outline",
          originalOutline,
          outlinePriority,
        );
        highlighted = null;
      }
      const element = paragraphId == null ? null : readingElements[paragraphId];
      if (element) {
        highlighted = element;
        originalOutline = element.style.getPropertyValue("outline");
        outlinePriority = element.style.getPropertyPriority("outline");
        element.style.outline = "2px solid #9abd70";
        if (msg.autoscroll)
          element.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
    return undefined;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      selecting = false;
      document.body.style.cursor = "";
      button.style.display = "none";
    }
  });
}
