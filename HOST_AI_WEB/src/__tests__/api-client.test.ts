import { hostAiApiClient } from "../api/client";
import { describe, expect, it, vi } from "vitest";

describe("api client", () => {
  it("interpreta envelope comun y conserva request_id", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-100",
        modo_seguro: true,
        datos_reales_modificados: false,
        dashboard: {},
      }),
    } as Response);

    const res = await hostAiApiClient.getDashboard();
    expect(res.request_id).toBe("REQ-100");
    expect(res.api_version).toBe("1.0");
  });
});
