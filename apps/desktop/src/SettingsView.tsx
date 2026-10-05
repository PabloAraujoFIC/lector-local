import { BrowserSetup } from "./BrowserSetup";
import { Check } from "lucide-react";
import type { Models, Settings } from "@lector/types";
import { send } from "./client";
interface Props {
  models: Models | null;
  busy: boolean;
  install: (engine: "kokoro" | "piper") => Promise<void>;
  settings: Settings | undefined;
  update: (values: Partial<Settings>) => Promise<void>;
  setModels: (value: Models) => void;
  setError: (value: string) => void;
}
export function SettingsView({
  models,
  busy,
  install,
  settings,
  update,
  setModels,
  setError,
}: Props) {
  return (
    <>
      <div className="eyebrow">A TU MEDIDA</div>
      <h1>
        Ajustes<span>.</span>
      </h1>
      <div className="settings-card">
        <h2>Motor de voz local</h2>
        <p>
          Descarga una voz una vez. Después, Kokoro y Piper leen sin conexión.
          Al pulsar Descargar aceptas conectar con GitHub (Kokoro) o Hugging
          Face (Piper). Los archivos se verifican con SHA-256.
        </p>
        <p className="model-state">
          {models?.kokoro.installed ? (
            <>
              <Check size={16} />
              Kokoro disponible
            </>
          ) : (
            "Instala el modelo para empezar a escuchar."
          )}
        </p>
        <p className="model-state">
          {models?.piper.installed
            ? "Piper · voz española disponible"
            : "Piper aún no descargado"}
        </p>
        {!models?.kokoro.installed && (
          <button
            className="primary"
            disabled={busy || models?.kokoro.installed}
            onClick={() => void install("kokoro")}
          >
            {busy ? "Descargando y verificando…" : "Descargar Kokoro · 354 MB"}
          </button>
        )}
        {!models?.piper.installed && (
          <button disabled={busy} onClick={() => void install("piper")}>
            {busy ? "Descargando y verificando…" : "Descargar Piper · 77 MB"}
          </button>
        )}
        <p className="path">
          Destino: {models?.directory ?? "directorio local de la aplicación"}
        </p>
        <div className="settings-grid">
          <label>
            Dispositivo
            <select
              value={settings?.device ?? "auto"}
              onChange={(e) => void update({ device: e.target.value })}
            >
              <option value="auto">Automático</option>
              <option value="cpu">CPU</option>
              <option value="cuda">CUDA (requiere runtime GPU)</option>
              <option value="mps" disabled>
                MPS · no disponible en ONNX
              </option>
            </select>
          </label>
          <label>
            Idioma
            <select
              value={settings?.language ?? "es"}
              onChange={(e) => {
                const map: Record<string, string> = {
                  es: "ef_dora",
                  "en-us": "af_heart",
                  "en-gb": "bf_emma",
                  "fr-fr": "ff_siwis",
                  it: "if_sara",
                  "pt-br": "pf_dora",
                };
                void update({
                  language: e.target.value,
                  ...(map[e.target.value]
                    ? { voice: map[e.target.value], engine: "kokoro" as const }
                    : {}),
                });
              }}
            >
              {[
                ["es", "Español"],
                ["auto", "Según la voz"],
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
          <label>
            Caché (MB)
            <input
              type="number"
              min="32"
              max="4096"
              value={settings?.cache_mb ?? 512}
              onChange={(e) =>
                void update({ cache_mb: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Buffer (fragmentos)
            <input
              type="number"
              min="1"
              max="6"
              value={settings?.prefetch ?? 3}
              onChange={(e) =>
                void update({ prefetch: Number(e.target.value) })
              }
            />
          </label>
        </div>
        <label className="toggle">
          <input
            type="checkbox"
            checked={settings?.autoscroll ?? true}
            onChange={(e) => void update({ autoscroll: e.target.checked })}
          />
          Seguir automáticamente el párrafo actual
        </label>
        <label className="toggle">
          <input
            type="checkbox"
            checked={settings?.ocr ?? false}
            onChange={(e) => void update({ ocr: e.target.checked })}
          />
          OCR local para PDF escaneados · español incluido
        </label>
        <label className="toggle">
          <input
            type="checkbox"
            checked={settings?.floating_button ?? false}
            onChange={(e) => void update({ floating_button: e.target.checked })}
          />
          Botón flotante en páginas activadas desde la extensión
        </label>
        <button
          onClick={() =>
            void send("clear_cache")
              .then(() => send<Models>("models"))
              .then(setModels)
              .catch((e) => setError(e.message))
          }
        >
          Vaciar caché ·{" "}
          {models ? Math.round(models.cache_bytes / 1024 / 1024) : 0} MB
        </button>
      </div>
      <BrowserSetup onError={setError} />
    </>
  );
}
