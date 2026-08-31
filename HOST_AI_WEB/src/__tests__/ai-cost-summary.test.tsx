import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { hostAiApiClient } from "../api/client";
import { AiAccumulatedCost, AiCostSummary, reportAiCost } from "../ui/components/AiCostSummary";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("muestra el coste discreto y el desglose real de modelo y Web Search", () => {
  render(<AiCostSummary title="Coste de búsqueda" cost={{
    operation_id: "PRICE-1", operation_type: "PRICE_WEB_SEARCH", currency: "USD", pricing_version: "TEST-V1", total_cost_usd: "0.01230000",
    items: [
      { provider: "OPENAI", model: "gpt-5.6-luna", input_tokens: 100, cached_input_tokens: 20, output_tokens: 30, cost_usd: "0.00230000" },
      { provider: "OPENAI", tool: "web_search", quantity: 1, cost_usd: "0.01000000" },
    ],
  }} />);
  expect(screen.getByText("Coste de búsqueda: $0.0123")).toBeInTheDocument();
  expect(screen.getByText(/gpt-5.6-luna/)).toHaveTextContent("entrada 100");
  expect(screen.getByText(/web_search/)).toHaveTextContent("1 llamada(s)");
  expect(screen.getByText("Tarifa: TEST-V1")).toBeInTheDocument();
});

it("explica que una lectura de caché tiene coste incremental cero", () => {
  render(<AiCostSummary title="Coste de búsqueda" cost={{ operation_id: "CACHE-1", operation_type: "PRICE_WEB_SEARCH", currency: "USD", total_cost_usd: "0", incremental_cost_usd: "0", cache_hit: true, items: [] }} />);
  expect(screen.getByText("Coste de búsqueda: $0.0000")).toBeInTheDocument();
  expect(screen.getByText(/Resultado reutilizado de caché/)).toBeInTheDocument();
});

it("un rerender del desglose no registra ni solicita un coste nuevo", () => {
  const summary = vi.spyOn(hostAiApiClient, "getAiCostSummary");
  const cost = { operation_id: "OP-RERENDER", operation_type: "ARTICLE_AI", currency: "USD" as const, total_cost_usd: "0.00100000", items: [{ provider: "OPENAI", model: "gpt-5.6-luna", cost_usd: "0.00100000" }] };
  const view = render(<AiCostSummary cost={cost} />);
  view.rerender(<AiCostSummary cost={cost} />);
  expect(screen.getByText("Coste IA: $0.0010")).toBeInTheDocument();
  expect(summary).not.toHaveBeenCalled();
});

it("recupera el acumulado persistido y lo refresca al registrarse otra operación", async () => {
  const summary = vi.spyOn(hostAiApiClient, "getAiCostSummary")
    .mockResolvedValueOnce({ ok: true, request_id: "R1", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, cost_summary: { total_cost_usd: "0.01000000", by_model: {}, by_capability: {}, events: 1 } })
    .mockResolvedValueOnce({ ok: true, request_id: "R2", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, cost_summary: { total_cost_usd: "0.03500000", by_model: {}, by_capability: {}, events: 3 } });
  render(<AiAccumulatedCost entityType="RECIPE" entityId="REC-1" title="Coste Host AI — esta receta" />);
  expect(await screen.findByText("Coste Host AI — esta receta: $0.0100 USD")).toBeInTheDocument();
  reportAiCost({ operation_id: "OP-3", operation_type: "ARTICLE_AI", currency: "USD", total_cost_usd: "0.005", items: [] });
  await waitFor(() => expect(screen.getByText("Coste Host AI — esta receta: $0.0350 USD")).toBeInTheDocument());
  expect(summary).toHaveBeenCalledWith("RECIPE", "REC-1");
});
