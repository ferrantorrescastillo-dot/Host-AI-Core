import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { dashboardService } from "../../services/dashboardService";
import { stockService } from "../../services/stockService";
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
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [refreshTick]);

  useEffect(() => {
    const refreshAfterRecipeWrite = (event: MessageEvent) => {
      if (event.origin !== window.location.origin || asRecord(event.data).type !== "host-ai-recipe-updated") return;
      setRefreshTick((current) => current + 1);
    };
    window.addEventListener("message", refreshAfterRecipeWrite);
    return () => window.removeEventListener("message", refreshAfterRecipeWrite);
  }, []);

  if (loading) {
    return <LoadingState label="Cargando dashboard..." />;
  }

  if (error) {
    return (
      <section
        className="panel"
        role="region"
        aria-labelledby="dashboard-title"
      >
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">HOST AI</p>
            <h2 id="dashboard-title">
              Estado operativo del restaurante
            </h2>
          </div>

          <button
            type="button"
            onClick={() => setRefreshTick((current) => current + 1)}
          >
            Reintentar
          </button>
        </header>

        <ErrorState
          title="No se pudo cargar el dashboard."
          detail={error}
        />

        <p className="meta-line">
          Request ID: {errorRequestId || "No disponible"}
        </p>
      </section>
    );
  }

  const dashboard = data?.dashboard ?? {};
  const empty = Object.keys(dashboard).length === 0;

  const prioridad = asRecord(dashboard.prioridad);
  const evento = asRecord(dashboard.evento_activo);
  const pendientes = asArray(dashboard.pendientes);
  const riesgos = asArray(dashboard.riesgos);
  const riskGroups = groupDashboardRisks(riesgos);
  const recomendaciones = asArray(dashboard.recomendaciones);
  const workflows = asArray(dashboard.workflows);

  const lastUpdate =
    valueToText(
      (dashboard as Record<string, unknown>).actualizado_en,
    ) ||
    valueToText(
      (dashboard as Record<string, unknown>).ultima_actualizacion,
    ) ||
    valueToText(
      (dashboard as Record<string, unknown>).updated_at,
    );

  const priorityAction =
    prioridad.titulo ||
    prioridad.workflow ||
    prioridad.codigo;

  const priorityMessage =
    prioridad.mensaje ||
    prioridad.justificacion ||
    prioridad.descripcion;

  const eventName =
    evento.nombre ||
    evento.prioritario_nombre;

  return (
    <section
      className="panel"
      role="region"
      aria-labelledby="dashboard-title"
    >
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">HOST AI</p>

          <h2 id="dashboard-title">
            Estado operativo del restaurante
          </h2>

          <p className="meta-line">
            Última actualización:{" "}
            {formatDateTime(lastUpdate) || "No disponible"}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setRefreshTick((current) => current + 1)}
        >
          Actualizar
        </button>
      </header>

      <section
        className="safe-mode"
        aria-label="Estado de seguridad"
      >
        <p>
          <strong>Modo seguro:</strong>{" "}
          {data?.modo_seguro ? "Activo" : "Inactivo"}
        </p>

        <p>
          <strong>Datos reales modificados:</strong>{" "}
          {data?.datos_reales_modificados ? "Sí" : "No"}
        </p>

        <p className="meta-line">
          Request ID: {data?.request_id || "No disponible"}
        </p>
      </section>

      {data?.datos_reales_modificados ? (
        <div
          className="panel-state panel-error"
          role="alert"
        >
          <p className="panel-error-title">
            Alerta técnica de seguridad
          </p>

          <p className="panel-error-detail">
            La API indica que se han modificado datos reales.
            Revisa esta situación antes de continuar.
          </p>
        </div>
      ) : null}

      {empty ? (
        <div className="panel-state">
          <p>No hay información operativa disponible.</p>
        </div>
      ) : (
        <>
          <section
            className="dashboard-grid"
            aria-label="Resumen operativo"
          >
            <StatCard
              title="Estado general"
              value={formatGeneralStatus(
                dashboard.estado_general,
              )}
            />

            <StatCard
              title="Prioridad"
              value={
                valueToText(priorityMessage) ||
                formatPriorityName(priorityAction) ||
                "Sin prioridad pendiente"
              }
            />

            <StatCard
              title="Pendientes"
              value={formatCount(
                pendientes.length,
                "Sin pendientes",
              )}
            />

            <StatCard
              title="Riesgos"
              value={formatCount(
                riskGroups.length,
                "Sin riesgos",
              )}
            />

            <StatCard
              title="Evento activo"
              value={
                valueToText(eventName) ||
                "Sin evento activo"
              }
            />

            <StatCard
              title="Workflows preparados"
              value={formatCount(
                workflows.length,
                "Ninguno preparado",
              )}
            />
          </section>

          <section
            className="feature-block feature-priority"
            aria-label="Prioridad del día"
          >
            <h3>Prioridad del día</h3>

            <p>
              <strong>Acción prioritaria:</strong>{" "}
              {formatPriorityName(priorityAction) ||
                "Sin acción prioritaria"}
            </p>

            <p>
              <strong>Justificación:</strong>{" "}
              {valueToText(priorityMessage) ||
                "Sin justificación disponible"}
            </p>

            <p>
              <strong>Siguiente recomendación:</strong>{" "}
              {formatRecommendation(
                recomendaciones[0],
              ) || "Sin recomendaciones pendientes"}
            </p>
          </section>

          <section
            className="feature-block"
            aria-label="Evento activo"
          >
            <h3>Evento activo</h3>

            {Object.keys(evento).length === 0 ? (
              <p>No hay ningún evento activo.</p>
            ) : (
              <ul className="clean-list">
                <li>
                  <strong>Nombre:</strong>{" "}
                  {valueToText(eventName) ||
                    "No disponible"}
                </li>

                <li>
                  <strong>Fecha:</strong>{" "}
                  {formatDateTime(
                    valueToText(evento.fecha),
                  ) || "No disponible"}
                </li>

                <li>
                  <strong>PAX:</strong>{" "}
                  {valueToText(evento.pax) ||
                    "No disponible"}
                </li>

                <li>
                  <strong>Estado:</strong>{" "}
                  {formatReadableCode(evento.estado) ||
                    "No disponible"}
                </li>

                <li>
                  <strong>Progreso del workflow:</strong>{" "}
                  {formatWorkflowProgress(
                    evento.progreso_workflow ||
                      evento.workflow_progreso,
                  )}
                </li>
              </ul>
            )}
          </section>

          <section
            className="feature-block"
            aria-label="Pendientes"
          >
            <h3>Pendientes</h3>

            {pendientes.length === 0 ? (
              <p>No hay tareas operativas pendientes.</p>
            ) : (
              <ol>
                {pendientes.map((item, index) => {
                  const pending = asRecord(item);

                  const pendingCode =
                    pending.nombre ||
                    pending.titulo ||
                    pending.codigo;

                  return (
                    <li
                      key={`${index}-${
                        valueToText(pending.codigo) ||
                        "pendiente"
                      }`}
                    >
                      <strong>
                        {formatReadableCode(pendingCode) ||
                          "Tarea pendiente"}
                      </strong>

                      <p>
                        {valueToText(
                          pending.descripcion ||
                            pending.motivo ||
                            pending.detalle ||
                            pending.mensaje,
                        ) || "Sin descripción disponible"}
                      </p>

                      <p className="meta-line">
                        Estado:{" "}
                        {formatReadableCode(
                          pending.estado,
                        ) || "No disponible"}
                        {" | "}
                        Prioridad:{" "}
                        {formatReadableCode(
                          pending.prioridad,
                        ) || "No disponible"}
                      </p>
                      {!asArray(pending.entidades).length ? <DashboardEntityAction value={pending} onResolved={() => setRefreshTick((current) => current + 1)} /> : null}
                      <PendingRecipes items={asArray(pending.entidades)} />
                    </li>
                  );
                })}
              </ol>
            )}
          </section>

          <section
            className="feature-block"
            aria-label="Riesgos"
          >
            <h3>Riesgos</h3>

            {riskGroups.length === 0 ? (
              <p>No hay riesgos operativos reportados.</p>
            ) : (
              <ul className="clean-list">
                {riskGroups.map((group) => {
                  const risk = group.risk;

                  const level = normalizeLevel(
                    valueToText(
                      risk.nivel ||
                        risk.severidad,
                    ),
                  );

                  return (
                    <li
                      key={group.key}
                      className={`risk-item risk-${level}`}
                    >
                      <p>
                        <strong>
                          {riskPrefix(level)}
                        </strong>{" "}
                        Nivel {formatRiskLevel(level)}
                      </p>

                      <p>
                        {valueToText(
                          risk.mensaje ||
                            risk.detalle ||
                            risk.descripcion,
                        ) || "Sin detalle disponible"}
                      </p>

                      <p className="meta-line">
                        Acción recomendada:{" "}
                        {valueToText(
                          risk.accion_recomendada ||
                            risk.recomendacion,
                        ) || "Sin acción recomendada"}
                      </p>

                      {group.items.length > 1 ? (
                        <details>
                          <summary>{group.items.length} incidencias agrupadas · ver detalle</summary>
                          <ul className="clean-list">
                            {group.items.map((detail, detailIndex) => (
                              <li key={`${group.key}-${detailIndex}`}>
                                <p>{valueToText(detail.mensaje || detail.detalle || detail.descripcion) || "Sin detalle disponible"}</p>
                                <DashboardEntityAction value={detail} onResolved={() => setRefreshTick((current) => current + 1)} />
                              </li>
                            ))}
                          </ul>
                        </details>
                      ) : null}
                      {group.items.length === 1 ? <DashboardEntityAction value={risk} onResolved={() => setRefreshTick((current) => current + 1)} /> : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section
            className="feature-block"
            aria-label="Recomendaciones"
          >
            <h3>Recomendaciones</h3>

            {recomendaciones.length === 0 ? (
              <p>No hay recomendaciones disponibles.</p>
            ) : (
              <ol>
                {recomendaciones.map(
                  (item, index) => (
                    <li key={`${index}-recomendacion`}>
                      {formatRecommendation(item) ||
                        "Recomendación no disponible"}
                    </li>
                  ),
                )}
              </ol>
            )}
          </section>

          <section
            className="feature-block"
            aria-label="Workflows preparados"
          >
            <h3>Workflows preparados</h3>

            {workflows.length === 0 ? (
              <p>No hay workflows preparados.</p>
            ) : (
              <ul className="clean-list">
                {workflows.map((item, index) => {
                  const workflow = asRecord(item);

                  const workflowName =
                    workflow.workflow ||
                    workflow.nombre ||
                    workflow.codigo;

                  return (
                    <li
                      key={`${index}-${
                        valueToText(
                          workflow.workflow ||
                            workflow.codigo,
                        ) || "workflow"
                      }`}
                    >
                      <strong>
                        {formatReadableCode(
                          workflowName,
                        ) || "Workflow"}
                      </strong>

                      <p className="meta-line">
                        Estado:{" "}
                        {formatReadableCode(
                          workflow.estado,
                        ) || "No disponible"}
                      </p>
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

function StatCard({
  title,
  value,
}: {
  title: string;
  value: unknown;
}) {
  return (
    <article className="data-card">
      <h3>{title}</h3>
      <p className="stat-value">
        {valueToText(value) || "No disponible"}
      </p>
    </article>
  );
}

function valueToText(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string") {
    return value.trim();
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return "";
}

function asRecord(
  value: unknown,
): Record<string, unknown> {
  if (
    value &&
    typeof value === "object" &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }

  return {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function formatCount(
  count: number,
  emptyText: string,
): string {
  return count === 0 ? emptyText : String(count);
}

function formatGeneralStatus(value: unknown): string {
  const status = valueToText(value).toLowerCase();

  const labels: Record<string, string> = {
    resumen_restaurante_generado:
      "Restaurante operativo",
    operativo: "Restaurante operativo",
    ok: "Restaurante operativo",
    up: "Restaurante operativo",
    estable: "Operación estable",
    sin_datos: "Sin información operativa",
    no_disponible: "Información no disponible",
    error: "Revisión necesaria",
  };

  if (!status) {
    return "Sin información";
  }

  return (
    labels[status] ||
    capitalizeWords(
      status.replaceAll("_", " "),
    )
  );
}

function formatPriorityName(
  value: unknown,
): string {
  const code = valueToText(value).toUpperCase();

  const labels: Record<string, string> = {
    PRODUCCION_PLAN:
      "Generar planificación de cocina",
    COMPRAS_PLAN:
      "Revisar necesidades de compra",
    STOCK_REVIEW:
      "Revisar existencias y stock crítico",
    EVENTO_REVIEW:
      "Revisar el evento activo",
    PRODUCCION_REVIEW:
      "Revisar la producción pendiente",
    COMPRAS_REVIEW:
      "Revisar pedidos y recepciones",
  };

  if (!code) {
    return "";
  }

  return (
    labels[code] ||
    capitalizeWords(
      code.replaceAll("_", " ").toLowerCase(),
    )
  );
}

function formatReadableCode(
  value: unknown,
): string {
  const text = valueToText(value);

  if (!text) {
    return "";
  }

  return capitalizeWords(
    text.replaceAll("_", " ").toLowerCase(),
  );
}

function formatRecommendation(
  value: unknown,
): string {
  const directText = valueToText(value);

  if (directText) {
    return directText;
  }

  const recommendation = asRecord(value);

  return (
    valueToText(
      recommendation.mensaje ||
        recommendation.descripcion ||
        recommendation.detalle ||
        recommendation.titulo ||
        recommendation.nombre,
    ) ||
    formatReadableCode(
      recommendation.codigo,
    )
  );
}

function formatWorkflowProgress(
  value: unknown,
): string {
  if (
    typeof value === "number" &&
    Number.isFinite(value)
  ) {
    if (value >= 0 && value <= 1) {
      return `${Math.round(value * 100)} %`;
    }

    return `${Math.round(value)} %`;
  }

  const text = valueToText(value);

  if (!text) {
    return "No disponible";
  }

  return formatReadableCode(text);
}

function formatDateTime(
  value: unknown,
): string {
  const text = valueToText(value);

  if (!text) {
    return "";
  }

  const date = new Date(text);

  if (Number.isNaN(date.getTime())) {
    return text;
  }

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function capitalizeWords(value: string): string {
  const trimmed = value.trim();

  if (!trimmed) {
    return "";
  }

  return trimmed
    .split(/\s+/)
    .map((word) => {
      if (!word) return word;

      return (
        word.charAt(0).toUpperCase() +
        word.slice(1)
      );
    })
    .join(" ");
}

function normalizeLevel(
  level: string,
): "alto" | "medio" | "bajo" {
  const raw = String(level || "").toLowerCase();

  if (
    raw.includes("alt") ||
    raw.includes("critic") ||
    raw.includes("grave")
  ) {
    return "alto";
  }

  if (
    raw.includes("baj") ||
    raw.includes("leve")
  ) {
    return "bajo";
  }

  return "medio";
}

function formatRiskLevel(
  level: "alto" | "medio" | "bajo",
): string {
  if (level === "alto") {
    return "Alto";
  }

  if (level === "bajo") {
    return "Bajo";
  }

  return "Medio";
}

function riskPrefix(
  level: "alto" | "medio" | "bajo",
): string {
  if (level === "alto") {
    return "[ALTO]";
  }

  if (level === "bajo") {
    return "[BAJO]";
  }

  return "[MEDIO]";
}

function groupDashboardRisks(values: unknown[]): Array<{ key: string; risk: Record<string, unknown>; items: Record<string, unknown>[] }> {
  const groups = new Map<string, Record<string, unknown>[]>();
  for (const value of values) {
    const risk = asRecord(value);
    const type = valueToText(risk.tipo || risk.codigo || risk.modulo || "riesgo").toLowerCase();
    const missingLocation = type.includes("ubic") || valueToText(risk.mensaje).toLowerCase().includes("sin ubicaci");
    const entity = valueToText(missingLocation ? (risk.articulo_id || risk.nombre) : (risk.lote_id || risk.entidad_id || risk.articulo_id || risk.plan_id || risk.mensaje));
    const key = `${normalizeLevel(valueToText(risk.nivel || risk.severidad))}:${type}:${entity.toLowerCase()}`;
    groups.set(key, [...(groups.get(key) || []), risk]);
  }
  const rank = { alto: 0, medio: 1, bajo: 2 } as const;
  return [...groups.entries()]
    .map(([key, items]) => ({ key, risk: items[0], items }))
    .sort((a, b) => rank[normalizeLevel(valueToText(a.risk.nivel || a.risk.severidad))] - rank[normalizeLevel(valueToText(b.risk.nivel || b.risk.severidad))]);
}

function DashboardEntityAction({ value, onResolved }: { value: Record<string, unknown>; onResolved: () => void }) {
  const entity = asRecord(value.entidad || value.entity);
  const code = valueToText(value.tipo || value.codigo || value.nombre).toUpperCase();
  let type = valueToText(value.tipo_entidad || value.modulo || entity.tipo || entity.modulo).toUpperCase();
  if (!type && value.lote_id) type = "LOTE";
  if (!type && value.plan_id) type = "PRODUCCION";
  if (!type && value.reserva_id) type = "RESERVA";
  if (!type && value.pedido_id) type = "PEDIDO";
  if (!type && value.evento_id) type = "EVENTO";
  if (!type && value.receta_id) type = code.includes("ESCANDALLO") ? "ESCANDALLO" : "RECETA";
  if (!type && value.articulo_id) type = code.includes("STOCK") || code.includes("BAJO") ? "STOCK_BAJO" : "ARTICULO";
  const id = valueToText(value.entidad_id || value.entity_id || value.lote_id || value.articulo_id || value.evento_id || value.reserva_id || value.pedido_id || value.receta_id || value.plan_id || entity.id);
  const aggregateRoutes: Record<string, { path: string; label: string }> = {
    RECETAS: { path: "/biblioteca/elaboraciones", label: "Ver recetas incompletas" },
    PRODUCCION: { path: "/produccion", label: "Abrir producciÃ³n" },
  };
  if (!id) {
    const aggregate = aggregateRoutes[type];
    return aggregate ? <div className="menu-actions"><a href={aggregate.path} target="_blank" rel="noopener noreferrer">{aggregate.label}</a></div> : null;
  }
  if (!/^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$/.test(id)) return null;
  const routes: Record<string, { path: string; label: string }> = {
    ARTICULO: { path: `/articulos/${encodeURIComponent(id)}`, label: "Abrir artículo" },
    CATALOGO: { path: `/articulos/${encodeURIComponent(id)}`, label: "Abrir artículo" },
    EVENTO: { path: `/eventos?${new URLSearchParams({ evento_id: id })}`, label: "Abrir evento" },
    EVENTOS: { path: `/eventos?${new URLSearchParams({ evento_id: id })}`, label: "Abrir evento" },
    RESERVA: { path: `/reservas/${encodeURIComponent(id)}`, label: "Abrir reserva" },
    COMPRA: { path: `/compras?${new URLSearchParams({ pedido_id: id })}`, label: "Abrir pedido" },
    PEDIDO: { path: `/compras?${new URLSearchParams({ pedido_id: id })}`, label: "Abrir pedido" },
    RECETA: { path: `/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=receta`, label: "Abrir receta" },
    ELABORACION: { path: `/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=receta`, label: "Abrir receta" },
    PRODUCCION: { path: `/produccion?${new URLSearchParams({ plan_id: id })}`, label: "Abrir producción" },
    ESCANDALLO: { path: `/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=escandallo`, label: "Editar escandallo" },
    STOCK_BAJO: { path: `/compras?${new URLSearchParams({ article_id: id })}`, label: "Preparar compra" },
  };
  if (type === "LOTE") return <DashboardLotLocationAction lotId={id} onResolved={onResolved} />;
  const route = routes[type];
  return route ? <div className="menu-actions"><a href={route.path} target="_blank" rel="noopener noreferrer">{route.label}</a></div> : null;
}

function PendingRecipes({ items }: { items: unknown[] }) {
  if (!items.length) return null;
  return <section aria-label={`Recetas pendientes de completar — ${items.length}`}>
    {items.map((raw) => {
      const recipe = asRecord(raw);
      const id = valueToText(recipe.receta_id || recipe.id);
      if (!id || !/^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$/.test(id)) return null;
      const missing = asArray(recipe.campos_faltantes).map(valueToText).filter(Boolean);
      const incidents = asArray(recipe.incidencias).map((item) => valueToText(asRecord(item).mensaje || asRecord(item).message || item)).filter(Boolean);
      return <details key={id}><summary>{valueToText(recipe.nombre) || id}</summary>
        <p className="meta-line">ID: {id} · Estado: {formatReadableCode(recipe.estado) || "Pendiente"}</p>
        {missing.length ? <><strong>Falta:</strong><ul>{missing.map((field) => <li key={field}>{formatReadableCode(field)}</li>)}</ul></> : null}
        {incidents.length ? <><strong>Incidencias:</strong><ul>{incidents.map((incident) => <li key={incident}>{incident}</li>)}</ul></> : null}
        <div className="menu-actions"><a href={`/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=receta`} target="_blank" rel="noopener noreferrer">Abrir receta</a><a href={`/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=receta&complete=1`} target="_blank" rel="noopener noreferrer">Completar</a></div>
      </details>;
    })}
  </section>;
}

function DashboardLotLocationAction({ lotId, onResolved }: { lotId: string; onResolved: () => void }) {
  const [open, setOpen] = useState(false);
  const [locations, setLocations] = useState<Array<{ id: string; nombre: string }>>([]);
  const [locationId, setLocationId] = useState("");
  const [preview, setPreview] = useState<{ preview_token: string; lote_antes: Record<string, unknown>; lote_despues: Record<string, unknown>; requiere_confirmacion: boolean } | null>(null);
  const [error, setError] = useState("");
  const begin = async () => { setOpen(true); setError(""); try { setLocations((await stockService.locations()).ubicaciones); } catch (reason) { setError((reason as Error).message); } };
  if (!open) return <div className="menu-actions"><a href={`/stock?${new URLSearchParams({ lote_id: lotId })}`} target="_blank" rel="noopener noreferrer">Abrir lote</a><button type="button" onClick={() => void begin()}>Asignar ubicación</button></div>;
  return <section className="draft-warning" aria-label={`Asignar ubicación a ${lotId}`}>
    <label>Ubicación<select aria-label="Ubicación canónica" value={locationId} onChange={(event) => { setLocationId(event.target.value); setPreview(null); }}><option value="">Seleccionar</option>{locations.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>
    {!preview ? <button type="button" disabled={!locationId} onClick={() => stockService.previewLocation(lotId, locationId).then(setPreview).catch((reason: Error) => setError(reason.message))}>Vista previa</button> : <><p>{String(preview.lote_antes.ubicacion || "Sin ubicación")} → {String(preview.lote_despues.ubicacion)}</p><p>La cantidad de stock no cambiará.</p><button type="button" disabled={!preview.requiere_confirmacion} onClick={() => stockService.confirmLocation(lotId, locationId, preview.preview_token).then(() => { setOpen(false); onResolved(); }).catch((reason: Error) => { setPreview(null); setError(reason.message); })}>Confirmar ubicación</button></>}
    <button type="button" onClick={() => { setOpen(false); setPreview(null); }}>Cancelar</button>
    {error ? <p role="alert">{error}</p> : null}
  </section>;
}
