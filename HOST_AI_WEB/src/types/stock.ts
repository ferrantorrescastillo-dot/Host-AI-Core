import type { ApiEnvelopeBase, StockMovimiento } from "./api";

export type StockMovementType = "INVENTARIO_INICIAL" | "AJUSTE_POSITIVO" | "AJUSTE_NEGATIVO";
export type StockMovementInput = { article_id: string; tipo: StockMovementType; cantidad: number; unidad: string; lote?: string; ubicacion?: string; caducidad?: string; observaciones?: string; production_plan_id?: string; return_to?: string; confirmar_existente?: boolean };
export type StockMovementResponse = ApiEnvelopeBase & { movimiento: (StockMovimiento & { movement_id: string; article_id: string; signo: number; usuario: string; origen: string }) | null; stock_anterior: number; stock_actual: number; mensaje: string; pedidos_creados: 0; recepciones_creadas: 0 };
export type StockAdjustmentInput = { article_id: string; cantidad_objetivo: number; unidad: string; motivo: string };
export type StockAdjustmentPreview = ApiEnvelopeBase & { preview_token: string; stock_anterior: number; stock_resultante: number; diferencia: number; unidad: string; motivo: string; requiere_confirmacion: boolean; datos_reales_modificados: false };
