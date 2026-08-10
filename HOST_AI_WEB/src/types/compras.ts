import type { ApiEnvelopeBase } from "./api";

export type CompraDraftLine = { id?: string; nombre: string; articulo_id?: string; cantidad: number; unidad: string; precio_unitario: number; observaciones?: string; propuesta_id?: string };
export type CompraDraft = { id: string; proveedor: string; estado: string; lineas: CompraDraftLine[]; importe_estimado: number; observaciones?: string; creado_en: string; actualizado_en: string; origen: { tipo: string; id: string; version: number; propuesta_id: string } };
export type CompraValidationIssue = { code: string; field: string; line_index?: number; message: string };
export type CompraDraftRevision = { valido: boolean; errores_bloqueantes: CompraValidationIssue[]; advertencias: CompraValidationIssue[] };
export type CompraDraftResponse = ApiEnvelopeBase & { borrador: CompraDraft; revision?: CompraDraftRevision };
export type CompraDraftInput = { proveedor: string; observaciones?: string; lineas: CompraDraftLine[] };
export type CompraConfirmationResponse = ApiEnvelopeBase & {
  pedido: CompraDraft; borrador: CompraDraft; idempotente: boolean;
  advertencias: CompraValidationIssue[]; stock_modificado: false; inventario_modificado: false; recepciones_creadas: 0;
};
export type ReceptionLine = { order_line_id: string; article_id: string; article_name: string; ordered_quantity: number; previously_received: number; pending_quantity: number; received_quantity: number; unit: string; canonical_unit?: string; stock_quantity?: number | null; order_price: number; received_price: number | null; lot: string; expiry: string; location: string; observations: string; incidences: Array<{ code: string; message: string; bloqueante: boolean }> };
export type PurchaseReception = { id: string; reception_id: string; order_id: string; proveedor: string; fecha: string; referencia: string; estado: "BORRADOR" | "CONFIRMADA"; lineas: ReceptionLine[]; incidencias: Array<{ code: string; message: string; bloqueante: boolean; order_line_id?: string }>; observaciones: string; confirmable: boolean; document_id?: string; document_name?: string; document_type?: string; document_reference?: string };
export type PurchaseReceptionResponse = ApiEnvelopeBase & { recepcion: PurchaseReception; idempotente?: boolean; stock_modificado: boolean; pedido?: CompraDraft; movimientos?: Array<Record<string, unknown>> };
