import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { stockService, type StockResult } from "../../services/stockService";
import type {
  StockAlerta,
  StockExistencia,
  StockLote,
  StockMovimiento,
} from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function StockPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<StockResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setErrorRequestId(null);
    stockService
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
          setError("No se pudo cargar el stock.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshTick]);

  if (loading) return <LoadingState label="Cargando stock..." />;

  return (
    <section className="panel" role="region" aria-labelledby="stock-title">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Inventario</p>
          <h2 id="stock-title">Stock</h2>
          <p className="meta-line">Existencias, lotes y movimientos registrados</p>
        </div>
        <button type="button" onClick={() => setRefreshTick((value) => value + 1)}>
          {error ? "Reintentar" : "Actualizar"}
        </button>
      </header>

      {error ? (
        <>
          <ErrorState title="No se pudo cargar el stock." detail={error} />
          <p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p>
        </>
      ) : (
        <>
          <section className="safe-mode" aria-label="Estado de seguridad">
            <p><strong>Modo seguro:</strong> {data?.modo_seguro ? "Activo" : "Inactivo"}</p>
            <p><strong>Datos reales modificados:</strong> {data?.datos_reales_modificados ? "Sí" : "No"}</p>
            <p><strong>Estado operativo:</strong> {readable(data?.estado_operativo) || readable(data?.estado) || "No disponible"}</p>
            <p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p>
          </section>

          <section className="dashboard-grid" aria-label="Resumen de stock">
            <SummaryCard title="Artículos" value={data?.resumen.articulos ?? data?.existencias.length ?? 0} />
            <SummaryCard title="Lotes" value={data?.resumen.lotes ?? data?.lotes.length ?? 0} />
            <SummaryCard title="Movimientos" value={data?.resumen.movimientos ?? data?.movimientos.length ?? 0} />
            <SummaryCard title="Alertas" value={data?.resumen.alertas ?? data?.alertas.length ?? 0} />
          </section>

          {data?.alertas.length ? <Alertas alertas={data.alertas} /> : null}

          {data?.existencias.length ? (
            <section className="stock-section" aria-labelledby="stock-existencias">
              <h3 id="stock-existencias">Existencias actuales</h3>
              <div className="stock-grid">
                {data.existencias.map((item, index) => (
                  <Existencia key={item.clave || item.articulo_id || `${item.nombre}-${index}`} item={item} />
                ))}
              </div>
            </section>
          ) : (
            <div className="panel-state">
              <p>No hay existencias de stock registradas.</p>
              {data?.mensaje ? <p className="meta-line">{data.mensaje}</p> : null}
            </div>
          )}

          {data?.lotes.length ? <Lotes lotes={data.lotes} /> : null}
          {data?.movimientos.length ? <Movimientos movimientos={data.movimientos} /> : null}
        </>
      )}
    </section>
  );
}

function Alertas({ alertas }: { alertas: StockAlerta[] }) {
  return (
    <section className="stock-section stock-alerts" aria-labelledby="stock-alertas">
      <h3 id="stock-alertas">Alertas de stock</h3>
      <ul className="clean-list">
        {alertas.map((alerta, index) => (
          <li key={`${alerta.tipo || "alerta"}-${index}`}>
            <strong>{readable(alerta.tipo) || "Aviso"}:</strong> {alerta.mensaje || "Sin detalle"}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Existencia({ item }: { item: StockExistencia }) {
  return (
    <article className="stock-card">
      <h4>{item.nombre || "Artículo sin nombre"}</h4>
      <p className="stock-quantity">{formatQuantity(item.cantidad, item.unidad)}</p>
      <p className="meta-line">{item.familia || "Familia no disponible"} · {item.lotes?.length ?? 0} lotes</p>
    </article>
  );
}

function Lotes({ lotes }: { lotes: StockLote[] }) {
  return (
    <section className="stock-section" aria-labelledby="stock-lotes">
      <h3 id="stock-lotes">Lotes</h3>
      <div className="stock-table-wrap">
        <table className="stock-table">
          <thead><tr><th>Artículo</th><th>Cantidad</th><th>Ubicación</th><th>Caducidad</th></tr></thead>
          <tbody>
            {lotes.map((lote, index) => (
              <tr key={lote.id || `${lote.nombre}-${index}`}>
                <td>{lote.nombre || "No disponible"}</td>
                <td>{formatQuantity(lote.cantidad, lote.unidad)}</td>
                <td>{lote.ubicacion || "Sin ubicación"}</td>
                <td>{formatDate(lote.caducidad)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Movimientos({ movimientos }: { movimientos: StockMovimiento[] }) {
  return (
    <section className="stock-section" aria-labelledby="stock-movimientos">
      <h3 id="stock-movimientos">Movimientos recientes</h3>
      <ul className="clean-list stock-movements">
        {movimientos.map((movimiento, index) => (
          <li key={movimiento.id || `${movimiento.nombre}-${index}`}>
            <div><strong>{movimiento.nombre || "Artículo"}</strong><p className="meta-line">{readable(movimiento.tipo) || "Movimiento"} · {movimiento.motivo || "Sin motivo"}</p></div>
            <span>{formatQuantity(movimiento.cantidad, movimiento.unidad)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SummaryCard({ title, value }: { title: string; value: number }) {
  return <article className="data-card"><h3>{title}</h3><p className="stat-value">{value}</p></article>;
}

function readable(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "";
  const normalized = value.trim().replaceAll("_", " ").toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatQuantity(value: unknown, unit: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "No disponible";
  const suffix = typeof unit === "string" && unit.trim() ? ` ${unit}` : "";
  return `${new Intl.NumberFormat("es-ES").format(value)}${suffix}`;
}

function formatDate(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "No disponible";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-ES", { dateStyle: "medium", timeZone: "UTC" }).format(date);
}
