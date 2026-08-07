import { hostAiApiClient } from "../api/client";
import type { ApiEnvelopeBase, ProduccionPlanListItem, ProduccionResumen } from "../types/api";
import type { ProductionPlan } from "../types/produccion";

export type ProduccionResult = ApiEnvelopeBase & {
  planes: ProduccionPlanListItem[];
  estado?: string;
  total: number;
  resumen: ProduccionResumen;
  detalles: ProductionPlan[];
  mensaje?: string;
};

export const produccionService = {
  async load(): Promise<ProduccionResult> {
    const response = await hostAiApiClient.getDashboard();
    const modulo = response.dashboard?.modulos?.produccion;
    const planes = Array.isArray(modulo?.items) ? modulo.items : [];
    const detalles = (await Promise.all(planes.map(async (plan) => {
      if (!plan.id) return null;
      return (await hostAiApiClient.getProductionPlan(String(plan.id))).plan;
    }))).filter((plan): plan is ProductionPlan => plan !== null);
    return {
      ok: response.ok,
      version: response.version,
      api_version: response.api_version,
      request_id: response.request_id,
      modo_seguro: response.modo_seguro,
      datos_reales_modificados: response.datos_reales_modificados,
      planes,
      estado: modulo?.estado,
      total: typeof modulo?.total === "number" ? modulo.total : planes.length,
      resumen: modulo?.resumen ?? {},
      mensaje: modulo?.mensaje,
      detalles,
    };
  },
  getPlan: (planId: string) => hostAiApiClient.getProductionPlan(planId),
  createPurchaseProposal: (planId: string) => hostAiApiClient.createProductionPurchaseProposal(planId),
};
