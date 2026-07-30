import { hostAiApiClient } from "../api/client";
import type { ApiEnvelopeBase, ProduccionPlanListItem, ProduccionResumen } from "../types/api";

export type ProduccionResult = ApiEnvelopeBase & {
  planes: ProduccionPlanListItem[];
  estado?: string;
  total: number;
  resumen: ProduccionResumen;
  mensaje?: string;
};

export const produccionService = {
  async load(): Promise<ProduccionResult> {
    const response = await hostAiApiClient.getDashboard();
    const modulo = response.dashboard?.modulos?.produccion;
    const planes = Array.isArray(modulo?.items) ? modulo.items : [];
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
    };
  },
};
