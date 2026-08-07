import type { ApiEnvelopeBase } from "./api";

export type MenuState = "BORRADOR" | "ACTIVO" | "ARCHIVADO";

export type MenuElaboration = {
  elaboracion_id: string;
  elaboracion_nombre: string;
  cantidad: number;
  coste_por_racion?: number | null;
  coste_linea_por_comensal?: number | null;
  coste_linea_total?: number | null;
  coste_por_comensal: number | null;
  estado_coste?: "DISPONIBLE" | "INCOMPLETO" | "SIN_COSTE";
  motivo_coste_no_disponible?: string | null;
  fecha_coste?: string | null;
  orden?: number;
  observaciones?: string;
  version_elaboracion?: number | null;
};

export type MenuSection = {
  id: string;
  nombre: string;
  orden: number;
  elaboraciones: MenuElaboration[];
};

export type IntelligentMenu = {
  id: string;
  codigo: string;
  nombre: string;
  estado: MenuState;
  estado_operativo: string;
  version: number;
  comensales: number;
  observaciones: string;
  secciones: MenuSection[];
  coste_total: number;
  coste_por_comensal: number;
  coste_completo: boolean;
  lineas_sin_coste: number;
  advertencias: string[];
  incidencias: Array<{ tipo?: string; detalle?: string }>;
  creado_en?: string | null;
  actualizado_en?: string | null;
};

export type MenuInput = {
  nombre: string;
  estado: MenuState;
  comensales: number;
  observaciones: string;
  secciones: Array<{
    nombre: string;
    elaboraciones: Array<{
      elaboracion_id: string;
      cantidad: number;
      orden?: number;
      observaciones?: string;
      version_elaboracion?: number | null;
      coste_por_racion?: number | null;
      coste_linea_por_comensal?: number | null;
      coste_linea_total?: number | null;
      estado_coste?: "DISPONIBLE" | "INCOMPLETO" | "SIN_COSTE";
      motivo_coste_no_disponible?: string | null;
    }>;
  }>;
  version?: number;
};

export type MenusResponse = ApiEnvelopeBase & {
  menus: IntelligentMenu[];
  total: number;
  resumen: { borradores: number; activos: number; archivados: number };
};

export type MenuResponse = ApiEnvelopeBase & { menu: IntelligentMenu };

export type MenuNeedOrigin = { seccion: string; elaboracion_id: string; elaboracion_nombre: string; cantidad: number; unidad: string; factor_escalado: number };
export type MenuNeedLine = {
  articulo_id: string | null; articulo_codigo: string | null; articulo_nombre: string | null; ingrediente_nombre: string;
  origenes: MenuNeedOrigin[]; cantidad_necesaria: number; unidad_necesaria: string;
  stock_fisico: number | null; stock_reservado: number | null; stock_comprometido: number | null;
  stock_disponible: number | null; cantidad_faltante: number | null; unidad_stock: string | null; estado: string;
  proveedor_preferente: string | null; formato_compra: string | null; cantidad_propuesta_compra: number | null;
  coste_estimado: number | null; motivo_no_resuelto: string | null;
};
export type MenuNeedsResponse = ApiEnvelopeBase & { necesidades: {
  menu_id: string; menu_version: number; comensales: number; generated_at: string; complete: boolean;
  lines: MenuNeedLine[]; warnings: string[]; blocking_errors: Array<{ code: string; message: string; articulo_id?: string | null }>;
  summary: { articulos: number; cubiertos: number; compra_necesaria: number; sin_relacionar: number; conversiones_pendientes: number; candidatas_propuesta: number };
  solo_lectura: true; datos_reales_modificados: false;
} };
export type MenuPurchaseProposalResponse = ApiEnvelopeBase & { propuesta: {
  id: string; estado: "BORRADOR" | "REVISADA" | "CONFIRMADA"; version: number; coste_estimado: number; coste_completo: boolean;
  lineas: MenuProposalLine[]; grupos_proveedor: Array<{ proveedor: string; lineas: MenuProposalLine[] }>;
  resumen: { articulos_propuestos: number; articulos_pendientes: number; proveedores_pendientes: number };
  advertencias: string[];
  crea_pedido: boolean; modifica_stock: false; datos_reales_modificados: boolean;
}; pedidos_creados?: MenuDraftOrder[]; lineas_incluidas?: MenuProposalLine[];
lineas_pendientes?: MenuProposalLine[]; lineas_excluidas?: MenuProposalLine[];
advertencias?: string[]; errores?: Array<{ code?: string; message: string }> };

export type MenuProposalLine = {
  id: string; incluir: boolean; articulo_id: string | null; articulo: string | null;
  cantidad_necesaria: number; cantidad_faltante: number | null; cantidad_final_propuesta: number | null;
  unidad_base: string; proveedor: string | null; formato_compra: string | null;
  precio_estimado: number | null; coste_estimado: number | null; estado: string;
  observaciones: string; advertencia: string | null; motivos_pendientes?: string[];
  proveedor_sugerido?: string | { nombre?: string } | null;
  proveedor_preferente?: string | { nombre?: string } | null;
  proveedor_validado?: boolean;
};

export type MenuDraftOrder = { id: string; proveedor: string; estado: "borrador"; lineas: Array<Record<string, unknown>>; importe_estimado: number; observaciones: string };

export type MenuOrdersResponse = ApiEnvelopeBase & {
  propuesta: MenuPurchaseProposalResponse["propuesta"];
  pedidos: MenuDraftOrder[]; pedidos_creados: MenuDraftOrder[];
  lineas_incluidas: MenuProposalLine[]; lineas_pendientes: MenuProposalLine[]; lineas_excluidas: MenuProposalLine[];
  advertencias: string[]; errores: Array<{ code?: string; message: string }>;
  idempotente: boolean; stock_modificado: false; recepciones_creadas: 0;
};

export type MenuElaborationOption = {
  id: string;
  codigo: string;
  nombre: string;
  familia: string;
};

export type MenuElaborationsResponse = ApiEnvelopeBase & {
  elaboraciones: MenuElaborationOption[];
  total: number;
};
