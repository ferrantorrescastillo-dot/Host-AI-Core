import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { dashboardService } from "../../services/dashboardService";
import type { DashboardResponse } from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setErrorRequestId(null);
    setData(null);

    dashboardService
      .load()
      .then((result) => {
        if (!active) return;
        setData(result);
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (err instanceof HostAiApiError) {
          setError(err.message);
          setErrorRequestId(err.requestId || null);
          return;
        }
        setError("No se pudo cargar el dashboard.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshTick]);

  if (loading) return <LoadingState label="Cargando dashboard..." />;
  if (error)
    return (
      <section className="panel" role="region" aria-labelledby="dashboard-title">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">HOST AI</p>
            <h2 id="dashboard-title">Estado operativo del restaurante</h2>
          </div>
          <button type="button" onClick={() => setRefreshTick((n) => n + 1)}>
            Reintentar
          </button>
        </header>
        <ErrorState title="No se pudo cargar el dashboard." detail={error} />
        <p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p>
      </section>
    );

  const dashboard = data?.dashboard ?? {};
  const empty = Object.keys(dashboard).length === 0;
  const prioridad = asRecord(dashboard.prioridad);
  const evento = asRecord(dashboard.evento_activo);
  const pendientes = asArray(dashboard.pendientes);
  const riesgos = asArray(dashboard.riesgos);
  const recomendaciones = asArray(dashboard.recomendaciones);
  const workflows = asArray(dashboard.workflows);
  const lastUpdate =
    valueToText((dashboard as Record<string, unknown>)?.actualizado_en) ||
    valueToText((dashboard as Record<string, unknown>)?.ultima_actualizacion) ||
    valueToText((dashboard as Record<string, unknown>)?.updated_at);

  return (
    <section className="panel" role="region" aria-labelledby="dashboard-title">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">HOST AI</p>
          <h2 id="dashboard-title">Estado operativo del restaurante</h2>
          <p className="meta-line">
            Ultima actualizacion: {lastUpdate || "No disponible"}
          </p>
        </div>
        <button type="button" onClick={() => setRefreshTick((n) => n + 1)}>
          Actualizar
        </button>
      </header>

      <section className="safe-mode" aria-label="Modo seguro">
        <p>
          <strong>Modo seguro activo:</strong> {data?.modo_seguro ? "si" : "no"}
        </p>
        <p>
          <strong>datos_reales_modificados:</strong> {String(data?.datos_reales_modificados)}
        </p>
        <p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p>
      </section>

      {data?.datos_reales_modificados ? (
        <div className="panel-state panel-error" role="alert">
          <p className="panel-error-title">Alerta tecnica de seguridad</p>
          <p className="panel-error-detail">
            La API reporta datos_reales_modificados=true. Revisar esta situacion.
          </p>
        </div>
      ) : null}

      {empty ? (
        <div className="panel-state">
          <p>No hay informacion operativa disponible.</p>
        </div>
      ) : (
        <>
          <section className="dashboard-grid" aria-label="Resumen operativo">
            <StatCard title="Estado general" value={dashboard.estado_general} />
            <StatCard title="Prioridad" value={prioridad.titulo || prioridad.workflow || dashboard.prioridad} />
            <StatCard title="Pendientes" value={String(pendientes.length)} />
            <StatCard title="Riesgos" value={String(riesgos.length)} />
            <StatCard title="Evento activo" value={evento.nombre || evento.prioritario_nombre || "No disponible"} />
            <StatCard title="Workflows preparados" value={String(workflows.length)} />
          </section>

          <section className="feature-block feature-priority" aria-label="Prioridad del dia">
            <h3>Prioridad del dia</h3>
            <p>
              <strong>Accion prioritaria:</strong> {valueToText(prioridad.titulo || prioridad.workflow) || "No disponible"}
            </p>
            <p>
              <strong>Justificacion:</strong> {valueToText(prioridad.mensaje || prioridad.justificacion) || "No disponible"}
            </p>
            <p>
              <strong>Siguiente recomendacion:</strong> {valueToText(firstText(recomendaciones)) || "No disponible"}
            </p>
          </section>

          <section className="feature-block" aria-label="Evento activo">
            <h3>Evento activo</h3>
            {Object.keys(evento).length === 0 ? (
              <p>No hay evento activo.</p>
            ) : (
              <ul className="clean-list">
                <li>
                  <strong>Nombre:</strong> {valueToText(evento.nombre || evento.prioritario_nombre) || "No disponible"}
                </li>
                <li>
                  <strong>Fecha:</strong> {valueToText(evento.fecha) || "No disponible"}
                </li>
                <li>
                  <strong>PAX:</strong> {valueToText(evento.pax) || "No disponible"}
                </li>
                <li>
                  <strong>Estado:</strong> {valueToText(evento.estado) || "No disponible"}
                </li>
                <li>
                  <strong>Progreso workflow:</strong> {valueToText(evento.progreso_workflow || evento.workflow_progreso) || "No disponible"}
                </li>
              </ul>
            )}
          </section>

          <section className="feature-block" aria-label="Pendientes">
            <h3>Pendientes</h3>
            {pendientes.length === 0 ? (
              <p>No hay tareas operativas pendientes.</p>
            ) : (
              <ol>
                {pendientes.map((item, idx) => {
                  const p = asRecord(item);
                  return (
                    <li key={`${idx}-${valueToText(p.codigo) || "pendiente"}`}>
                      <strong>{valueToText(p.nombre || p.titulo || p.codigo) || "No disponible"}</strong>
                      <p>{valueToText(p.descripcion || p.motivo || p.detalle) || "No disponible"}</p>
                      <p className="meta-line">
                        Estado: {valueToText(p.estado) || "No disponible"} | Prioridad: {valueToText(p.prioridad) || "No disponible"}
                      </p>
                    </li>
                  );
                })}
              </ol>
            )}
          </section>

          <section className="feature-block" aria-label="Riesgos">
            <h3>Riesgos</h3>
            {riesgos.length === 0 ? (
              <p>No hay riesgos operativos reportados.</p>
            ) : (
              <ul className="clean-list">
                {riesgos.map((item, idx) => {
                  const risk = asRecord(item);
                  const level = normalizeLevel(valueToText(risk.nivel || risk.severidad));
                  return (
                    <li key={`${idx}-${level}`} className={`risk-item risk-${level}`}>
                      <p>
                        <strong>{riskPrefix(level)}</strong> Nivel {level.toUpperCase()}
                      </p>
                      <p>{valueToText(risk.mensaje || risk.detalle) || "No disponible"}</p>
                      <p className="meta-line">
                        Accion recomendada: {valueToText(risk.accion_recomendada || risk.recomendacion) || "No disponible"}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section className="feature-block" aria-label="Recomendaciones">
            <h3>Recomendaciones</h3>
            {recomendaciones.length === 0 ? (
              <p>No hay recomendaciones disponibles.</p>
            ) : (
              <ol>
                {recomendaciones.map((item, idx) => (
                  <li key={`${idx}-rec`}>{valueToText(item) || "No disponible"}</li>
                ))}
              </ol>
            )}
          </section>

          <section className="feature-block" aria-label="Workflows preparados">
            <h3>Workflows preparados</h3>
            {workflows.length === 0 ? (
              <p>No hay workflows preparados.</p>
            ) : (
              <ul className="clean-list">
                {workflows.map((item, idx) => {
                  const wf = asRecord(item);
                  return (
                    <li key={`${idx}-${valueToText(wf.workflow || wf.codigo) || "workflow"}`}>
                      <strong>{valueToText(wf.workflow || wf.nombre || wf.codigo) || "No disponible"}</strong>
                      <p className="meta-line">Estado: {valueToText(wf.estado) || "No disponible"}</p>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}

function StatCard({ title, value }: { title: string; value: unknown }) {
  return (
    <article className="data-card">
      <h3>{title}</h3>
      <p className="stat-value">{valueToText(value) || "No disponible"}</p>
    </article>
  );
}

function valueToText(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return "";
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function firstText(items: unknown[]): string {
  if (items.length === 0) return "";
  return valueToText(items[0]);
}

function normalizeLevel(level: string): "alto" | "medio" | "bajo" {
  const raw = String(level || "").toLowerCase();
  if (raw.includes("alt")) return "alto";
  if (raw.includes("baj")) return "bajo";
  return "medio";
}

function riskPrefix(level: "alto" | "medio" | "bajo"): string {
  if (level === "alto") return "[ALTO]";
  if (level === "bajo") return "[BAJO]";
  return "[MEDIO]";
}
