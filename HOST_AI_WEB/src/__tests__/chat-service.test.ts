import { describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  hostAiApiClient: {
    sendChatMessage: vi.fn(),
  },
}));

import { hostAiApiClient } from "../api/client";
import { chatService } from "../services/chatService";

describe("chat service", () => {
  it("consume exclusivamente el cliente API para POST /api/v1/chat", async () => {
    const mockedClient = vi.mocked(hostAiApiClient);
    mockedClient.sendChatMessage.mockResolvedValue({
      ok: true,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-SERVICE",
      modo_seguro: true,
      datos_reales_modificados: false,
    });

    await chatService.send({ mensaje: "hola", contexto: { origen: "test" } });

    expect(mockedClient.sendChatMessage).toHaveBeenCalledTimes(1);
    expect(mockedClient.sendChatMessage).toHaveBeenCalledWith({
      mensaje: "hola",
      contexto: { origen: "test" },
    });
  });
});
