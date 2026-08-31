import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { isCanonicalReservaId, reservasService } from "../../services/reservasService";
import type { ReservaAlcance, ReservaEstado, ReservaServicio, ReservaResumen, ReservasFilters, ReservasResponse } from "../../types/reservas";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReservaWritePanel } from "../components/ReservaWritePanel";
import { SearchField } from "../components/SearchField";

const ESTADOS: ReservaEstado[] = ["PENDIENTE", "CONFIRMADA", "CANCELADA", "NO_SHOW", "COMPLETADA"];
const SERVICIOS: ReservaServicio[] = ["COMIDA", "CENA"];

export function ReservasPage() {
  const [filters, setFilters] = useState<ReservasFilters>({ alcance: "todas", limite: 50 });
  const [draft, setDraft] = useState<ReservasFilters>(filters);
  const [data, setData] = useState<ReservasResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true); setError(null); setErrorRequestId("");
    reservasService.list(filters).then((response) => { if (active) setData(response); }).catch((reason: unknown) => {
      if (!active) return;
      setData(null);
      if (reason instanceof HostAiApiError) { setError(reason.message); setErrorRequestId(reason.requestId || ""); }
      else setError("No se pudieron cargar las reservas.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filters]);

  function setAlcance(alcance: ReservaAlcance) {
    setDraft((current) => ({ ...current, alcance, fecha: alcance === "todas" ? current.fecha : "" }));
    setFilters((current) => ({ ...current, alcance, fecha: alcance === "todas" ? current.fecha : "" }));
  }

  function submit(event: FormEvent) { event.preventDefault(); setFilters({ ...draft, limite: 50 }); }
  if (loading) return <LoadingState label="Cargando reservas..." />;

  return <section className="panel reservas-page" aria-labelledby="reservas-title">
    <header className="dashboard-header"><div><p className="eyebrow">Operativa</p><h2 id="reservas-title">Reservas</h2><p className="meta-line">Gestión segura con confirmación previa</p></div><ReservaWritePanel operation="CREAR" label="Nueva reserva" onConfirmed={() => setFilters((current) => ({ ...current }))} /></header>
    {error ? <><ErrorState title="No se pudieron cargar las reservas." detail={error} /><p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p></> : <>
      <p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p>
      <form className="reservas-filters" aria-label="Filtros de reservas" onSubmit={submit}>
        <fieldset><legend>Alcance</legend>{(["todas", "hoy", "proximas"] as ReservaAlcance[]).map((scope) => <button key={scope} type="button" aria-pressed={filters.alcance === scope} onClick={() => setAlcance(scope)}>{scope === "proximas" ? "Próximas" : scope.charAt(0).toUpperCase() + scope.slice(1)}</button>)}</fieldset>
        <SearchField value={draft.q || ""} onChange={(value) => setDraft({ ...draft, q: value })} onClear={() => setFilters({ ...draft, q: "", limite: 50 })} placeholder="Cliente o referencia..." ariaLabel="Buscar por nombre" />
        <label>Fecha<input aria-label="Fecha" type="date" disabled={draft.alcance !== "todas"} value={draft.fecha || ""} onChange={(e) => setDraft({ ...draft, fecha: e.target.value })} /></label>
        <label>Estado<select aria-label="Estado" value={draft.estado || ""} onChange={(e) => setDraft({ ...draft, estado: e.target.value as ReservaEstado | "" })}><option value="">Todos</option>{ESTADOS.map((value) => <option key={value} value={value}>{readable(value)}</option>)}</select></label>
        <label>Servicio<select aria-label="Servicio" value={draft.servicio || ""} onChange={(e) => setDraft({ ...draft, servicio: e.target.value as ReservaServicio | "" })}><option value="">Todos</option>{SERVICIOS.map((value) => <option key={value} value={value}>{readable(value)}</option>)}</select></label>
        <button type="submit">Aplicar filtros</button>
      </form>
      {data?.reservas.items.length ? <div className="reservas-list" aria-label="Listado de reservas">{data.reservas.items.map((item) => <ReservaCard key={item.reserva_id} reserva={item} />)}</div> : <div className="panel-state"><p>No hay reservas registradas.</p></div>}
    </>}
  </section>;
}

function ReservaCard({ reserva }: { reserva: ReservaResumen }) {
  return <article className="reserva-card"><header><h3>{reserva.nombre_cliente}</h3><span className="evento-status">{readable(reserva.estado)}</span></header><dl className="evento-details"><div><dt>Fecha</dt><dd>{formatDate(reserva.fecha)}</dd></div><div><dt>Hora</dt><dd>{reserva.hora}</dd></div><div><dt>PAX</dt><dd>{reserva.pax}</dd></div><div><dt>Servicio</dt><dd>{readable(reserva.servicio)}</dd></div></dl>{isCanonicalReservaId(reserva.reserva_id) ? <div className="menu-actions"><Link to={`/reservas/${reserva.reserva_id}`}>Abrir</Link><Link to={`/reservas/${reserva.reserva_id}?edit=1`}>Editar</Link><Link to={`/reservas/${reserva.reserva_id}?delete=1`}>Eliminar</Link></div> : <p className="meta-line">Identificador no válido</p>}</article>;
}

function readable(value: string) { const text = value.replaceAll("_", " ").toLowerCase(); return text.charAt(0).toUpperCase() + text.slice(1); }
function formatDate(value: string) { const date = new Date(`${value}T00:00:00Z`); return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeZone: "UTC" }).format(date); }
