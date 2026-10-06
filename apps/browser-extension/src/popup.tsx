import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import browser from "webextension-polyfill";
import { Controls, Privacy } from "@lector/ui";
import {
  request,
  unwrap,
  type Send,
  type State,
  type Response,
} from "@lector/types";
import "@lector/ui/style.css";
import "./popup.css";
const installationURL = `https://github.com/PabloAraujoFIC/lector-local/releases/tag/v${browser.runtime.getManifest().version}`;
const send: Send = async (command, payload = {}) =>
  unwrap(
    (await browser.runtime.sendMessage({
      kind: "request",
      request: request(command, payload),
    })) as Response<never>,
  );
function Popup() {
  const [state, setState] = useState<State | null>(null);
  const [error, setError] = useState("");
  const [connectionError, setConnectionError] = useState("");
  const [connected, setConnected] = useState(false);
  const [hostMissing, setHostMissing] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const result = (await browser.runtime.sendMessage({
          kind: "status",
        })) as {
          state: State | null;
          connected: boolean;
          error: string;
          hostMissing: boolean;
        };
        if (active) {
          setState(result.state);
          setConnected(result.connected);
          setConnectionError(result.error);
          setHostMissing(result.hostMissing);
        }
      } catch (e) {
        if (active) setConnectionError((e as Error).message);
      }
    };
    void send("state")
      .then((value) => {
        if (active) {
          setState(value);
          setConnected(true);
          setHostMissing(false);
          setConnectionError("");
        }
      })
      .catch((e) => {
        if (active) setConnectionError(e.message);
      });
    const timer = setInterval(() => void poll(), 400);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);
  const reconnect = async () => {
    setError("");
    setConnectionError("");
    setReconnecting(true);
    try {
      setState(await send("state"));
      setConnected(true);
      setHostMissing(false);
      setConnectionError("");
    } catch (e) {
      setConnected(false);
      setConnectionError((e as Error).message);
    } finally {
      setReconnecting(false);
    }
  };
  const read = async (mode: string) => {
    setError("");
    try {
      const result = (await browser.runtime.sendMessage({
        kind: "page",
        mode,
      })) as { success?: boolean; error?: { message: string } };
      if (result.success === false) throw new Error(result.error?.message);
      if (mode === "from") window.close();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <div className="popup">
      <div className="popup-brand">
        ◖ Lector <span>Local</span>
        <small>
          <i className="status-dot" />
          {connected ? "Conectado" : "Sin conectar"}
        </small>
      </div>
      <h2>{state?.document?.title ?? "Dale voz a esta página"}</h2>
      <p className="subtitle">Voz local. Tu contenido permanece contigo.</p>
      {hostMissing && (
        <section
          className="installation-panel"
          aria-labelledby="installation-title"
        >
          <h3 id="installation-title">Necesitas instalar Lector Local</h3>
          <p>
            La aplicación de escritorio genera la voz en tu ordenador. Elige el
            instalador de tu sistema en GitHub.
          </p>
          <a
            className="download-button"
            href={installationURL}
            target="_blank"
            rel="noopener noreferrer"
          >
            Descargar aplicación
          </a>
          <a
            className="installation-link"
            href={installationURL}
            target="_blank"
            rel="noopener noreferrer"
          >
            Ver instaladores e instrucciones en GitHub
          </a>
          <p>
            Si ya la tienes, ábrela y registra tu navegador desde Ajustes →
            Escucha desde tu navegador. En Zen, usa Registrar Firefox.
          </p>
          <button disabled={reconnecting} onClick={() => void reconnect()}>
            Ya la instalé — reintentar
          </button>
        </section>
      )}
      <div hidden={hostMissing}>
        <div className="page-actions">
          <button onClick={() => void read("selection")}>Leer selección</button>
          <button onClick={() => void read("article")}>Leer artículo</button>
          <button onClick={() => void read("from")}>Leer desde aquí →</button>
        </div>
        <Controls compact state={state} send={send} onError={setError} />
        <label className="popup-language">
          Idioma
          <select
            aria-label="Idioma"
            value={state?.settings.language ?? "es"}
            onChange={(e) => {
              const map: Record<string, string> = {
                es: "ef_dora",
                "en-us": "af_heart",
                "en-gb": "bf_emma",
                "fr-fr": "ff_siwis",
                it: "if_sara",
                "pt-br": "pf_dora",
              };
              void send("settings", {
                values: {
                  language: e.target.value,
                  voice: map[e.target.value],
                  engine: "kokoro",
                },
              }).catch((error) => setError(error.message));
            }}
          >
            {[
              ["es", "Español"],
              ["en-us", "Inglés (EE. UU.)"],
              ["en-gb", "Inglés (Reino Unido)"],
              ["fr-fr", "Francés"],
              ["it", "Italiano"],
              ["pt-br", "Portugués"],
            ].map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {((!hostMissing && connectionError) || error) && (
        <p className="error-banner" role="alert">
          {error || connectionError}
        </p>
      )}
      {!connected && !hostMissing && (
        <button disabled={reconnecting} onClick={() => void reconnect()}>
          Reintentar conexión
        </button>
      )}
      {state?.error && <p className="error-banner">{state.error.message}</p>}
      <Privacy />
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<Popup />);
