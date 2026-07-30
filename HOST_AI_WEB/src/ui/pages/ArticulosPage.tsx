import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import type { CatalogoResponse } from "../../types/articulos";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ArticulosPage() {
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get("q") || "");
  const [data, setData] = useState<CatalogoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const page = Number(params.get("page") || 1);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const next = new URLSearchParams(params);
      if (search) next.set("q", search); else next.delete("q");
      if (search !== (params.get("q") || "")) next.set("page", "1");
      setParams(next, { replace: true });
    }, 300);
    return () => window.clearTimeout(timer);
  }, [search, params, setParams]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    articulosService.list({
      q: params.get("q") || undefined,
      familia: params.get("familia") || undefined,
      proveedor: params.get("proveedor") || undefined,
      estado: params.get("estado") || undefined,
      con_stock: params.has("con_stock") ? params.get("con_stock") === "true" : undefined,
      orden: (params.get("orden") as "nombre") || "nombre",
      direccion: (params.get("direccion") as "asc") || "asc",
      page,
      page_size: 20,
    }).then((result) => active && setData(result)).catch((reason: unknown) => {
      if (active) setError(reason instanceof HostAiApiError ? reason.message : "No se pudo cargar el catálogo.");
    }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [params, page]);

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    next.set("page", "1");
    setParams(next);
  };

  return (
    <section className="panel catalog-page" aria-labelledby="catalog-title">
      <header className="dashboard-header"><div><p className="eyebrow">Catálogo maestro</p><h2 id="catalog-title">Artículos</h2><p className="meta-line">Consulta de artículos, stock y proveedores reales</p></div></header>
      <div className="catalog-filters">
        <label>Buscar<input aria-label="Buscar artículos" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Nombre, código, familia o proveedor" /></label>
        <Select label="Familia" value={params.get("familia") || ""} values={data?.catalogo.filtros.familias || []} onChange={(v) => update("familia", v)} />
        <Select label="Proveedor" value={params.get("proveedor") || ""} values={data?.catalogo.filtros.proveedores || []} onChange={(v) => update("proveedor", v)} />
        <Select label="Estado" value={params.get("estado") || ""} values={data?.catalogo.filtros.estados || []} onChange={(v) => update("estado", v)} />
        <label>Stock<select value={params.get("con_stock") || ""} onChange={(e) => update("con_stock", e.target.value)}><option value="">Todos</option><option value="true">Con stock</option><option value="false">Sin stock</option></select></label>
        <label>Orden<select value={params.get("orden") || "nombre"} onChange={(e) => update("orden", e.target.value)}><option value="nombre">Nombre</option><option value="codigo">Código</option><option value="precio">Precio</option><option value="stock">Stock</option><option value="actualizacion">Actualización</option></select></label>
      </div>
      {loading ? <LoadingState label="Cargando artículos..." /> : error ? <ErrorState title="No se pudo cargar el catálogo." detail={error} /> : !data?.catalogo.items.length ? <div className="panel-state"><p>No hay artículos para los filtros seleccionados.</p></div> : (
        <>
          <p className="meta-line">{data.catalogo.total} artículos encontrados</p>
          <div className="catalog-table-wrap"><table className="catalog-table"><thead><tr><th>Código</th><th>Artículo</th><th>Familia</th><th>Proveedor</th><th>Precio</th><th>Stock</th><th>Estado</th></tr></thead><tbody>{data.catalogo.items.map((item) => <tr key={item.id}><td>{item.codigo}</td><td><Link to={`/articulos/${encodeURIComponent(item.id)}`} state={{ from: `${location.pathname}${location.search}` }}>{item.nombre}</Link></td><td>{item.familia || "—"}</td><td>{item.proveedor || "—"}</td><td>{item.precio == null ? "—" : `${item.precio.toFixed(2)} €`}</td><td>{item.stock == null ? "—" : `${item.stock} ${item.unidad_stock || ""}`}</td><td>{item.estado}</td></tr>)}</tbody></table></div>
          <nav className="catalog-pagination" aria-label="Paginación"><button disabled={page <= 1} onClick={() => update("page", String(page - 1))}>Anterior</button><span>Página {page} de {data.catalogo.total_pages || 1}</span><button disabled={page >= data.catalogo.total_pages} onClick={() => update("page", String(page + 1))}>Siguiente</button></nav>
        </>
      )}
    </section>
  );
}

function Select({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (v: string) => void }) {
  return <label>{label}<select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)}><option value="">Todos</option>{values.map((item) => <option key={item}>{item}</option>)}</select></label>;
}
