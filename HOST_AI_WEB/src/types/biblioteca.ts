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
  tiene_produccion: boolean;
  tiene_relaciones_menu_evento: boolean;
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
  articulo_codigo?: string | null;
  articulo_nombre?: string | null;
  codigo?: string | null;
  nombre_articulo?: string | null;
  unidad_base?: string | null;
  nombre_original: string;
  cantidad_texto?: string | null;
  cantidad?: number | null;
  unidad?: string | null;
  merma?: number | null;
  cantidad_neta?: number | null;
  cantidad_receta?: number | null;
  unidad_receta?: string | null;
  coste_unitario?: number | null;
  precio_unitario?: number | null;
  precio_original?: number | null;
  unidad_precio_original?: string | null;
  precio_aplicado?: number | null;
  unidad_precio_aplicado?: string | null;
  coste_linea?: number | null;
  unidad_precio?: string | null;
  origen_precio?: string | null;
  proveedor_precio?: string | null;
  fecha_precio?: string | null;
  factor_conversion?: number | null;
  tipo_conversion?: "directa" | "metrica" | "envase" | "normalizacion_heredada" | "no_disponible" | string | null;
  cantidad_utilizada?: number | null;
  cantidad_con_merma?: number | null;
  coste_con_merma?: number | null;
  estado_coste?: string | null;
  motivo_sin_coste?: string | null;
  observaciones?: string | null;
  estado_relacion: "relacionado" | "sin_relacionar" | "coincidencia_dudosa";
};

export type EscandalloElaboracion = {
  id?: string | null;
  estado?: string | null;
  estado_coste: string;
  lineas: IngredienteReceta[];
  coste_ingredientes?: number | null;
  coste_ingredientes_parcial?: number | null;
  otros_costes?: number | null;
  coste_total?: number | null;
  coste_total_parcial?: number | null;
  rendimiento?: number | null;
  coste_por_racion?: number | null;
  precio_objetivo?: number | null;
  margen?: number | null;
  fecha_calculo?: string | null;
  desactualizado: boolean;
  ingredientes_sin_coste: number;
  ingredientes_sin_conversion: number;
  incidencias: Record<string, unknown>[];
};

export type ElaboracionDetalle = ElaboracionResumen & {
  receta: {
    ingredientes: IngredienteReceta[];
    procedimiento?: string | null;
    pasos: Array<string | Record<string, unknown>>;
    observaciones?: string | null;
    tiempo_total?: string | null;
    tiempo_activo?: string | null;
    tiempo_pasivo?: string | null;
    temperaturas: Array<string | Record<string, unknown>>;
    tecnicas: string[];
    rendimiento?: number | null;
    unidad_rendimiento?: string | null;
    raciones?: number | null;
  };
  escandallo?: EscandalloElaboracion | null;
  ficha_tecnica: {
    estado: string;
    origen: string;
    persistida: boolean;
    identificacion: Record<string, unknown>;
    descripcion?: string | null;
    fotografia?: string | null;
    ingredientes: IngredienteReceta[];
    proceso: {
      procedimiento?: string | null;
      pasos: Array<string | Record<string, unknown>>;
      observaciones?: string | null;
    };
    tiempos: Record<string, string | null>;
    temperaturas: Array<string | Record<string, unknown>>;
    rendimiento?: number | null;
    unidad_rendimiento?: string | null;
    raciones?: number | null;
    escandallo?: EscandalloElaboracion | null;
    alergenos: string[];
    conservacion?: string | null;
    caducidad?: string | null;
    regeneracion?: string | null;
    presentacion?: string | null;
    utensilios: string[];
    produccion: ProduccionElaboracion;
    documentos: DocumentoElaboracion[];
    version?: number | null;
    actualizado_en?: string | null;
    campos_pendientes: string[];
    datos_persistidos?: Record<string, unknown> | null;
  };
  alergenos: string[];
  conservacion?: string | null;
  regeneracion?: string | null;
  produccion: ProduccionElaboracion;
  documentos: DocumentoElaboracion[];
  imagenes: string[];
  versiones: Array<{ version?: number; fecha?: string }>;
  menus: string[];
  eventos: string[];
  historial: Record<string, unknown>[];
  pendientes: string[];
  avisos: string[];
};

export type ElaboracionResponse = ApiEnvelope & { elaboracion: ElaboracionDetalle };

export type ProduccionElaboracion = {
  indicaciones: {
    produccion_minima?: string | number | null;
    produccion_maxima?: string | number | null;
    personal_recomendado?: string | number | null;
    recursos: string[];
    notas?: string | null;
  };
  ordenes: Record<string, unknown>[];
  necesidades: Record<string, unknown>[];
  historial: Record<string, unknown>[];
};

export type DocumentoElaboracion = {
  tipo: string;
  nombre: string;
  referencia: string;
  fecha?: string | null;
  origen?: string | null;
  descripcion?: string | null;
  estado?: string | null;
};

export type ImportProposal = {
  id: string;
  tipo: string;
  estado: "PENDIENTE_REVISION";
  confianza: { valor: number; explicacion: string };
  explicacion: string;
  titulo: string;
  origen: { importacion_id: string; nombre: string; tipo: string };
  entidad_origen: string | null;
  bloques_origen: string[];
  advertencias: string[];
  conflictos: Array<Record<string, unknown>>;
  datos_propuestos: Record<string, unknown>;
  persistida: false;
};

export type BibliotecaImportEntity = {
  id: string;
  kind: "RECETA" | "INGREDIENTE" | string;
  name: string;
  fields: {
    ingredientes_estructurados?: Array<{
      nombre_original: string;
      cantidad_texto: string;
      unidad?: string | null;
      estado_relacion: "relacionado" | "coincidencia_dudosa" | "sin_relacionar";
      articulo_id?: string | null;
    }>;
    pasos?: string[];
    estado_relacion?: "relacionado" | "coincidencia_dudosa" | "sin_relacionar";
    cantidad_texto?: string;
    unidad?: string | null;
    receta?: string;
    [key: string]: unknown;
  };
  confidence: { valor: number; explicacion: string };
};

export type BibliotecaImportSession = {
  documento: {
    id: string;
    nombre: string;
    tipo_mime: string;
    tamano: number;
    origen: string;
    clasificacion: {
      tipo: string;
      confianza: { valor: number; explicacion: string };
      evidencias: string[];
      advertencias: string[];
    };
    secciones: Array<Record<string, unknown>>;
    entidades: BibliotecaImportEntity[];
    advertencias: string[];
    contenido_almacenado: false;
  };
  resumen: {
    secciones: number;
    entidades: number;
    propuestas: number;
    incidencias: number;
    recetas_detectadas: number;
    ingredientes_detectados: number;
    ingredientes_relacionados: number;
    coincidencias_dudosas: number;
    ingredientes_sin_relacionar: number;
    ingredientes_nuevos: number;
    duplicados_detectados: number;
    estado: "PENDIENTE_REVISION";
  };
  propuestas: ImportProposal[];
  solo_previsualizacion: true;
  confirmacion_disponible: false;
  limitaciones: string[];
};

export type BibliotecaImportResponse = ApiEnvelope & {
  importacion: BibliotecaImportSession;
};

export type BibliotecaImportProposalsResponse = ApiEnvelope & {
  importacion_id: string;
  propuestas: ImportProposal[];
  total: number;
  solo_previsualizacion: true;
};
