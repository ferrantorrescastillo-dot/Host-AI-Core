import type { ApiEnvelopeBase } from "./api";

export type CompraDraftLine = { id?: string; nombre: string; articulo_id?: string; cantidad: number; unidad: string; precio_unitario: number; observaciones?: string; propuesta_id?: string };
export type CompraDraft = { id: string; proveedor: string; estado: string; lineas: CompraDraftLine[]; importe_estimado: number; observaciones?: string; creado_en: string; actualizado_en: string; origen: { tipo: string; id: string; version: number; propuesta_id: string } };
export type CompraDraftResponse = ApiEnvelopeBase & { borrador: CompraDraft };
export type CompraDraftInput = { proveedor: string; observaciones?: string; lineas: CompraDraftLine[] };
