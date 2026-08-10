import { hostAiApiClient } from "../api/client";
import type {
  ApiEnvelopeBase,
  CompraHistorialListItem,
  CompraListItem,
  PropuestaCompraListItem,
  ProveedorCompraListItem,
} from "../types/api";
import type { CompraDraftInput, CompraDraftResponse, PurchaseReception, ReceptionLine } from "../types/compras";

export type ComprasResult = ApiEnvelopeBase & {
  compras: CompraListItem[];
  propuestas: PropuestaCompraListItem[];
  proveedores: ProveedorCompraListItem[];
  historial: CompraHistorialListItem[];
  pedidos: Array<{ id: string; proveedor: string; estado: string; lineas: Array<{ nombre: string; cantidad: number; unidad: string }>; importe_estimado: number; observaciones?: string }>;
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
    const pedidos = Array.isArray((modulo as typeof modulo & { pedidos?: ComprasResult["pedidos"] })?.pedidos)
      ? (modulo as typeof modulo & { pedidos: ComprasResult["pedidos"] }).pedidos : [];

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
      pedidos,
      estado: modulo?.estado,
      total:
        typeof modulo?.total === "number"
          ? modulo.total
          : compras.length,
      mensaje: modulo?.mensaje,
    };
  },
  getDraft(id: string): Promise<CompraDraftResponse> {
    return hostAiApiClient.getCompraDraft(id);
  },
  saveDraft(id: string, input: CompraDraftInput): Promise<CompraDraftResponse> {
    return hostAiApiClient.updateCompraDraft(id, input);
  },
  confirmDraft(id: string, actualizadoEn: string) {
    return hostAiApiClient.confirmCompraDraft(id, actualizadoEn);
  },
  createReception: (orderId: string) => hostAiApiClient.createPurchaseReception(orderId),
  saveReception: (id: string, lines: ReceptionLine[], header: Record<string, unknown>) => hostAiApiClient.updatePurchaseReception(id, lines, header),
  confirmReception: (reception: PurchaseReception) => hostAiApiClient.confirmPurchaseReception(reception),
};
