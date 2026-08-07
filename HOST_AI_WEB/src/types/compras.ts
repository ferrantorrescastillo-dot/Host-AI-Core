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
