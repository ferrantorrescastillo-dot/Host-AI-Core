import { NavLink } from "react-router-dom";

const links = [
  ["/biblioteca", "Resumen"],
  ["/biblioteca/elaboraciones", "Elaboraciones"],
  ["/biblioteca/recetas", "Recetas"],
  ["/biblioteca/escandallos", "Escandallos"],
  ["/biblioteca/fichas-tecnicas", "Fichas técnicas"],
  ["/biblioteca/menus", "Menús"],
  ["/biblioteca/documentacion", "Documentación"],
  ["/biblioteca/importaciones", "Importaciones"],
];

export function BibliotecaNav() {
  return <nav className="library-nav" aria-label="Secciones de Biblioteca">
    {links.map(([to, label]) => <NavLink key={to} to={to} end={to === "/biblioteca"}>{label}</NavLink>)}
  </nav>;
}
