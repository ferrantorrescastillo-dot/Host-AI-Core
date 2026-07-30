import type { ApiEnvelope } from "./articulos";

export type ElaboracionResumen = {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  categoria?: string | null;
  tipo: string;
  estado: string;
  rendimiento?: number | null;
  unidad_rendimiento?: string | null;
  raciones?: number | null;
  coste_total?: number | null;
  coste_por_racion?: number | null;
  tiene_receta: boolean;
  tiene_escandallo: boolean;
  tiene_ficha_tecnica: boolean;
  tiene_fotografia: boolean;
  tiene_documentos: boolean;
  completitud?: number | null;
  actualizado_en?: string | null;
};

export type BibliotecaResponse = ApiEnvelope & {
  biblioteca: {
    estado: string;
    total_elaboraciones: number;
    sin_receta: number;
    sin_escandallo: number;
    sin_ficha_tecnica: number;
    con_documentos: number;
    capacidades: Record<string, boolean>;
  };
};

export type ElaboracionesResponse = ApiEnvelope & {
  elaboraciones: {
    items: ElaboracionResumen[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    filters: { estados: string[]; categorias: string[] };
    capabilities: Record<string, boolean>;
  };
};

export type IngredienteReceta = {
  articulo_id?: string | null;
  nombre_original: string;
  cantidad_texto?: string | null;
  cantidad?: number | null;
  unidad?: string | null;
  merma?: number | null;
  cantidad_neta?: number | null;
  coste_unitario?: number | null;
  coste_linea?: number | null;
  observaciones?: string | null;
  estado_relacion: "relacionado" | "sin_relacionar" | "coincidencia_dudosa";
};

export type ElaboracionDetalle = ElaboracionResumen & {
  receta: {
    ingredientes: IngredienteReceta[];
    procedimiento?: string | null;
    observaciones?: string | null;
    tiempo_total?: string | null;
    tiempo_activo?: string | null;
    tiempo_pasivo?: string | null;
    tecnicas: string[];
  };
  escandallo?: {
    id?: string | null;
    estado?: string | null;
    coste_ingredientes?: number | null;
    otros_costes?: number | null;
    coste_total?: number | null;
    rendimiento?: number | null;
    coste_por_racion?: number | null;
    precio_objetivo?: number | null;
    margen?: number | null;
    fecha_calculo?: string | null;
    desactualizado: boolean;
    incidencias: Record<string, unknown>[];
  } | null;
  ficha_tecnica?: Record<string, unknown> | null;
  alergenos: string[];
  conservacion?: string | null;
  regeneracion?: string | null;
  produccion: Record<string, unknown>;
  documentos: Array<{ tipo: string; nombre: string; referencia: string }>;
  imagenes: string[];
  versiones: Array<{ version?: number; fecha?: string }>;
  menus: string[];
  eventos: string[];
  historial: Record<string, unknown>[];
  pendientes: string[];
};

export type ElaboracionResponse = ApiEnvelope & { elaboracion: ElaboracionDetalle };
