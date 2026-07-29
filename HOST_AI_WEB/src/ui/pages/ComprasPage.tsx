import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import {
  comprasService,
  type ComprasResult,
} from "../../services/comprasService";
import type {
  CompraHistorialListItem,
  CompraListItem,
  PropuestaCompraListItem,
  ProveedorCompraListItem,
} from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ComprasPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<ComprasResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError(null);
    setErrorRequestId(null);

    comprasService
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
          setError("No se pudo cargar la información de compras.");
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
    return <LoadingState label="Cargando compras..." />;
  }

  return (
    <section
      className="panel"
      role="region"
      aria-labelledby="compras-title"
    >
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Operativa</p>
          <h2 id="compras-title">Compras</h2>
          <p className="meta-line">
            Necesidades pendientes y seguimiento de aprovisionamiento
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
            title="No se pudo cargar la información de compras."
            detail={error}
          />
          <p className="meta-line">
            Request ID: {errorRequestId || "No disponible"}
          </p>
        </>
      ) : (
        <ComprasContent data={data} />
      )}
    </section>
  );
}

function ComprasContent({ data }: { data: ComprasResult | null }) {
  const compras = data?.compras ?? [];
  const propuestas = data?.propuestas ?? [];
  const proveedores = data?.proveedores ?? [];
  const historial = data?.historial ?? [];

  return (
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

      <section className="dashboard-grid" aria-label="Resumen de compras">
        <SummaryCard title="Necesidades abiertas" value={data?.total ?? 0} />
        <SummaryCard title="Propuestas pendientes" value={propuestas.length} />
        <SummaryCard title="Proveedores activos" value={proveedores.length} />
        <SummaryCard title="Compras registradas" value={historial.length} />
        <SummaryCard
          title="Estado del módulo"
          value={readable(data?.estado) || "No disponible"}
        />
      </section>

      <section className="feature-block" aria-label="Compras pendientes">
        <h3>Compras pendientes</h3>
        {compras.length ? (
          <ul className="clean-list compras-list">
            {compras.map((compra, index) => (
              <CompraItem
                key={compra.id || `${compra.nombre || "compra"}-${index}`}
                compra={compra}
              />
            ))}
          </ul>
        ) : (
          <div className="panel-state">
            <p>No hay necesidades de compra pendientes.</p>
            {data?.mensaje ? (
              <p className="meta-line">{data.mensaje}</p>
            ) : null}
          </div>
        )}
      </section>

      <PropuestasSection items={propuestas} />
      <ProveedoresSection items={proveedores} />
      <HistorialSection items={historial} />
      <UnavailableSection
        title="Recepciones e incidencias"
        text="La API pública actual no expone recepciones ni incidencias específicas de compras."
      />
    </>
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

function CompraItem({ compra }: { compra: CompraListItem }) {
  return (
    <li className="compra-item">
      <div>
        <strong>{text(compra.nombre) || "Compra sin nombre"}</strong>
        <p className="meta-line">
          Estado: {readable(compra.estado) || "No disponible"}
        </p>
      </div>
      <dl className="compra-meta">
        <div>
          <dt>Prioridad</dt>
          <dd>{formatPriority(compra.prioridad)}</dd>
        </div>
        <div>
          <dt>Fecha necesaria</dt>
          <dd>{formatDate(compra.fecha_necesaria) || "No disponible"}</dd>
        </div>
      </dl>
    </li>
  );
}

function PropuestasSection({
  items,
}: {
  items: PropuestaCompraListItem[];
}) {
  return (
    <section className="feature-block" aria-label="Propuestas de compra">
      <h3>Propuestas de compra</h3>
      {items.length ? (
        <ul className="clean-list compras-list">
          {items.map((item, index) => (
            <li
              className="compra-item"
              key={item.id || `${item.producto || "propuesta"}-${index}`}
            >
              <div>
                <strong>{text(item.producto) || "Producto sin nombre"}</strong>
                <p className="meta-line">
                  Estado: {readable(item.estado) || "No disponible"}
                </p>
              </div>
              <p>
                {formatQuantity(item.comprar, item.unidad)}
                {" · "}
                {text(item.proveedor_sugerido) || "Sin proveedor sugerido"}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="panel-state">
          <p>No hay propuestas de compra pendientes.</p>
        </div>
      )}
    </section>
  );
}

function ProveedoresSection({
  items,
}: {
  items: ProveedorCompraListItem[];
}) {
  return (
    <section className="feature-block" aria-label="Proveedores activos">
      <h3>Proveedores activos</h3>
      {items.length ? (
        <ul className="clean-list compras-list">
          {items.map((item, index) => (
            <li
              className="compra-item"
              key={item.id || `${item.nombre || "proveedor"}-${index}`}
            >
              <div>
                <strong>{text(item.nombre) || "Proveedor sin nombre"}</strong>
                <p className="meta-line">
                  Estado: {readable(item.estado) || "No disponible"}
                </p>
              </div>
              <p>{text(item.email) || text(item.telefono) || "Sin contacto"}</p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="panel-state">
          <p>No hay proveedores activos.</p>
        </div>
      )}
    </section>
  );
}

function HistorialSection({
  items,
}: {
  items: CompraHistorialListItem[];
}) {
  return (
    <section className="feature-block" aria-label="Historial de compras">
      <h3>Historial de compras</h3>
      {items.length ? (
        <ul className="clean-list compras-list">
          {items.map((item, index) => (
            <li
              className="compra-item"
              key={item.id || `${item.producto || "compra"}-${index}`}
            >
              <div>
                <strong>{text(item.producto) || "Producto sin nombre"}</strong>
                <p className="meta-line">
                  {text(item.proveedor) || "Sin proveedor"}
                </p>
              </div>
              <p>
                {formatQuantity(item.cantidad, item.unidad)}
                {" · "}
                {formatDate(item.creado_en) || "Fecha no disponible"}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="panel-state">
          <p>No hay compras registradas.</p>
        </div>
      )}
    </section>
  );
}

function UnavailableSection({
  title,
  text: detail,
}: {
  title: string;
  text: string;
}) {
  return (
    <section className="feature-block" aria-label={title}>
      <h3>{title}</h3>
      <p className="meta-line">{detail}</p>
    </section>
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

function formatPriority(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "No disponible";
  }
  return String(value);
}

function formatQuantity(value: unknown, unit: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "Cantidad no disponible";
  }
  return `${value.toLocaleString("es-ES")} ${text(unit)}`.trim();
}

function formatDate(value: unknown): string {
  const valueText = text(value);
  if (!valueText) return "";
  const isoDate = /^\d{4}-\d{2}-\d{2}$/.test(valueText);
  const date = new Date(isoDate ? `${valueText}T00:00:00Z` : valueText);
  if (Number.isNaN(date.getTime())) return valueText;
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeZone: isoDate ? "UTC" : undefined,
  }).format(date);
}
