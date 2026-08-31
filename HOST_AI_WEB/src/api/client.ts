import { HOST_AI_API_BASE_URL } from "../config/env";
import type { ChatResponse, DashboardResponse } from "../types/api";
import type { ArticleDocumentationResponse, ArticuloCosteDerivado, ArticuloResponse, ArticuloSinPrecio, ArticuloUpdateInput, CatalogoResponse, ManualPriceResponse, PrecioReferencia, ReclassificationCandidate, ReclassificationPreview, ReferenciaImportPreviewRow, ReferenciasImportPreview } from "../types/articulos";
import type {
  BibliotecaImportProposalsResponse,
  BibliotecaImportResponse,
  BibliotecaDraftResponse,
  BibliotecaResponse,
  ElaboracionResponse,
  ElaboracionesResponse,
  RendimientoConfirmationResponse,
  RendimientoInput,
  RendimientoPreviewResponse,
  LegacyCanonicalizationPreviewResponse,
  LegacyCanonicalizationConfirmationResponse,
} from "../types/biblioteca";
import type {
  MenuElaborationsResponse,
  MenuInput,
  MenuNeedsResponse,
  MenuPurchaseProposalResponse,
  MenuOrdersResponse,
  MenuResponse,
  MenusResponse,
} from "../types/menus";
import type { CompraConfirmationResponse, CompraDraftInput, CompraDraftResponse, PurchaseReception, PurchaseReceptionResponse, ReceptionDocumentResponse, ReceptionExtractionLine, ReceptionExtractionResponse, ReceptionLine } from "../types/compras";
import type { ProductionPlanResponse, ProductionProposalResponse, ProductionStockReviewResponse } from "../types/produccion";
import type { StockMovementInput, StockMovementResponse } from "../types/stock";
import type { ReservaConfirmationResponse, ReservaPreviewResponse, ReservaResponse, ReservasResponse, ReservaWriteOperation } from "../types/reservas";

type Envelope = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
  error?: { status?: number; code?: string; message?: string };
  resultado?: unknown;
};

const AI_SESSION_KEY = "host-ai-cost-session-id";
export function getAiSessionId(): string {
  const existing = sessionStorage.getItem(AI_SESSION_KEY);
  if (existing) return existing;
  const value = `WEB-${crypto.randomUUID()}`;
  sessionStorage.setItem(AI_SESSION_KEY, value);
  return value;
}

export class HostAiApiError extends Error {
  requestId?: string;
  statusCode?: number;
  modoSeguro?: boolean;
  datosRealesModificados?: boolean;
  details?: unknown;

  constructor(
    message: string,
    opts?: {
      requestId?: string;
      statusCode?: number;
      modoSeguro?: boolean;
      datosRealesModificados?: boolean;
      details?: unknown;
    },
  ) {
    super(message);
    this.name = "HostAiApiError";
    this.requestId = opts?.requestId;
    this.statusCode = opts?.statusCode;
    this.modoSeguro = opts?.modoSeguro;
    this.datosRealesModificados = opts?.datosRealesModificados;
    this.details = opts?.details;
  }
}

function assertEnvelope(payload: any): asserts payload is Envelope {
  const ok = payload && typeof payload === "object" && typeof payload.ok === "boolean";
  const requestId = typeof payload?.request_id === "string";
  const apiVersion = typeof payload?.api_version === "string";
  if (!ok || !requestId || !apiVersion) {
    throw new HostAiApiError("Respuesta de API no valida.");
  }
}

async function request<T extends Envelope>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${HOST_AI_API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
      ...init,
    });
  } catch {
    throw new HostAiApiError("No se pudo conectar con la API.");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new HostAiApiError("No se pudo leer la respuesta del servidor.", {
      statusCode: response.status,
    });
  }

  assertEnvelope(payload);

  if (!response.ok || payload.ok === false) {
    const safeMessage = payload.error?.message || "No se pudo completar la solicitud.";
    throw new HostAiApiError(safeMessage, {
      requestId: payload.request_id,
      statusCode: response.status,
      modoSeguro: payload.modo_seguro,
      datosRealesModificados: payload.datos_reales_modificados,
      details: payload.resultado,
    });
  }

  return payload as T;
}

export const hostAiApiClient = {
  getEvento(id: string): Promise<Envelope & { evento: Record<string, unknown> }> {
    return request(`/api/v1/eventos/${encodeURIComponent(id)}`, { method: "GET" });
  },
  previewCatalogCrud(domain: "EVENTO" | "ARTICULO" | "RECETA", operation: "CREAR" | "MODIFICAR" | "ARCHIVAR", payload: Record<string, unknown>, entityId = "", sessionId = "web", fieldOrigins: Record<string, "IA" | "USUARIO"> = {}): Promise<Envelope & { preview_token: string; antes?: Record<string, unknown>; propuesto: Record<string, unknown>; requiere_confirmacion: true }> {
    return request("/api/v1/catalogo/preview", { method: "POST", body: JSON.stringify({ dominio: domain, operacion: operation, payload, entity_id: entityId, session_id: sessionId, field_origins: fieldOrigins }) });
  },
  proposeArticleDraft(draft: Record<string, unknown>, culinaryContext: import("../types/articulos").ArticleCulinaryContext = {}): Promise<Envelope & { datos_propuestos_ia: Record<string, unknown>; campos_descartados: string[]; cost_breakdown?: import("../types/articulos").AICostBreakdown }> {
    return request("/api/v1/articulos/documentacion/propuesta-borrador", { method: "POST", body: JSON.stringify({ draft, culinary_context: culinaryContext, session_id: getAiSessionId() }) });
  },
  confirmCatalogCrud(previewToken: string, sessionId = "web"): Promise<Envelope & { registro: Record<string, unknown>; idempotente: boolean }> {
    return request("/api/v1/catalogo/confirmar", { method: "POST", body: JSON.stringify({ preview_token: previewToken, session_id: sessionId }) });
  },
  getReservas(query = ""): Promise<ReservasResponse> {
    return request<ReservasResponse>(`/api/v1/reservas${query}`, { method: "GET" });
  },
  getReserva(id: string): Promise<ReservaResponse> {
    return request<ReservaResponse>(`/api/v1/reservas/${encodeURIComponent(id)}`, { method: "GET" });
  },
  previewReserva(operation: ReservaWriteOperation, payload: Record<string, unknown>, reservaId = "", sessionId = "web"): Promise<ReservaPreviewResponse> {
    return request<ReservaPreviewResponse>("/api/v1/reservas/preview", { method: "POST", body: JSON.stringify({ operacion: operation, reserva_id: reservaId, payload, session_id: sessionId }) });
  },
  confirmReserva(previewToken: string, sessionId = "web"): Promise<ReservaConfirmationResponse> {
    return request<ReservaConfirmationResponse>("/api/v1/reservas/confirmar", { method: "POST", body: JSON.stringify({ preview_token: previewToken, session_id: sessionId }) });
  },
  getDashboard(): Promise<DashboardResponse> {
    return request<DashboardResponse>("/api/v1/dashboard", { method: "GET" });
  },
  getAiCostSummary(entityType = "", entityId = ""): Promise<Envelope & { cost_summary: { total_cost_usd: string; by_model: Record<string, string>; by_capability: Record<string, string>; events: number } }> {
    const query = new URLSearchParams({ session_id: getAiSessionId() });
    if (entityType) query.set("entity_type", entityType);
    if (entityId) query.set("entity_id", entityId);
    return request(`/api/v1/ai-costs/summary?${query}`, { method: "GET" });
  },
  createStockMovement(input: StockMovementInput): Promise<StockMovementResponse> {
    return request<StockMovementResponse>("/api/v1/stock/movimientos", { method: "POST", body: JSON.stringify({ ...input, confirmacion: "REGISTRAR_MOVIMIENTO_STOCK", usuario: "web" }) });
  },
  previewStockAdjustment(input: import("../types/stock").StockAdjustmentInput): Promise<import("../types/stock").StockAdjustmentPreview> {
    return request("/api/v1/stock/ajustes/preview", { method: "POST", body: JSON.stringify(input) });
  },
  confirmStockAdjustment(previewToken: string): Promise<StockMovementResponse & { estado: string; idempotente: boolean }> {
    return request("/api/v1/stock/ajustes/confirmar", { method: "POST", body: JSON.stringify({ preview_token: previewToken }) });
  },
  discardStockAdjustment(previewToken: string): Promise<Envelope & { estado: string }> {
    return request("/api/v1/stock/ajustes/descartar", { method: "POST", body: JSON.stringify({ preview_token: previewToken }) });
  },
  getStockLocations(): Promise<Envelope & { ubicaciones: Array<{ id: string; nombre: string; lotes?: Array<Record<string, unknown>>; total_lotes?: number; total_articulos?: number }> }> {
    return request("/api/v1/stock/ubicaciones", { method: "GET" });
  },
  getStockLot(id: string): Promise<Envelope & { lote: Record<string, unknown>; incidencias: Array<Record<string, string>>; movimientos?: Array<Record<string, unknown>>; acciones: string[] }> {
    return request(`/api/v1/stock/lotes/${encodeURIComponent(id)}`, { method: "GET" });
  },
  previewStockLotLocation(id: string, locationId: string): Promise<Envelope & { preview_token: string; lote_antes: Record<string, unknown>; lote_despues: Record<string, unknown>; requiere_confirmacion: boolean }> {
    return request(`/api/v1/stock/lotes/${encodeURIComponent(id)}/ubicacion/preview`, { method: "POST", body: JSON.stringify({ location_id: locationId }) });
  },
  confirmStockLotLocation(id: string, locationId: string, previewToken: string): Promise<Envelope & { lote: Record<string, unknown> }> {
    return request(`/api/v1/stock/lotes/${encodeURIComponent(id)}/ubicacion/confirmar`, { method: "POST", body: JSON.stringify({ location_id: locationId, preview_token: previewToken }) });
  },
  previewCostingEdit(id: string, changes: Record<string, unknown>): Promise<Envelope & { preview_token: string; escandallo_propuesto: Record<string, any> }> {
    return request(`/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/escandallo/preview`, { method: "POST", body: JSON.stringify({ changes }) });
  },
  confirmCostingEdit(id: string, changes: Record<string, unknown>, previewToken: string): Promise<Envelope & { escandallo: Record<string, any> }> {
    return request(`/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/escandallo/confirmar`, { method: "POST", body: JSON.stringify({ changes, preview_token: previewToken }) });
  },
  proposeRecipeDocumentation(id: string, proposed: Record<string, unknown>, detectedAllergens: string[] = []): Promise<Envelope & Record<string, any>> {
    return request(`/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/documentacion/propuesta`, { method: "POST", body: JSON.stringify({ proposed, detected_allergens: detectedAllergens, session_id: getAiSessionId() }) });
  },
  previewRecipeDocumentation(id: string, selected: Record<string, unknown>, overwriteFields: string[] = []): Promise<Envelope & { preview_token: string; cambios_seleccionados: Record<string, unknown> }> {
    return request(`/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/documentacion/preview`, { method: "POST", body: JSON.stringify({ selected, overwrite_fields: overwriteFields }) });
  },
  confirmRecipeDocumentation(id: string, selected: Record<string, unknown>, overwriteFields: string[], previewToken: string): Promise<Envelope & Record<string, any>> {
    return request(`/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/documentacion/confirmar`, { method: "POST", body: JSON.stringify({ selected, overwrite_fields: overwriteFields, preview_token: previewToken }) });
  },
  recipeBatchSummary(): Promise<Envelope & { recetas_incompletas: number; recipe_ids: string[] }> {
    return request("/api/v1/biblioteca/recetas/completado-ia/resumen", { method: "GET" });
  },
  startRecipeBatch(): Promise<Envelope & Record<string, any>> {
    return request("/api/v1/biblioteca/recetas/completado-ia/iniciar", { method: "POST", body: "{}" });
  },
  getRecipeBatch(id: string): Promise<Envelope & Record<string, any>> {
    return request(`/api/v1/biblioteca/recetas/completado-ia/${encodeURIComponent(id)}/estado`, { method: "GET" });
  },
  advanceRecipeBatch(id: string): Promise<Envelope & Record<string, any>> {
    return request(`/api/v1/biblioteca/recetas/completado-ia/${encodeURIComponent(id)}/siguiente`, { method: "POST", body: JSON.stringify({ session_id: getAiSessionId() }) });
  },
  recipeBatchAction(id: string, operation: "cancelar" | "seleccion" | "preview" | "confirmar", body: Record<string, unknown> = {}): Promise<Envelope & Record<string, any>> {
    return request(`/api/v1/biblioteca/recetas/completado-ia/${encodeURIComponent(id)}/${operation}`, { method: "POST", body: JSON.stringify(body) });
  },

  getCompraDraft(id: string): Promise<CompraDraftResponse> {
    return request<CompraDraftResponse>(`/api/v1/compras/borradores/${encodeURIComponent(id)}`, { method: "GET" });
  },
  createManualCompraDraft(input: CompraDraftInput): Promise<CompraDraftResponse> {
    return request<CompraDraftResponse>("/api/v1/compras/borradores", { method: "POST", body: JSON.stringify(input) });
  },

  updateCompraDraft(id: string, input: CompraDraftInput): Promise<CompraDraftResponse> {
    return request<CompraDraftResponse>(`/api/v1/compras/borradores/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(input) });
  },

  confirmCompraDraft(id: string, actualizadoEn: string): Promise<CompraConfirmationResponse> {
    return request<CompraConfirmationResponse>(`/api/v1/compras/borradores/${encodeURIComponent(id)}/confirmar`, {
      method: "POST", body: JSON.stringify({ confirmacion: "CONFIRMAR_PEDIDO", usuario: "web", actualizado_en: actualizadoEn }),
    });
  },
  createPurchaseReception(orderId: string): Promise<PurchaseReceptionResponse> {
    return request<PurchaseReceptionResponse>(`/api/v1/compras/pedidos/${encodeURIComponent(orderId)}/recepciones`, { method: "POST", body: "{}" });
  },
  updatePurchaseReception(id: string, lineas: ReceptionLine[], header: Record<string, unknown>): Promise<PurchaseReceptionResponse> {
    return request<PurchaseReceptionResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify({ ...header, lineas }) });
  },
  confirmPurchaseReception(reception: PurchaseReception): Promise<PurchaseReceptionResponse> {
    return request<PurchaseReceptionResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(reception.id)}/confirmar`, { method: "POST", body: JSON.stringify({ confirmacion: "CONFIRMAR_RECEPCION", usuario: "web", actualizado_en: reception.actualizado_en, fecha: reception.fecha, referencia: reception.referencia, observaciones: reception.observaciones, lineas: reception.lineas }) });
  },
  attachPurchaseReceptionDocument(id: string, input: { nombre: string; tipo_mime: string; contenido_base64: string; usuario: string; referencia?: string }): Promise<ReceptionDocumentResponse> {
    return request<ReceptionDocumentResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(id)}/documento`, { method: "POST", body: JSON.stringify(input) });
  },
  getPurchaseReceptionDocument(id: string): Promise<ReceptionDocumentResponse> {
    return request<ReceptionDocumentResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(id)}/documento`, { method: "GET" });
  },
  removePurchaseReceptionDocument(id: string): Promise<PurchaseReceptionResponse> {
    return request<PurchaseReceptionResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(id)}/documento`, { method: "DELETE" });
  },
  analyzePurchaseReceptionDocument(id: string, textoOcr = ""): Promise<ReceptionExtractionResponse> {
    return request<ReceptionExtractionResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(id)}/documento/analizar`, { method: "POST", body: JSON.stringify({ texto_ocr: textoOcr }) });
  },
  applyPurchaseReceptionExtraction(id: string, extractionId: string, lines: ReceptionExtractionLine[]): Promise<ReceptionExtractionResponse> {
    return request<ReceptionExtractionResponse>(`/api/v1/compras/recepciones/${encodeURIComponent(id)}/extraccion/aplicar`, { method: "POST", body: JSON.stringify({ extraction_id: extractionId, lines }) });
  },

  getArticulos(query = ""): Promise<CatalogoResponse> {
    return request<CatalogoResponse>(`/api/v1/articulos${query}`, { method: "GET" });
  },

  getArticulo(id: string): Promise<ArticuloResponse> {
    return request<ArticuloResponse>(`/api/v1/articulos/${encodeURIComponent(id)}`, { method: "GET" });
  },
  proposeArticleDocumentation(id: string, culinaryContext: import("../types/articulos").ArticleCulinaryContext = {}): Promise<ArticleDocumentationResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/documentacion/propuesta`, { method: "POST", body: JSON.stringify({ culinary_context: culinaryContext, session_id: getAiSessionId() }) });
  },
  previewArticleDocumentation(id: string, selected: Record<string, unknown>): Promise<ArticleDocumentationResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/documentacion/preview`, { method: "POST", body: JSON.stringify({ selected }) });
  },
  confirmArticleDocumentation(id: string, selected: Record<string, unknown>, previewToken: string): Promise<ArticleDocumentationResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/documentacion/confirmar`, { method: "POST", body: JSON.stringify({ selected, preview_token: previewToken }) });
  },
  previewManualPrice(id: string, result: Record<string, unknown>): Promise<ManualPriceResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/precio-referencia-manual/preview`, { method: "POST", body: JSON.stringify({ result }) });
  },
  confirmManualPrice(id: string, result: Record<string, unknown>, previewToken: string): Promise<ManualPriceResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/precio-referencia-manual/confirmar`, { method: "POST", body: JSON.stringify({ result, preview_token: previewToken }) });
  },
  getArticlesWithoutPrice(): Promise<Envelope & { articulos: ArticuloSinPrecio[]; total: number; costes_derivados?: ArticuloCosteDerivado[]; total_costes_derivados?: number; coste_ia_usd: string }> {
    return request("/api/v1/articulos/sin-precio", { method: "GET" });
  },
  getReclassificationCandidates(): Promise<Envelope & { candidatos: ReclassificationCandidate[]; total: number; datos_reales_modificados: false }> {
    return request("/api/v1/articulos/reclasificacion/candidatos", { method: "GET" });
  },
  previewReclassification(rows: Array<{ article_id: string; tipo_entidad: string; elaboracion_id?: string | null }>): Promise<ReclassificationPreview> {
    return request("/api/v1/articulos/reclasificacion/preview", { method: "POST", body: JSON.stringify({ rows }) });
  },
  confirmReclassification(rows: Array<{ article_id: string; tipo_entidad: string; elaboracion_id?: string | null }>, previewToken: string): Promise<Envelope & { modificados: string[]; sin_cambios: string[]; idempotente: boolean; writes_logicos: number }> {
    return request("/api/v1/articulos/reclasificacion/confirmar", { method: "POST", body: JSON.stringify({ rows, preview_token: previewToken }) });
  },
  exportArticlesWithoutPrice(): Promise<Envelope & { texto: string; total: number; coste_ia_usd: string }> {
    return request("/api/v1/articulos/sin-precio/exportar", { method: "GET" });
  },
  previewImportedReferences(raw: string): Promise<ReferenciasImportPreview> {
    return request("/api/v1/articulos/referencias-importadas/preview", { method: "POST", body: JSON.stringify({ raw }) });
  },
  confirmImportedReferences(rows: ReferenciaImportPreviewRow[]): Promise<Envelope & { confirmadas: number; lectura_posterior_verificada: boolean; coste_ia_usd: string }> {
    return request("/api/v1/articulos/referencias-importadas/confirmar", { method: "POST", body: JSON.stringify({ rows }) });
  },
  previewWebPrice(id: string, result: PrecioReferencia): Promise<ManualPriceResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/precio-referencia-web/preview`, { method: "POST", body: JSON.stringify({ result }) });
  },
  confirmWebPrice(id: string, result: PrecioReferencia, previewToken: string): Promise<ManualPriceResponse> {
    return request(`/api/v1/articulos/${encodeURIComponent(id)}/precio-referencia-web/confirmar`, { method: "POST", body: JSON.stringify({ result, preview_token: previewToken }) });
  },
  updateArticulo(id: string, input: ArticuloUpdateInput): Promise<ArticuloResponse & { mensaje: string }> {
    return request<ArticuloResponse & { mensaje: string }>(`/api/v1/articulos/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify({ ...input, confirmacion: "ACTUALIZAR_ARTICULO_MAESTRO" }) });
  },

  getMenus(): Promise<MenusResponse> {
    return request<MenusResponse>("/api/v1/menus", { method: "GET" });
  },

  getMenu(id: string): Promise<MenuResponse> {
    return request<MenuResponse>(`/api/v1/menus/${encodeURIComponent(id)}`, { method: "GET" });
  },

  getMenuElaborations(): Promise<MenuElaborationsResponse> {
    return request<MenuElaborationsResponse>("/api/v1/menus/elaboraciones", { method: "GET" });
  },

  createMenu(input: MenuInput): Promise<MenuResponse> {
    return request<MenuResponse>("/api/v1/menus", { method: "POST", body: JSON.stringify(input) });
  },

  updateMenu(id: string, input: MenuInput): Promise<MenuResponse> {
    return request<MenuResponse>(`/api/v1/menus/${encodeURIComponent(id)}`, {
      method: "PATCH", body: JSON.stringify(input),
    });
  },

  archiveMenu(id: string, version: number): Promise<MenuResponse> {
    return request<MenuResponse>(`/api/v1/menus/${encodeURIComponent(id)}`, {
      method: "DELETE", body: JSON.stringify({ version }),
    });
  },

  getMenuNeeds(id: string): Promise<MenuNeedsResponse> {
    return request<MenuNeedsResponse>(`/api/v1/menus/${encodeURIComponent(id)}/necesidades`, { method: "GET" });
  },

  createMenuPurchaseProposal(id: string): Promise<MenuPurchaseProposalResponse> {
    return request<MenuPurchaseProposalResponse>(`/api/v1/menus/${encodeURIComponent(id)}/propuesta-compra`, { method: "POST" });
  },

  getMenuPurchaseProposal(menuId: string, proposalId: string): Promise<MenuPurchaseProposalResponse> {
    return request<MenuPurchaseProposalResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/propuesta-compra/${encodeURIComponent(proposalId)}`, { method: "GET" });
  },

  updateMenuPurchaseProposal(menuId: string, proposalId: string, input: Record<string, unknown>): Promise<MenuPurchaseProposalResponse> {
    return request<MenuPurchaseProposalResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/propuesta-compra/${encodeURIComponent(proposalId)}`, { method: "PATCH", body: JSON.stringify(input) });
  },

  createMenuDraftOrders(menuId: string, proposalId: string, version: number): Promise<MenuOrdersResponse> {
    return request<MenuOrdersResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/propuesta-compra/${encodeURIComponent(proposalId)}/crear-pedidos`, { method: "POST", body: JSON.stringify({ confirmacion: "CREAR_BORRADORES", usuario: "web", version }) });
  },

  createMenuProductionPlan(menuId: string): Promise<ProductionPlanResponse> {
    return request<ProductionPlanResponse>(`/api/v1/menus/${encodeURIComponent(menuId)}/plan-produccion`, { method: "POST", body: "{}" });
  },
  getProductionPlan(planId: string): Promise<ProductionPlanResponse> {
    return request<ProductionPlanResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}`, { method: "GET" });
  },
  createProductionPurchaseProposal(planId: string): Promise<ProductionProposalResponse> {
    return request<ProductionProposalResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}/propuesta-compra`, { method: "POST", body: "{}" });
  },
  getProductionStockReview(planId: string): Promise<ProductionStockReviewResponse> {
    return request<ProductionStockReviewResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}/stock-resolution`, { method: "GET" });
  },
  createProductionStockMovement(planId: string, input: StockMovementInput): Promise<StockMovementResponse> {
    return request<StockMovementResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}/stock-resolution/movement`, {
      method: "POST", body: JSON.stringify({ ...input, confirmacion: "REGISTRAR_STOCK_DESDE_PRODUCCION", usuario: "web" }),
    });
  },
  linkProductionIngredient(planId: string, input: { elaboration_id: string; ingredient_name: string; article_id: string }): Promise<ProductionStockReviewResponse> {
    return request<ProductionStockReviewResponse>(`/api/v1/produccion/planes/${encodeURIComponent(planId)}/stock-resolution/article`, { method: "POST", body: JSON.stringify({ ...input, confirmacion: "RELACIONAR_INGREDIENTE_ARTICULO" }) });
  },
  getBiblioteca(): Promise<BibliotecaResponse> {
    return request<BibliotecaResponse>("/api/v1/biblioteca", { method: "GET" });
  },

  getElaboraciones(query = ""): Promise<ElaboracionesResponse> {
    return request<ElaboracionesResponse>(`/api/v1/biblioteca/elaboraciones${query}`, { method: "GET" });
  },

  getElaboracion(id: string): Promise<ElaboracionResponse> {
    return request<ElaboracionResponse>(
      `/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}`,
      { method: "GET" },
    );
  },

  previewElaborationYield(id: string, input: RendimientoInput): Promise<RendimientoPreviewResponse> {
    return request<RendimientoPreviewResponse>(
      `/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/rendimiento/preview`,
      { method: "POST", body: JSON.stringify(input) },
    );
  },

  confirmElaborationYield(id: string, input: RendimientoInput, previewToken: string): Promise<RendimientoConfirmationResponse> {
    return request<RendimientoConfirmationResponse>(
      `/api/v1/biblioteca/elaboraciones/${encodeURIComponent(id)}/rendimiento/confirmar`,
      { method: "POST", body: JSON.stringify({ ...input, preview_token: previewToken }) },
    );
  },

  createBibliotecaImport(input: {
    nombre?: string;
    tipo_mime?: string;
    contenido_base64?: string;
    texto?: string;
    texto_pegado?: string;
    resolver_ambiguedades_ia?: boolean;
    analizar_documento_con_ia?: boolean;
    excluir_ap_antiguos?: boolean;
    hostai_import_package?: Record<string, unknown>;
    archivos?: Array<{
      nombre: string;
      tipo_mime: string;
      contenido_base64: string;
      texto?: string;
    }>;
  }): Promise<BibliotecaImportResponse> {
    return request<BibliotecaImportResponse>("/api/v1/biblioteca/importaciones", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  getBibliotecaImport(id: string): Promise<BibliotecaImportResponse> {
    return request<BibliotecaImportResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}`,
      { method: "GET" },
    );
  },

  getBibliotecaImportProposals(id: string): Promise<BibliotecaImportProposalsResponse> {
    return request<BibliotecaImportProposalsResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/propuestas`,
      { method: "GET" },
    );
  },

  getBibliotecaImportDraft(id: string): Promise<BibliotecaDraftResponse> {
    return request<BibliotecaDraftResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/borrador`,
      { method: "GET" },
    );
  },

  updateBibliotecaImportDraft(
    id: string,
    input: { draft_version: number; recipes: unknown[]; variant_decisions?: unknown[]; article_decisions?: unknown[] },
  ): Promise<BibliotecaDraftResponse> {
    return request<BibliotecaDraftResponse>(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/borrador`,
      { method: "PATCH", body: JSON.stringify(input) },
    );
  },

  confirmBibliotecaImport(
    id: string,
    input: { draft_version: number; usuario: string; confirmacion: "CONFIRMAR"; preview_fingerprint?: string },
  ): Promise<import("../types/biblioteca").BibliotecaImportConfirmationResponse> {
    return request(
      `/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/confirmar`,
      { method: "POST", body: JSON.stringify(input) },
    );
  },

  previewLegacyCanonicalization(id: string, legacyIds: string[]): Promise<LegacyCanonicalizationPreviewResponse> {
    return request(`/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/canonicalizacion-existentes/preview`, {
      method: "POST", body: JSON.stringify({ legacy_ids: legacyIds }),
    });
  },

  confirmLegacyCanonicalization(id: string, previewToken: string): Promise<LegacyCanonicalizationConfirmationResponse> {
    return request(`/api/v1/biblioteca/importaciones/${encodeURIComponent(id)}/canonicalizacion-existentes/confirmar`, {
      method: "POST", body: JSON.stringify({ preview_token: previewToken }),
    });
  },

  sendChatMessage(input: { mensaje: string; contexto?: Record<string, unknown>; action_id?: string; action_context_id?: string }): Promise<ChatResponse> {
    return request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        mensaje: input.mensaje,
        contexto: input.contexto || {},
        ...(input.action_id ? { action_id: input.action_id } : {}),
        ...(input.action_context_id ? { action_context_id: input.action_context_id } : {}),
      }),
    });
  },
};
