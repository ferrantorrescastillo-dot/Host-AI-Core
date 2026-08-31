import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { menusService } from "../../services/menusService";
import type { IntelligentMenu } from "../../types/menus";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function BibliotecaMenusPage() {
  const [menus, setMenus] = useState<IntelligentMenu[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { menusService.list().then((response) => setMenus(response.menus)).catch((reason: Error) => setError(reason.message)); }, []);
  return <section className="panel">
    <header className="dashboard-header"><div><p className="eyebrow">Biblioteca Culinaria</p><h2>Menús</h2></div></header>
    <BibliotecaNav />
    <nav className="library-tabs" aria-label="Recetas y menús"><Link to="/biblioteca/recetas">Recetas</Link><Link aria-current="page" className="active" to="/biblioteca/menus">Menús</Link></nav>
    <p>Menús canónicos existentes. Esta vista es de solo lectura.</p>
    {error ? <ErrorState title="No se pudieron cargar los menús." detail={error} /> : !menus ? <LoadingState label="Cargando menús canónicos..." /> : !menus.length ? <p>No hay menús canónicos.</p> : <div className="catalog-table-wrap"><table className="catalog-table"><thead><tr><th>Menú</th><th>Líneas</th><th>Estado</th><th>Procedencia</th><th></th></tr></thead><tbody>{menus.map((menu) => <tr key={menu.id}><td><strong>{menu.nombre}</strong><small>{menu.id}</small></td><td>{menu.secciones.reduce((total, section) => total + section.elaboraciones.length, 0)}</td><td>{menu.estado}</td><td>{menu.origen || "No informada"}</td><td><Link to={`/biblioteca/menus/${encodeURIComponent(menu.id)}`}>Ver menú</Link></td></tr>)}</tbody></table></div>}
  </section>;
}
