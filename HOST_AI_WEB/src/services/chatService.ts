import { hostAiApiClient } from "../api/client";
import type { ChatResponse } from "../types/api";

export type ChatInput = {
  mensaje: string;
  contexto?: Record<string, unknown>;
};

export const chatService = {
  send(input: ChatInput): Promise<ChatResponse> {
    return hostAiApiClient.sendChatMessage({
      mensaje: input.mensaje,
      contexto: input.contexto || {},
    });
  },
};
