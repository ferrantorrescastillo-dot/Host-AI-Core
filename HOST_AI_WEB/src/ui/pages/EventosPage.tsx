import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import {
  eventosService,
  type EventosResult,
} from "../../services/eventosService";
import type { EventoListItem } from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function EventosPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<EventosResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

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
      </header>

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

          {data?.eventos.length ? (
            <div className="eventos-list" aria-label="Listado de eventos">
              {data.eventos.map((evento, index) => (
                <EventoCard
                  key={evento.id || `${evento.nombre || "evento"}-${index}`}
                  evento={evento}
                />
              ))}
            </div>
          ) : (
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
    </article>
  );
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
