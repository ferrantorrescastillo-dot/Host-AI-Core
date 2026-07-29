import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <section className="panel">
      <h2>Host AI Web</h2>
      <p>Interfaz operativa conectada a Host AI Platform API.</p>
      <div className="home-actions">
        <Link to="/dashboard" className="button-link">
          Ir a Dashboard
        </Link>
        <Link to="/chat" className="button-link button-link-secondary">
          Abrir Chat
        </Link>
      </div>
    </section>
  );
}
