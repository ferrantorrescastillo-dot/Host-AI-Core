import { hostAiApiClient } from "../api/client";

export type CatalogoQuery = {
  q?: string;
  familia?: string;
  proveedor?: string;
  estado?: string;
  con_stock?: boolean;
  page?: number;
  page_size?: number;
  orden?: "nombre" | "codigo" | "precio" | "stock" | "actualizacion";
  direccion?: "asc" | "desc";
};

export const articulosService = {
  list(query: CatalogoQuery = {}) {
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, String(value));
    });
    const suffix = params.size ? `?${params.toString()}` : "";
    return hostAiApiClient.getArticulos(suffix);
  },
  get(id: string) {
    return hostAiApiClient.getArticulo(id);
  },
  update: hostAiApiClient.updateArticulo,
  proposeDocumentation: hostAiApiClient.proposeArticleDocumentation,
  previewDocumentation: hostAiApiClient.previewArticleDocumentation,
  confirmDocumentation: hostAiApiClient.confirmArticleDocumentation,
  previewManualPrice: hostAiApiClient.previewManualPrice,
  confirmManualPrice: hostAiApiClient.confirmManualPrice,
  withoutPrice: hostAiApiClient.getArticlesWithoutPrice,
  reclassificationCandidates: hostAiApiClient.getReclassificationCandidates,
  previewReclassification: hostAiApiClient.previewReclassification,
  confirmReclassification: hostAiApiClient.confirmReclassification,
  exportWithoutPrice: hostAiApiClient.exportArticlesWithoutPrice,
  previewImportedReferences: hostAiApiClient.previewImportedReferences,
  confirmImportedReferences: hostAiApiClient.confirmImportedReferences,
  importedReferencesState: hostAiApiClient.getImportedReferencesState,
  discardImportedReferences: hostAiApiClient.discardImportedReferences,
  previewWebPrice: hostAiApiClient.previewWebPrice,
  confirmWebPrice: hostAiApiClient.confirmWebPrice,
};
