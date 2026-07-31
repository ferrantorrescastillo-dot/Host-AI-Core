import type { ApiEnvelopeBase } from "./api";

export type MenuState = "BORRADOR" | "ACTIVO" | "ARCHIVADO";

export type MenuElaboration = {
  elaboracion_id: string;
  elaboracion_nombre: string;
  cantidad: number;
  coste_por_comensal: number;
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
