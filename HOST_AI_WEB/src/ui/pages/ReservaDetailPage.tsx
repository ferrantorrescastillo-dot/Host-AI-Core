import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { isCanonicalReservaId, reservasService } from "../../services/reservasService";
import type { ReservaResponse } from "../../types/reservas";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReservaWritePanel } from "../components/ReservaWritePanel";

export function ReservaDetailPage() {
  const { reservaId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState<ReservaResponse | null>(null);
  const [loading, setLoading] = useState(isCanonicalReservaId(reservaId));
  const [error, setError] = useState(isCanonicalReservaId(reservaId) ? "" : "Identificador de reserva no válido.");
  const [requestId, setRequestId] = useState("");
  useEffect(() => {
    if (!isCanonicalReservaId(reservaId)) return;
    let active = true;
    reservasService.detail(reservaId).then((result) => { if (active) setData(result); }).catch((reason: unknown) => {
      if (!active) return;
      setError(reason instanceof HostAiApiError ? reason.message : "No se pudo cargar la reserva.");
      if (reason instanceof HostAiApiError) setRequestId(reason.requestId || "");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reservaId]);
  if (loading) return <LoadingState label="Cargando detalle de reserva..." />;
  if (error || !data) return <section className="panel"><ErrorState title="Reserva no disponible." detail={error || "Reserva no encontrada."} /><p className="meta-line">Request ID: {requestId || "No disponible"}</p><Link to="/reservas">Volver a Reservas</Link></section>;
  const item = data.reserva;
  const refresh = (reserva: typeof item) => setData({ ...data, reserva });
  const query = new URLSearchParams(location.search);
  return <section className="panel reserva-detail" aria-labelledby="reserva-detail-title"><p><Link to="/reservas">Volver a Reservas</Link></p><header><p className="eyebrow">Reserva</p><h2 id="reserva-detail-title">{item.nombre_cliente}</h2><p className="meta-line">ID: {item.reserva_id} · Request ID: {data.request_id || "No disponible"}</p></header><dl className="detail-grid"><dt>Fecha</dt><dd>{item.fecha}</dd><dt>Hora</dt><dd>{item.hora}</dd><dt>PAX</dt><dd>{item.pax}</dd><dt>Estado</dt><dd>{item.estado}</dd><dt>Servicio</dt><dd>{item.servicio}</dd>{item.evento_id ? <><dt>Evento asociado</dt><dd>{item.evento_id}</dd></> : null}<dt>Observaciones</dt><dd>{item.observaciones || "Sin observaciones."}</dd><dt>Origen</dt><dd>{item.origen || "No disponible"}</dd><dt>Creada</dt><dd>{item.creado_en || "No disponible"}</dd><dt>Última actualización</dt><dd>{item.actualizado_en || "No disponible"}</dd></dl><div className="reserva-actions"><ReservaWritePanel operation="MODIFICAR" reservaId={item.reserva_id} initial={item} label="Editar" defaultOpen={query.get("edit") === "1"} onConfirmed={refresh} /><ReservaWritePanel operation="ELIMINAR" reservaId={item.reserva_id} initial={item} label="Eliminar" defaultOpen={query.get("delete") === "1"} onConfirmed={() => navigate("/reservas")} />{item.estado === "PENDIENTE" ? <ReservaWritePanel operation="CONFIRMAR" reservaId={item.reserva_id} initial={item} label="Confirmar reserva" onConfirmed={refresh} /> : null}{["PENDIENTE", "CONFIRMADA"].includes(item.estado) ? <ReservaWritePanel operation="CANCELAR" reservaId={item.reserva_id} initial={item} label="Cancelar reserva" onConfirmed={refresh} /> : null}{item.estado === "CONFIRMADA" ? <ReservaWritePanel operation="NO_SHOW" reservaId={item.reserva_id} initial={item} label="Marcar no-show" onConfirmed={refresh} /> : null}{item.estado === "CONFIRMADA" ? <ReservaWritePanel operation="COMPLETAR" reservaId={item.reserva_id} initial={item} label="Completar" onConfirmed={refresh} /> : null}</div></section>;
}
