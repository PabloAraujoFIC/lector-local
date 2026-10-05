import { ReaderView } from "./ReaderView";
import { SettingsView } from "./SettingsView";
import { PrivacyView } from "./PrivacyView";
import { useCallback, useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import {
  BookOpen,
  FolderOpen,
  Headphones,
  Settings2,
  ShieldCheck,
  ChevronRight,
  X,
} from "lucide-react";
import { Controls } from "@lector/ui";
import type { Models, Paragraph, Settings, State } from "@lector/types";
import { isDesktop, send } from "./client";

const labels: Record<State["status"], string> = {
  idle: "Listo para leer",
  ready: "Listo para leer",
  playing: "Leyendo",
  paused: "En pausa",
  stopped: "Detenido",
  buffering: "Preparando voz local…",
  finished: "Lectura completada",
  error: "Requiere atención",
};
export default function App() {
  const [state, setState] = useState<State | null>(null);
  const [error, setError] = useState("");
  const [view, setView] = useState<"reader" | "settings" | "privacy">("reader");
  const [paragraphs, setParagraphs] = useState<Paragraph[]>([]);
  const [page, setPage] = useState(0);
  const [models, setModels] = useState<Models | null>(null);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const docId = state?.document?.id;
  const settings = state?.settings;
  const current = useRef<HTMLButtonElement | null>(null);
  const load = useCallback(async (path: string) => {
    setBusy(true);
    setError("");
    try {
      setState(await send("load_document", { path }));
      setView("reader");
      setPage(0);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);
  useEffect(() => {
    if (!isDesktop) return;
    let active = true;
    let polling = false;
    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        const value = await send("state");
        if (active) setState(value);
      } catch (e) {
        if (active) setError((e as Error).message);
      } finally {
        polling = false;
      }
    };
    void poll();
    const interval = setInterval(() => void poll(), 450);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);
  useEffect(() => {
    if (!isDesktop) return;
    let disposed = false;
    let off: (() => void) | undefined;
    void getCurrentWebviewWindow()
      .onDragDropEvent((event) => {
        if (event.payload.type === "drop" && event.payload.paths[0])
          void load(event.payload.paths[0]);
      })
      .then((fn) => {
        if (disposed) fn();
        else off = fn;
      });
    return () => {
      disposed = true;
      off?.();
    };
  }, [load]);
  useEffect(() => {
    if (!docId) return;
    let active = true;
    void send<{ paragraphs: Paragraph[] }>("document_page", {
      start: page * 80,
      count: 80,
    })
      .then((value) => {
        if (active) setParagraphs(value.paragraphs);
      })
      .catch((e) => setError(e.message));
    return () => {
      active = false;
    };
  }, [docId, page]);
  useEffect(() => {
    if (
      settings?.autoscroll &&
      state?.paragraph_id != null &&
      state.status === "playing"
    ) {
      const target = Math.floor(state.paragraph_id / 80);
      if (target !== page) setPage(target);
      else
        current.current?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
    }
  }, [state?.paragraph_id, state?.status, settings?.autoscroll, page]);
  useEffect(() => {
    if (view === "settings" && isDesktop)
      void send<Models>("models")
        .then(setModels)
        .catch((e) => setError(e.message));
  }, [view]);
  const choose = async () => {
    if (!isDesktop) {
      setError(
        "Abre la aplicación con npm run dev para conectar con el core local.",
      );
      return;
    }
    const path = await open({
      multiple: false,
      filters: [
        {
          name: "Documentos",
          extensions: [
            "txt",
            "pdf",
            "odt",
            "docx",
            "epub",
            "md",
            "html",
            "htm",
            "rtf",
          ],
        },
      ],
    });
    if (path) await load(path);
  };
  const update = async (values: Partial<Settings>) => {
    try {
      setState(await send("settings", { values }));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const install = async (engine: "kokoro" | "piper") => {
    setBusy(true);
    setError("");
    try {
      await invoke("install_model", { engine });
      setModels(await send<Models>("models"));
      await update({
        engine,
        voice: engine === "piper" ? "piper_es" : "ef_dora",
        language: "es",
      });
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="app-shell" data-theme={settings?.theme ?? "dark"}>
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">
            <Headphones size={21} />
          </span>
          <span>
            Lector<span className="brand-light"> Local</span>
          </span>
        </div>
        <span className="workspace-label">TU ESPACIO DE LECTURA</span>
        <nav>
          <button
            className={view === "reader" ? "active" : ""}
            onClick={() => setView("reader")}
          >
            <BookOpen size={18} />
            Mi lectura
            <span className="nav-count">{state?.document ? 1 : 0}</span>
          </button>
          <button
            className={view === "settings" ? "active" : ""}
            onClick={() => setView("settings")}
          >
            <Settings2 size={18} />
            Ajustes
          </button>
          <button
            className={view === "privacy" ? "active" : ""}
            onClick={() => setView("privacy")}
          >
            <ShieldCheck size={18} />
            Privacidad
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <span className="status-dot" />
            <div>
              <strong>Tu voz, en tu dispositivo</strong>
              <p>Procesamiento 100 % local</p>
            </div>
            <ShieldCheck size={16} />
          </div>
          <span className="version">
            LECTOR LOCAL <span>v0.1.0</span>
          </span>
        </div>
      </aside>
      <main className="main">
        <header>
          <div className="breadcrumb">
            Tu biblioteca <ChevronRight size={13} />
            <span>
              {view === "reader"
                ? "Mi lectura"
                : view === "settings"
                  ? "Ajustes"
                  : "Privacidad"}
            </span>
          </div>
          <button
            className="open-button"
            onClick={() => void choose()}
            disabled={busy}
          >
            <FolderOpen size={16} />
            Abrir documento<span className="keycap">↗</span>
          </button>
        </header>
        <div className="content">
          {(error || state?.error) && (
            <div className="error-banner">
              {error || state?.error?.message}
              <button aria-label="Cerrar aviso" onClick={() => setError("")}>
                <X size={14} />
              </button>
            </div>
          )}
          {!isDesktop && (
            <div className="preview-note">
              <span className="status-dot" />
              Vista de interfaz · inicia Tauri para conectar el lector local
            </div>
          )}
          {view === "reader" ? (
            <ReaderView
              state={state}
              busy={busy}
              choose={choose}
              paragraphs={paragraphs}
              query={query}
              setQuery={setQuery}
              page={page}
              setPage={setPage}
              setError={setError}
              current={current}
            />
          ) : view === "privacy" ? (
            <PrivacyView setError={setError} />
          ) : (
            <SettingsView
              models={models}
              busy={busy}
              install={install}
              settings={settings}
              update={update}
              setModels={setModels}
              setError={setError}
            />
          )}
        </div>
        <footer className="player-bar">
          <div className="now-reading">
            <span className="cover-mini">
              <BookOpen size={21} />
            </span>
            <div>
              <strong>
                {state?.document?.title ?? "Sin documento abierto"}
              </strong>
              <span>
                <i
                  className={
                    "status-dot " +
                    (state?.status === "playing" ? "playing" : "")
                  }
                />
                {busy
                  ? "Procesando…"
                  : state
                    ? labels[state.status]
                    : "Core desconectado"}
              </span>
            </div>
          </div>
          <div className="player-center">
            <Controls state={state} send={send} onError={setError} />
            <input
              className="progress"
              aria-label="Progreso de lectura"
              type="range"
              min="0"
              max={Math.max(0, (state?.document?.chunk_count ?? 1) - 1)}
              value={state?.chunk ?? 0}
              disabled={!state?.document}
              onChange={(e) =>
                void send("seek", { chunk: Number(e.target.value) }).catch(
                  (e) => setError(e.message),
                )
              }
            />
          </div>
          <div className="player-end">
            <span>
              {Math.round((state?.progress ?? 0) * 100)}
              <small>%</small>
            </span>
            <p>
              <Headphones size={13} />
              Voz local
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
