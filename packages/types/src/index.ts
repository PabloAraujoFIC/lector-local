export const PROTOCOL_VERSION = 1;
export type Command =
  | "state"
  | "document_page"
  | "load_document"
  | "speak_text"
  | "play"
  | "pause"
  | "resume"
  | "stop"
  | "next"
  | "previous"
  | "seek"
  | "settings"
  | "clear_cache"
  | "models";
export interface Request {
  protocol_version: 1;
  id: string;
  type: "command";
  command: Command;
  payload: Record<string, unknown>;
}
export interface Settings {
  engine: "kokoro" | "piper";
  voice: string;
  language: string;
  speed: number;
  volume: number;
  device: string;
  cache_mb: number;
  prefetch: number;
  ocr: boolean;
  ocr_language: string;
  autoscroll: boolean;
  floating_button: boolean;
  theme: "dark" | "light";
  pronunciation: Record<string, string>;
}
export interface Paragraph {
  id: number;
  text: string;
  section_id: number;
}
export interface DocumentSummary {
  id: string;
  title: string;
  source_type: string;
  paragraph_count: number;
  chunk_count: number;
}
export interface State {
  status:
    | "idle"
    | "ready"
    | "buffering"
    | "playing"
    | "paused"
    | "stopped"
    | "finished"
    | "error";
  document: DocumentSummary | null;
  chunk: number;
  paragraph_id: number | null;
  start_offset: number | null;
  end_offset: number | null;
  progress: number;
  seconds: number;
  settings: Settings;
  error: { code: string; message: string } | null;
  revision: number;
}
export interface Response<T = State> {
  protocol_version: 1;
  id: string;
  type: "response";
  success: boolean;
  payload?: T;
  error?: { code: string; message: string };
}
export type Send = <T = State>(
  command: Command,
  payload?: Record<string, unknown>,
) => Promise<T>;
export interface Models {
  directory: string;
  kokoro: { installed: boolean; license: string; approximate_mb: number };
  piper: { installed: boolean; license: string };
  cache_bytes: number;
}
export function request(
  command: Command,
  payload: Record<string, unknown> = {},
): Request {
  return {
    protocol_version: 1,
    id: crypto.randomUUID(),
    type: "command",
    command,
    payload,
  };
}
export function unwrap<T>(response: Response<T>): T {
  if (response.protocol_version !== 1)
    throw new Error("Versión del core incompatible.");
  if (!response.success || response.payload === undefined)
    throw new Error(response.error?.message ?? "El core no respondió.");
  return response.payload;
}
