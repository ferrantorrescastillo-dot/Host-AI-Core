import { HostAiApiError, hostAiApiClient } from "../api/client";
import type { ReservaConfirmationResponse, ReservaPreviewResponse, ReservaResponse, ReservasFilters, ReservasResponse, ReservaWriteOperation } from "../types/reservas";

const RESERVA_ID_PATTERN = /^RES-[A-F0-9]{12}$/;

export function isCanonicalReservaId(value: string): boolean {
  return RESERVA_ID_PATTERN.test(String(value || "").trim());
}

export function buildReservasQuery(filters: ReservasFilters = {}): string {
  const params = new URLSearchParams();
  if (filters.alcance) params.set("alcance", filters.alcance);
  if (filters.q?.trim()) params.set("q", filters.q.trim());
  if (filters.fecha) params.set("fecha", filters.fecha);
  if (filters.estado) params.set("estado", filters.estado);
  if (filters.servicio) params.set("servicio", filters.servicio);
  if (filters.limite !== undefined) params.set("limite", String(Math.max(1, Math.min(100, Math.trunc(filters.limite)))));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const reservasService = {
  list(filters: ReservasFilters = {}): Promise<ReservasResponse> {
    return hostAiApiClient.getReservas(buildReservasQuery(filters));
  },

  detail(reservaId: string): Promise<ReservaResponse> {
    if (!isCanonicalReservaId(reservaId)) {
      return Promise.reject(new HostAiApiError("Identificador de reserva no válido."));
    }
    return hostAiApiClient.getReserva(reservaId);
  },
  preview(operation: ReservaWriteOperation, payload: Record<string, unknown>, reservaId = "", sessionId = "web"): Promise<ReservaPreviewResponse> {
    if (operation !== "CREAR" && !isCanonicalReservaId(reservaId)) return Promise.reject(new HostAiApiError("Identificador de reserva no válido."));
    return hostAiApiClient.previewReserva(operation, payload, reservaId, sessionId);
  },
  confirm(previewToken: string, sessionId = "web"): Promise<ReservaConfirmationResponse> {
    if (!previewToken.trim()) return Promise.reject(new HostAiApiError("Falta la confirmación de la vista previa."));
    return hostAiApiClient.confirmReserva(previewToken, sessionId);
  },
};
