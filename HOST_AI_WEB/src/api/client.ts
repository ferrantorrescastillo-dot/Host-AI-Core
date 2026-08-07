import { HOST_AI_API_BASE_URL } from "../config/env";
import type { ChatResponse, DashboardResponse } from "../types/api";
import type { ArticuloResponse, CatalogoResponse } from "../types/articulos";
import type {
  BibliotecaImportProposalsResponse,
  BibliotecaImportResponse,
  BibliotecaDraftResponse,
  BibliotecaResponse,
  ElaboracionResponse,
  ElaboracionesResponse,
} from "../types/biblioteca";
import type {
  MenuElaborationsResponse,
  MenuInput,
  MenuNeedsResponse,
  MenuPurchaseProposalResponse,
  MenuOrdersResponse,
  MenuResponse,
  MenusResponse,
} from "../types/menus";
import type { CompraConfirmationResponse, CompraDraftInput, CompraDraftResponse } from "../types/compras";
import type { ProductionConfirmationResponse, ProductionPlanResponse, ProductionPreviewResponse } from "../types/produccion";

type Envelope = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
  error?: { status?: number; code?: string; message?: string };
  resultado?: unknown;
};

export class HostAiApiError extends Error {
  requestId?: string;
  statusCode?: number;
  modoSeguro?: boolean;
  datosRealesModificados?: boolean;
  details?: unknown;

  constructor(
    message: string,
    opts?: {
      requestId?: string;
      statusCode?: number;
      modoSeguro?: boolean;
      datosRealesModificados?: boolean;
      details?: unknown;
    },
  ) {
    super(message);
    this.name = "HostAiApiError";
    this.requestId = opts?.requestId;
    this.statusCode = opts?.statusCode;
    this.modoSeguro = opts?.modoSeguro;
    this.datosRealesModificados = opts?.datosRealesModificados;
    this.details = opts?.details;
  }
}

function assertEnvelope(payload: any): asserts payload is Envelope {
  const ok = payload && typeof payload === "object" && typeof payload.ok === "boolean";
  const requestId = typeof payload?.request_id === "string";
  const apiVersion = typeof payload?.api_version === "string";
  if (!ok || !requestId || !apiVersion) {
    throw new HostAiApiError("Respuesta de API no valida.");
  }
}

async function request<T extends Envelope>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${HOST_AI_API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
      ...init,
    });
  } catch {
    throw new HostAiApiError("No se pudo conectar con la API.");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new HostAiApiError("No se pudo leer la respuesta del servidor.", {
      statusCode: response.status,
    });
  }

  assertEnvelope(payload);

  if (!response.ok || payload.ok === false) {
    const safeMessage = payload.error?.message || "No se pudo completar la solicitud.";
    throw new HostAiApiError(safeMessage, {
      requestId: payload.request_id,
      statusCode: response.status,
      modoSeguro: payload.modo_seguro,
      datosRealesModificados: payload.datos_reales_modificados,
      details: payload.resultado,
    });
  }

  return payload as T;
}

export const hostAiApiClient = {
  getDashboard(): Promise<DashboardResponse> {
    return request<DashboardResponse>("/api/v1/dashboard", { method: "GET" });
  },

  getCompraDraft(id: string): Promise<CompraDraftResponse> {
    return request<CompraDraftResponse>(`/api/v1/compras/borradores/${encodeURIComponent(id)}`, { method: "GET" });
  },

  updateCompraDraft(id: string, input: CompraDraftInput): Promise<CompraDraftResponse> {
    return request<CompraDraftResponse>(`/api/v1/compras/borradores/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(input) });
  },

  confirmCompraDraft(id: string, actualizadoEn: string): Promise<CompraConfirmationResponse> {
    return request<CompraConfirmationResponse>(`/api/v1/compras/borradores/${encodeURIComponent(id)}/confirmar`, {
      method: "POST", body: JSON.stringify({ confirmacion: "CONFIRMAR_PEDIDO", usuario: "web", actualizado_en: actualizadoEn }),
    });
  },

  getArticulos(query = ""): Promise<CatalogoResponse> {
    return request<CatalogoResponse>(`/api/v1/articulos${query}`, { method: "GET" });
  },

  getArticulo(id: string): Promise<ArticuloResponse> {
    return request<ArticuloResponse>(`/api/v1/articulos/${encodeURIComponent(id)}`, { method: "GET" });
  },

  getMenus(): Promise<MenusResponse> {
    return request<MenusResponse>("/api/v1/menus", { method: "GET" });
  },

  getMenu(id: string): Promise<MenuResponse> {
    return request<MenuResponse>(`/api/v1/menus/${encodeURIComponent(id)}`, { method: "GET" });
  },

  getMenuElaborations(): Promise<MenuElaborationsResponse> {
    return request<MenuElaborationsResponse>("/api/v1/menus/elaboraciones", { method: "GET" });
  },

  createMenu(input: MenuInput): Promise<MenuResponse> {
    return request<MenuResponse>("/api/v1/menus", { method: "POST", body: JSON.stringify(input) });
  },

  updateMenu(id: string, input: MenuInput): Promise<MenuResponse> {
    return request<MenuResponse>(`/api/v1/menus/${encodeURIComponent(id)}`, {
      method: "PATCH", body: JSON.stringify(input),
    });
  },

  archiveMenu(id: string, version: number): Promise<MenuResponse> {
    return request<MenuResponse>(`/api/v1/menus/${encodeURIComponent(id)}`, {
      method: "DELETE", body: JSON.stringify({ version }),
    });
  },

  getMenuNeeds(id: string): Promise<MenuNeedsResponse> {
    return request<MenuNeedsResponse>(`/api/v1/menus/${encodeURIComponent(id)}/necesidades`, { method: "GET" });
  },

  createMenuPurchaseProposal(id: string): Promise<MenuPurchaseProposalResponse> {
    return request<MenuPurchaseProposalResponse>(`/api/v1/menus/${encodeURIComponent(id)}/propuesta-compra`, { method: "POST" });
  },

  updateMenuPurchaseProposal(menuId: string, proposalId: string, input: Record<string, unknown>): Promise<MenuPurchaseProposalResponse> {
    return request<MenuPurchaseProposalResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/propuesta-compra/${encodeURIComponent(proposalId)}`, { method: "PATCH", body: JSON.stringify(input) });
  },

  createMenuDraftOrders(menuId: string, proposalId: string, version: number): Promise<MenuOrdersResponse> {
    return request<MenuOrdersResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/propuesta-compra/${encodeURIComponent(proposalId)}/crear-pedidos`, { method: "POST", body: JSON.stringify({ confirmacion: "CREAR_BORRADORES", usuario: "web", version }) });
  },

  createMenuProductionPlan(menuId: string): Promise<ProductionPlanResponse> {
    return request<ProductionPlanResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/plan-produccion`, { method: "POST", body: "{}" });
  },
  getProductionPlan(planId: string): Promise<ProductionPlanResponse> {
    return request<ProductionPlanResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}`, { method: "GET" });
  },
  getProductionPreview(planId: string, taskId: string): Promise<ProductionPreviewResponse> {
    return request<ProductionPreviewResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}/tareas/${encodeURIComponent(taskId)}/consumo-previsto`, { method: "GET" });
  },
  confirmProduction(planId: string, taskId: string): Promise<ProductionConfirmationResponse> {
    return request<ProductionConfirmationResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}/tareas/${encodeURIComponent(taskId)}/confirmar`, { method: "POST", body: JSON.stringify({ confirmacion: "CONFIRMAR_PRODUCCION_TERMINADA", usuario: "web" }) });
  },

  getBiblioteca(): Promise<BibliotecaResponse> {
    return request<BibliotecaResponse>("/api/v1/biblioteca", { method: "GET" });
  },

  getElaboraciones(query = ""): Promise<ElaboracionesResponse> {
    return request<ElaboracionesResponse>(`/api/v1/biblioteca/elaboraciones${query}`, { method: "GET" });
  },

  getElaboracion(id: string): Promise<ElaboracionResponse> {
    return request<ElaboracionResponse>(
      `/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}`,
      { method: "GET" },
    );
  },

  createBibliotecaImport(input: {
    nombre: string;
    tipo_mime: string;
    contenido_base64: string;
    texto?: string;
  }): Promise<BibliotecaImportResponse> {
    return request<BibliotecaImportResponse>("/api/v1/biblioteca/importaciones", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  getBibliotecaImport(id: string): Promise<BibliotecaImportResponse> {
    return request<BibliotecaImportResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}`,
      { method: "GET" },
    );
  },

  getBibliotecaImportProposals(id: string): Promise<BibliotecaImportProposalsResponse> {
    return request<BibliotecaImportProposalsResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/propuestas`,
      { method: "GET" },
    );
  },

  getBibliotecaImportDraft(id: string): Promise<BibliotecaDraftResponse> {
    return request<BibliotecaDraftResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/borrador`,
      { method: "GET" },
    );
  },

  updateBibliotecaImportDraft(
    id: string,
    input: { draft_version: number; recipes: unknown[] },
  ): Promise<BibliotecaDraftResponse> {
    return request<BibliotecaDraftResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/borrador`,
      { method: "PATCH", body: JSON.stringify(input) },
    );
  },

  confirmBibliotecaImport(
    id: string,
    input: { draft_version: number; usuario: string; confirmacion: "CONFIRMAR" },
  ): Promise<import("../types/biblioteca").BibliotecaImportConfirmationResponse> {
    return request(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/confirmar`,
      { method: "POST", body: JSON.stringify(input) },
    );
  },

  sendChatMessage(input: { mensaje: string; contexto?: Record<string, unknown> }): Promise<ChatResponse> {
    return request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        mensaje: input.mensaje,
        contexto: input.contexto || {},
      }),
    });
  },
};
