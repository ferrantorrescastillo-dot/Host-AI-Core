import { hostAiApiClient } from "../api/client";
import type {
  ApiEnvelopeBase,
  CompraListItem,
  EventoListItem,
  ProduccionPlanListItem,
  StockAlerta,
} from "../types/api";

export type ExecutiveKpis = {
  produccionEnCurso: number;
  comprasPendientes: number;
  eventosProximos: number;
  paxProximos: number;
  alertasStock: number;
};

export type ExecutiveDashboardResult = ApiEnvelopeBase & {
  kpis: ExecutiveKpis;
  produccion: ProduccionPlanListItem[];
  compras: CompraListItem[];
  eventos: EventoListItem[];
  alertasStock: StockAlerta[];
  riesgos: string[];
  incidencias: string[];
  recomendaciones: string[];
};

export const executiveDashboardService = {
  async load(): Promise<ExecutiveDashboardResult> {
    const response = await hostAiApiClient.getDashboard();
    const modulos = response.dashboard?.modulos;
    const produccion = asArray(modulos?.produccion?.items);
    const necesidadesCompra = asArray(modulos?.compras?.items);
    const propuestasCompra = asArray(modulos?.compras?.propuestas);
    const compras = [
      ...necesidadesCompra,
      ...propuestasCompra.map((propuesta) => ({
        id: propuesta.id,
        nombre: propuesta.producto,
        estado: propuesta.estado,
        fecha_necesaria: propuesta.creado_en,
      })),
    ];
    const eventos = asArray(modulos?.eventos?.items);
    const alertasStock = asArray(
      modulos?.stock?.alertas ?? modulos?.stock?.items,
    );

    const produccionEnCurso = numberOr(
      modulos?.produccion?.tareas_en_curso,
      modulos?.produccion?.resumen?.en_curso,
      0,
    );
    const comprasPendientes =
      numberOr(modulos?.compras?.necesidades_pendientes, necesidadesCompra.length) +
      numberOr(modulos?.compras?.propuestas_pendientes, propuestasCompra.length);
    const eventosProximos = numberOr(
      modulos?.eventos?.eventos_activos,
      eventos.length,
    );
    const paxProximos = numberOr(
      modulos?.eventos?.resumen?.pax_total,
      eventos.reduce((total, item) => total + numberOr(item.pax, 0), 0),
    );

    const riesgos = unique([
      ...eventos.flatMap((evento) => textArray(evento.riesgos)),
    ]);
    const incidencias = unique([
      ...eventos.flatMap((evento) => textArray(evento.avisos)),
      ...produccion.flatMap((plan) => [
        ...textArray(plan.avisos),
        ...textArray(plan.alertas),
        ...(plan.tareas ?? []).flatMap((tarea) => [
          ...textArray(tarea.incidencias),
          ...(tarea.bloqueo ? [tarea.bloqueo] : []),
        ]),
      ]),
    ]);

    return {
      ok: response.ok,
      version: response.version,
      api_version: response.api_version,
      request_id: response.request_id,
      modo_seguro: response.modo_seguro,
      datos_reales_modificados: response.datos_reales_modificados,
      kpis: {
        produccionEnCurso,
        comprasPendientes,
        eventosProximos,
        paxProximos,
        alertasStock: alertasStock.length,
      },
      produccion,
      compras,
      eventos,
      alertasStock,
      riesgos,
      incidencias,
      recomendaciones: recommendations({
        produccionEnCurso,
        comprasPendientes,
        eventosProximos,
        alertasStock: alertasStock.length,
        riesgos: riesgos.length,
        incidencias: incidencias.length,
      }),
    };
  },
};

function asArray<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function numberOr(...values: unknown[]): number {
  for (const value of values) {
    if (typeof value === "number" && Number.isFinite(value)) return value;
  }
  return 0;
}

function textArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item;
      if (!item || typeof item !== "object") return "";
      const record = item as Record<string, unknown>;
      const text =
        record.mensaje ?? record.detalle ?? record.descripcion ?? record.tipo;
      return typeof text === "string" ? text : "";
    })
    .filter(Boolean);
}

function unique(items: string[]): string[] {
  return [...new Set(items.map((item) => item.trim()).filter(Boolean))];
}

function recommendations(input: {
  produccionEnCurso: number;
  comprasPendientes: number;
  eventosProximos: number;
  alertasStock: number;
  riesgos: number;
  incidencias: number;
}): string[] {
  const result: string[] = [];
  if (input.riesgos > 0) result.push("Revisar los riesgos operativos detectados.");
  if (input.incidencias > 0) result.push("Resolver las incidencias relevantes antes del servicio.");
  if (input.alertasStock > 0) result.push("Atender las alertas de stock antes de los próximos eventos.");
  if (input.comprasPendientes > 0) result.push("Revisar las compras pendientes y sus fechas necesarias.");
  if (input.eventosProximos > 0 && input.produccionEnCurso === 0) {
    result.push("Revisar la planificación de producción de los próximos eventos.");
  }
  return result;
}
