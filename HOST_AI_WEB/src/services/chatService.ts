import { hostAiApiClient } from "../api/client";
import type { ChatResponse } from "../types/api";

export type ChatInput = {
  mensaje: string;
  contexto?: Record<string, unknown>;
  actionId?: string;
  actionContextId?: string;
};

export const chatService = {
  send(input: ChatInput): Promise<ChatResponse> {
    return hostAiApiClient.sendChatMessage({
      mensaje: input.mensaje,
      contexto: input.contexto || {},
      action_id: input.actionId,
      action_context_id: input.actionContextId,
    });
  },
};
