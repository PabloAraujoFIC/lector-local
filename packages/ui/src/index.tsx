import {
  Play,
  Pause,
  Square,
  SkipBack,
  SkipForward,
  Volume2,
  ChevronDown,
} from "lucide-react";
import type { Send, State } from "@lector/types";

export const voices = [
  ["ef_dora", "Dora", "es"],
  ["em_alex", "Alex", "es"],
  ["em_santa", "Santa", "es"],
  ["af_heart", "Heart", "en-us"],
  ["bf_emma", "Emma", "en-gb"],
  ["ff_siwis", "Siwis", "fr-fr"],
  ["if_sara", "Sara", "it"],
  ["pf_dora", "Dora", "pt-br"],
  ["piper_es", "Piper · español", "es"],
];
export function Controls({
  state,
  send,
  onError,
  compact = false,
}: {
  state: State | null;
  send: Send;
  onError: (error: string) => void;
  compact?: boolean;
}) {
  const run = (
    command: Parameters<Send>[0],
    payload?: Record<string, unknown>,
  ) => {
    void send(command, payload).catch((e) => onError(String(e.message)));
  };
  const playing = state?.status === "playing" || state?.status === "buffering";
  return (
    <div className={"player-controls " + (compact ? "compact" : "")}>
      <div className="transport">
        <button
          aria-label="Párrafo anterior"
          title="Párrafo anterior"
          disabled={!state?.document}
          onClick={() => run("previous")}
        >
          <SkipBack size={19} />
        </button>
        {!compact && (
          <button
            className="seconds"
            disabled={!state?.document}
            onClick={() => run("seek", { seconds: -10 })}
            aria-label="Retroceder 10 segundos"
          >
            −10<span>s</span>
          </button>
        )}
        <button
          className="play-button"
          aria-label={playing ? "Pausar" : "Reproducir"}
          disabled={!state?.document}
          onClick={() =>
            run(
              playing
                ? "pause"
                : state?.status === "paused"
                  ? "resume"
                  : "play",
            )
          }
        >
          {playing ? (
            <Pause size={24} fill="currentColor" />
          ) : (
            <Play size={24} fill="currentColor" />
          )}
        </button>
        {!compact && (
          <button
            className="seconds"
            disabled={!state?.document}
            onClick={() => run("seek", { seconds: 10 })}
            aria-label="Avanzar 10 segundos"
          >
            +10<span>s</span>
          </button>
        )}
        <button
          aria-label="Párrafo siguiente"
          title="Párrafo siguiente"
          disabled={!state?.document}
          onClick={() => run("next")}
        >
          <SkipForward size={19} />
        </button>
        <button
          aria-label="Detener"
          title="Detener"
          disabled={!state?.document}
          onClick={() => run("stop")}
        >
          <Square size={17} />
        </button>
      </div>
      <div className="voice-settings">
        <label>
          Voz{" "}
          <div className="select-wrap">
            <select
              aria-label="Voz"
              value={state?.settings.voice ?? "ef_dora"}
              onChange={(e) => {
                const voice = voices.find((v) => v[0] === e.target.value)!;
                run("settings", {
                  values: {
                    voice: voice[0],
                    language: voice[2],
                    engine: voice[0] === "piper_es" ? "piper" : "kokoro",
                  },
                });
              }}
            >
              {voices.map(([id, name, language]) => (
                <option key={id} value={id}>
                  {name} · {language}
                </option>
              ))}
            </select>
            <ChevronDown size={13} />
          </div>
        </label>
        <label>
          Velocidad{" "}
          <div className="select-wrap">
            <select
              aria-label="Velocidad"
              value={state?.settings.speed ?? 1}
              onChange={(e) =>
                run("settings", { values: { speed: Number(e.target.value) } })
              }
            >
              {[0.5, 0.75, 1, 1.1, 1.25, 1.5, 1.75, 2].map((n) => (
                <option key={n} value={n}>
                  {n}×
                </option>
              ))}
            </select>
            <ChevronDown size={13} />
          </div>
        </label>
        {!compact && (
          <label className="volume-label">
            <Volume2 size={17} />
            <input
              aria-label="Volumen"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={state?.settings.volume ?? 0.85}
              onChange={(e) =>
                run("settings", { values: { volume: Number(e.target.value) } })
              }
            />
          </label>
        )}
      </div>
    </div>
  );
}
export function Privacy() {
  return (
    <p className="privacy">
      Todo el contenido se procesa localmente en tu dispositivo. Sin cuentas,
      telemetría ni servicios externos de voz.
    </p>
  );
}
