import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="panel" role="alert">
      <h2>Pagina no encontrada</h2>
      <p>La ruta solicitada no esta disponible en esta version.</p>
      <Link to="/" className="button-link">
        Volver al inicio
      </Link>
    </section>
  );
}
