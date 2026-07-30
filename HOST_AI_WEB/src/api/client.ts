import { HOST_AI_API_BASE_URL } from "../config/env";
import type { ChatResponse, DashboardResponse } from "../types/api";
import type { ArticuloResponse, CatalogoResponse } from "../types/articulos";
import type {
  BibliotecaImportProposalsResponse,
  BibliotecaImportResponse,
  BibliotecaResponse,
  ElaboracionResponse,
  ElaboracionesResponse,
} from "../types/biblioteca";

type Envelope = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
  error?: { status?: number; code?: string; message?: string };
};

export class HostAiApiError extends Error {
  requestId?: string;
  statusCode?: number;
  modoSeguro?: boolean;
  datosRealesModificados?: boolean;

  constructor(
    message: string,
    opts?: {
      requestId?: string;
      statusCode?: number;
      modoSeguro?: boolean;
      datosRealesModificados?: boolean;
    },
  ) {
    super(message);
    this.name = "HostAiApiError";
    this.requestId = opts?.requestId;
    this.statusCode = opts?.statusCode;
    this.modoSeguro = opts?.modoSeguro;
    this.datosRealesModificados = opts?.datosRealesModificados;
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
    });
  }

  return payload as T;
}

export const hostAiApiClient = {
  getDashboard(): Promise<DashboardResponse> {
    return request<DashboardResponse>("/api/v1/dashboard", { method: "GET" });
  },

  getArticulos(query = ""): Promise<CatalogoResponse> {
    return request<CatalogoResponse>(`/api/v1/articulos${query}`, { method: "GET" });
  },

  getArticulo(id: string): Promise<ArticuloResponse> {
    return request<ArticuloResponse>(`/api/v1/articulos/${encodeURIComponent(id)}`, { method: "GET" });
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
