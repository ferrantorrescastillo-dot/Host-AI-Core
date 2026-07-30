import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import type { ArticuloDetalle } from "../../types/articulos";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ArticuloDetailPage() {
  const { articuloId = "" } = useParams();
  const location = useLocation();
  const [item, setItem] = useState<ArticuloDetalle | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    setError(null);
    articulosService.get(articuloId).then((r) => active && setItem(r.articulo)).catch((e: unknown) => active && setError(e instanceof HostAiApiError ? e.message : "No se pudo cargar el artículo."));
    return () => { active = false; };
  }, [articuloId]);
  const back = typeof location.state?.from === "string" ? location.state.from : "/articulos";
  if (error) return <section className="panel"><Link to={back}>← Volver al catálogo</Link><ErrorState title="No se pudo cargar el artículo." detail={error} /></section>;
  if (!item) return <LoadingState label="Cargando artículo..." />;
  return <section className="panel catalog-detail" aria-labelledby="article-title">
    <Link to={back}>← Volver al catálogo</Link>
    <header><p className="eyebrow">{item.codigo}</p><h2 id="article-title">{item.nombre}</h2><p className="meta-line">{item.familia || "Sin familia"} · {item.estado}</p></header>
    <div className="dashboard-grid"><Card title="Precio" value={item.precio == null ? "No disponible" : `${item.precio.toFixed(2)} € / ${item.unidad || "unidad"}`} /><Card title="Stock" value={item.stock_detalle.cantidad == null ? "No disponible" : `${item.stock_detalle.cantidad} ${item.stock_detalle.unidad || ""}`} /><Card title="Proveedor" value={item.proveedor || "No disponible"} /></div>
    <Section title="Datos del artículo"><dl className="detail-grid"><dt>Marca</dt><dd>{item.marca || "No disponible"}</dd><dt>Referencia proveedor</dt><dd>{item.referencia_proveedor || "No disponible"}</dd><dt>Unidad de compra</dt><dd>{item.unidad_compra || "No disponible"}</dd><dt>Conservación</dt><dd>{item.conservacion || "No disponible"}</dd><dt>Alérgenos</dt><dd>{item.alergenos.length ? item.alergenos.join(", ") : "No disponibles"}</dd></dl></Section>
    <Section title="Proveedores y precios">{item.proveedores.length ? <ul>{item.proveedores.map((p, i) => <li key={`${p.nombre}-${i}`}>{p.nombre || "Proveedor"}{p.precio == null ? "" : ` · ${p.precio.toFixed(2)} €`}{p.preferente ? " · preferente" : ""}</li>)}</ul> : <p>No hay proveedores asociados.</p>}</Section>
    <Section title="Lotes">{item.stock_detalle.lotes.length ? <p>{item.stock_detalle.lotes.length} lotes registrados.</p> : <p>No hay lotes asociados.</p>}</Section>
    <Section title="Documentación y ficha técnica"><p>No hay documentación técnica asociada mediante un identificador verificable.</p></Section>
    <Section title="Recetas y escandallos"><p>No hay relaciones verificables con recetas o escandallos.</p></Section>
    <Section title="Historial">{item.historial.length ? <ul>{item.historial.map((h, i) => <li key={`${h.fecha}-${i}`}>{h.fecha || "Sin fecha"} · {h.descripcion}{h.precio == null ? "" : ` · ${h.precio.toFixed(2)} €`}</li>)}</ul> : <p>No hay historial disponible.</p>}</Section>
  </section>;
}
function Card({ title, value }: { title: string; value: string }) { return <article className="summary-card"><h3>{title}</h3><p>{value}</p></article>; }
function Section({ title, children }: React.PropsWithChildren<{ title: string }>) { return <section className="catalog-section"><h3>{title}</h3>{children}</section>; }
