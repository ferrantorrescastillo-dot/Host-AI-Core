import { NavLink, useLocation } from "react-router-dom";
import type { PropsWithChildren } from "react";

const LINKS = [
  { to: "/", label: "Inicio" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/chat", label: "Chat" },
  { to: "/eventos", label: "Eventos" },
  { to: "/reservas", label: "Reservas" },
  { to: "/produccion", label: "Produccion" },
  { to: "/compras", label: "Compras" },
  { to: "/stock", label: "Stock" },
  { to: "/articulos", label: "Articulos" },
  { to: "/biblioteca", label: "Biblioteca" },
  { to: "/menus", label: "Menus" },
  { to: "/executive", label: "Executive" },
  { to: "/configuracion", label: "Configuracion" },
];

export function AppLayout({ children }: PropsWithChildren) {
  const location = useLocation();
  const immersiveChat = location.pathname === "/chat";
  return (
    <div className="app-shell" data-testid="app-shell">
      {!immersiveChat ? <header className="topbar">
        <div className="topbar-context">
          <p className="eyebrow">Espacio operativo</p>
          <h1>Host AI</h1>
        </div>
        <span className="badge-safe"><span aria-hidden="true">●</span> Modo seguro</span>
      </header> : null}

      <div className="workspace">
        <aside className="sidebar" aria-label="Navegacion lateral">
          <div className="sidebar-brand" aria-label="Host AI">
            <span className="sidebar-brand-mark" aria-hidden="true">H</span>
            <span><strong>Host AI</strong><small>Operaciones</small></span>
          </div>
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
