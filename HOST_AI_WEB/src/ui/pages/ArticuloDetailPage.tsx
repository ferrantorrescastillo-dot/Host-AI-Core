import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import type { ArticuloDetalle, ArticuloUpdateInput } from "../../types/articulos";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ArticuloDetailPage() {
  const { articuloId = "" } = useParams();
  const location = useLocation();
  const [item, setItem] = useState<ArticuloDetalle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
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
    <header><p className="eyebrow">{item.codigo}</p><h2 id="article-title">{item.nombre}</h2><p className="meta-line">{item.familia || "Sin familia"} · {item.estado}</p><button type="button" onClick={() => setEditing((value) => !value)}>{editing ? "Cancelar edición" : "Editar artículo"}</button></header>
    {editing ? <ArticleEditForm item={item} onSaved={(updated) => { setItem(updated); setEditing(false); }} /> : null}
    <div className="dashboard-grid"><Card title="Precio" value={item.precio == null ? "No disponible" : `${item.precio.toFixed(2)} € · ${item.unidad_base || "unidad pendiente"}`} /><Card title="Unidad base" value={item.unidad_base || "Pendiente"} /><Card title="Stock" value={item.stock_detalle.cantidad == null ? "No disponible" : `${item.stock_detalle.cantidad} ${item.stock_detalle.unidad || ""}`} /><Card title="Proveedor" value={item.proveedor || "Pendiente"} /></div>
    <Section title="Estado operativo"><dl className="detail-grid"><dt>Operativo para Stock</dt><dd>{item.operatividad.stock ? "Sí" : "No"}</dd><dt>Operativo para Compras</dt><dd>{item.operatividad.compras ? "Sí" : "No"}</dd><dt>Operativo para Escandallos</dt><dd>{item.operatividad.escandallos ? "Sí" : "No"}</dd></dl></Section>
    <Section title="Datos generales"><dl className="detail-grid"><dt>Marca</dt><dd>{item.marca || "No disponible"}</dd><dt>Referencia proveedor</dt><dd>{item.referencia_proveedor || "No disponible"}</dd><dt>Conservación</dt><dd>{item.conservacion || "No disponible"}</dd><dt>Alérgenos</dt><dd>{item.alergenos.length ? item.alergenos.join(", ") : "No disponibles"}</dd><dt>Observaciones</dt><dd>{item.observaciones || "No disponibles"}</dd></dl></Section>
    <Section title="Unidades y formatos"><dl className="detail-grid"><dt>Unidad base</dt><dd>{item.unidad_base || "Pendiente"}</dd><dt>Unidad de compra</dt><dd>{item.unidad_compra || "Pendiente"}</dd><dt>Cantidad por formato</dt><dd>{item.cantidad_formato == null ? "Pendiente" : `${item.cantidad_formato} ${item.unidad_base || ""}`}</dd></dl></Section>
    <Section title="Proveedores y precios">{item.proveedores.length ? <ul>{item.proveedores.map((p, i) => <li key={`${p.nombre}-${i}`}>{p.nombre || "Proveedor"}{p.precio == null ? "" : ` · ${p.precio.toFixed(2)} €`}{p.preferente ? " · preferente" : ""}</li>)}</ul> : <p>No hay proveedores asociados.</p>}</Section>
    <Section title="Lotes">{item.stock_detalle.lotes.length ? <p>{item.stock_detalle.lotes.length} lotes registrados.</p> : <p>No hay lotes asociados.</p>}</Section>
    <Section title="Conversiones"><p>{item.conversion_unidades || "No hay conversiones verificadas."}</p></Section>
    <Section title="Documentación y ficha técnica"><p>No hay documentación técnica asociada mediante un identificador verificable.</p></Section>
    <Section title="Recetas y escandallos"><p>No hay relaciones verificables con recetas o escandallos.</p></Section>
    <Section title="Historial">{item.historial.length ? <ul>{item.historial.map((h, i) => <li key={`${h.fecha}-${i}`}>{h.fecha || "Sin fecha"} · {h.descripcion}{h.precio == null ? "" : ` · ${h.precio.toFixed(2)} €`}</li>)}</ul> : <p>No hay historial disponible.</p>}</Section>
  </section>;
}

function ArticleEditForm({ item, onSaved }: { item: ArticuloDetalle; onSaved: (item: ArticuloDetalle) => void }) {
  const [form, setForm] = useState<ArticuloUpdateInput>({ nombre: item.nombre, familia: item.familia || "", unidad_base: item.unidad_base || "", unidad_compra: item.unidad_compra || "", cantidad_formato: item.cantidad_formato, proveedor_preferente: item.proveedor || "", precio: item.precio, referencia_proveedor: item.referencia_proveedor || "", marca: item.marca || "", conservacion: item.conservacion || "", alergenos: item.alergenos, observaciones: item.observaciones || "" });
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const set = (key: keyof ArticuloUpdateInput, value: string | number | string[] | null) => setForm((current) => ({ ...current, [key]: value }));
  const save = async () => { setBusy(true); setError(""); try { const response = await articulosService.update(item.id, form); onSaved(response.articulo); } catch (reason) { setError((reason as Error).message); } finally { setBusy(false); } };
  return <section className="catalog-section" aria-label="Editar artículo maestro"><h3>Editar artículo</h3>
    <label>Nombre<input aria-label="Nombre" value={form.nombre} onChange={(e) => set("nombre", e.target.value)} /></label><label>Familia<input aria-label="Familia" value={form.familia || ""} onChange={(e) => set("familia", e.target.value)} /></label>
    <label>Unidad base<select aria-label="Unidad base" value={form.unidad_base} onChange={(e) => set("unidad_base", e.target.value)}><option value="">Selecciona unidad</option>{item.edicion.unidades_base.map((unit) => <option key={unit}>{unit}</option>)}</select></label><label>Unidad de compra<input aria-label="Unidad de compra" value={form.unidad_compra || ""} onChange={(e) => set("unidad_compra", e.target.value)} /></label><label>Cantidad por formato<input aria-label="Cantidad por formato" type="number" min="0" step="any" value={form.cantidad_formato ?? ""} onChange={(e) => set("cantidad_formato", e.target.value ? Number(e.target.value) : null)} /></label>
    <label>Proveedor preferente<select aria-label="Proveedor preferente" value={form.proveedor_preferente || ""} onChange={(e) => set("proveedor_preferente", e.target.value)}><option value="">Sin proveedor</option>{item.edicion.proveedores.map((provider) => <option key={provider.id || provider.nombre}>{provider.nombre}</option>)}</select></label><label>Precio vigente<input aria-label="Precio vigente" type="number" min="0" step="any" value={form.precio ?? ""} onChange={(e) => set("precio", e.target.value ? Number(e.target.value) : null)} /></label>
    <label>Referencia proveedor<input aria-label="Referencia proveedor" value={form.referencia_proveedor || ""} onChange={(e) => set("referencia_proveedor", e.target.value)} /></label><label>Marca<input aria-label="Marca" value={form.marca || ""} onChange={(e) => set("marca", e.target.value)} /></label><label>Conservación<input aria-label="Conservación" value={form.conservacion || ""} onChange={(e) => set("conservacion", e.target.value)} /></label><label>Alérgenos<input aria-label="Alérgenos" value={(form.alergenos || []).join(", ")} onChange={(e) => set("alergenos", e.target.value.split(",").map((value) => value.trim()).filter(Boolean))} /></label><label>Observaciones<textarea aria-label="Observaciones" value={form.observaciones || ""} onChange={(e) => set("observaciones", e.target.value)} /></label>
    <button type="button" disabled={busy || !form.nombre || !form.unidad_base} onClick={() => void save()}>{busy ? "Guardando..." : "Guardar artículo"}</button>{error ? <p role="alert">{error}</p> : null}
  </section>;
}
function Card({ title, value }: { title: string; value: string }) { return <article className="summary-card"><h3>{title}</h3><p>{value}</p></article>; }
function Section({ title, children }: React.PropsWithChildren<{ title: string }>) { return <section className="catalog-section"><h3>{title}</h3>{children}</section>; }
