import { ShieldCheck } from "lucide-react";
import { Privacy } from "@lector/ui";
import { send } from "./client";
export function PrivacyView({
  setError,
}: {
  setError: (value: string) => void;
}) {
  return (
    <>
      <div className="eyebrow">PRIVACIDAD POR DISEÑO</div>
      <h1>
        Tu lectura te pertenece<span>.</span>
      </h1>
      <div className="settings-card">
        <ShieldCheck size={40} />
        <h2>Todo permanece en tu equipo</h2>
        <Privacy />
        <p>
          No enviamos documentos, texto, audio ni estadísticas. No hay cuentas
          ni servicios de voz externos. Los motores vienen incluidos. Descarga
          una voz desde Ajustes una vez; después puedes leer sin conexión.
        </p>
        <p>
          Las descargas de modelos solo se realizan cuando las solicitas. El
          historial, preferencias y caché se guardan en el directorio local de
          la aplicación.
        </p>
        <button
          onClick={() =>
            void send("clear_cache").catch((e) => setError(e.message))
          }
        >
          Limpiar caché de audio
        </button>
      </div>
    </>
  );
}
