import type { AICostBreakdown } from "../../types/articulos";
import { useEffect, useState } from "react";
import { hostAiApiClient } from "../../api/client";

export function reportAiCost(cost?: AICostBreakdown | null) {
  if (cost) window.dispatchEvent(new CustomEvent("host-ai-cost-recorded", { detail: cost }));
}

export function AiCostSummary({ cost, title = "Coste IA" }: { cost?: AICostBreakdown | null; title?: string }) {
  if (!cost) return null;
  const total = Number(cost.incremental_cost_usd ?? cost.total_cost_usd ?? 0);
  return <details className="ai-cost-summary"><summary>{title}: ${total.toFixed(4)}</summary>
    <p>{cost.cache_hit ? "Resultado reutilizado de caché · coste adicional" : cost.label || "Coste calculado según tarifas configuradas"}: ${total.toFixed(6)} USD</p>
    {(cost.items || []).map((item, index) => <p key={`${item.model || item.tool}-${index}`}>{item.tool ? `${item.tool} · ${item.quantity || 0} llamada(s)` : `${item.model || "Modelo"} · entrada ${item.input_tokens || 0} · caché ${item.cached_input_tokens || 0} · salida ${item.output_tokens || 0}`} · $${Number(item.cost_usd || 0).toFixed(6)}</p>)}
    {cost.pricing_version ? <small>Tarifa: {cost.pricing_version}</small> : null}
  </details>;
}

export function AiAccumulatedCost({ entityType = "", entityId = "", title = "Gasto Host AI en esta sesión" }: { entityType?: string; entityId?: string; title?: string }) {
  const [total, setTotal] = useState<string | null>(null);
  useEffect(() => {
    const load = () => void hostAiApiClient.getAiCostSummary(entityType, entityId).then((value) => setTotal(value.cost_summary.total_cost_usd)).catch(() => undefined);
    load(); window.addEventListener("host-ai-cost-recorded", load); return () => window.removeEventListener("host-ai-cost-recorded", load);
  }, [entityType, entityId]);
  return total == null ? null : <p className="ai-cost-total">{title}: ${Number(total).toFixed(4)} USD</p>;
}
