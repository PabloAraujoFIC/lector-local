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
  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const result = (await browser.runtime.sendMessage({
          kind: "status",
        })) as { state: State | null; connected: boolean; error: string };
        if (active) {
          setState(result.state);
          setConnected(result.connected);
          setConnectionError(result.error);
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
    try {
      setState(await send("state"));
      setConnected(true);
      setConnectionError("");
    } catch (e) {
      setConnected(false);
      setConnectionError((e as Error).message);
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
      {(connectionError || error) && (
        <p className="error-banner" role="alert">
          {connectionError || error}
        </p>
      )}
      {!connected && (
        <button onClick={() => void reconnect()}>Reintentar conexión</button>
      )}
      {state?.error && <p className="error-banner">{state.error.message}</p>}
      <Privacy />
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<Popup />);
