import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { bibliotecaService } from "../../services/bibliotecaService";
import type { BibliotecaResponse } from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function BibliotecaPage() {
  const [data, setData] = useState<BibliotecaResponse | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { bibliotecaService.summary().then(setData).catch((e: Error) => setError(e.message)); }, []);
  if (error) return <section className="panel"><ErrorState title="No se pudo cargar la Biblioteca." detail={error} /></section>;
  if (!data) return <LoadingState label="Cargando Biblioteca..." />;
  const b = data.biblioteca;
  return <section className="panel" aria-labelledby="library-title">
    <p className="eyebrow">Conocimiento culinario reutilizable</p><h2 id="library-title">Biblioteca</h2>
    <p>Cada dato se introduce una sola vez y se reutiliza en todo el sistema.</p>
    <BibliotecaNav />
    <div className="dashboard-grid">
      <Metric label="Elaboraciones" value={b.total_elaboraciones} />
      <Metric label="Sin receta" value={b.sin_receta} />
      <Metric label="Sin escandallo" value={b.sin_escandallo} />
      <Metric label="Sin ficha técnica" value={b.sin_ficha_tecnica} />
    </div>
    {b.total_elaboraciones ? <Link className="button-link" to="/biblioteca/elaboraciones">Explorar elaboraciones</Link> : <div className="panel-state"><p>No hay elaboraciones registradas todavía.</p></div>}
  </section>;
}
function Metric({ label, value }: { label: string; value: number }) { return <article className="summary-card"><h3>{label}</h3><p>{value}</p></article>; }
