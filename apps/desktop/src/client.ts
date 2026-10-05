import { invoke } from "@tauri-apps/api/core";
import { request, unwrap, type Response, type Send } from "@lector/types";
export const send: Send = async (command, payload = {}) => {
  const response = await invoke<Response<never>>("core_request", {
    message: request(command, payload),
  });
  return unwrap(response);
};
export const isDesktop = "__TAURI_INTERNALS__" in window;
