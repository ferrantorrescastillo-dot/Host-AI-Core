import { hostAiApiClient } from "../api/client";
import type {
  ApiEnvelopeBase,
  EventoListItem,
  EventosResumen,
} from "../types/api";

export type EventosResult = ApiEnvelopeBase & {
  eventos: EventoListItem[];
  estado?: string;
  total: number;
  resumen: EventosResumen;
  mensaje?: string;
};

export const eventosService = {
  detail(id: string) { return hostAiApiClient.getEvento(id); },
  async load(): Promise<EventosResult> {
    const response = await hostAiApiClient.getDashboard();
    const modulo = response.dashboard?.modulos?.eventos;
    const eventos = Array.isArray(modulo?.items)
      ? modulo.items
      : [];

    return {
      ok: response.ok,
      version: response.version,
      api_version: response.api_version,
      request_id: response.request_id,
      modo_seguro: response.modo_seguro,
      datos_reales_modificados:
        response.datos_reales_modificados,
      eventos,
      estado: modulo?.estado,
      total:
        typeof modulo?.total === "number"
          ? modulo.total
          : eventos.length,
      resumen: modulo?.resumen ?? {},
      mensaje: modulo?.mensaje,
    };
  },
};
