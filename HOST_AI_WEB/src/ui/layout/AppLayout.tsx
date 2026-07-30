import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";

const LINKS = [
  { to: "/", label: "Inicio" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/chat", label: "Chat" },
  { to: "/eventos", label: "Eventos" },
  { to: "/produccion", label: "Produccion" },
  { to: "/compras", label: "Compras" },
  { to: "/stock", label: "Stock" },
  { to: "/articulos", label: "Articulos" },
  { to: "/executive", label: "Executive" },
  { to: "/configuracion", label: "Configuracion" },
];

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="app-shell" data-testid="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Host AI Web</p>
          <h1>Operacion diaria</h1>
        </div>
        <span className="badge-safe">Modo seguro activo</span>
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="Navegacion lateral">
          <nav>
            {LINKS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `nav-link${isActive ? " nav-link-active" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="content" aria-live="polite">
          {children}
        </main>
      </div>
    </div>
  );
}
