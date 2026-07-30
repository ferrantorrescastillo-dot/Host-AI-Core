import { hostAiApiClient } from "../api/client";
import type {
  ApiEnvelopeBase,
  StockAlerta,
  StockExistencia,
  StockLote,
  StockMovimiento,
  StockResumen,
} from "../types/api";

export type StockResult = ApiEnvelopeBase & {
  estado?: string;
  estado_operativo?: string;
  alertas: StockAlerta[];
  existencias: StockExistencia[];
  lotes: StockLote[];
  movimientos: StockMovimiento[];
  caducidades: StockAlerta[];
  resumen: StockResumen;
  mensaje?: string;
};

export const stockService = {
  async load(): Promise<StockResult> {
    const response = await hostAiApiClient.getDashboard();
    const modulo = response.dashboard?.modulos?.stock;
    return {
      ok: response.ok,
      version: response.version,
      api_version: response.api_version,
      request_id: response.request_id,
      modo_seguro: response.modo_seguro,
      datos_reales_modificados: response.datos_reales_modificados,
      estado: modulo?.estado,
      estado_operativo: modulo?.estado_operativo,
      alertas: array(modulo?.alertas ?? modulo?.items),
      existencias: array(modulo?.existencias),
      lotes: array(modulo?.lotes),
      movimientos: array(modulo?.movimientos),
      caducidades: array(modulo?.caducidades),
      resumen: modulo?.resumen ?? {},
      mensaje: modulo?.mensaje,
    };
  },
};

function array<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}
