import { hostAiApiClient } from "../api/client";
import { HOST_AI_API_BASE_URL } from "../config/env";
import type { RendimientoInput } from "../types/biblioteca";

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
  previewYield: (id: string, input: RendimientoInput) => hostAiApiClient.previewElaborationYield(id, input),
  confirmYield: (id: string, input: RendimientoInput, previewToken: string) => hostAiApiClient.confirmElaborationYield(id, input, previewToken),
  previewCosting: hostAiApiClient.previewCostingEdit,
  confirmCosting: hostAiApiClient.confirmCostingEdit,
  proposeDocumentation: hostAiApiClient.proposeRecipeDocumentation,
  previewDocumentation: hostAiApiClient.previewRecipeDocumentation,
  confirmDocumentation: hostAiApiClient.confirmRecipeDocumentation,
  recipeBatchSummary: hostAiApiClient.recipeBatchSummary,
  startRecipeBatch: hostAiApiClient.startRecipeBatch,
  getRecipeBatch: hostAiApiClient.getRecipeBatch,
  advanceRecipeBatch: hostAiApiClient.advanceRecipeBatch,
  recipeBatchAction: hostAiApiClient.recipeBatchAction,
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
  importRestaurantData: async (files: File[], pastedText = "", resolveAmbiguitiesWithAi = false, analyzeDocumentWithAi = false, excludeLegacyAp = false) => {
    const encode = async (file: File) => {
      const buffer = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      const chunkSize = 0x8000;
      for (let index = 0; index < buffer.length; index += chunkSize) {
        binary += String.fromCharCode(...buffer.subarray(index, index + chunkSize));
      }
      const textual = /\.(csv|tsv|json|txt|md)$/i.test(file.name);
      return {
        nombre: file.name,
        tipo_mime: file.type || "application/octet-stream",
        contenido_base64: btoa(binary),
        texto: textual ? new TextDecoder().decode(buffer) : undefined,
      };
    };
    return hostAiApiClient.createBibliotecaImport({
      archivos: await Promise.all(files.map(encode)),
      texto_pegado: pastedText.trim() || undefined,
      resolver_ambiguedades_ia: resolveAmbiguitiesWithAi || undefined,
      analizar_documento_con_ia: analyzeDocumentWithAi || undefined,
      excluir_ap_antiguos: excludeLegacyAp || undefined,
    });
  },
  importPreparedData: async (file: File) => {
    const parsed = JSON.parse(await file.text()) as Record<string, unknown>;
    return hostAiApiClient.createBibliotecaImport({ hostai_import_package: parsed });
  },
  prepareForExternalAi: async (file: File) => {
    const buffer = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    const chunkSize = 0x8000;
    for (let index = 0; index < buffer.length; index += chunkSize) {
      binary += String.fromCharCode(...buffer.subarray(index, index + chunkSize));
    }
    const response = await fetch(`${HOST_AI_API_BASE_URL}/api/v1/biblioteca/importaciones/preparar-para-ia`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre: file.name, contenido_base64: btoa(binary) }),
    });
    if (!response.ok) throw new Error("No se pudo preparar el ZIP para IA.");
    const disposition = response.headers.get("Content-Disposition") || "";
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || "HOSTAI_PARA_IA_documento.zip";
    return { blob: await response.blob(), filename };
  },
  importDetail: (id: string) => hostAiApiClient.getBibliotecaImport(id),
  importProposals: (id: string) => hostAiApiClient.getBibliotecaImportProposals(id),
  importDraft: (id: string) => hostAiApiClient.getBibliotecaImportDraft(id),
  updateImportDraft: (
    id: string,
    draft: { draft_version: number; recipes: unknown[]; variant_decisions?: unknown[]; article_decisions?: unknown[]; menu_decisions?: unknown[] },
  ) => hostAiApiClient.updateBibliotecaImportDraft(id, draft),
  confirmImport: (id: string, draftVersion: number, usuario: string, previewFingerprint?: string) =>
    hostAiApiClient.confirmBibliotecaImport(id, {
      draft_version: draftVersion,
      usuario,
      confirmacion: "CONFIRMAR",
      preview_fingerprint: previewFingerprint,
    }),
  previewLegacyCanonicalization: (id: string, legacyIds: string[]) =>
    hostAiApiClient.previewLegacyCanonicalization(id, legacyIds),
  confirmLegacyCanonicalization: (id: string, previewToken: string) =>
    hostAiApiClient.confirmLegacyCanonicalization(id, previewToken),
};
