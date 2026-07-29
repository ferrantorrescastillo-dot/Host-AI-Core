import { hostAiApiClient } from "../api/client";
import type {
  ApiEnvelopeBase,
  CompraHistorialListItem,
  CompraListItem,
  PropuestaCompraListItem,
  ProveedorCompraListItem,
} from "../types/api";

export type ComprasResult = ApiEnvelopeBase & {
  compras: CompraListItem[];
  propuestas: PropuestaCompraListItem[];
  proveedores: ProveedorCompraListItem[];
  historial: CompraHistorialListItem[];
  estado?: string;
  total: number;
  mensaje?: string;
};

export const comprasService = {
  async load(): Promise<ComprasResult> {
    const response = await hostAiApiClient.getDashboard();
    const modulo = response.dashboard?.modulos?.compras;
    const compras = Array.isArray(modulo?.items)
      ? modulo.items
      : [];
    const propuestas = Array.isArray(modulo?.propuestas)
      ? modulo.propuestas
      : [];
    const proveedores = Array.isArray(modulo?.proveedores)
      ? modulo.proveedores
      : [];
    const historial = Array.isArray(modulo?.historial)
      ? modulo.historial
      : [];

    return {
      ok: response.ok,
      version: response.version,
      api_version: response.api_version,
      request_id: response.request_id,
      modo_seguro: response.modo_seguro,
      datos_reales_modificados:
        response.datos_reales_modificados,
      compras,
      propuestas,
      proveedores,
      historial,
      estado: modulo?.estado,
      total:
        typeof modulo?.total === "number"
          ? modulo.total
          : compras.length,
      mensaje: modulo?.mensaje,
    };
  },
};
