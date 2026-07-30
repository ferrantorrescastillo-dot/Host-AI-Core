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
  importDocument: async (file: File) => {
    const buffer = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    const chunkSize = 0x8000;
    for (let index = 0; index < buffer.length; index += chunkSize) {
      binary += String.fromCharCode(...buffer.subarray(index, index + chunkSize));
    }
    return hostAiApiClient.createBibliotecaImport({
      nombre: file.name,
      tipo_mime: file.type || "application/octet-stream",
      contenido_base64: btoa(binary),
      texto: file.name.toLowerCase().endsWith(".txt")
        ? new TextDecoder().decode(buffer)
        : undefined,
    });
  },
  importDetail: (id: string) => hostAiApiClient.getBibliotecaImport(id),
  importProposals: (id: string) => hostAiApiClient.getBibliotecaImportProposals(id),
  importDraft: (id: string) => hostAiApiClient.getBibliotecaImportDraft(id),
  updateImportDraft: (
    id: string,
    draft: { draft_version: number; recipes: unknown[] },
  ) => hostAiApiClient.updateBibliotecaImportDraft(id, draft),
  confirmImport: (id: string, draftVersion: number, usuario: string) =>
    hostAiApiClient.confirmBibliotecaImport(id, {
      draft_version: draftVersion,
      usuario,
      confirmacion: "CONFIRMAR",
    }),
};
