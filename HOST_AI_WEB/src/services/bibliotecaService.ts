import { hostAiApiClient } from "../api/client";

export type ElaboracionesQuery = {
  q?: string;
  page?: number;
  page_size?: number;
  estado?: string;
  categoria?: string;
  tiene_receta?: boolean;
  tiene_escandallo?: boolean;
  tiene_ficha_tecnica?: boolean;
  tiene_documentos?: boolean;
  orden?: "nombre" | "actualizacion" | "coste" | "categoria" | "estado";
  direccion?: "asc" | "desc";
};

function serialize(query: ElaboracionesQuery): string {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  return params.size ? `?${params}` : "";
}

export const bibliotecaService = {
  summary: () => hostAiApiClient.getBiblioteca(),
  list: (query: ElaboracionesQuery = {}) => hostAiApiClient.getElaboraciones(serialize(query)),
  detail: (id: string) => hostAiApiClient.getElaboracion(id),
};
