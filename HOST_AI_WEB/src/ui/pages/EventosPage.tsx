import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import {
  eventosService,
  type EventosResult,
} from "../../services/eventosService";
import type { EventoListItem } from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { SearchField } from "../components/SearchField";
import { SafeCatalogWritePanel } from "../components/SafeCatalogWritePanel";

export function EventosPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<EventosResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [params, setParams] = useSearchParams();
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [detailError, setDetailError] = useState("");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState(false);
  const eventId = params.get("evento_id") || "";
  const editRequested = params.get("edit") === "1";

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError(null);
    setErrorRequestId(null);

    eventosService
      .load()
      .then((result) => {
        if (active) setData(result);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setData(null);
        if (err instanceof HostAiApiError) {
          setError(err.message);
          setErrorRequestId(err.requestId || null);
        } else {
          setError("No se pudieron cargar los eventos.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshTick]);

  useEffect(() => { if (!eventId) { setDetail(null); setDetailError(""); return; } eventosService.detail(eventId).then((response) => { setDetail(response.evento); setDetailError(""); }).catch((reason) => { setDetail(null); setDetailError(reason instanceof Error ? reason.message : "No se ha encontrado el evento solicitado."); }); }, [eventId, refreshTick]);
  useEffect(() => { setEditing(Boolean(eventId && editRequested)); }, [eventId, editRequested]);

  const statuses = useMemo(() => [...new Set((data?.eventos ?? []).map((item) => text(item.estado)).filter(Boolean))], [data]);
  const visibleEvents = useMemo(() => {
    const needle = normalize(query);
    return (data?.eventos ?? []).filter((item) => (!status || item.estado === status) && (!needle || normalize([item.nombre, item.fecha, item.estado, item.id].join(" ")).includes(needle)));
  }, [data, query, status]);

  if (loading) {
    return <LoadingState label="Cargando eventos..." />;
  }

  return (
    <section
      className="panel"
      role="region"
      aria-labelledby="eventos-title"
    >
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Operativa</p>
          <h2 id="eventos-title">Eventos</h2>
          <p className="meta-line">
            Próximos servicios y celebraciones
          </p>
        </div>
        <button
          type="button"
          onClick={() => setRefreshTick((value) => value + 1)}
        >
          {error ? "Reintentar" : "Actualizar"}
        </button>
        <button type="button" onClick={() => { setCreating(true); setEditing(false); }}>+ Nuevo evento</button>
      </header>

      {creating ? <SafeCatalogWritePanel domain="EVENTO" operation="CREAR" onCancel={() => setCreating(false)} onConfirmed={(record) => { setCreating(false); setParams({ evento_id: String(record.id || "") }); setRefreshTick((value) => value + 1); }} /> : null}
      {detailError ? <div className="panel-state panel-error" role="alert"><p>{detailError}</p><button type="button" onClick={() => setParams({})}>Volver al listado</button></div> : null}
      {detail && !editing ? <EventDetail event={detail} onBack={() => setParams({})} onEdit={() => setEditing(true)} /> : null}
      {detail && editing ? <SafeCatalogWritePanel domain="EVENTO" operation="MODIFICAR" entityId={eventId} initial={detail} onCancel={() => setEditing(false)} onConfirmed={(record) => { setDetail(record); setEditing(false); setRefreshTick((value) => value + 1); }} /> : null}

      {error ? (
        <>
          <ErrorState
            title="No se pudieron cargar los eventos."
            detail={error}
          />
          <p className="meta-line">
            Request ID: {errorRequestId || "No disponible"}
          </p>
        </>
      ) : (
        <>
          <section className="safe-mode" aria-label="Estado de seguridad">
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
            <div className="panel-state panel-error" role="alert">
              <p className="panel-error-title">
                La API indica que se han modificado datos reales.
              </p>
            </div>
          ) : null}

          <section className="dashboard-grid" aria-label="Resumen de eventos">
            <SummaryCard title="Eventos próximos" value={data?.total ?? 0} />
            <SummaryCard
              title="PAX previstos"
              value={data?.resumen.pax_total ?? 0}
            />
            <SummaryCard
              title="Servicios asociados"
              value={data?.resumen.servicios ?? 0}
            />
            <SummaryCard
              title="Avisos operativos"
              value={data?.resumen.avisos ?? 0}
            />
          </section>

          <div className="module-toolbar"><SearchField value={query} onChange={setQuery} placeholder="Buscar eventos..." ariaLabel="Buscar eventos" />{statuses.length ? <label>Estado<select aria-label="Filtrar eventos por estado" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Todos</option>{statuses.map((value) => <option key={value}>{readable(value)}</option>)}</select></label> : null}</div>

          {visibleEvents.length ? (
            <div className="eventos-list" aria-label="Listado de eventos">
              {visibleEvents.map((evento, index) => (
                <EventoCard
                  key={evento.id || `${evento.nombre || "evento"}-${index}`}
                  evento={evento}
                />
              ))}
            </div>
          ) : query || status ? <div className="module-empty-search"><p>No hay eventos que coincidan con “{query || readable(status)}”.</p></div> : (
            <div className="panel-state">
              <p>No hay próximos eventos disponibles.</p>
              {data?.mensaje ? (
                <p className="meta-line">{data.mensaje}</p>
              ) : null}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function EventoCard({ evento }: { evento: EventoListItem }) {
  return (
    <article className="evento-card">
      <header>
        <h3>{text(evento.nombre) || "Evento sin nombre"}</h3>
        <span className="evento-status">
          {readable(evento.estado) || "Estado no disponible"}
        </span>
      </header>
      <dl className="evento-details">
        <div>
          <dt>Fecha</dt>
          <dd>{formatDate(evento.fecha) || "No disponible"}</dd>
        </div>
        <div>
          <dt>PAX</dt>
          <dd>{formatNumber(evento.pax)}</dd>
        </div>
        <div>
          <dt>Días</dt>
          <dd>{formatDays(evento.dias)}</dd>
        </div>
        <div>
          <dt>Servicios</dt>
          <dd>{formatServices(evento.servicios)}</dd>
        </div>
      </dl>
      {evento.avisos?.length ? (
        <section className="evento-alerts" aria-label="Avisos del evento">
          <h4>Avisos operativos</h4>
          <ul className="clean-list">
            {evento.avisos.map((aviso, index) => (
              <li key={`${evento.id || "evento"}-aviso-${index}`}>
                {aviso}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {evento.id ? <div className="menu-actions"><a href={`/eventos?evento_id=${encodeURIComponent(evento.id)}`}>Abrir</a><a href={`/eventos?evento_id=${encodeURIComponent(evento.id)}&edit=1`}>Editar</a></div> : null}
    </article>
  );
}

function EventDetail({ event, onBack, onEdit }: { event: Record<string, unknown>; onBack: () => void; onEdit: () => void }) {
  const services = Array.isArray(event.servicios) ? event.servicios : [];
  const related = [
    ["menu_id", "Menú", (id: string) => `/menus?${new URLSearchParams({ menu_id: id })}`],
    ["plan_produccion_id", "Producción", (id: string) => `/produccion?${new URLSearchParams({ plan_id: id })}`],
    ["pedido_id", "Compras", (id: string) => `/compras?${new URLSearchParams({ pedido_id: id })}`],
    ["reserva_id", "Reserva", (id: string) => `/reservas/${encodeURIComponent(id)}`],
  ] as const;
  return <section className="feature-block evento-detail" aria-label="Detalle del evento">
    <header><p className="eyebrow">Evento</p><h3>{String(event.nombre || "Evento")}</h3><span className="evento-status">{readable(event.estado) || "Estado no disponible"}</span></header>
    <EventSection title="Resumen" event={event} keys={["nombre", "tipo", "estado", "ubicacion"]} />
    <EventSection title="Cliente" event={event} keys={["cliente", "contacto", "telefono", "email"]} />
    <EventSection title="Fecha y asistentes" event={event} keys={["fecha", "hora_inicio", "hora_fin", "pax"]} />
    <section><h4>Servicios, menús y pases</h4>{services.length ? <div className="related-grid">{services.map((service, index) => <EventStructuredValue key={index} value={service} />)}</div> : <p>Sin servicios registrados.</p>}</section>
    <EventSection title="Incidencias y bloqueos" event={event} keys={["incidencias", "bloqueos", "avisos"]} />
    <EventSection title="Notas" event={event} keys={["observaciones", "notas"]} />
    <div className="menu-actions" aria-label="Acciones del evento"><button type="button" onClick={onEdit}>Editar evento</button>{related.map(([key, label, route]) => { const id = String(event[key] || ""); return id && /^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$/.test(id) ? <a key={key} href={route(id)} target="_blank" rel="noopener noreferrer">Ver {label.toLowerCase()}</a> : null; })}<button type="button" className="secondary" onClick={onBack}>Volver al listado</button></div>
  </section>;
}

function EventSection({ title, event, keys }: { title: string; event: Record<string, unknown>; keys: string[] }) {
  const available = keys.filter((key) => event[key] !== undefined && event[key] !== null && event[key] !== "");
  return <section><h4>{title}</h4>{available.length ? <dl className="detail-grid">{available.map((key) => <div key={key}><dt>{readable(key)}</dt><dd><EventStructuredValue value={event[key]} /></dd></div>)}</dl> : <p>Sin información registrada.</p>}</section>;
}

function EventStructuredValue({ value }: { value: unknown }) {
  if (Array.isArray(value)) return value.length ? <ul>{value.map((item, index) => <li key={index}><EventStructuredValue value={item} /></li>)}</ul> : <>Sin información</>;
  if (value && typeof value === "object") return <dl className="detail-grid">{Object.entries(value as Record<string, unknown>).filter(([, item]) => item !== null && item !== "").map(([key, item]) => <div key={key}><dt>{readable(key)}</dt><dd><EventStructuredValue value={item} /></dd></div>)}</dl>;
  return <>{String(value ?? "No disponible")}</>;
}

function SummaryCard({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <article className="data-card">
      <h3>{title}</h3>
      <p className="stat-value">{value}</p>
    </article>
  );
}

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function normalize(value: unknown): string { return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim(); }

function readable(value: unknown): string {
  const valueText = text(value);
  if (!valueText) return "";
  const normalized = valueText.replaceAll("_", " ").toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatDate(value: unknown): string {
  const valueText = text(value);
  if (!valueText) return "";
  const isoDate = /^\d{4}-\d{2}-\d{2}$/.test(valueText);
  const date = new Date(isoDate ? `${valueText}T00:00:00Z` : valueText);
  if (Number.isNaN(date.getTime())) return valueText;
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "long",
    timeZone: isoDate ? "UTC" : undefined,
  }).format(date);
}

function formatNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("es-ES").format(value)
    : "No disponible";
}

function formatDays(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value) || value === 999) {
    return "No disponible";
  }
  if (value === 0) return "Hoy";
  if (value === 1) return "Mañana";
  return `En ${value} días`;
}

function formatServices(value: unknown): string {
  const count = Array.isArray(value) ? value.length : value;
  if (typeof count !== "number" || !Number.isFinite(count)) {
    return "No disponible";
  }
  return `${count} ${count === 1 ? "servicio" : "servicios"}`;
}
