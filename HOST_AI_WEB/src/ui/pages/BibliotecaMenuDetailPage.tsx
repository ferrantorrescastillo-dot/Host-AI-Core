import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { menusService } from "../../services/menusService";
import type { IntelligentMenu, MenuElaboration } from "../../types/menus";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function BibliotecaMenuDetailPage() {
  const { menuId = "" } = useParams();
  const [menu, setMenu] = useState<IntelligentMenu | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { menusService.get(menuId).then((response) => setMenu(response.menu)).catch((reason: Error) => setError(reason.message)); }, [menuId]);
  if (error) return <section className="panel"><BibliotecaNav /><ErrorState title="No se pudo cargar el menú." detail={error} /></section>;
  if (!menu) return <LoadingState label="Cargando menú canónico..." />;
  return <section className="panel library-detail">
    <BibliotecaNav /><Link to="/biblioteca/menus">← Volver a Menús</Link>
    <header className="recipe-hero"><div><p className="eyebrow">{menu.id}</p><h2>{menu.nombre}</h2></div><dl className="recipe-kpis"><div><dt>Estado</dt><dd>{menu.estado}</dd></div><div><dt>Procedencia</dt><dd>{menu.origen || "No informada"}</dd></div><div><dt>Entidad</dt><dd>{menu.modelo_biblioteca || "MENU_601"}</dd></div></dl></header>
    <section className="catalog-section"><h3>Líneas del menú</h3>{menu.secciones.map((section) => <section key={section.id}><h4>{section.nombre}</h4><ul>{section.elaboraciones.map((line, index) => <li key={`${line.referencia_canonica || line.elaboracion_id}-${index}`}><strong>{line.elaboracion_nombre}</strong> · {line.tipo_referencia || "RECETA"} · <CanonicalReference line={line} /></li>)}</ul></section>)}</section>
  </section>;
}

function CanonicalReference({ line }: { line: MenuElaboration }) {
  const id = line.referencia_canonica || line.elaboracion_id;
  if (line.tipo_referencia === "PRODUCTO" || id.startsWith("ART")) return <Link to={`/articulos/${encodeURIComponent(id)}`}>{id}</Link>;
  return <Link to={`/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=receta`}>{id}</Link>;
}
