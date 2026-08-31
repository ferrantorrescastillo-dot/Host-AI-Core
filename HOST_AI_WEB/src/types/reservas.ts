export type ReservaAlcance = "todas" | "hoy" | "proximas";
export type ReservaEstado = "PENDIENTE" | "CONFIRMADA" | "CANCELADA" | "NO_SHOW" | "COMPLETADA";
export type ReservaServicio = "COMIDA" | "CENA";

export type ReservaResumen = {
  reserva_id: string;
  nombre_cliente: string;
  fecha: string;
  hora: string;
  pax: number;
  estado: ReservaEstado;
  servicio: ReservaServicio;
  evento_id: string | null;
};

export type ReservaDetalle = ReservaResumen & {
  observaciones: string;
  origen?: string;
  creado_en?: string;
  actualizado_en?: string;
};

export type ReservasFilters = {
  alcance?: ReservaAlcance;
  q?: string;
  fecha?: string;
  estado?: ReservaEstado | "";
  servicio?: ReservaServicio | "";
  limite?: number;
};

type ApiEnvelope = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
};

export type ReservasResponse = ApiEnvelope & {
  reservas: { items: ReservaResumen[]; total: number };
};

export type ReservaResponse = ApiEnvelope & {
  reserva: ReservaDetalle;
};

export type ReservaWriteOperation = "CREAR" | "MODIFICAR" | "CONFIRMAR" | "CANCELAR" | "NO_SHOW" | "COMPLETAR" | "ELIMINAR";
export type ReservaWriteInput = {
  nombre_cliente: string; fecha: string; hora: string; pax: number;
  servicio: ReservaServicio; observaciones?: string; evento_id?: string | null;
};
export type ReservaPreviewResponse = ApiEnvelope & {
  estado: "LISTO_PARA_CONFIRMAR"; operacion: ReservaWriteOperation;
  reserva_id: string | null; antes: Partial<ReservaDetalle> | null;
  propuesto: Partial<ReservaDetalle>; preview_token: string; expira_en: string;
  requiere_confirmacion: true;
};
export type ReservaConfirmationResponse = ApiEnvelope & {
  estado: "CONFIRMADO"; operacion: ReservaWriteOperation; reserva: ReservaDetalle;
  idempotente: boolean;
};
