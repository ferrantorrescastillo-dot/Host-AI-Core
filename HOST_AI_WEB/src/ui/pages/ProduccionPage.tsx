import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { produccionService, type ProduccionResult } from "../../services/produccionService";
import type { ProductionPlan, ProductionTask, ProductionTree } from "../../types/produccion";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ProduccionPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<ProduccionResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true); setError(null); setErrorRequestId(null);
    produccionService.load().then((result) => { if (active) setData(result); }).catch((err: unknown) => {
      if (!active) return;
      setData(null);
      if (err instanceof HostAiApiError) { setError(err.message); setErrorRequestId(err.requestId || null); }
      else setError("No se pudo cargar la producción.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refreshTick]);

  if (loading) return <LoadingState label="Cargando producción..." />;
  return <section className="panel" role="region" aria-labelledby="produccion-title">
    <header className="dashboard-header"><div><p className="eyebrow">Operativa</p><h2 id="produccion-title">Plan de producción</h2><p className="meta-line">Planificación desde Menús, sin movimientos de Stock</p></div><button type="button" onClick={() => setRefreshTick((value) => value + 1)}>{error ? "Reintentar" : "Actualizar"}</button></header>
    {error ? <><ErrorState title="No se pudo cargar la producción." detail={error} /><p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p></> : <>
      <section className="safe-mode" aria-label="Estado de seguridad"><p><strong>Modo seguro:</strong> {data?.modo_seguro ? "Activo" : "Inactivo"}</p><p><strong>Datos reales modificados:</strong> {data?.datos_reales_modificados ? "Sí" : "No"}</p><p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p></section>
      <section className="dashboard-grid" aria-label="Resumen de producción"><SummaryCard title="Elaboraciones" value={sum(data?.detalles, "elaboraciones")} /><SummaryCard title="Subelaboraciones" value={sum(data?.detalles, "subelaboraciones")} /><SummaryCard title="Ingredientes necesarios" value={sum(data?.detalles, "ingredientes")} /><SummaryCard title="Faltantes" value={sum(data?.detalles, "faltantes")} /><SummaryCard title="Coste previsto" value={`${sum(data?.detalles, "coste_previsto").toLocaleString("es-ES", { minimumFractionDigits: 2 })} €`} /></section>
      {data?.detalles.length ? <div className="produccion-list" aria-label="Planes de producción">{data.detalles.map((plan) => <PlanCard key={plan.id} plan={plan} />)}</div> : <div className="panel-state"><p>No hay planes de producción activos.</p>{data?.mensaje ? <p className="meta-line">{data.mensaje}</p> : null}</div>}
    </>}
  </section>;
}

function PlanCard({ plan }: { plan: ProductionPlan }) {
  const [proposalId, setProposalId] = useState(plan.propuesta_compra_id || "");
  const [proposalLines, setProposalLines] = useState(0);
  const [proposalBusy, setProposalBusy] = useState(false);
  const [proposalError, setProposalError] = useState("");
  const createProposal = async () => {
    setProposalBusy(true); setProposalError("");
    try { const response = await produccionService.createPurchaseProposal(plan.id); setProposalId(response.propuesta.id); setProposalLines(response.propuesta.lineas.length); }
    catch (error) { setProposalError((error as Error).message); }
    finally { setProposalBusy(false); }
  };
  return <article className="produccion-card"><header><div><h3>{plan.nombre || "Plan sin nombre"}</h3><p className="meta-line">Menú {plan.menu_id || "sin identificar"} · versión {plan.menu_version || "-"}</p></div><span className="evento-status">{plan.estado}</span></header>
    <dl className="produccion-details"><Detail label="Fecha" value={formatDate(plan.fecha)} /><Detail label="Comensales" value={formatNumber(plan.comensales)} /><Detail label="Elaboraciones" value={formatNumber(plan.resumen.elaboraciones)} /><Detail label="Faltantes" value={formatNumber(plan.resumen.faltantes)} /></dl>
    <section aria-label={`Clasificación de necesidades de ${plan.nombre}`}><p>Faltantes conocidos: <strong>{plan.clasificacion.faltantes_conocidos}</strong></p><p>Stock desconocido: <strong>{plan.clasificacion.stock_desconocido}</strong></p><p>Sin relacionar: <strong>{plan.clasificacion.sin_relacionar}</strong></p></section>
    <ul className="clean-list produccion-tasks" aria-label={`Tareas de ${plan.nombre}`}>{plan.elaboraciones.map((task) => <TaskCard key={task.id} task={task} />)}</ul>
    <div className="menu-actions">{proposalId ? <Link to="/compras">Ver propuesta existente</Link> : <button type="button" disabled={proposalBusy || plan.clasificacion.faltantes_conocidos === 0} onClick={() => void createProposal()}>{proposalBusy ? "Generando propuesta..." : "Generar propuesta de compra"}</button>}<Link to="/stock">Revisar stock</Link><Link to="/articulos">Resolver artículos</Link></div>
    {proposalId ? <p role="status">Propuesta {proposalId} preparada · {proposalLines || plan.clasificacion.faltantes_conocidos} faltantes conocidos · sin pedidos creados.</p> : null}{proposalError ? <p role="alert">{proposalError}</p> : null}<p className="meta-line">Planificación de solo lectura: no genera pedidos ni movimientos de Stock.</p>
  </article>;
}

function TaskCard({ task }: { task: ProductionTask }) {
  const [showIngredients, setShowIngredients] = useState(false);
  const [showDependencies, setShowDependencies] = useState(false);
  return <li><div><strong>{task.titulo}</strong><p className="meta-line">{formatQuantity(task.cantidad_a_producir, task.unidad)} · rendimiento {formatNumber(task.rendimiento_base)} · factor {formatNumber(task.factor_escalado)} · {task.origen}</p></div>
    <p className={task.estado === "BLOQUEADO" ? "produccion-alert" : "meta-line"}>{task.estado === "BLOQUEADO" ? "BLOQUEADO — faltan ingredientes" : "LISTO"}</p>
    <button type="button" onClick={() => setShowIngredients((value) => !value)}>Ver ingredientes</button><button type="button" onClick={() => setShowDependencies((value) => !value)}>Ver dependencias</button>
    {showIngredients ? <section aria-label={`Ingredientes de ${task.titulo}`}>{task.ingredientes.map((item, index) => <p key={`${item.articulo_id}-${index}`}>{item.nombre}: {formatQuantity(item.cantidad, item.unidad)} · disponible {formatQuantity(item.disponible, item.unidad)}{Number(item.faltante) > 0 ? <span className="produccion-alert"> · Faltan {formatQuantity(item.faltante, item.unidad)}</span> : null}</p>)}</section> : null}
    {showDependencies ? <section aria-label={`Dependencias de ${task.titulo}`}><DependencyTree node={task.subelaboraciones} /></section> : null}
  </li>;
}

function DependencyTree({ node }: { node: ProductionTree }) {
  const children = node.componentes?.filter((item) => item.tipo === "elaboracion") ?? [];
  if (!children.length) return <p>Sin subelaboraciones.</p>;
  return <ul>{children.map((item, index) => <li key={`${item.nombre}-${index}`}>{item.nombre}: {formatQuantity(item.cantidad_necesaria, item.unidad)}{item.detalle ? <DependencyTree node={item.detalle} /> : null}</li>)}</ul>;
}

function Detail({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div>; }
function SummaryCard({ title, value }: { title: string; value: number | string }) { return <article className="data-card"><h3>{title}</h3><p className="stat-value">{value}</p></article>; }
function formatDate(value: unknown): string { if (typeof value !== "string" || !value.trim()) return "No disponible"; const iso = /^\d{4}-\d{2}-\d{2}$/.test(value); const date = new Date(iso ? `${value}T00:00:00Z` : value); return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeZone: iso ? "UTC" : undefined }).format(date); }
function formatNumber(value: unknown): string { return typeof value === "number" && Number.isFinite(value) ? new Intl.NumberFormat("es-ES").format(value) : "No disponible"; }
function formatQuantity(value: unknown, unit: unknown): string { if (typeof value !== "number" || !Number.isFinite(value)) return "Cantidad no disponible"; return `${new Intl.NumberFormat("es-ES").format(value)}${typeof unit === "string" && unit.trim() ? ` ${unit}` : ""}`; }
function sum(plans: ProductionPlan[] | undefined, field: keyof ProductionPlan["resumen"]): number { return (plans ?? []).reduce((total, plan) => total + Number(plan.resumen[field] || 0), 0); }
