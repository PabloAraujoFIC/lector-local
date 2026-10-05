import type { RefObject } from "react";
import {
  ShieldCheck,
  FileText,
  Upload,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import type { Paragraph, State } from "@lector/types";
import { send } from "./client";
interface Props {
  state: State | null;
  busy: boolean;
  choose: () => Promise<void>;
  paragraphs: Paragraph[];
  query: string;
  setQuery: (value: string) => void;
  page: number;
  setPage: (value: number) => void;
  setError: (value: string) => void;
  current: RefObject<HTMLButtonElement | null>;
}
export function ReaderView({
  state,
  busy,
  choose,
  paragraphs,
  query,
  setQuery,
  page,
  setPage,
  setError,
  current,
}: Props) {
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">UN MOMENTO PARA ESCUCHAR</div>
          <h1>
            Mi lectura<span>.</span>
          </h1>
          <p>Abre un documento. Encuentra tu ritmo.</p>
        </div>
        <span className="private-badge">
          <ShieldCheck size={14} />
          Solo en tu dispositivo
        </span>
      </div>
      {!state?.document ? (
        <div className="empty-reader">
          <div className="paper-stack">
            <div />
            <div />
            <FileText size={43} strokeWidth={1} />
          </div>
          <span className="eyebrow">LAS PALABRAS COBRAN VOZ</span>
          <h2>Tu próxima lectura empieza aquí</h2>
          <p>
            Arrastra un documento y deja que una voz local
            <br />
            te acompañe, párrafo a párrafo.
          </p>
          <button
            className="primary"
            onClick={() => void choose()}
            disabled={busy}
          >
            <Upload size={16} />
            {busy ? "Abriendo…" : "Elegir un documento"}
            <ArrowUpRight size={15} />
          </button>
          <div className="formats">
            TXT <span>·</span> PDF <span>·</span> EPUB <span>·</span> DOCX{" "}
            <span>·</span> ODT <span>·</span> y más
          </div>
          <div className="empty-divider" />
          <div className="offline-note">
            <ShieldCheck size={15} />
            <span>Sin conexión. Sin cuentas. A tu ritmo.</span>
          </div>
        </div>
      ) : (
        <section className="document-reader">
          <div className="document-heading">
            <div>
              <span className="document-type">
                {state.document.source_type.toUpperCase()}
              </span>
              <h2>{state.document.title}</h2>
              <p>
                {state.document.paragraph_count} párrafos ·{" "}
                {Math.round(state.progress * 100)} % leído
              </p>
            </div>
            <label className="search">
              <Search size={15} />
              <input
                value={query}
                placeholder="Buscar en esta página"
                aria-label="Buscar texto"
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
          </div>
          <div className="paragraphs">
            {paragraphs
              .filter(
                (p) =>
                  !query || p.text.toLowerCase().includes(query.toLowerCase()),
              )
              .map((p) => (
                <button
                  ref={state.paragraph_id === p.id ? current : undefined}
                  key={p.id}
                  className={
                    "paragraph " +
                    (state.paragraph_id === p.id ? "current" : "")
                  }
                  onClick={() =>
                    void send("seek", { paragraph: p.id })
                      .then(() => send("play"))
                      .catch((e) => setError(e.message))
                  }
                >
                  <span className="paragraph-number">
                    {String(p.id + 1).padStart(2, "0")}
                  </span>
                  <span>
                    {state.paragraph_id === p.id &&
                    state.start_offset != null &&
                    state.end_offset != null ? (
                      <>
                        {p.text.slice(0, state.start_offset)}
                        <mark>
                          {p.text.slice(state.start_offset, state.end_offset)}
                        </mark>
                        {p.text.slice(state.end_offset)}
                      </>
                    ) : (
                      p.text
                    )}
                  </span>
                </button>
              ))}
          </div>
          <div className="pagination">
            <button disabled={page === 0} onClick={() => setPage(page - 1)}>
              <ChevronLeft size={16} />
              Anterior
            </button>
            <span>
              Página {page + 1} de{" "}
              {Math.ceil(state.document.paragraph_count / 80)}
            </span>
            <button
              disabled={(page + 1) * 80 >= state.document.paragraph_count}
              onClick={() => setPage(page + 1)}
            >
              Siguiente
              <ChevronRight size={16} />
            </button>
          </div>
        </section>
      )}
      <div className="reading-tips">
        <div>
          <span>01</span>
          <strong>Elige una voz</strong>
          <p>Español natural, sin salir de tu equipo.</p>
        </div>
        <div>
          <span>02</span>
          <strong>Hazlo a tu ritmo</strong>
          <p>Ajusta la velocidad y salta entre párrafos.</p>
        </div>
        <div>
          <span>03</span>
          <strong>Retoma cuando quieras</strong>
          <p>Tu punto de lectura se guarda localmente.</p>
        </div>
      </div>
    </>
  );
}
