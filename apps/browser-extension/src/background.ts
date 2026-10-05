import browser from "webextension-polyfill";
import {
  request,
  type Request,
  type Response,
  type State,
} from "@lector/types";

const HOST = "org.lector.local";
let port: ReturnType<typeof browser.runtime.connectNative> | null = null;
let state: State | null = null;
let lastError = "";
let activeTab: number | undefined;
let readingDocument: string | undefined;
const pendingSpeak = new Set<string>();
const pending = new Map<
  string,
  {
    resolve: (value: Response<unknown>) => void;
    reject: (error: Error) => void;
    timer: ReturnType<typeof setTimeout>;
  }
>();
function connect() {
  if (port) return port;
  port = browser.runtime.connectNative(HOST);
  const nativePort = port;
  port.onMessage.addListener((message) => {
    const response = message as Response<State> & { event?: string };
    if (response.protocol_version !== 1) {
      lastError = "Host incompatible: actualiza Lector Local.";
      port?.disconnect();
      return;
    }
    if (response.type === "response") {
      const item = pending.get(response.id);
      if (item) {
        clearTimeout(item.timer);
        pending.delete(response.id);
        if (
          response.payload &&
          "status" in response.payload &&
          pendingSpeak.has(response.id)
        ) {
          readingDocument = response.payload.document?.id;
          pendingSpeak.delete(response.id);
        }
        item.resolve(response);
      }
    }
    if (response.payload && "status" in response.payload) {
      state = response.payload;
      lastError = "";
      void browser.action.setBadgeText({ text: "" });
    }
    if (state && activeTab != null) {
      if (state.document?.id === readingDocument)
        void browser.tabs
          .sendMessage(activeTab, {
            kind: "highlight",
            paragraph_id: state.paragraph_id,
            autoscroll: state.settings.autoscroll,
          })
          .catch(() => {});
      void browser.tabs
        .sendMessage(activeTab, {
          kind: "preferences",
          floating: state.settings.floating_button,
        })
        .catch(() => {});
    }
  });
  port.onDisconnect.addListener(() => {
    const detail =
      nativePort.error?.message ??
      "Host local desconectado. Instala o registra Lector Local.";
    lastError =
      /No such native application|Specified native messaging host not found/i.test(
        detail,
      )
        ? "No se encuentra el motor local de Lector Local. Abre la aplicación de escritorio → Ajustes → Escucha desde tu navegador y registra el host. En Zen usa Registrar Firefox. Después pulsa Reintentar conexión."
        : detail;
    port = null;
    for (const item of pending.values()) {
      clearTimeout(item.timer);
      item.reject(new Error(lastError));
    }
    pending.clear();
    pendingSpeak.clear();
  });
  return port;
}
async function dispatch(message: Request): Promise<Response<unknown>> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(message.id);
      pendingSpeak.delete(message.id);
      reject(new Error("El core local no respondió a tiempo."));
    }, 120000);
    pending.set(message.id, { resolve, reject, timer });
    if (message.command === "speak_text") pendingSpeak.add(message.id);
    try {
      connect().postMessage(message);
    } catch (error) {
      clearTimeout(timer);
      pending.delete(message.id);
      reject(error as Error);
    }
  });
}
async function inject(tabId: number) {
  activeTab = tabId;
  await browser.scripting.executeScript({
    target: { tabId },
    files: ["content.js"],
  });
  if (state)
    await browser.tabs.sendMessage(tabId, {
      kind: "preferences",
      floating: state.settings.floating_button,
    });
}
async function readPage(tabId: number, kind: "article" | "from") {
  await inject(tabId);
  const value = (await browser.tabs.sendMessage(tabId, { kind })) as {
    text?: string;
    title?: string;
    error?: string;
  };
  if (value.error) throw new Error(value.error);
  if (value.text)
    return dispatch(
      request("speak_text", {
        text: value.text,
        title: value.title || "Artículo",
      }),
    );
  return { ok: true };
}
function record(error: unknown) {
  lastError = (error as Error).message || String(error);
  void browser.action.setBadgeText({ text: "!" });
  void browser.action.setBadgeBackgroundColor({ color: "#a55638" });
}
browser.runtime.onInstalled.addListener(() => {
  void browser.contextMenus.removeAll().then(() => {
    browser.contextMenus.create({
      id: "selection",
      title: "Leer selección",
      contexts: ["selection"],
    });
    browser.contextMenus.create({
      id: "article",
      title: "Leer artículo",
      contexts: ["page"],
    });
    browser.contextMenus.create({
      id: "from",
      title: "Leer desde aquí…",
      contexts: ["page"],
    });
    browser.contextMenus.create({
      id: "pause",
      title: "Pausar / reanudar lectura",
      contexts: ["all"],
    });
    browser.contextMenus.create({
      id: "stop",
      title: "Detener lectura",
      contexts: ["all"],
    });
  });
});
browser.contextMenus.onClicked.addListener((info, tab) => {
  const act = async () => {
    if (info.menuItemId === "selection") {
      activeTab = undefined;
      return dispatch(
        request("speak_text", {
          text: (info.selectionText ?? "").slice(0, 200000),
          title: tab?.title || "Selección",
        }),
      );
    }
    if (info.menuItemId === "pause")
      return dispatch(request(state?.status === "paused" ? "resume" : "pause"));
    if (info.menuItemId === "stop") return dispatch(request("stop"));
    if (tab?.id != null)
      return readPage(tab.id, info.menuItemId === "from" ? "from" : "article");
  };
  void act().catch(record);
});
browser.runtime.onMessage.addListener(
  (message: unknown, sender: browser.Runtime.MessageSender) => {
    const msg = message as {
      kind: string;
      request?: Request;
      text?: string;
      title?: string;
      mode?: "article" | "from" | "selection";
    };
    const process = async () => {
      if (sender.id !== browser.runtime.id) throw new Error("Origen inválido.");
      if (sender.tab && !sender.url?.startsWith(browser.runtime.getURL(""))) {
        if (
          msg.kind !== "speak" ||
          typeof msg.text !== "string" ||
          msg.text.length > 200000
        )
          throw new Error("Mensaje de página inválido.");
        activeTab = sender.tab.id;
        return dispatch(
          request("speak_text", {
            text: msg.text,
            title: typeof msg.title === "string" ? msg.title : "Página",
          }),
        );
      }
      if (msg.kind === "status")
        return { state, connected: port !== null, error: lastError };
      if (msg.kind === "request" && msg.request) {
        if (
          ![
            "state",
            "play",
            "pause",
            "resume",
            "stop",
            "next",
            "previous",
            "seek",
            "settings",
            "models",
            "clear_cache",
          ].includes(msg.request.command)
        )
          throw new Error("Comando no permitido.");
        return dispatch(msg.request);
      }
      if (msg.kind === "page") {
        const [tab] = await browser.tabs.query({
          active: true,
          currentWindow: true,
        });
        if (tab?.id == null) throw new Error("No hay pestaña activa.");
        if (msg.mode === "selection") {
          await inject(tab.id);
          const value = (await browser.tabs.sendMessage(tab.id, {
            kind: "selection",
          })) as { text: string; title: string };
          return dispatch(request("speak_text", value));
        }
        return readPage(tab.id, msg.mode === "from" ? "from" : "article");
      }
      throw new Error("Mensaje desconocido.");
    };
    return process().catch((error) => {
      record(error);
      return { success: false, error: { message: (error as Error).message } };
    });
  },
);
