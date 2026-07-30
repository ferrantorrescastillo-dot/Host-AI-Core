import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { bibliotecaService } from "../../services/bibliotecaService";
import type { ElaboracionesResponse } from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ElaboracionesPage({ preset }: { preset?: "receta" | "escandallo" | "ficha" }) {
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get("q") || "");
  const [data, setData] = useState<ElaboracionesResponse | null>(null);
  const [error, setError] = useState("");
  const page = Number(params.get("page") || 1);
  useEffect(() => {
    const timer = setTimeout(() => {
      const next = new URLSearchParams(params);
      search ? next.set("q", search) : next.delete("q");
      setParams(next, { replace: true });
    }, 300);
    return () => clearTimeout(timer);
  }, [search, params, setParams]);
  useEffect(() => {
    setError("");
    bibliotecaService.list({
      q: params.get("q") || undefined, page, page_size: 20,
      estado: params.get("estado") || undefined, categoria: params.get("categoria") || undefined,
      tiene_receta: preset === "receta" ? true : undefined,
      tiene_escandallo: preset === "escandallo" ? true : undefined,
      tiene_ficha_tecnica: preset === "ficha" ? true : undefined,
      orden: "nombre", direccion: "asc",
    }).then(setData).catch((e: Error) => setError(e.message));
  }, [params, page, preset]);
  const title = preset === "receta" ? "Recetas" : preset === "escandallo" ? "Escandallos" : preset === "ficha" ? "Fichas técnicas" : "Elaboraciones";
  const detailTab = preset === "receta" ? "?tab=receta" : preset === "escandallo" ? "?tab=escandallo" : preset === "ficha" ? "?tab=ficha-tecnica" : "";
  const update = (key: string, value: string) => { const next = new URLSearchParams(params); value ? next.set(key, value) : next.delete(key); next.set("page", "1"); setParams(next); };
  return <section className="panel" aria-labelledby="elaborations-title">
    <p className="eyebrow">Biblioteca Culinaria</p><h2 id="elaborations-title">{title}</h2><BibliotecaNav />
    <div className="catalog-filters">
      <label>Buscar<input aria-label="Buscar elaboraciones" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Nombre, código, categoría o ingrediente" /></label>
      <label>Estado<select value={params.get("estado") || ""} onChange={(e) => update("estado", e.target.value)}><option value="">Todos</option>{data?.elaboraciones.filters.estados.map((x) => <option key={x} value={x}>{statusLabel(x)}</option>)}</select></label>
      <label>Categoría<select value={params.get("categoria") || ""} onChange={(e) => update("categoria", e.target.value)}><option value="">Todas</option>{data?.elaboraciones.filters.categorias.map((x) => <option key={x}>{x}</option>)}</select></label>
    </div>
    {error ? <ErrorState title={`No se pudo cargar ${title}.`} detail={error} /> : !data ? <LoadingState label={`Cargando ${title.toLowerCase()}...`} /> : !data.elaboraciones.items.length ? <div className="panel-state"><p>No hay {title.toLowerCase()} para los filtros seleccionados.</p></div> : <>
      <div className="catalog-table-wrap"><table className="catalog-table"><thead><tr><th>Elaboración</th><th>Categoría</th><th>Rendimiento</th><th>Receta</th><th>Escandallo</th><th>Ficha técnica</th><th>Coste/ración</th><th>Estado</th></tr></thead><tbody>{data.elaboraciones.items.map((x) => <tr key={x.id}><td><Link to={`/biblioteca/elaboraciones/${encodeURIComponent(x.id)}${detailTab}`}>{x.nombre}</Link><small>{x.codigo}{x.actualizado_en ? ` · Actualizada ${formatDate(x.actualizado_en)}` : ""}</small></td><td>{x.categoria || "Sin categoría"}</td><td>{x.rendimiento == null ? "Rendimiento no disponible" : `${x.rendimiento} ${x.unidad_rendimiento || ""}`.trim()}</td><td>{yes(x.tiene_receta)}</td><td>{yes(x.tiene_escandallo)}</td><td>{yes(x.tiene_ficha_tecnica)}</td><td>{x.coste_por_racion == null ? "Coste no disponible" : `${x.coste_por_racion.toFixed(2)} €`}</td><td>{statusLabel(x.estado)}</td></tr>)}</tbody></table></div>
      <nav className="catalog-pagination"><button disabled={page <= 1} onClick={() => update("page", String(page - 1))}>Anterior</button><span>Página {page} de {data.elaboraciones.total_pages || 1}</span><button disabled={page >= data.elaboraciones.total_pages} onClick={() => update("page", String(page + 1))}>Siguiente</button></nav>
    </>}
  </section>;
}
function yes(value: boolean) { return value ? "Disponible" : "Pendiente"; }
function statusLabel(value: string) {
  const labels: Record<string, string> = {
    PENDIENTE_DE_COMPLETAR: "Pendiente de completar",
    COMPLETO: "Completo", BORRADOR: "Borrador", ACTIVO: "Activo",
    INACTIVO: "Inactivo", DESACTUALIZADO: "Desactualizado",
    OPERATIVA: "Operativa", ARCHIVADA: "Archivada",
  };
  return labels[value] || value.replaceAll("_", " ").toLowerCase().replace(/^./, (x) => x.toUpperCase());
}
function formatDate(value: string) { return new Intl.DateTimeFormat("es-ES").format(new Date(value)); }
