import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Check, Globe } from "lucide-react";

export function BrowserSetup({
  onError,
}: {
  onError: (message: string) => void;
}) {
  const [id, setId] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const register = async (firefoxOnly: boolean) => {
    setBusy(true);
    setDone(false);
    try {
      await invoke("register_host", { chromiumId: id.trim(), firefoxOnly });
      setDone(true);
    } catch (error) {
      onError(String(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="settings-card browser-setup">
      <Globe size={25} />
      <h2>Escucha desde tu navegador</h2>
      <p>
        Instala la extensión y registra el host para utilizar la misma voz local
        sin abrir el escritorio.
      </p>
      <ol>
        <li>
          En Chromium, Chrome, Edge o Brave, carga la carpeta{" "}
          <code>apps/browser-extension/dist/chromium</code> desde la página de
          extensiones en modo desarrollador.
        </li>
        <li>Copia el ID de la extensión y pégalo aquí.</li>
      </ol>
      <label className="browser-id">
        ID de la extensión Chromium
        <input
          value={id}
          maxLength={32}
          onChange={(event) => setId(event.target.value)}
          placeholder="32 letras de a a p"
          autoComplete="off"
          spellCheck={false}
        />
      </label>
      <div className="browser-buttons">
        <button
          className="primary"
          disabled={busy || !/^[a-p]{32}$/.test(id.trim())}
          onClick={() => void register(false)}
        >
          Registrar navegadores detectados
        </button>
        <button disabled={busy} onClick={() => void register(true)}>
          Registrar Firefox
        </button>
      </div>
      {done && (
        <p className="model-state">
          <Check size={16} />
          Host registrado. Recarga la extensión para conectar.
        </p>
      )}
      <p className="path">
        Firefox: carga el manifest de dist/firefox desde about:debugging. El
        registro utiliza el ID fijo de esa extensión. No se modifica ningún host
        ajeno.
      </p>
    </section>
  );
}
