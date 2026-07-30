import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { produccionService, type ProduccionResult } from "../../services/produccionService";
import type { ProduccionPlanListItem, ProduccionTareaListItem } from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ProduccionPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<ProduccionResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setErrorRequestId(null);
    produccionService.load().then((result) => {
      if (active) setData(result);
    }).catch((err: unknown) => {
      if (!active) return;
      setData(null);
      if (err instanceof HostAiApiError) {
        setError(err.message);
        setErrorRequestId(err.requestId || null);
      } else {
        setError("No se pudo cargar la producción.");
      }
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [refreshTick]);

  if (loading) return <LoadingState label="Cargando producción..." />;

  return (
    <section className="panel" role="region" aria-labelledby="produccion-title">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Operativa</p>
          <h2 id="produccion-title">Producción</h2>
          <p className="meta-line">Planes y tareas de cocina en curso</p>
        </div>
        <button type="button" onClick={() => setRefreshTick((value) => value + 1)}>
          {error ? "Reintentar" : "Actualizar"}
        </button>
      </header>
      {error ? (
        <>
          <ErrorState title="No se pudo cargar la producción." detail={error} />
          <p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p>
        </>
      ) : (
        <>
          <section className="safe-mode" aria-label="Estado de seguridad">
            <p><strong>Modo seguro:</strong> {data?.modo_seguro ? "Activo" : "Inactivo"}</p>
            <p><strong>Datos reales modificados:</strong> {data?.datos_reales_modificados ? "Sí" : "No"}</p>
            <p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p>
          </section>
          <section className="dashboard-grid" aria-label="Resumen de producción">
            <SummaryCard title="Planes activos" value={data?.resumen.planes_activos ?? data?.total ?? 0} />
            <SummaryCard title="Tareas pendientes" value={data?.resumen.pendientes ?? 0} />
            <SummaryCard title="Tareas en curso" value={data?.resumen.en_curso ?? 0} />
            <SummaryCard title="Tareas bloqueadas" value={data?.resumen.bloqueadas ?? 0} />
          </section>
          {data?.planes.length ? (
            <div className="produccion-list" aria-label="Planes de producción">
              {data.planes.map((plan, index) => (
                <PlanCard key={plan.id || `${plan.nombre || "plan"}-${index}`} plan={plan} />
              ))}
            </div>
          ) : (
            <div className="panel-state">
              <p>No hay planes de producción activos.</p>
              {data?.mensaje ? <p className="meta-line">{data.mensaje}</p> : null}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function PlanCard({ plan }: { plan: ProduccionPlanListItem }) {
  return (
    <article className="produccion-card">
      <header>
        <div><h3>{plan.nombre || "Plan sin nombre"}</h3><p className="meta-line">{plan.evento || "Sin evento asociado"}</p></div>
        <span className="evento-status">{readable(plan.estado) || "Estado no disponible"}</span>
      </header>
      <dl className="produccion-details">
        <Detail label="Fecha" value={formatDate(plan.fecha)} />
        <Detail label="PAX" value={formatNumber(plan.pax)} />
        <Detail label="Responsable" value={plan.responsable || "No asignado"} />
        <Detail label="Progreso" value={formatPercent(plan.porcentaje_completado)} />
      </dl>
      {plan.tareas?.length ? (
        <ul className="clean-list produccion-tasks" aria-label={`Tareas de ${plan.nombre || "producción"}`}>
          {plan.tareas.map((tarea, index) => <Tarea key={tarea.id || `${tarea.titulo || "tarea"}-${index}`} tarea={tarea} />)}
        </ul>
      ) : null}
    </article>
  );
}

function Tarea({ tarea }: { tarea: ProduccionTareaListItem }) {
  return (
    <li>
      <div><strong>{tarea.titulo || "Tarea sin nombre"}</strong><p className="meta-line">{formatQuantity(tarea.cantidad, tarea.unidad)} · {readable(tarea.estado) || "Sin estado"}</p></div>
      {tarea.bloqueo ? <p className="produccion-alert">Bloqueo: {tarea.bloqueo}</p> : null}
    </li>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}

function SummaryCard({ title, value }: { title: string; value: number }) {
  return <article className="data-card"><h3>{title}</h3><p className="stat-value">{value}</p></article>;
}

function readable(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "";
  const normalized = value.trim().replaceAll("_", " ").toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatDate(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "No disponible";
  const isoDate = /^\d{4}-\d{2}-\d{2}$/.test(value);
  const date = new Date(isoDate ? `${value}T00:00:00Z` : value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeZone: isoDate ? "UTC" : undefined }).format(date);
}

function formatNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? new Intl.NumberFormat("es-ES").format(value) : "No disponible";
}

function formatPercent(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value}%` : "No disponible";
}

function formatQuantity(value: unknown, unit: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Cantidad no disponible";
  const suffix = typeof unit === "string" && unit.trim() ? ` ${unit}` : "";
  return `${new Intl.NumberFormat("es-ES").format(value)}${suffix}`;
}
