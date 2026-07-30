import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import {
  executiveDashboardService,
  type ExecutiveDashboardResult,
} from "../../services/executiveDashboardService";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ExecutiveDashboardPage() {
  const [data, setData] = useState<ExecutiveDashboardResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setErrorRequestId(null);
    executiveDashboardService
      .load()
      .then((result) => {
        if (active) setData(result);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setData(null);
        if (reason instanceof HostAiApiError) {
          setError(reason.message);
          setErrorRequestId(reason.requestId || null);
        } else {
          setError("No se pudo cargar el resumen ejecutivo.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshTick]);

  if (loading) return <LoadingState label="Cargando dashboard ejecutivo..." />;

  return (
    <section className="panel" role="region" aria-labelledby="executive-title">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">HOST AI · DIRECCIÓN</p>
          <h2 id="executive-title">Resumen ejecutivo</h2>
          <p className="meta-line">Vista agregada de la operación disponible</p>
        </div>
        <button type="button" onClick={() => setRefreshTick((value) => value + 1)}>
          {error ? "Reintentar" : "Actualizar"}
        </button>
      </header>

      {error ? (
        <>
          <ErrorState title="No se pudo cargar el resumen ejecutivo." detail={error} />
          <p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p>
        </>
      ) : (
        <>
          <section className="safe-mode" aria-label="Estado de seguridad">
            <p><strong>Modo seguro:</strong> {data?.modo_seguro ? "Activo" : "Inactivo"}</p>
            <p><strong>Datos reales modificados:</strong> {data?.datos_reales_modificados ? "Sí" : "No"}</p>
            <p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p>
          </section>

          <section className="dashboard-grid" aria-label="KPIs principales">
            <Kpi title="Producción en curso" value={data?.kpis.produccionEnCurso ?? 0} />
            <Kpi title="Compras pendientes" value={data?.kpis.comprasPendientes ?? 0} />
            <Kpi title="Próximos eventos" value={data?.kpis.eventosProximos ?? 0} />
            <Kpi title="PAX próximos" value={data?.kpis.paxProximos ?? 0} />
            <Kpi title="Alertas de stock" value={data?.kpis.alertasStock ?? 0} />
          </section>

          <ModuleSection title="Producción en curso" empty="No hay producción en curso.">
            {data?.produccion.map((plan, index) => (
              <li key={plan.id || `${plan.nombre}-${index}`}>
                <strong>{plan.nombre || "Plan de producción"}</strong>
                <span className="meta-line">Estado: {readable(plan.estado)}</span>
              </li>
            ))}
          </ModuleSection>

          <ModuleSection title="Compras pendientes" empty="No hay compras pendientes.">
            {data?.compras.map((item, index) => (
              <li key={item.id || `${item.nombre}-${index}`}>
                <strong>{item.nombre || "Necesidad de compra"}</strong>
                <span className="meta-line">Necesaria: {item.fecha_necesaria || "Sin fecha"}</span>
              </li>
            ))}
          </ModuleSection>

          <ModuleSection title="Próximos eventos" empty="No hay próximos eventos.">
            {data?.eventos.map((evento, index) => (
              <li key={evento.id || `${evento.nombre}-${index}`}>
                <strong>{evento.nombre || "Evento"}</strong>
                <span className="meta-line">
                  {evento.fecha || "Sin fecha"} · {evento.pax ?? 0} PAX · {readable(evento.estado)}
                </span>
              </li>
            ))}
          </ModuleSection>

          <TextSection title="Alertas de stock" items={data?.alertasStock.map((item) => item.mensaje || item.tipo || "Alerta") ?? []} />
          <TextSection title="Riesgos" items={data?.riesgos ?? []} />
          <TextSection title="Incidencias relevantes" items={data?.incidencias ?? []} />
          <TextSection title="Recomendaciones" items={data?.recomendaciones ?? []} />
        </>
      )}
    </section>
  );
}

function Kpi({ title, value }: { title: string; value: number }) {
  return <article className="data-card"><h3>{title}</h3><p className="stat-value">{value}</p></article>;
}

function ModuleSection({
  title,
  empty,
  children,
}: {
  title: string;
  empty: string;
  children: React.ReactNode[] | undefined;
}) {
  const items = children?.filter(Boolean) ?? [];
  return <section className="feature-block" aria-label={title}><h3>{title}</h3>{items.length ? <ul className="clean-list">{items}</ul> : <p>{empty}</p>}</section>;
}

function TextSection({ title, items }: { title: string; items: string[] }) {
  return <section className="feature-block" aria-label={title}><h3>{title}</h3>{items.length ? <ul className="clean-list">{items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}</ul> : <p>Sin información relevante.</p>}</section>;
}

function readable(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "No disponible";
  const normalized = value.trim().replaceAll("_", " ").toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}
