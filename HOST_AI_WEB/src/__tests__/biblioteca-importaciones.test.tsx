import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

const emptyImportListResponse = {
  ok: true,
  status: 200,
  json: async () => ({ ok: true, importaciones: [], total: 0, datos_reales_modificados: false }),
} as Response;

function isImportListRequest(input: RequestInfo | URL, init?: RequestInit): boolean {
  const url = String(input);
  return (init?.method || "GET") === "GET" && /\/api\/v1\/biblioteca\/importaciones$/.test(url);
}

function spyOnImportFetch(listResponse: Response = emptyImportListResponse) {
  const businessFetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => emptyImportListResponse);
  const routedFetch = new Proxy(businessFetch, {
    apply(target, thisArg, args: [RequestInfo | URL, RequestInit?]) {
      if (isImportListRequest(args[0], args[1])) return Promise.resolve(listResponse);
      return Reflect.apply(target, thisArg, args);
    },
  });
  vi.stubGlobal("fetch", routedFetch as typeof fetch);
  return businessFetch;
}

const response = {
  ok: true,
  version: "1.0",
  api_version: "1.0",
  request_id: "IMP-REQ-1",
  modo_seguro: true,
  datos_reales_modificados: false,
  importacion: {
    documento: {
      id: "IMPWEB-1",
      nombre: "receta.txt",
      tipo_mime: "text/plain",
      tamano: 42,
      origen: "TEXTO",
      clasificacion: {
        tipo: "RECETA",
        confianza: { valor: 0.82, explicacion: "Marcadores detectados: receta, ingredientes." },
        evidencias: ["Marcadores culinarios detectados."],
        advertencias: [],
      },
      secciones: [],
      entidades: [{
        id: "ENT-REC-001",
        kind: "RECETA",
        name: "Salsa verde",
        fields: {
          ingredientes_estructurados: [{
            nombre_original: "Perejil",
            cantidad_texto: "100",
            unidad: "g",
            estado_relacion: "relacionado",
            articulo_id: "M.P-PER",
          }],
          pasos: ["Triturar."],
        },
        confidence: { valor: 0.78, explicacion: "Estructura Word." },
      }, {
        id: "ENT-REC-002",
        kind: "RECETA",
        name: "Salsa roja",
        fields: { ingredientes_estructurados: [], pasos: [] },
        confidence: { valor: 0.75, explicacion: "Estructura Word." },
      }],
      advertencias: [],
      contenido_almacenado: false,
    },
    resumen: {
      secciones: 4, entidades: 3, propuestas: 1, incidencias: 0,
      recetas_detectadas: 2, ingredientes_detectados: 1,
      ingredientes_relacionados: 1, coincidencias_dudosas: 0,
      ingredientes_sin_relacionar: 0, ingredientes_nuevos: 0,
      duplicados_detectados: 0, estado: "PENDIENTE_REVISION",
    },
    propuestas: [{
      id: "IMPWEB-1-PROP-001",
      tipo: "CREAR_RECETA",
      estado: "PENDIENTE_REVISION",
      confianza: { valor: 0.75, explicacion: "Receta detectada." },
      explicacion: "Una única operación conceptual crea la ficha culinaria canónica; no son dos entidades independientes.",
      titulo: "Crear elaboración/receta canónica: Salsa verde",
      origen: { importacion_id: "IMPWEB-1", nombre: "receta.txt", tipo: "TEXTO" },
      entidad_origen: "ENT-REC-001",
      bloques_origen: ["bloque:0"],
      advertencias: [],
      conflictos: [],
      datos_propuestos: {},
      persistida: false,
    }],
    solo_previsualizacion: true,
    confirmacion_disponible: false,
    limitaciones: ["Las imágenes incrustadas no se interpretan en esta fase."],
    borrador: {
      id: "IMPWEB-1-DRAFT",
      document_id: "IMPWEB-1",
      status: "PENDIENTE_REVISION",
      classification: "RECETA",
      confidence: 0.82,
      version: 1,
      draft_version: 1,
      created_at: "2026-07-30T10:00:00Z",
      updated_at: "2026-07-30T10:00:00Z",
      persisted: false,
      confirmation_available: false,
      warnings: [],
      conflicts: [],
      recipes: [{
        id: "REC-WORD-001",
        title: "Salsa verde",
        entity_type: "PRINCIPAL",
        parent_recipe_id: null,
        order: 1,
        description: "",
        ingredients: [{
          id: "ING-DRAFT-001-001",
          original_text: "2 3 l nata",
          quantity_raw: "2 3",
          quantity: null,
          unit_raw: "l",
          unit: "l",
          name_raw: "nata",
          normalized_name: "nata",
          observations: "",
          article_id: null,
          article_candidates: [{
            articulo_id: "ART-NATA",
            codigo: "ART-NATA",
            nombre: "Nata culinaria",
            categoria: "Lácteos",
            unidad: "l",
            precio: 4.5,
            nivel_coincidencia: 0.7,
            motivo: "Nombre parecido; requiere elección del usuario.",
            unidad_compatible: true,
          }],
          relation_status: "REVISAR_COINCIDENCIA",
          confidence: 0.7,
          validation_errors: [{
            code: "CANTIDAD_AMBIGUA",
            level: "ADVERTENCIA",
            message: "«2 3» puede representar una fracción, un decimal o un rango.",
            field: "quantity",
          }],
        }],
        procedure: ["Triturar."],
        yield_value: null,
        servings: null,
        times: {},
        temperatures: [],
        notes: "",
        source_blocks: ["bloque:0"],
        confidence: 0.75,
        proposed_action: "CREAR_RECETA",
        duplicate_candidates: [],
        validation_errors: [],
      }, {
        id: "REC-WORD-002",
        title: "Salsa roja",
        entity_type: "PRINCIPAL",
        parent_recipe_id: null,
        order: 2,
        description: "",
        ingredients: [],
        procedure: [],
        yield_value: null,
        servings: null,
        times: {},
        temperatures: [],
        notes: "",
        source_blocks: ["bloque:4"],
        confidence: 0.75,
        proposed_action: "CREAR_RECETA",
        duplicate_candidates: [],
        validation_errors: [],
      }],
    },
  },
};

describe("Importador Inteligente de Biblioteca", () => {
  beforeEach(() => { sessionStorage.clear(); localStorage.clear(); });
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    sessionStorage.clear();
    localStorage.clear();
  });

  it("rehidrata desde backend la importaciÃ³n activa y sus decisiones tras remount", async () => {
    const fixture: any = structuredClone(response);
    fixture.importacion.borrador.recipes[0].id = "REC-DEC-1";
    fixture.importacion.borrador.recipes[0].identity_decision = "RECETA_NUEVA";
    fixture.importacion.borrador.recipes[0].proposed_action = "CREAR_RECETA";
    fixture.importacion.borrador.variant_decisions = [{ group_id: "VG-REFRESH", decision: "RECETAS_DIFERENTES" }];
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 1, ya_canonicas: 0, ya_conocidas_legacy: 0, nuevas_reales: 1, posibles_variantes: 2, requiere_revision: 0,
        grupos: { ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [], posibles_variantes: [],
          requieren_revision: [{ id: "REC-DEC-1", nombre: "Salsa verde" }] } },
      articulos: { total: 0, ya_existentes: 0, nuevos_reales: 0, requieren_revision: 0 },
      variantes: { apariciones: 2, grupos: 1, duplicados_exactos_colapsados: 0, grupos_requieren_decision: 0,
        items: [{ id: "VG-REFRESH", nombre: "Patatas Bravas", tipo_entidad_propuesto: "RECETA_O_ELABORACION",
          apariciones: 2, versiones_estructurales: 2, duplicados_exactos: 0, requiere_decision: false,
          versiones: [{ id: "A", nombre: "A", ingredientes: [], origenes: [], apariciones: 1 },
            { id: "B", nombre: "B", ingredientes: [], origenes: [], apariciones: 1 }], diferencias: [] }] },
    };
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => fixture } as Response);

    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Documento recibido")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/importaciones/IMPWEB-1"), expect.objectContaining({ method: "GET" }));
    const decisionCounter = screen.getByText(/Necesitan tu decisi/).closest("div");
    expect(decisionCounter).toHaveTextContent(/^0/);
    fireEvent.click(screen.getByRole("button", { name: "Revisar decisiones" }));
    expect(screen.getByRole("button", { name: "Es una receta nueva" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Volver al resumen" }));
    fireEvent.click(screen.getByRole("button", { name: "Revisar variantes" }));
    expect(screen.getByRole("button", { name: "Son recetas diferentes" })).toHaveAttribute("aria-pressed", "true");
  });

  it("descubre una importación POST-FIX durable sin sessionStorage ni localStorage", async () => {
    const fixture: any = structuredClone(response);
    fixture.importacion.schema_version = 2;
    fixture.importacion.created_at = "2026-09-05T11:10:43Z";
    fixture.importacion.updated_at = "2026-09-05T11:12:33Z";
    fixture.importacion.borrador.recipes[0].procedure = [];
    fixture.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    fixture.importacion.completado_recetas_activo = {
      batch_id: "RECIPE-BATCH-COMPLETADO", import_id: "IMPWEB-1", estado: "COMPLETADO",
      modo_generacion: "ARCHIVO_EXTERNO", recipe_ids: ["REC601-A"], resultados: [],
      selecciones: { "REC601-A": { elaboracion: "Mezclar." } }, selecciones_individuales: {},
      preview: { fingerprint: "preview-completado", recetas_afectadas: 1, cambios_a_aplicar: 1, items: [] },
      cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }],
      progreso: { total: 34, analizadas: 34, exitosas: 34, fallidas: 0, pendientes: 0, con_propuestas: 34, necesitan_usuario: 0, ya_completas: 0, propuestas: 392 },
    };
    fixture.importacion.created_at = "2026-09-01T10:00:00Z";
    fixture.importacion.updated_at = "2026-09-01T10:05:00Z";
    const listResponse = {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "IMP-LIST-1",
        modo_seguro: true,
        datos_reales_modificados: false,
        total: 1,
        importaciones: [{
          importacion_id: "IMPWEB-1", estado: "PENDIENTE_REVISION", schema_version: 2,
          created_at: fixture.importacion.created_at, updated_at: fixture.importacion.updated_at,
          post_persistence: true,
        }],
      }),
    } as Response;
    const fetchMock = spyOnImportFetch(listResponse).mockResolvedValue({
      ok: true, status: 200, json: async () => fixture,
    } as Response);

    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    expect(await screen.findByText("Documento recibido")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/biblioteca/importaciones/IMPWEB-1"),
      expect.objectContaining({ method: "GET" }),
    );
    expect(localStorage.getItem("hostai.active_import_session_id")).toBe("IMPWEB-1");
    const cta = await screen.findByRole("button", { name: "Revisar propuestas externas · 34 recetas" });
    fireEvent.click(cta);
    expect(screen.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toHaveTextContent("Propuestas generadas: 392");
  });

  it("limpia un token expirado sin inventar un borrador", async () => {
    sessionStorage.setItem("hostai.active_import_session_id", "IMP-EXPIRADA");
    spyOnImportFetch().mockResolvedValue({
      ok: false, status: 404, json: async () => ({ ...response, ok: false, error: { code: "import_not_found", message: "No encontrada" } }),
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    expect(await screen.findByText(/No hay una importaci/)).toBeInTheDocument();
    expect(sessionStorage.getItem("hostai.active_import_session_id")).toBeNull();
    expect(screen.queryByText("ImportaciÃ³n analizada")).not.toBeInTheDocument();
  });

  it("una importaciÃ³n nueva sustituye la referencia activa anterior", async () => {
    let sequence = 0;
    spyOnImportFetch().mockImplementation(async () => {
      sequence += 1;
      const fixture: any = structuredClone(response);
      fixture.importacion.documento.id = `IMP-NUEVA-${sequence}`;
      fixture.importacion.borrador.document_id = fixture.importacion.documento.id;
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const first = new File(["uno"], "uno.xlsx");
    Object.defineProperty(first, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [first] } });
    await waitFor(() => expect(sessionStorage.getItem("hostai.active_import_session_id")).toBe("IMP-NUEVA-1"));
    const second = new File(["dos"], "dos.xlsx");
    Object.defineProperty(second, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [second] } });
    await waitFor(() => expect(sessionStorage.getItem("hostai.active_import_session_id")).toBe("IMP-NUEVA-2"));
    fireEvent.click(screen.getByRole("button", { name: /Descartar importaci/ }));
    expect(sessionStorage.getItem("hostai.active_import_session_id")).toBeNull();
  });

  it("muestra artículos agrupados, guarda la decisión en draft y la recupera tras refresh", async () => {
    const fixture: any = structuredClone(response);
    const article = {
      id: "ART-DRAFT-001", nombre: "A.P CROQUETA DE SETAS.", accion: "REQUIERE_REVISION", estado: "PENDIENTE",
      tipo_entidad: "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE", tipo_semantico: "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE",
      motivo: "La clasificación semántica no demuestra que sea un artículo comprado.", candidatos: [],
      origen: { sheet: "Listado", row: 7 }, evidencia_tipo: { reason: "prefijo A.P" },
    };
    fixture.importacion.borrador.catalogo = { articulos: [article], proveedores: [], relaciones: [] };
    fixture.importacion.resumen.ingredientes_detectados = 229;
    fixture.importacion.resumen.ingredientes_relacionados = 224;
    fixture.importacion.borrador.article_decisions = [{ article_draft_id: article.id, decision: "PENDIENTE", article_id: null }];
    fixture.importacion.preview_global = {
      proveedores: { crear: [], reutilizar: [], requiere_revision: [], ignorar: [] },
      articulos: { crear: [], reutilizar: [], requiere_revision: [article], ignorar: [] },
      elaboraciones: { crear_nueva: [], reutilizar_existente: [], requiere_revision: [] },
      relaciones: { crear: [], reutilizar: [], requiere_revision: [], ignorar: [] },
      ignorados: [], errores: [], solo_previsualizacion: true,
      contadores: { proveedores_nuevos: 0, proveedores_reutilizados: 0, articulos_nuevos: 0,
        articulos_reutilizados: 0, articulos_requieren_revision: 1, recetas_elaboraciones: 0,
        relaciones: 0, pendientes: 1 },
    };
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 0, ya_canonicas: 0, ya_conocidas_legacy: 0, nuevas_reales: 0, posibles_variantes: 0, requieren_revision: 0,
        grupos: { ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [], posibles_variantes: [], requieren_revision: [] } },
      articulos: { total: 1, ya_existentes: 0, nuevos_reales: 0, requieren_revision: 1 },
    };
    let serverDraft = structuredClone(fixture.importacion.borrador);
    spyOnImportFetch().mockImplementation(async (_url, init) => {
      if (init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        serverDraft = { ...serverDraft, article_decisions: body.article_decisions,
          version: serverDraft.version + 1, draft_version: serverDraft.draft_version + 1 };
        const pending = serverDraft.article_decisions.filter((item: any) => item.decision === "PENDIENTE").length;
        const elaborations = serverDraft.article_decisions.filter((item: any) => item.decision === "ES_ELABORACION").length;
        const canonicalPreview = structuredClone(fixture.importacion.preview_global);
        canonicalPreview.articulos.requiere_revision = [article].filter((item) => serverDraft.article_decisions.some(
          (decision: any) => decision.article_draft_id === item.id && decision.decision === "PENDIENTE",
        ));
        canonicalPreview.articulos.es_elaboracion = [article].filter((item) => serverDraft.article_decisions.some(
          (decision: any) => decision.article_draft_id === item.id && decision.decision === "ES_ELABORACION",
        ));
        canonicalPreview.contadores.articulos_requieren_revision = pending;
        canonicalPreview.contadores.articulos_reclasificados_elaboracion = elaborations;
        canonicalPreview.contadores.pendientes = pending;
        canonicalPreview.contadores.pendientes_desglose = { identidad_receta: 0, articulo: pending, relacion: 0, proveedor: 0, documentacion: 0, otro: 0 };
        canonicalPreview.draft_version = serverDraft.draft_version;
        canonicalPreview.draft_fingerprint = `fingerprint-${serverDraft.draft_version}`;
        return { ok: true, status: 200, json: async () => ({ ...fixture, borrador: serverDraft, preview_global: canonicalPreview }) } as Response;
      }
      fixture.importacion.borrador = serverDraft;
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    const view = render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat.json");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Revisar artículos · 1" }));
    const review = screen.getByRole("region", { name: "Revisar artículos" });
    expect(review).toHaveTextContent("No es un artículo de compra · 1 pendientes / 1");
    expect(review).toHaveTextContent("A.P CROQUETA DE SETAS.");
    expect(review).toHaveTextContent("La clasificación semántica no demuestra");
    fireEvent.click(screen.getByText("Ver detalles técnicos"));
    expect(screen.getByText("Ingredientes detectados").parentElement).toHaveTextContent("229");
    expect(screen.getByText("Ingredientes relacionados").parentElement).toHaveTextContent("224");
    fireEvent.click(within(review).getByRole("button", { name: "Es elaboración/receta" }));
    await waitFor(() => expect(within(review).getByRole("status")).toHaveTextContent("0"));
    expect(within(review).queryByRole("checkbox", { name: "Seleccionar A.P CROQUETA DE SETAS." })).not.toBeInTheDocument();
    expect(review).toHaveTextContent("Clasificados como elaboración/receta · 1");
    expect(review).not.toHaveTextContent("Eliminados de esta importación · 1");
    view.unmount();
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Documento recibido")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Revisar artículos · 0" }));
    const rehydrated = screen.getByRole("region", { name: "Revisar artículos" });
    expect(rehydrated).toHaveTextContent("Clasificados como elaboración/receta · 1");
    expect(within(rehydrated).queryByRole("checkbox", { name: "Seleccionar A.P CROQUETA DE SETAS." })).not.toBeInTheDocument();
    fireEvent.click(within(rehydrated).getByRole("button", { name: "Restaurar a pendiente" }));
    await waitFor(() => expect(rehydrated).toHaveTextContent("1 requieren revisión"));
    expect(screen.queryByText(/^\s*-\s*$/)).not.toBeInTheDocument();
  });

  it("elimina tres registros seleccionados, conserva dos pendientes y persiste tras refresh", async () => {
    const fixture: any = structuredClone(response);
    const articles = Array.from({ length: 5 }, (_, index) => ({
      id: `ART-DRAFT-${index + 1}`, nombre: `A.P Registro ${index + 1}`, accion: "REQUIERE_REVISION", estado: "PENDIENTE",
      tipo_entidad: "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE", tipo_semantico: "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE",
      motivo: "La clasificación semántica no demuestra que sea un artículo comprado.", candidatos: [],
    }));
    fixture.importacion.borrador.catalogo = { articulos: articles, proveedores: [], relaciones: [] };
    fixture.importacion.borrador.article_decisions = articles.map((item) => ({ article_draft_id: item.id, decision: "PENDIENTE", article_id: null }));
    fixture.importacion.preview_global = {
      proveedores: { crear: [], reutilizar: [], requiere_revision: [], ignorar: [] },
      articulos: { crear: [], reutilizar: [], requiere_revision: articles, ignorar: [] },
      elaboraciones: { crear_nueva: [], reutilizar_existente: [], requiere_revision: [] },
      relaciones: { crear: [], reutilizar: [], requiere_revision: [], ignorar: [] }, ignorados: [], errores: [], solo_previsualizacion: true,
      contadores: { proveedores_nuevos: 0, proveedores_reutilizados: 0, articulos_nuevos: 0, articulos_reutilizados: 0,
        articulos_requieren_revision: 5, articulos_ignorados: 0, recetas_elaboraciones: 0, relaciones: 0, pendientes: 5 },
    };
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 0, ya_canonicas: 0, ya_conocidas_legacy: 0, nuevas_reales: 0, posibles_variantes: 0, requieren_revision: 0,
        grupos: { ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [], posibles_variantes: [], requieren_revision: [] } },
      articulos: { total: 5, ya_existentes: 0, nuevos_reales: 0, requieren_revision: 5 },
    };
    let serverDraft = structuredClone(fixture.importacion.borrador);
    spyOnImportFetch().mockImplementation(async (_url, init) => {
      if (init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        serverDraft = { ...serverDraft, article_decisions: body.article_decisions,
          version: serverDraft.version + 1, draft_version: serverDraft.draft_version + 1 };
        const pending = serverDraft.article_decisions.filter((item: any) => item.decision === "PENDIENTE").length;
        const elaborations = serverDraft.article_decisions.filter((item: any) => item.decision === "ES_ELABORACION").length;
        const canonicalPreview = structuredClone(fixture.importacion.preview_global);
        canonicalPreview.articulos.requiere_revision = articles.filter((item) => serverDraft.article_decisions.some(
          (decision: any) => decision.article_draft_id === item.id && decision.decision === "PENDIENTE",
        ));
        canonicalPreview.articulos.es_elaboracion = articles.filter((item) => serverDraft.article_decisions.some(
          (decision: any) => decision.article_draft_id === item.id && decision.decision === "ES_ELABORACION",
        ));
        canonicalPreview.contadores.articulos_requieren_revision = pending;
        canonicalPreview.contadores.articulos_reclasificados_elaboracion = elaborations;
        canonicalPreview.contadores.pendientes = pending;
        canonicalPreview.contadores.pendientes_desglose = { identidad_receta: 0, articulo: pending, relacion: 0, proveedor: 0, documentacion: 0, otro: 0 };
        canonicalPreview.draft_version = serverDraft.draft_version;
        canonicalPreview.draft_fingerprint = `fingerprint-${serverDraft.draft_version}`;
        return { ok: true, status: 200, json: async () => ({ ...fixture, borrador: serverDraft, preview_global: canonicalPreview }) } as Response;
      }
      fixture.importacion.borrador = serverDraft;
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    const view = render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat.json");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Revisar artículos · 5" }));
    for (const index of [1, 2, 3]) fireEvent.click(screen.getByRole("checkbox", { name: `Seleccionar A.P Registro ${index}` }));
    fireEvent.click(screen.getByRole("button", { name: "Eliminar seleccionados · 3" }));
    const activeReview = screen.getByRole("region", { name: "Revisar artículos" });
    await waitFor(() => expect(activeReview).toHaveTextContent("2 requieren revisión"));
    for (const index of [1, 2, 3]) expect(within(activeReview).queryByRole("checkbox", { name: `Seleccionar A.P Registro ${index}` })).not.toBeInTheDocument();
    expect(activeReview).toHaveTextContent("Eliminados de esta importación · 3");
    fireEvent.click(within(activeReview).getByRole("checkbox", { name: "Seleccionar todos los visibles" }));
    expect(within(activeReview).getByRole("checkbox", { name: "Seleccionar A.P Registro 4" })).toBeChecked();
    expect(within(activeReview).getByRole("checkbox", { name: "Seleccionar A.P Registro 5" })).toBeChecked();
    for (const index of [1, 2, 3]) expect(within(activeReview).getByRole("checkbox", { name: `Seleccionar eliminado A.P Registro ${index}` })).not.toBeChecked();
    expect(serverDraft.article_decisions.filter((item: any) => item.decision === "IGNORAR")).toHaveLength(3);
    view.unmount();
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Revisar artículos · 2" }));
    const restored = screen.getByRole("region", { name: "Revisar artículos" });
    expect(restored).toHaveTextContent("2 requieren revisión");
    expect(restored).toHaveTextContent("Eliminados de esta importación · 3");
    for (const index of [1, 2, 3]) expect(within(restored).queryByRole("checkbox", { name: `Seleccionar A.P Registro ${index}` })).not.toBeInTheDocument();
    fireEvent.click(within(restored).getByRole("checkbox", { name: "Seleccionar todos los eliminados" }));
    fireEvent.click(within(restored).getByRole("button", { name: "Restaurar seleccionados · 3" }));
    await waitFor(() => expect(restored).toHaveTextContent("5 requieren revisión"));
    expect(restored).not.toHaveTextContent("Eliminados de esta importación");
    fireEvent.click(within(restored).getByRole("checkbox", { name: "Seleccionar todos los visibles" }));
    fireEvent.click(within(restored).getByRole("button", { name: "Marcar seleccionados como elaboración/receta · 5" }));
    await waitFor(() => expect(restored).toHaveTextContent("0 requieren revisión"));
    expect(restored).toHaveTextContent("Clasificados como elaboración/receta · 5");
    expect(within(restored).getByRole("button", { name: "Marcar seleccionados como elaboración/receta · 0" })).toBeDisabled();
    fireEvent.click(within(restored).getByRole("button", { name: "Volver al resumen" }));
    fireEvent.click(screen.getByText("Ver detalles técnicos"));
    const technicalPreview = screen.getByRole("region", { name: "Preview global de importación" });
    expect(technicalPreview).toHaveTextContent("Clasificados como elaboración/receta5");
    expect(technicalPreview).toHaveTextContent("Pendientes bloqueantes totales0");
  });

  it("sube, clasifica y muestra propuestas sin ofrecer escritura", async () => {
    spyOnImportFetch().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => response,
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Importador Inteligente" })).toBeInTheDocument();
    const file = new File(["Receta\nIngredientes\nPerejil"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta\nIngredientes\nPerejil").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });

    expect(await screen.findByText("Documento recibido")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Ver detalles técnicos"));
    expect(screen.getByText("RECETA")).toBeInTheDocument();
    expect(screen.getByText(/Crear elaboración\/receta canónica: Salsa verde/)).toBeInTheDocument();
    expect(screen.queryByText("Crear elaboración: Salsa verde")).not.toBeInTheDocument();
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    expect(screen.queryByText(/Lector Word pendiente/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Revisar pendientes" }));
    expect(screen.getByRole("heading", { name: "Revisar pendientes" })).toBeInTheDocument();
    expect(screen.getAllByText("Salsa verde").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Salsa roja").length).toBeGreaterThan(0);
    expect(screen.getByText(/guardar este borrador no aplica ninguna propuesta/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Título de la sección"), {
      target: { value: "Salsa verde revisada" },
    });
    fireEvent.change(screen.getByLabelText("Tipo culinario"), {
      target: { value: "SUBELABORACION" },
    });
    fireEvent.change(screen.getByLabelText("Elaboración principal"), {
      target: { value: "REC-WORD-002" },
    });
    fireEvent.change(screen.getByLabelText("Cantidad nata"), {
      target: { value: "2,3" },
    });
    fireEvent.change(screen.getByLabelText("Relación nata"), {
      target: { value: "ART-NATA" },
    });
    expect(screen.queryByText(/puede representar una fracción/)).not.toBeInTheDocument();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones",
      expect.objectContaining({ method: "POST" }),
    ));
    const request = vi.mocked(global.fetch).mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).toMatchObject({
      archivos: [{ nombre: "receta.txt", tipo_mime: "text/plain" }],
    });
  });

  it("guarda el borrador versionado sin aplicar propuestas", async () => {
    spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => response } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          ...response,
          importacion_id: "IMPWEB-1",
          borrador: { ...response.importacion.borrador, version: 2, draft_version: 2 },
          datos_reales_modificados: false,
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Receta"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByRole("button", { name: "Revisar pendientes" }));
    fireEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));
    expect(await screen.findByText(/Borrador guardado/)).toBeInTheDocument();
    expect(global.fetch).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones/IMPWEB-1/borrador",
      expect.objectContaining({ method: "PATCH" }),
    );
    expect(screen.getByRole("button", { name: "Confirmar importación" })).toBeDisabled();
  });

  it("añade ingredientes a una receta vacía, permite varios y elimina uno", async () => {
    spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => response } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          ...response,
          importacion_id: "IMPWEB-1",
          borrador: { ...response.importacion.borrador, version: 2, draft_version: 2 },
          datos_reales_modificados: false,
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Receta"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByRole("button", { name: "Revisar pendientes" }));
    fireEvent.click(screen.getByRole("button", { name: /Salsa roja.*0 ingredientes/ }));
    expect(screen.getByText(/No hay ingredientes/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Añadir ingrediente" }));
    fireEvent.click(screen.getByRole("button", { name: "Añadir ingrediente" }));
    const names = screen.getAllByLabelText(/^Ingrediente/);
    const quantities = screen.getAllByLabelText(/^Cantidad/);
    fireEvent.change(names[0], { target: { value: "Naranja" } });
    fireEvent.change(quantities[0], { target: { value: "2" } });
    fireEvent.change(names[1], { target: { value: "Fondo" } });
    fireEvent.change(quantities[1], { target: { value: "0,5" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Eliminar ingrediente" })[1]);
    expect(screen.getByText(/Guarda el borrador revisado antes de confirmar/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(/Guarda el borrador revisado antes de confirmar/)).not.toBeInTheDocument();
    const request = vi.mocked(global.fetch).mock.calls[1][1] as RequestInit;
    const body = JSON.parse(String(request.body));
    const salsaRoja = body.recipes.find((recipe: { id: string }) => recipe.id === "REC-WORD-002");
    expect(salsaRoja.ingredients).toHaveLength(1);
    expect(salsaRoja.ingredients[0]).toMatchObject({
      name_raw: "Naranja",
      quantity_raw: "2",
      relation_status: "SIN_RELACIONAR",
    });
  });

  it("muestra bloqueos con receta y campo, permite enfocarlos y actualiza al guardar", async () => {
    const blocked: any = structuredClone(response);
    const recipe = blocked.importacion.borrador.recipes[0];
    const ingredient = recipe.ingredients[0];
    ingredient.validation_errors = [{
      code: "CANTIDAD_INVALIDA",
      level: "ERROR",
      message: "No se reconoce la cantidad «desconocida».",
      field: "quantity",
    }];
    recipe.validation_errors = [{
      code: "PROCEDIMIENTO_VACIO",
      level: "ERROR",
      message: "El procedimiento es obligatorio antes de confirmar.",
      field: "procedure",
    }];
    blocked.importacion.borrador.validation = {
      valid: false,
      blocking_errors: [{
        code: "CANTIDAD_INVALIDA",
        level: "BLOQUEANTE",
        recipe_id: recipe.id,
        recipe_title: recipe.title,
        recipe_index: 0,
        ingredient_id: ingredient.id,
        ingredient_index: 0,
        field: "quantity",
        message: "No se reconoce la cantidad «desconocida».",
      }],
      warnings: [{
        code: "ARTICULO_PENDIENTE",
        level: "ADVERTENCIA",
        recipe_id: recipe.id,
        recipe_title: recipe.title,
        recipe_index: 0,
        ingredient_id: ingredient.id,
        ingredient_index: 0,
        field: "article_id",
        message: "La coincidencia de artículo sigue pendiente.",
      }],
    };
    const corrected: any = structuredClone(blocked);
    corrected.importacion.borrador.version = 2;
    corrected.importacion.borrador.draft_version = 2;
    corrected.importacion.borrador.validation = {
      valid: true, blocking_errors: [], warnings: [],
    };
    corrected.importacion.borrador.recipes[0].validation_errors = [];
    corrected.importacion.borrador.recipes[0].ingredients[0].validation_errors = [];

    spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => blocked } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          ...corrected,
          borrador: corrected.importacion.borrador,
          datos_reales_modificados: false,
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Receta"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByRole("button", { name: "Revisar pendientes" }));
    fireEvent.click(screen.getByText("Decisiones obligatorias · 1"));
    fireEvent.click(screen.getByText("Otras revisiones · 1"));
    expect(screen.getAllByText(/No se reconoce la cantidad/).length).toBeGreaterThan(0);
    expect(screen.getByText(/La coincidencia de artículo sigue pendiente/)).toBeInTheDocument();
    const quantityIssue = screen.getAllByText(/No se reconoce la cantidad/)
      .find((element) => element.closest("li"))?.closest("li");
    fireEvent.click(within(quantityIssue as HTMLElement).getByRole("button", { name: "Revisar" }));
    await waitFor(() => expect(screen.getByLabelText("Cantidad nata")).toHaveFocus());
    fireEvent.change(screen.getByLabelText("Cantidad nata"), { target: { value: "2,3" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));

    await waitFor(() => expect(
      screen.queryByText("Decisiones obligatorias · 1"),
    ).not.toBeInTheDocument());
  });

  it("exige aceptación explícita y confirma mediante la API pública", async () => {
    const safe: any = structuredClone(response);
    safe.importacion.resumen.coincidencias_dudosas = 0;
    safe.importacion.borrador.recipes[0].ingredients[0].relation_status = "RELACIONADO";
    safe.importacion.borrador.validation = { valid: true, blocking_errors: [], warnings: [] };
    spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => safe } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          ...response,
          importacion_id: "IMPWEB-1",
          estado: "CONFIRMADA",
          resultado: {
            estado: "COMPLETADA",
            acciones: [{ tipo: "CREAR_RECETA", id: "REC601-000001" }],
            entidades: [{ tipo: "RECETA", id: "REC601-000001", nombre: "Salsa" }],
            errores: [],
            rollback: false,
          },
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Receta"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByRole("button", { name: "Importar lo seguro" }));
    await screen.findByText("Confirmación final");
    const button = screen.getByRole("button", { name: "Confirmar importación" });
    expect(button).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", {
      name: "He revisado el resumen y autorizo aplicar estos cambios.",
    }));
    fireEvent.click(button);
    expect(await screen.findByText("Importación completada")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones/IMPWEB-1/confirmar",
      expect.objectContaining({ method: "POST" }),
    );
    expect(sessionStorage.getItem("hostai.active_import_session_id")).toBeNull();
  });

  it("habilita un único Confirm cuando los 13 pendientes quedan excluidos", async () => {
    const safeSubset: any = structuredClone(response);
    safeSubset.importacion.documento.id = "IMPWEB-SAFE-SUBSET";
    safeSubset.importacion.borrador.document_id = "IMPWEB-SAFE-SUBSET";
    safeSubset.importacion.borrador.version = 7;
    safeSubset.importacion.borrador.draft_version = 7;
    safeSubset.importacion.borrador.validation = {
      valid: false,
      blocking_errors: [{
        code: "RECETA_REQUIERE_REVISION", level: "BLOQUEANTE",
        recipe_id: "REC-PENDIENTE", recipe_title: "Crema catalana.",
        field: "proposed_action", message: "Pendiente excluida.",
      }],
      warnings: [],
    };
    safeSubset.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {},
      menus: { crear: Array.from({ length: 5 }, (_, index) => ({ nombre: `Menú ${index}`, accion: "CREAR" })), reutilizar: [], actualizar: [], pendientes: Array.from({ length: 9 }, (_, index) => ({ nombre: `Menú pendiente ${index}`, accion: "PENDIENTE" })), no_soportados: [] },
      ignorados: [], errores: [], solo_previsualizacion: true,
      draft_version: 7, draft_fingerprint: "fingerprint-safe-subset",
      contadores: {
        proveedores_nuevos: 0, proveedores_reutilizados: 0,
        articulos_nuevos: 0, articulos_reutilizados: 298,
        articulos_reclasificados_elaboracion: 13, articulos_requieren_revision: 3,
        recetas_elaboraciones: 46, recetas_nuevas: 25, recetas_reutilizadas: 20,
        recetas_requieren_revision: 1, relaciones: 0, pendientes: 13,
        menus_recibidos: 14, menus_crear: 5, menus_reutilizar: 0, menus_pendientes: 9,
        pendientes_desglose: { identidad_receta: 1, articulo: 3, relacion: 0, proveedor: 0, documentacion: 0, menu: 9, otro: 0 },
      },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => safeSubset } as Response)
      .mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({
          ...response,
          importacion_id: "IMPWEB-SAFE-SUBSET", estado: "CONFIRMADA",
          resultado: { estado: "COMPLETADA", acciones: [], entidades: [], errores: [], rollback: false },
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat-limpio.json", { type: "application/json" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByRole("button", { name: "Importar lo seguro" }));
    const checkbox = screen.getByRole("checkbox", { name: /He revisado el resumen/ });
    const button = screen.getByRole("button", { name: "Confirmar importación" });
    expect(button).toBeDisabled();
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    expect(button).toBeEnabled();
    fireEvent.click(button);
    await screen.findByText("Importación completada");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones/IMPWEB-SAFE-SUBSET/confirmar",
      expect.objectContaining({ method: "POST" }),
    );
    const payload = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(payload).toEqual({
      draft_version: 7, usuario: "usuario_web", confirmacion: "CONFIRMAR",
      preview_fingerprint: "fingerprint-safe-subset",
    });
  });

  it("muestra el conflicto de versión de forma controlada", async () => {
    spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => response } as Response)
      .mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({
          ok: false, version: "1.0", api_version: "1.0", request_id: "IMP-CONFLICT",
          modo_seguro: true, datos_reales_modificados: false,
          error: { status: 409, code: "draft_version_conflict", message: "Conflicto." },
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Receta"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByRole("button", { name: "Revisar pendientes" }));
    fireEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));
    expect(await screen.findByText(/cambió en otra revisión/)).toBeInTheDocument();
  });

  it("muestra el error concreto cuando Confirm revierte sin WRITE", async () => {
    const safe: any = structuredClone(response);
    safe.importacion.borrador.validation = {
      valid: false,
      blocking_errors: [{ code: "RECETA_REQUIERE_REVISION", message: "Pendiente excluida." }],
      warnings: [],
    };
    safe.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {}, menus: {},
      ignorados: [], errores: [], solo_previsualizacion: true,
      draft_version: safe.importacion.borrador.version,
      draft_fingerprint: "fingerprint-confirm-failure",
      contadores: { pendientes: 1, recetas_requieren_revision: 1 },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => safe } as Response)
      .mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({
          ok: false, version: "1.0", api_version: "1.0", request_id: "IMP-CONFIRM-FAILED",
          modo_seguro: true, datos_reales_modificados: false,
          error: { status: 409, code: "confirmation_failed", message: "La confirmación fue revertida." },
          resultado: {
            estado: "FALLIDA", acciones: [], entidades: [], rollback: true,
            errores: [{ mensaje: "Receta a reutilizar no encontrada: Vermouth rojo con Gilda MasBoronat." }],
          },
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat-limpio.json", { type: "application/json" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Importar lo seguro" }));
    fireEvent.click(screen.getByRole("checkbox", { name: /He revisado el resumen/ }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar importación" }));

    expect(await screen.findByText("Receta a reutilizar no encontrada: Vermouth rojo con Gilda MasBoronat.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(screen.queryByText("Importación completada")).not.toBeInTheDocument();
  });

  it("muestra un error controlado", async () => {
    spyOnImportFetch().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        ok: false, version: "1.0", api_version: "1.0", request_id: "IMP-ERR",
        modo_seguro: true, datos_reales_modificados: false,
        error: { status: 400, code: "contenido_no_interpretable", message: "Documento inválido." },
      }),
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("x").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    expect(await screen.findByText("No se pudo interpretar el documento.")).toBeInTheDocument();
    expect(screen.getByText("Documento inválido.")).toBeInTheDocument();
  });

  it("expone entrada multifuente, pegado y referencias de precio separadas", async () => {
    spyOnImportFetch().mockResolvedValue({
      ok: true, status: 200, json: async () => response,
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "Importar datos del restaurante" })).toBeInTheDocument();
    expect(screen.getByText("Arrastra aquí tus archivos")).toBeInTheDocument();
    expect(screen.getByLabelText("Seleccionar documento")).toHaveAttribute("multiple");
    expect(screen.getByLabelText("Pegar datos del restaurante")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir importador de referencias" }))
      .toHaveAttribute("href", "/articulos?panel=referencias");

    const first = new File(["Producto,Proveedor\nNata,SARDA"], "articulos.csv", { type: "text/csv" });
    const second = new File(["[]"], "recetas.json", { type: "application/json" });
    Object.defineProperty(first, "arrayBuffer", { value: async () => new TextEncoder().encode("Producto,Proveedor\nNata,SARDA").buffer });
    Object.defineProperty(second, "arrayBuffer", { value: async () => new TextEncoder().encode("[]").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [first, second] } });
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const request = vi.mocked(global.fetch).mock.calls[0][1] as RequestInit;
    const body = JSON.parse(String(request.body));
    expect(body.archivos).toHaveLength(2);
    expect(body.archivos.map((item: { nombre: string }) => item.nombre)).toEqual(["articulos.csv", "recetas.json"]);
  });

  it("muestra el preview global de proveedores y artículos sin escribir", async () => {
    const withCatalog: any = structuredClone(response);
    withCatalog.importacion.preview_global = {
      proveedores: { crear: [{ nombre: "Makro", accion: "CREAR" }], reutilizar: [], requiere_revision: [], ignorar: [] },
      articulos: { crear: [{ nombre: "Nata 35%", accion: "CREAR", proveedor: "Makro" }], reutilizar: [{ nombre: "Sal fina", accion: "REUTILIZAR", article_id: "ART-1" }], requiere_revision: [], ignorar: [] },
      elaboraciones: { crear_o_reutilizar: [{ nombre: "Salsa" }] },
      relaciones: { crear: [{ articulo: "Nata 35%", proveedor: "Makro", accion: "CREAR" }], reutilizar: [], requiere_revision: [], ignorar: [] },
      menus: { crear: [{ nombre: "Menú degustación", accion: "CREAR", lineas_resueltas: 3, lineas_pendientes: 0 }], reutilizar: [], actualizar: [], pendientes: [], no_soportados: [] },
      ignorados: [], errores: [], solo_previsualizacion: true,
      contadores: { proveedores_nuevos: 1, proveedores_reutilizados: 0, articulos_nuevos: 1, articulos_reutilizados: 1, recetas_elaboraciones: 1, relaciones: 1, relaciones_a_escribir: 1, menus_recibidos: 1, menus_crear: 1, menus_reutilizar: 0, menus_pendientes: 0, menu_lineas_resueltas: 3, menu_lineas_pendientes: 0, menus_no_soportados: 0, pendientes: 0 },
    };
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => withCatalog } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Producto\nNata"], "articulos.csv", { type: "text/csv" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("Producto\nNata").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    await screen.findByText("Importar lo seguro");
    fireEvent.click(screen.getByText("Ver detalles técnicos"));
    expect(screen.getByRole("region", { name: "Preview global de importación" })).toHaveTextContent("Nata 35%");
    expect(screen.getByRole("region", { name: "Preview global de importación" })).toHaveTextContent("Sal fina → ART-1");
    expect(screen.getByRole("region", { name: "Resumen de menús a importar" })).toHaveTextContent("1 detectados");
    expect(screen.getByRole("region", { name: "Resumen de menús a importar" })).toHaveTextContent("1 crear · 0 reutilizar · 0 pendientes");
    expect(screen.getByRole("region", { name: "Preview global de importación" })).toHaveTextContent("Menú degustación");
    expect(screen.getByText(/todavía no se ha modificado ningún dato operativo/i)).toBeInTheDocument();
  });

  it("resume cuatro recetas en lenguaje humano y reduce pendientes al resolver un duplicado", async () => {
    const ux: any = structuredClone(response);
    const baseRecipe = ux.importacion.borrador.recipes[0];
    const recipe = (id: string, title: string, action: string) => ({
      ...structuredClone(baseRecipe), id, title, proposed_action: action,
      ingredients: [], procedure: ["Preparar."], servings: 10,
      duplicate_candidates: [], validation_errors: [],
    });
    ux.importacion.borrador.recipes = [
      recipe("A", "Receta nueva", "CREAR_RECETA"),
      recipe("B", "Receta existente", "REUTILIZAR_EXISTENTE"),
      { ...recipe("C", "Receta incompleta", "CREAR_RECETA"), procedure: [], servings: null },
      { ...recipe("D", "Salsa Romesco", "REQUIERE_REVISION"), duplicate_candidates: [{ nombre: "Salsa romesco" }] },
    ];
    ux.importacion.resumen.recetas_detectadas = 4;
    ux.importacion.resumen.coincidencias_dudosas = 0;
    ux.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {}, ignorados: [], errores: [], solo_previsualizacion: true,
      contadores: { proveedores_nuevos: 0, proveedores_reutilizados: 0, articulos_nuevos: 0, articulos_reutilizados: 0, recetas_elaboraciones: 4, recetas_nuevas: 2, recetas_reutilizadas: 1, recetas_requieren_revision: 1, relaciones: 0, pendientes: 1 },
    };
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => ux } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Recetas"], "cuatro.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    const summary = await screen.findByRole("region", { name: "Resumen sencillo de importación" });
    expect(summary).toHaveTextContent("4Recetas");
    expect(summary).toHaveTextContent("1Ya en Biblioteca · recetas");
    expect(summary).toHaveTextContent("2Nuevas reales · recetas");
    expect(summary).toHaveTextContent("1Necesitan tu decisión · decisiones");
    expect(summary).toHaveTextContent("1Incompletas · recetas");
    expect(screen.queryByText("REUTILIZAR_EXISTENTE")).not.toBeInTheDocument();
    expect((screen.getByText("Ver detalles técnicos").parentElement as HTMLDetailsElement).open).toBe(false);

    fireEvent.click(within(summary).getByRole("button", { name: "Revisar pendientes" }));
    fireEvent.click(screen.getByRole("button", { name: /Salsa Romesco/ }));
    expect(screen.getByRole("status")).toHaveTextContent("Pendientes por resolver: 1");
    fireEvent.click(screen.getByRole("button", { name: "Usar la existente" }));
    expect(screen.getByRole("status")).toHaveTextContent("Pendientes por resolver: 0");
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("separa decisiones humanas, recetas incompletas, avisos técnicos y bloqueos de confirmación", async () => {
    const semantic: any = structuredClone(response);
    const baseRecipe = semantic.importacion.borrador.recipes[0];
    semantic.importacion.borrador.recipes = Array.from({ length: 3 }, (_, index) => ({
      ...structuredClone(baseRecipe), id: `REC-${index}`, title: `Receta ${index + 1}`,
      procedure: [], servings: null, yield_value: null, ingredients: [],
      selected_canonical_recipe_id: `REC601-CAN-${index}`,
    }));
    semantic.importacion.resumen.recetas_detectadas = 3;
    semantic.importacion.analisis_restaurante = {
      archivos: [{ nombre: "operativa.xlsx", tipo: "xlsx", tamano: 100, estado: "ANALIZADO", hojas: 1, filas: 50 }],
      hojas: [],
      resumen: {
        archivos_analizados: 1, hojas_analizadas: 1, filas_analizadas: 50,
        posibles_articulos: 20, posibles_recetas: 3, posibles_subelaboraciones: 0,
        posibles_productos_vendibles: 0, proveedores: 4, relaciones_detectadas: 12,
        duplicados_posibles: 0, ambiguedades: 50, articulos_sin_coste: 0,
        warnings_tecnicos: 50, decisiones_usuario: 2,
      },
      dudas: { clasificacion: [], precio: [], duplicados: [], relaciones: [] },
      regiones_ambiguas: Array.from({ length: 8 }, (_, index) => ({ region_id: `R-${index}` })),
      decisiones_usuario: [
        { tipo: "MAPPING_AMBIGUO", region_id: "R-1" },
        { tipo: "POSIBLE_VARIANTE", nombre: "Salsa" },
      ],
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 },
      solo_previsualizacion: true, datos_operativos_modificados: false,
    };
    semantic.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {},
      ignorados: [], errores: [], solo_previsualizacion: true,
      contadores: {
        proveedores_nuevos: 0, proveedores_reutilizados: 0, articulos_nuevos: 0,
        articulos_reutilizados: 0, recetas_elaboraciones: 3, relaciones: 0, pendientes: 40,
      },
    };
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => semantic } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "operativa.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    const summary = await screen.findByRole("region", { name: "Resumen sencillo de importación" });
    expect(summary).toHaveTextContent("2Necesitan tu decisión · decisiones");
    expect(summary).not.toHaveTextContent("40Necesitan tu decisión");
    expect(screen.getByRole("region", { name: "Necesito que decidas" })).toHaveTextContent("2 decisiones");
    expect(screen.getByRole("region", { name: "Puedes completar después" })).toHaveTextContent("3 recetas tienen datos pendientes");
    expect(screen.getByRole("button", { name: "Completar recetas de esta importación con IA · 3" })).toBeEnabled();
    expect(summary).toHaveTextContent("8 bloques técnicos");

    fireEvent.click(within(summary).getByRole("button", { name: "Importar lo seguro" }));
    expect(screen.getByText("Pendientes excluidos de esta confirmación").parentElement).toHaveTextContent("40");
    expect(screen.getByRole("button", { name: "Confirmar importación" })).toBeDisabled();
    fireEvent.click(screen.getByText("Ver detalles técnicos"));
    expect(screen.getByText("Avisos técnicos").parentElement).toHaveTextContent("50");
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("presenta el total semántico de Boronat sin confundirlo con los bloqueos globales", async () => {
    const boronat: any = structuredClone(response);
    const baseRecipe = boronat.importacion.borrador.recipes[0];
    boronat.importacion.borrador.recipes = Array.from({ length: 57 }, (_, index) => ({
      ...structuredClone(baseRecipe), id: `BOR-${index}`, title: `Receta Boronat ${index + 1}`,
      procedure: [], servings: null, yield_value: null, ingredients: [],
      selected_canonical_recipe_id: `REC601-BOR-${index}`,
    }));
    boronat.importacion.resumen.recetas_detectadas = 57;
    boronat.importacion.analisis_restaurante = {
      archivos: [], hojas: [],
      resumen: {
        archivos_analizados: 1, hojas_analizadas: 12, filas_analizadas: 1000,
        posibles_articulos: 352, posibles_recetas: 57, posibles_subelaboraciones: 0,
        posibles_productos_vendibles: 0, proveedores: 0, relaciones_detectadas: 0,
        duplicados_posibles: 16, ambiguedades: 153, articulos_sin_coste: 0,
        warnings_tecnicos: 153, decisiones_usuario: 23,
      },
      dudas: { clasificacion: [], precio: [], duplicados: [], relaciones: [] },
      regiones_ambiguas: Array.from({ length: 79 }, (_, index) => ({ region_id: `BOR-R-${index}` })),
      decisiones_usuario: Array.from({ length: 23 }, (_, index) => ({ tipo: index < 5 ? "MAPPING_AMBIGUO" : index < 10 ? "POSIBLE_VARIANTE" : "REQUIERE_REVISION" })),
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 },
      solo_previsualizacion: true, datos_operativos_modificados: false,
    };
    boronat.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {},
      ignorados: [], errores: [], solo_previsualizacion: true,
      contadores: {
        proveedores_nuevos: 0, proveedores_reutilizados: 0, articulos_nuevos: 0,
        articulos_reutilizados: 0, recetas_elaboraciones: 57, relaciones: 0, pendientes: 364,
      },
    };
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => boronat } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    const summary = await screen.findByRole("region", { name: "Resumen sencillo de importación" });
    expect(summary).toHaveTextContent("23Necesitan tu decisión · decisiones");
    expect(summary).not.toHaveTextContent("364Necesitan tu decisión");
    expect(screen.getByRole("region", { name: "Puedes completar después" })).toHaveTextContent("57 recetas tienen datos pendientes");
    expect(screen.getByRole("button", { name: "Completar recetas de esta importación con IA · 57" })).toBeEnabled();
    expect(summary).toHaveTextContent("79 bloques técnicos");
  });

  it("resuelve ambigüedades con IA solo tras opt-in explícito y conserva archivos", async () => {
    const hybrid: any = structuredClone(response);
    hybrid.importacion.analisis_restaurante = {
      archivos: [{ nombre: "ambiguo.csv", tipo: "csv", tamano: 10, estado: "ANALIZADO", hojas: 1, filas: 1 }],
      hojas: [],
      resumen: {
        archivos_analizados: 1, hojas_analizadas: 1, filas_analizadas: 1,
        posibles_articulos: 0, posibles_recetas: 0, posibles_subelaboraciones: 0,
        posibles_productos_vendibles: 0, proveedores: 0, relaciones_detectadas: 0,
        duplicados_posibles: 0, ambiguedades: 1, articulos_sin_coste: 0,
        warnings_tecnicos: 50, decisiones_usuario: 1,
      },
      dudas: { clasificacion: [], precio: [], duplicados: [], relaciones: [] },
      regiones_ambiguas: [{ region_id: "R1" }],
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 },
      solo_previsualizacion: true, datos_operativos_modificados: false,
    };
    const fetchMock = spyOnImportFetch().mockResolvedValue({
      ok: true, status: 200, json: async () => hybrid,
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["Campo X,Campo Y\nA,1"], "ambiguo.csv", { type: "text/csv" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Campo X,Campo Y\nA,1").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    const button = await screen.findByRole("button", { name: "Intentar resolver con IA · 1 bloques" });
    expect(screen.getByText("Dudas documentales totales").parentElement).toHaveTextContent("1");
    expect(screen.getByText("Avisos técnicos").parentElement).toHaveTextContent("50");
    expect(JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body)).resolver_ambiguedades_ia).toBeUndefined();
    fireEvent.click(button);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const secondBody = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(secondBody.resolver_ambiguedades_ia).toBe(true);
    expect(secondBody.archivos[0].nombre).toBe("ambiguo.csv");
  });

  it("separa legacy, nuevas, variantes y articulos y exige preview antes de actualizar", async () => {
    const legacy: any = structuredClone(response);
    legacy.importacion.resolucion_identidad = {
      recetas: { total: 10, ya_canonicas: 0, ya_conocidas_legacy: 4, nuevas_reales: 3,
        posibles_variantes: 2, requieren_revision: 1,
        grupos: { ya_canonicas: [], nuevas_reales: [], posibles_variantes: [], requieren_revision: [],
          ya_conocidas_legacy: Array.from({ length: 4 }, (_, index) => ({ id: `R-${index}`, nombre: `Existente ${index}`, legacy_source_ids: [`LEG-${index}`] })) } },
      articulos: { total: 100, ya_existentes: 80, nuevos_reales: 10, requieren_revision: 10 },
    };
    const preview = { ...response, estado: "LISTO_PARA_CONFIRMAR", preview_token: "TOKEN", canonicalizaciones: [
      { legacy_source_id: "LEG-0", nombre: "Ensaladilla de gamba" },
      { legacy_source_id: "LEG-1", nombre: "Tartar de fuet" },
      { legacy_source_id: "LEG-2", nombre: "Ceviche de corvina" },
      { legacy_source_id: "LEG-3", nombre: "Salsa brava" },
    ], resumen_impacto: { recetas_601: 4, stock: 0, lotes: 0, movimientos_stock: 0, recepciones: 0, compras: 0 } };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => legacy } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => preview } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "legacy.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    const summary = await screen.findByRole("region", { name: "Resumen sencillo de importación" });
    expect(summary).toHaveTextContent("4Ya conocidas por Host AI");
    expect(summary).toHaveTextContent("3Nuevas reales");
    expect(summary).toHaveTextContent("2Posibles variantes");
    expect(summary).toHaveTextContent("Ya existen / reutilizar80");
    expect(summary).toHaveTextContent("Nuevos reales10");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Actualizar 4 elaboraciones" }));
    const dialog = await screen.findByRole("dialog", { name: "Actualizar elaboraciones existentes" });
    expect(dialog).toHaveTextContent("No se modificarán: Stock, lotes, movimientos, recepciones ni compras");
    expect(dialog).toHaveTextContent("4 elaboraciones se actualizarán");
    for (const name of ["Ensaladilla de gamba", "Tartar de fuet", "Ceviche de corvina", "Salsa brava"]) {
      expect(dialog).toHaveTextContent(name);
    }
    expect(dialog).not.toHaveTextContent("Variante externa");
    expect(dialog).not.toHaveTextContent("Ambigua externa");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("separa 6 decisiones humanas de 57 recetas incompletas, variantes y revisiones", async () => {
    const fixture: any = structuredClone(response);
    const recipe = fixture.importacion.borrador.recipes[0];
    fixture.importacion.borrador.recipes = Array.from({ length: 57 }, (_, index) => ({
      ...structuredClone(recipe), id: index < 6 ? `DEC-${index}` : `REC-${index}`, title: `Receta ${index + 1}`,
      procedure: [], servings: null, yield_value: null,
      identity_decision: index < 6 ? null : "RECETA_NUEVA",
      proposed_action: index < 6 ? "REQUIERE_REVISION" : "CREAR_RECETA",
    }));
    fixture.importacion.resumen.recetas_detectadas = 57;
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 57, ya_canonicas: 16, ya_conocidas_legacy: 0, nuevas_reales: 20,
        posibles_variantes: 15, requieren_revision: 6,
        grupos: {
          ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [],
          posibles_variantes: Array.from({ length: 15 }, (_, index) => ({ id: `VAR-${index}`, nombre: `Variante ${index + 1}` })),
          requieren_revision: Array.from({ length: 6 }, (_, index) => ({ id: `DEC-${index}`, nombre: `Decisión real ${index + 1}` })),
        } },
      articulos: { total: 352, ya_existentes: 300, nuevos_reales: 29, requieren_revision: 23 },
    };
    fixture.importacion.analisis_restaurante = {
      archivos: [], hojas: [], resumen: { archivos_analizados: 1, hojas_analizadas: 1, filas_analizadas: 1,
        posibles_articulos: 352, posibles_recetas: 57, posibles_subelaboraciones: 0, posibles_productos_vendibles: 0,
        proveedores: 0, relaciones_detectadas: 0, duplicados_posibles: 0, ambiguedades: 89,
        articulos_sin_coste: 0, warnings_tecnicos: 89, decisiones_usuario: 6 },
      dudas: { clasificacion: [], precio: [], duplicados: [], relaciones: [] },
      regiones_ambiguas: Array.from({ length: 79 }, (_, index) => ({ region_id: `IA-${index}` })),
      decisiones_usuario: Array.from({ length: 6 }, (_, index) => ({ tipo: "REQUIERE_REVISION", nombre: `Decisión real ${index + 1}` })),
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 }, solo_previsualizacion: true, datos_operativos_modificados: false,
    };
    let serverDraft = structuredClone(fixture.importacion.borrador);
    spyOnImportFetch().mockImplementation(async (_url, init) => {
      if (init?.method === "PATCH") {
        const payload = JSON.parse(String(init.body));
        serverDraft = { ...serverDraft, recipes: payload.recipes, variant_decisions: payload.variant_decisions,
          version: serverDraft.version + 1, draft_version: serverDraft.draft_version + 1 };
        return { ok: true, status: 200, json: async () => ({ ...fixture, borrador: serverDraft }) } as Response;
      }
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "decisiones.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    expect(await screen.findByRole("button", { name: "Revisar recetas · 6" })).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Revisar decisiones" }));
    const decisions = screen.getByRole("region", { name: "Revisar decisiones" });
    expect(decisions).toHaveTextContent("Decisión 1 de 6");
    expect(decisions).not.toHaveTextContent("Problema 1 de 57");
    expect(decisions).not.toHaveTextContent("89");
    for (const index of [1, 2, 3]) fireEvent.click(within(decisions).getByRole("checkbox", { name: `Seleccionar receta Decisión real ${index}` }));
    fireEvent.click(within(decisions).getByRole("button", { name: "Crear como nuevas · 3" }));
    await waitFor(() => expect(serverDraft.recipes.filter((item: any) => item.id.startsWith("DEC-") && item.identity_decision === "RECETA_NUEVA")).toHaveLength(3));
    expect(within(decisions).getByRole("button", { name: "Crear como nuevas · 0" })).toBeDisabled();
    for (let index = 2; index <= 6; index += 1) {
      fireEvent.click(within(decisions).getByRole("button", { name: "Siguiente" }));
      expect(decisions).toHaveTextContent(`Decisión ${index} de 6`);
    }
    fireEvent.click(within(decisions).getByRole("button", { name: "Dejar pendiente" }));
    fireEvent.click(screen.getByRole("button", { name: "Revisar pendientes" }));
    expect(screen.getByText("Problema 1 de 57")).toBeInTheDocument();
  });

  it("permite decidir identidad con candidato y evidencia visible sin WRITE", async () => {
    const fixture: any = structuredClone(response);
    const imported = {
      ...structuredClone(fixture.importacion.borrador.recipes[0]),
      id: "CREMA-1", title: "Crema catalana.", proposed_action: "REQUIERE_REVISION",
      identity_decision: null, source_blocks: ["Boronat.xlsx:CREMA:12"],
      duplicate_candidates: [{
        id: "REC601-000002", nombre: "Crema Catalana quemada con carquiñoli",
        tipo: "POSTRE", coincidencia_linguistica: true, estructura_compatible: false,
        coincidencia_ingredientes: 0.5, ingredientes_importados: 4, ingredientes_existentes: 5,
        diferencias: [
          { campo: "ingredientes", actual: ["leche", "carquiñoli"], importado: ["leche", "canela"] },
          { campo: "rendimiento", actual: 12, importado: 20 },
        ],
      }],
    };
    fixture.importacion.borrador.recipes = [imported];
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 1, ya_canonicas: 0, ya_conocidas_legacy: 0, nuevas_reales: 0,
        posibles_variantes: 0, requieren_revision: 1,
        grupos: { ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [], posibles_variantes: [],
          requieren_revision: [{ id: "CREMA-1", nombre: "Crema catalana." }] } },
      articulos: { total: 0, ya_existentes: 0, nuevos_reales: 0, requieren_revision: 0 },
    };
    fixture.importacion.analisis_restaurante = {
      archivos: [], hojas: [], resumen: { archivos_analizados: 1, hojas_analizadas: 1, filas_analizadas: 1,
        posibles_articulos: 0, posibles_recetas: 1, posibles_subelaboraciones: 0, posibles_productos_vendibles: 0,
        proveedores: 0, relaciones_detectadas: 0, duplicados_posibles: 1, ambiguedades: 2,
        articulos_sin_coste: 0, warnings_tecnicos: 0, decisiones_usuario: 2 },
      dudas: { clasificacion: [{ tipo: "IDENTIDAD" }, { tipo: "DOCUMENTAL" }], precio: [], duplicados: [], relaciones: [] },
      regiones_ambiguas: [], decisiones_usuario: [{ tipo: "REQUIERE_REVISION" }, { tipo: "DATO_DOCUMENTAL" }],
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 }, solo_previsualizacion: true, datos_operativos_modificados: false,
    };
    fixture.importacion.borrador.variant_decisions = [{ group_id: "VG-1", decision: "PENDIENTE" }];
    let variantDraft = structuredClone(fixture.importacion.borrador);
    spyOnImportFetch().mockImplementation(async (_url, init) => {
      if (init?.method === "PATCH") {
        const payload = JSON.parse(String(init.body));
        variantDraft = { ...variantDraft, recipes: payload.recipes, variant_decisions: payload.variant_decisions,
          version: variantDraft.version + 1, draft_version: variantDraft.draft_version + 1 };
        return { ok: true, status: 200, json: async () => ({ ...fixture, borrador: variantDraft }) } as Response;
      }
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat-package.json", { type: "application/json" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    expect(await screen.findByRole("region", { name: "Otras dudas del documento" })).toHaveTextContent("1 duda documental adicional");
    fireEvent.click(screen.getByRole("button", { name: "Revisar decisiones" }));
    const review = screen.getByRole("region", { name: "Revisar decisiones" });
    expect(review).toHaveTextContent("Crema catalana.");
    expect(review).toHaveTextContent("Crema Catalana quemada con carquiñoli");
    expect(review).toHaveTextContent("coincidencia lingüística");
    expect(review).toHaveTextContent("50%");
    expect(review).toHaveTextContent("diferente o insuficiente");
    expect(review).toHaveTextContent("Boronat.xlsx:CREMA:12");

    fireEvent.click(within(review).getByRole("button", { name: "Es la misma receta" }));
    await waitFor(() => expect(within(review).getByRole("button", { name: "Es la misma receta" })).toHaveAttribute("aria-pressed", "true"));
    fireEvent.click(within(review).getByRole("button", { name: "Es una variante" }));
    await waitFor(() => expect(within(review).getByRole("button", { name: "Es una variante" })).toHaveAttribute("aria-pressed", "true"));
    fireEvent.click(within(review).getByRole("button", { name: "Es una receta nueva" }));
    await waitFor(() => expect(within(review).getByRole("button", { name: "Es una receta nueva" })).toHaveAttribute("aria-pressed", "true"));
    fireEvent.click(within(review).getByRole("button", { name: "Volver al resumen" }));
    fireEvent.click(screen.getByRole("button", { name: "Revisar decisiones" }));
    expect(within(screen.getByRole("region", { name: "Revisar decisiones" })).getByRole("button", { name: "Es una receta nueva" })).toHaveAttribute("aria-pressed", "true");
    expect(global.fetch).toHaveBeenCalledTimes(4);
  });

  it("revisa variantes por grupos con origen y diferencias en vez de filas repetidas", async () => {
    const fixture: any = structuredClone(response);
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 5, ya_canonicas: 0, ya_conocidas_legacy: 0, nuevas_reales: 0,
        posibles_variantes: 5, requieren_revision: 0,
        grupos: { ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [], requieren_revision: [], posibles_variantes: [] } },
      articulos: { total: 0, ya_existentes: 0, nuevos_reales: 0, requieren_revision: 0 },
      variantes: { apariciones: 10, grupos: 2, duplicados_exactos_colapsados: 6, grupos_requieren_decision: 2,
        items: [{ id: "VG-1", nombre: "Patatas Bravas", tipo_entidad_propuesto: "RECETA_O_ELABORACION",
          apariciones: 5, versiones_estructurales: 2, duplicados_exactos: 3, requiere_decision: true,
          versiones: [
            { id: "VA", nombre: "Patatas Bravas", ingredientes: [{ nombre_original: "Patata", cantidad_texto: "1", unidad: "kg" }], rendimiento: { valor: 10, unidad: "raciones" }, origenes: [{ archivo: "fixture.xlsx", hoja: "Hoja A", region: "REGION-1" }, "fixture.xlsx:Hoja B:REGION-2"], apariciones: 4 },
            { id: "VB", nombre: "Patatas bravas.", ingredientes: [{ nombre_original: "Patata", cantidad_texto: "2", unidad: "kg" }, { nombre_original: "Salsa brava", cantidad_texto: "1", unidad: "kg" }], rendimiento: 20, origenes: ["fixture.xlsx:Hoja C:REGION-3"], apariciones: 1 },
          ], diferencias: [
            { version: 2, tipo: "INGREDIENTE_ANADIDO", nombre: "Salsa brava" },
            { version: 2, tipo: "CANTIDAD_CAMBIA", nombre: "Patata", antes: ["1", "kg"], despues: ["2", "kg"] },
            { version: 2, tipo: "RENDIMIENTO_CAMBIA", antes: 10, despues: 20 },
          ] }, { id: "VG-2", nombre: "Patatas Bravas picantes", tipo_entidad_propuesto: "RECETA_O_ELABORACION",
          apariciones: 5, versiones_estructurales: 2, duplicados_exactos: 3, requiere_decision: true,
          versiones: [
            { id: "VC", nombre: "Patatas Bravas picantes", ingredientes: [{ nombre_original: "Patata", cantidad_texto: "1", unidad: "kg" }], rendimiento: 10, origenes: ["fixture.xlsx:Hoja D:REGION-4"], apariciones: 4 },
            { id: "VD", nombre: "Patatas Bravas picantes.", ingredientes: [{ nombre_original: "Patata", cantidad_texto: "2", unidad: "kg" }], rendimiento: 20, origenes: ["fixture.xlsx:Hoja E:REGION-5"], apariciones: 1 },
          ], diferencias: [{ version: 2, tipo: "CANTIDAD_CAMBIA", nombre: "Patata", antes: ["1", "kg"], despues: ["2", "kg"] }] }],
      },
    };
    fixture.importacion.borrador.variant_decisions = [{ group_id: "VG-1", decision: "PENDIENTE" }, { group_id: "VG-2", decision: "PENDIENTE" }];
    let persistedVariantDraft = structuredClone(fixture.importacion.borrador);
    spyOnImportFetch().mockImplementation(async (_url, init) => {
      if (init?.method === "PATCH") {
        const payload = JSON.parse(String(init.body));
        persistedVariantDraft = { ...persistedVariantDraft, recipes: payload.recipes,
          variant_decisions: payload.variant_decisions, version: persistedVariantDraft.version + 1,
          draft_version: persistedVariantDraft.draft_version + 1 };
        return { ok: true, status: 200, json: async () => ({ ...fixture, borrador: persistedVariantDraft }) } as Response;
      }
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "variantes.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Revisar variantes" }));
    const review = screen.getByRole("region", { name: "Revisar variantes" });
    expect(review).toHaveTextContent("10 apariciones agrupadas en 2 recetas o contextos");
    expect(review).toHaveTextContent("2 versiones estructurales");
    expect(review).toHaveTextContent("3 repeticiones exactas consolidadas");
    expect(review).toHaveTextContent("fixture.xlsx · Hoja A · REGION-1");
    expect(review).toHaveTextContent("10 raciones");
    expect(review).toHaveTextContent("+ Ingrediente en otra versión: Salsa brava");
    expect(review).toHaveTextContent("Cantidad de Patata");
    expect(review).toHaveTextContent("Rendimiento: 10 → 20");
    fireEvent.click(within(review).getByRole("checkbox", { name: "Seleccionar todos los grupos pendientes" }));
    fireEvent.click(within(review).getByRole("button", { name: "Marcar como recetas diferentes · 2" }));
    await waitFor(() => expect(persistedVariantDraft.variant_decisions.every((item: any) => item.decision === "RECETAS_DIFERENTES")).toBe(true));
    expect(within(review).getByRole("button", { name: "Marcar como recetas diferentes · 0" })).toBeDisabled();
    fireEvent.click(within(review).getByRole("button", { name: "Dejar pendiente" }));
    await waitFor(() => expect(within(review).getByRole("button", { name: "Dejar pendiente" })).toHaveAttribute("aria-pressed", "true"));
    fireEvent.click(within(review).getByRole("button", { name: "Son la misma receta" }));
    await waitFor(() => expect(within(review).getByRole("button", { name: "Son la misma receta" })).toHaveAttribute("aria-pressed", "true"));
    expect(review).toHaveTextContent("0 grupos requieren comparación");
    fireEvent.click(within(review).getByRole("button", { name: "Volver al resumen" }));
    fireEvent.click(screen.getByRole("button", { name: "Revisar variantes" }));
    expect(within(screen.getByRole("region", { name: "Revisar variantes" })).getByRole("button", { name: "Son la misma receta" })).toHaveAttribute("aria-pressed", "true");
    expect(document.body.textContent).not.toContain("[object Object]");
  });

  it("ofrece importar un HostAIImportPackage preparado por el mismo preview seguro", async () => {
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => response } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    expect(screen.getByRole("button", { name: "Preparar para IA" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Importar resultado de IA" })).toBeInTheDocument();
    expect(screen.queryByText(/ChatGPT|Claude|Gemini/i)).not.toBeInTheDocument();
    const content = JSON.stringify({
      schema: "hostai.import.package", version: "0.1", metadata: { source: "fixture" },
      recipes: [], articles: [], suppliers: [], menus: [], relations: [], ambiguities: [], variant_groups: [],
    });
    const file = new File([content], "hostai-package.json", { type: "application/json" });
    Object.defineProperty(file, "text", { value: async () => content });
    fireEvent.change(screen.getByLabelText("Seleccionar paquete Host AI preparado"), {
      target: { files: [file] },
    });
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const request = vi.mocked(global.fetch).mock.calls[0][1] as RequestInit;
    const body = JSON.parse(String(request.body));
    expect(body.hostai_import_package.schema).toBe("hostai.import.package");
    expect(body.hostai_import_package.version).toBe("0.1");
    expect(body.archivos).toBeUndefined();
    expect(await screen.findByText("Documento recibido")).toBeInTheDocument();
  });

  it("descarga un único ZIP al preparar el documento para IA", async () => {
    const zip = new Blob(["zip-fixture"], { type: "application/zip" });
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => response } as Response)
      .mockResolvedValueOnce({
        ok: true, status: 200,
        headers: new Headers({ "Content-Disposition": 'attachment; filename="HOSTAI_PARA_IA_menu.zip"' }),
        blob: async () => zip,
      } as Response);
    const createObjectURL = vi.fn(() => "blob:hostai-zip");
    const revokeObjectURL = vi.fn();
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createObjectURL });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeObjectURL });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const original = new Uint8Array([80, 75, 3, 4]);
    const file = new File([original], "menú.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => original.buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    const prepare = screen.getByRole("button", { name: "Preparar para IA" });
    await waitFor(() => expect(prepare).toBeEnabled());
    fireEvent.click(prepare);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    expect(fetchMock.mock.calls[1][0]).toBe("http://127.0.0.1:8000/api/v1/biblioteca/importaciones/preparar-para-ia");
    const payload = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(payload.nombre).toBe("menú.xlsx");
    expect(atob(payload.contenido_base64)).toBe("PK\x03\x04");
    expect(createObjectURL).toHaveBeenCalledWith(zip);
    expect(click).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:hostai-zip");
  });

  it("ofrece análisis documental IA solo tras lectura compleja y requiere click explícito", async () => {
    const basic: any = structuredClone(response);
    basic.importacion.analisis_restaurante = {
      resumen: { posibles_recetas: 2, posibles_articulos: 0, decisiones_usuario: 4 },
      dudas: { relaciones: [] }, regiones_ambiguas: [], decisiones_usuario: [], warnings_tecnicos: [],
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 },
      ai_import: { used: false, offered: true, classification: "COMPLEX",
        structural_summary: { sheets: 21, regions: 47, unresolved_regions: 4 } },
    };
    const interpreted: any = structuredClone(basic);
    interpreted.importacion.analisis_restaurante.ai_import = {
      used: true, offered: false, fingerprint: "abc", cache_hit: false,
      cost_breakdown: { total_cost: "0.001" },
      structural_summary: { sheets: 21, regions: 47, rows_sent: 400 },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => basic } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => interpreted } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "complejo.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("x").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    const button = await screen.findByRole("button", { name: "Analizar con IA" });
    expect(screen.getByText(/21 hojas y 47 regiones relevantes/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fireEvent.click(button);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("0.001")).toBeInTheDocument();
    const payload = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(payload.analizar_documento_con_ia).toBe(true);
  });

  it("permite volver al análisis básico cuando falla la interpretación IA", async () => {
    const basic: any = structuredClone(response);
    basic.importacion.analisis_restaurante = {
      resumen: { posibles_recetas: 1, posibles_articulos: 0, decisiones_usuario: 1 }, dudas: { relaciones: [] },
      regiones_ambiguas: [], decisiones_usuario: [], warnings_tecnicos: [],
      coste_ia: { usada: false, ambiguedades_enviadas: 0, total: 0 },
      ai_import: { used: false, offered: true, classification: "COMPLEX", structural_summary: { sheets: 2, regions: 8 } },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => basic } as Response)
      .mockResolvedValueOnce({ ok: false, status: 422, json: async () => ({
        ok: false, request_id: "REQ-AI-FAIL", api_version: "v1",
        error: { code: "ai_import_interpretation_failed", message: "No he podido interpretar el archivo con IA." },
      }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => response } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "complejo.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("x").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Analizar con IA" }));
    expect(await screen.findByText("No he podido interpretar el archivo con IA.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Usar análisis básico" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const payload = JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body));
    expect(payload.analizar_documento_con_ia).toBeUndefined();
  });

  it("revisa menús pendientes, persiste la decisión y conserva el draft al recargar", async () => {
    const initial: any = structuredClone(response);
    initial.importacion.borrador.menus = [{ nombre: "Menú pendiente", tipo: "MENU", componentes: [{ nombre: "Plato dudoso" }], origen: { sheet: "Menús" } }];
    initial.importacion.borrador.menu_decisions = [];
    initial.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {}, ignorados: [], errores: [], solo_previsualizacion: true,
      menus: {
        crear: [], actualizar: [], no_soportados: [],
        reutilizar: Array.from({ length: 5 }, (_, index) => ({ id: `MENU-DRAFT-${index + 2}`, nombre: `Existente ${index}`, accion: "REUTILIZAR", menu_id: `MENU601-00000${index + 4}` })),
        pendientes: [
          { id: "MENU-DRAFT-001", nombre: "Menú pendiente", accion: "PENDIENTE", origen: { sheet: "Menús" }, motivos: ["Línea sin identidad canónica."], lineas: [{ indice: 1, nombre: "Plato dudoso", seccion: "Principal", estado: "PENDIENTE" }] },
          ...Array.from({ length: 8 }, (_, index) => ({ id: `MENU-DRAFT-${String(index + 2).padStart(3, "0")}`, nombre: `Otro menú pendiente ${index + 2}`, accion: "PENDIENTE", origen: { sheet: "Menús" }, motivos: ["Pendiente."], lineas: [] })),
        ],
      },
      contadores: { pendientes: 9, menus_recibidos: 14, menus_crear: 0, menus_reutilizar: 5, menus_pendientes: 9, menu_lineas_resueltas: 148, menu_lineas_pendientes: 2 },
    };
    const updated: any = structuredClone(initial);
    updated.importacion.borrador.draft_version = 2;
    updated.importacion.borrador.version = 2;
    updated.importacion.borrador.menu_decisions = [{ menu_draft_id: "MENU-DRAFT-001", decision: "PENDIENTE", nombre_final: "Menú pendiente", line_decisions: [{ line_index: 1, decision: "USAR_REFERENCIA", tipo_referencia: "RECETA", referencia: "REC601-000043" }] }];
    updated.importacion.preview_global.contadores.menus_pendientes = 8;
    updated.importacion.preview_global.contadores.menu_lineas_pendientes = 1;
    updated.importacion.preview_global.menus.pendientes = initial.importacion.preview_global.menus.pendientes.slice(1);
    const patchResponse = { ...updated, borrador: updated.importacion.borrador, preview_global: updated.importacion.preview_global };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => initial } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ ...response, elaboraciones: { items: [{ id: "REC601-000042" }, { id: "REC601-000043" }] } }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ ...response, elaboracion: { id: "REC601-000042", nombre: "Tabla de quesos", estado: "PENDIENTE_DE_COMPLETAR", rendimiento: null, receta: { ingredientes: [{ nombre_original: "Queso A" }] }, historial_procedencia: [{ origen: "IMPORTADO" }] } }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ ...response, elaboracion: { id: "REC601-000043", nombre: "Tabla de quesos", estado: "PENDIENTE_DE_COMPLETAR", rendimiento: null, receta: { ingredientes: [{ nombre_original: "Queso A" }, { nombre_original: "Queso B" }] }, historial_procedencia: [{ origen: "IMPORTADO" }] } }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => patchResponse } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => updated } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "menus.json", { type: "application/json" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("x").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Revisar menús · 9" }));
    const review = screen.getByRole("region", { name: "Revisar menús" });
    expect(within(review).getByText("Menú pendiente")).toBeInTheDocument();
    expect(within(review).queryByText("Existente 0")).not.toBeInTheDocument();
    fireEvent.change(within(review).getByLabelText("Buscar receta canónica por nombre, alias o recipe_id"), { target: { value: "tabla de quesos" } });
    fireEvent.click(within(review).getByRole("button", { name: "Buscar en Biblioteca" }));
    expect(await within(review).findByRole("button", { name: "Elegir REC601-000042" })).toBeInTheDocument();
    expect(within(review).getByRole("button", { name: "Elegir REC601-000043" })).toBeInTheDocument();
    fireEvent.click(within(review).getByRole("button", { name: "Elegir REC601-000043" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    const payload = JSON.parse(String((fetchMock.mock.calls[4][1] as RequestInit).body));
    expect(payload.menu_decisions[0].line_decisions[0]).toMatchObject({ referencia: "REC601-000043", decision: "USAR_REFERENCIA" });
    cleanup();
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(6));
    expect(await screen.findByRole("button", { name: "Revisar menús · 8" })).toBeInTheDocument();
  });

  it("muestra la revisión de los 9 menús del Analyze aunque falte el contador auxiliar", async () => {
    const analyzed: any = structuredClone(response);
    const pendingMenus = Array.from({ length: 9 }, (_, index) => ({
      id: `MENU-DRAFT-${String(index + 1).padStart(3, "0")}`,
      nombre: `Menú pendiente ${index + 1}`,
      accion: "PENDIENTE",
      origen: { sheet: `Menú ${index + 1}` },
      motivos: ["Línea sin identidad canónica."],
      lineas: [{ indice: 1, nombre: `Plato dudoso ${index + 1}`, estado: "PENDIENTE" }],
    }));
    analyzed.importacion.borrador.menus = [
      ...pendingMenus.map((menu) => ({ nombre: menu.nombre, tipo: "MENU", componentes: menu.lineas, origen: menu.origen })),
      ...Array.from({ length: 5 }, (_, index) => ({ nombre: `Menú existente ${index + 1}`, tipo: "MENU", componentes: [] })),
    ];
    analyzed.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {}, ignorados: [], errores: [], solo_previsualizacion: true,
      menus: {
        crear: [], actualizar: [], no_soportados: [], pendientes: pendingMenus,
        reutilizar: Array.from({ length: 5 }, (_, index) => ({ id: `MENU-EXISTENTE-${index + 1}`, accion: "REUTILIZAR" })),
      },
      contadores: { pendientes: 9, menus_recibidos: 14, menus_crear: 0, menus_reutilizar: 5 },
    };
    analyzed.importacion.resumen = {
      ...analyzed.importacion.resumen,
      recetas_detectadas: 46,
      articulos_detectados: 314,
      recetas_existentes: 34,
      decisiones_humanas: 12,
    };
    analyzed.importacion.borrador.article_decisions = Array.from({ length: 16 }, (_, index) => ({
      article_draft_id: `ART-DRAFT-${index + 1}`,
      decision: "PENDIENTE",
    }));
    spyOnImportFetch().mockResolvedValueOnce({ ok: true, status: 200, json: async () => analyzed } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "boronat.json", { type: "application/json" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("x").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    expect(await screen.findByRole("button", { name: "Revisar pendientes" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Revisar artículos · 16" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Revisar menús · 9" }));

    const review = screen.getByRole("region", { name: "Revisar menús" });
    expect(within(review).getAllByText(/^Menú pendiente \d+$/)).toHaveLength(9);
    expect(within(review).queryByText("Menú existente 1")).not.toBeInTheDocument();
  });

  it("persiste nombre final por draft id y excluye menús documentales sin bloquear", async () => {
    const initial: any = structuredClone(response);
    initial.importacion.borrador.menus = [
      { nombre: "MENU FIN DE AÑO", tipo: "CONTEXT", componentes: [], origen: { sheet: "Contexto 1" } },
      { nombre: "MENU FIN DE AÑO", tipo: "MENU", componentes: [{ nombre: "Plato pendiente" }], origen: { sheet: "Contexto 2" } },
    ];
    initial.importacion.borrador.menu_decisions = [];
    const pendingMenus = [
      { id: "MENU-DRAFT-001", nombre: "MENU FIN DE AÑO", nombre_importado: "MENU FIN DE AÑO", accion: "PENDIENTE", origen: { sheet: "Contexto 1" }, motivos: ["El bloque es CONTEXT, no un menú operativo canónico."], lineas: [] },
      { id: "MENU-DRAFT-002", nombre: "MENU FIN DE AÑO", nombre_importado: "MENU FIN DE AÑO", accion: "PENDIENTE", origen: { sheet: "Contexto 2" }, motivos: ["Línea pendiente."], lineas: [{ indice: 1, nombre: "Plato pendiente", seccion: "Otros", estado: "PENDIENTE" }] },
    ];
    initial.importacion.preview_global = {
      proveedores: {}, articulos: {}, elaboraciones: {}, relaciones: {}, ignorados: [], errores: [], solo_previsualizacion: true,
      menus: { crear: [], reutilizar: Array.from({ length: 5 }, (_, index) => ({ id: `MENU-DRAFT-${index + 3}`, nombre: `Existente ${index}`, accion: "REUTILIZAR" })), actualizar: [], pendientes: pendingMenus, excluidos: [], no_soportados: [] },
      contadores: { pendientes: 2, menus_recibidos: 7, menus_crear: 0, menus_reutilizar: 5, menus_pendientes: 2, menus_excluidos: 0, menu_lineas_resueltas: 0, menu_lineas_pendientes: 1 },
    };
    const renamed: any = structuredClone(initial);
    renamed.importacion.borrador.draft_version = 2; renamed.importacion.borrador.version = 2;
    renamed.importacion.borrador.menu_decisions = [{ menu_draft_id: "MENU-DRAFT-001", decision: "PENDIENTE", nombre_final: "MENÚ CONTEXTO FINAL", line_decisions: [] }];
    renamed.importacion.preview_global.menus.pendientes[0].nombre = "MENÚ CONTEXTO FINAL";
    const excluded: any = structuredClone(renamed);
    excluded.importacion.borrador.draft_version = 3; excluded.importacion.borrador.version = 3;
    excluded.importacion.borrador.menu_decisions[0].decision = "EXCLUIR_MENU_DOCUMENTAL";
    excluded.importacion.preview_global.menus.excluidos = [excluded.importacion.preview_global.menus.pendientes[0]];
    excluded.importacion.preview_global.menus.pendientes = [excluded.importacion.preview_global.menus.pendientes[1]];
    excluded.importacion.preview_global.contadores.menus_pendientes = 1;
    excluded.importacion.preview_global.contadores.menus_excluidos = 1;
    excluded.importacion.preview_global.contadores.pendientes = 1;
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => initial } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ ...renamed, borrador: renamed.importacion.borrador, preview_global: renamed.importacion.preview_global }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ ...excluded, borrador: excluded.importacion.borrador, preview_global: excluded.importacion.preview_global }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => excluded } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "menus-context.json", { type: "application/json" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("x").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Revisar menús · 2" }));
    const names = screen.getAllByLabelText("Nombre final del menú");
    fireEvent.change(names[0], { target: { value: "MENÚ CONTEXTO FINAL" } });
    fireEvent.blur(names[0]);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    let payload = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(payload.menu_decisions).toEqual([expect.objectContaining({ menu_draft_id: "MENU-DRAFT-001", nombre_final: "MENÚ CONTEXTO FINAL" })]);
    fireEvent.click(screen.getAllByRole("button", { name: "Excluir menú documental" })[0]);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    payload = JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body));
    expect(payload.menu_decisions[0].decision).toBe("EXCLUIR_MENU_DOCUMENTAL");
    expect(await screen.findByRole("button", { name: "Revisar menús · 1" })).toBeInTheDocument();
    cleanup();
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(await screen.findByRole("button", { name: "Revisar menús · 1" })).toBeInTheDocument();
  });

  it("inicia desde una importación exactamente con los IDs canónicos mostrados", async () => {
    const imported: any = structuredClone(response);
    const baseRecipe = imported.importacion.borrador.recipes[0];
    imported.importacion.borrador.recipes = ["REC601-A", "REC601-B"].map((id, index) => ({
      ...structuredClone(baseRecipe), id: `DRAFT-${index}`, title: `Receta ${index + 1}`,
      procedure: [], servings: null, yield_value: null, ingredients: [],
      selected_canonical_recipe_id: id,
    }));
    imported.importacion.resumen.recetas_detectadas = 2;
    const batch = {
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-BATCH",
      modo_seguro: true, datos_reales_modificados: false,
      batch_id: "RECIPE-BATCH-IMPORT", estado: "PROPUESTAS_LISTAS",
      recipe_ids: ["REC601-A", "REC601-B"], resultados: [], selecciones: {}, selecciones_individuales: {}, cola: [],
      progreso: { total: 2, analizadas: 2, exitosas: 2, fallidas: 0, pendientes: 0, con_propuestas: 0, necesitan_usuario: 0, ya_completas: 2, propuestas: 0 },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => batch } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "importacion.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    const button = await screen.findByRole("button", { name: "Completar recetas de esta importación con IA · 2" });
    fireEvent.click(button);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const startCall = fetchMock.mock.calls[1];
    expect(String(startCall[0])).toContain("/completado-ia/iniciar");
    expect(JSON.parse(String((startCall[1] as RequestInit).body))).toEqual({ recipe_ids: ["REC601-A", "REC601-B"] });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Analizadas: 2 / 2"));
  });

  it("distingue fallidas y pendientes y permite reintentar todas sin perder propuestas", async () => {
    const imported: any = structuredClone(response);
    const baseRecipe = imported.importacion.borrador.recipes[0];
    imported.importacion.borrador.recipes = ["REC601-A", "REC601-B"].map((id, index) => ({
      ...structuredClone(baseRecipe), id: `DRAFT-RETRY-${index}`, title: `Receta retry ${index + 1}`,
      procedure: [], servings: null, yield_value: null, ingredients: [], selected_canonical_recipe_id: id,
    }));
    imported.importacion.resumen.recetas_detectadas = 2;
    const successA = {
      recipe_id: "REC601-A", nombre: "Receta A", estado: "CON_PROPUESTAS",
      datos_propuestos_ia: { elaboracion: "Propuesta A" },
      datos_propuestos_seguros_masivo: { elaboracion: "Propuesta A" },
      datos_requieren_revision_individual: {}, campos_pendientes_no_proponibles: [],
    };
    const failureB = {
      recipe_id: "REC601-B", nombre: "Receta B", estado: "ERROR_PROVIDER",
      datos_propuestos_ia: {}, datos_propuestos_seguros_masivo: {}, datos_requieren_revision_individual: {},
      campos_pendientes_no_proponibles: [], reintento_disponible: true,
      error: { code: "ai_provider_timeout", message: "El proveedor IA no respondió a tiempo." },
    };
    const failedBatch: any = {
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-BATCH-RETRY", modo_seguro: true, datos_reales_modificados: false,
      batch_id: "RECIPE-BATCH-RETRY", estado: "PROPUESTAS_LISTAS_CON_ERRORES",
      recipe_ids: ["REC601-A", "REC601-B"], resultados: [successA, failureB],
      selecciones: {}, selecciones_individuales: {}, cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }, { recipe_id: "REC601-B", estado: "ERROR_PROVIDER" }],
      progreso: { total: 2, analizadas: 2, exitosas: 1, fallidas: 1, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 1 },
    };
    const retrying = {
      ...failedBatch, estado: "GENERANDO", resultados: [successA],
      cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }, { recipe_id: "REC601-B", estado: "PENDIENTE" }],
      progreso: { ...failedBatch.progreso, analizadas: 1, fallidas: 0, pendientes: 1 },
    };
    const completed = {
      ...failedBatch, estado: "PROPUESTAS_LISTAS",
      resultados: [successA, { ...successA, recipe_id: "REC601-B", nombre: "Receta B", datos_propuestos_ia: { elaboracion: "Propuesta B" }, datos_propuestos_seguros_masivo: { elaboracion: "Propuesta B" } }],
      cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }, { recipe_id: "REC601-B", estado: "CON_PROPUESTAS" }],
      progreso: { total: 2, analizadas: 2, exitosas: 2, fallidas: 0, pendientes: 0, con_propuestas: 2, necesitan_usuario: 0, ya_completas: 0, propuestas: 2 },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => failedBatch } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => retrying } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => completed } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "retry.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar recetas de esta importación con IA · 2" }));

    expect(await screen.findByText(/Receta B · ERROR_PROVIDER/)).toBeInTheDocument();
    expect(screen.getByText("Fallidas").parentElement).toHaveTextContent("1");
    expect(screen.getByText("Pendientes").parentElement).toHaveTextContent("0");
    fireEvent.click(screen.getByRole("button", { name: "Reintentar todas las fallidas" }));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Analizadas: 2 / 2"));
    await waitFor(() => expect(screen.getByText("Fallidas").parentElement).toHaveTextContent("0"));
    expect(String(fetchMock.mock.calls[2][0])).toContain("/reintentar-fallidas");
    expect(String(fetchMock.mock.calls[3][0])).toContain("/siguiente");
  });

  it("aceptar todas envía solo propuestas culinarias seguras y separa las críticas", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const item = {
      recipe_id: "REC601-A", nombre: "Salsa", estado: "CON_PROPUESTAS",
      datos_propuestos_ia: { elaboracion: "Mezclar.", alergenos: ["gluten"], vida_util_refrigerado: "48 horas" },
      datos_propuestos_seguros_masivo: { elaboracion: "Mezclar." },
      datos_requieren_revision_individual: { alergenos: ["gluten"], vida_util_refrigerado: "48 horas" },
      campos_pendientes_no_proponibles: [],
    };
    const batch: any = {
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-BATCH-SAFE", modo_seguro: true, datos_reales_modificados: false,
      batch_id: "RECIPE-BATCH-SAFE", estado: "PROPUESTAS_LISTAS", recipe_ids: ["REC601-A"],
      resultados: [item], selecciones: {}, selecciones_individuales: {}, cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }],
      progreso: { total: 1, analizadas: 1, exitosas: 1, fallidas: 0, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 3 },
    };
    const selected = { ...batch, selecciones: { "REC601-A": { elaboracion: "Mezclar." } } };
    const preview = {
      ...selected, estado: "PREVIEW",
      preview: {
        fingerprint: "preview-safe", recetas_afectadas: 1, cambios_a_aplicar: 1,
        items: [{
          recipe_id: "REC601-A", nombre: "Salsa", cambios: { elaboracion: "Mezclar." },
          proposal_source: { fuente: "HOST_AI_API", origen_externo: "OPENAI_API" },
          detalle_cambios: [{ campo: "elaboracion", valor_actual: null, valor_propuesto: "Mezclar.", procedencia: { fuente: "HOST_AI_API", origen_externo: "OPENAI_API" }, clasificacion: "SELECCION_MASIVA", sobrescribe: false, completa: true }],
        }],
      },
    };
    const selectedIndividual = { ...selected, preview: null, selecciones_individuales: { "REC601-A": { alergenos: ["gluten"] } } };
    const previewIndividual = {
      ...selectedIndividual, estado: "PREVIEW",
      preview: {
        fingerprint: "preview-individual", recetas_afectadas: 1, cambios_a_aplicar: 2,
        items: [{
          recipe_id: "REC601-A", nombre: "Salsa", cambios: { elaboracion: "Mezclar.", alergenos: ["gluten"] },
          detalle_cambios: [
            { campo: "elaboracion", valor_actual: null, valor_propuesto: "Mezclar.", procedencia: { fuente: "HOST_AI_API" }, clasificacion: "SELECCION_MASIVA", sobrescribe: false, completa: true },
            { campo: "alergenos", valor_actual: [], valor_propuesto: ["gluten"], procedencia: { fuente: "HOST_AI_API" }, clasificacion: "REVISION_INDIVIDUAL", sobrescribe: false, completa: true },
          ],
        }],
      },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => batch } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => selected } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => preview } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => selectedIndividual } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => previewIndividual } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "safe.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar recetas de esta importación con IA · 1" }));
    expect(await screen.findByText("Requieren validación humana individual")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Aceptar propuestas seguras de todas" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    const payload = JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body));
    expect(payload.selections).toEqual({ "REC601-A": { elaboracion: "Mezclar." } });
    expect(JSON.stringify(payload)).not.toContain("alergenos");
    expect(JSON.stringify(payload)).not.toContain("vida_util_refrigerado");
    expect(String(fetchMock.mock.calls[3][0])).toContain("/preview");
    expect(screen.getByText(/1 propuestas seguras seleccionadas/)).toHaveTextContent("Aún no se ha escrito ningún dato");
    expect(screen.getByRole("region", { name: "Preview consolidado" })).toHaveTextContent("Vista previa de cambios");
    expect(screen.getByRole("region", { name: "Preview consolidado" })).toHaveTextContent("elaboracion");
    expect(screen.getByRole("region", { name: "Preview consolidado" })).not.toHaveTextContent("vida_util_refrigerado");

    fireEvent.click(screen.getByRole("button", { name: "Volver a propuestas" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Validar y seleccionar este campo" })[0]);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(6));
    const individualPayload = JSON.parse(String((fetchMock.mock.calls[4][1] as RequestInit).body));
    expect(individualPayload.selections).toEqual({ "REC601-A": { elaboracion: "Mezclar." } });
    expect(individualPayload.individual_selections).toEqual({ "REC601-A": { alergenos: ["gluten"] } });
    expect(screen.getByText(/1 propuestas seguras seleccionadas/)).toHaveTextContent("1 críticas validadas individualmente");
    expect(screen.getByRole("region", { name: "Preview consolidado" })).toHaveTextContent("Revisión individual");
  });

  it("muestra el error útil devuelto por el backend al iniciar el completado", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({
        ok: false, status: 422,
        json: async () => ({
          ok: false, version: "1.0", api_version: "1.0", request_id: "REQ-PROVIDER",
          modo_seguro: true, datos_reales_modificados: false,
          error: { status: 422, code: "ai_provider_timeout", message: "El proveedor IA no respondió a tiempo." },
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "error.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar recetas de esta importación con IA · 1" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("El proveedor IA no respondió a tiempo");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("exporta el XLSX externo con la frontera canónica exacta de la importación", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const exported = {
      ...response, contenido_base64: btoa("xlsx"), filename: "hostai-completado-recetas-IMPWEB-1.xlsx",
      tipo_mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", recetas_exportadas: 1,
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => exported } as Response);
    const createUrl = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:completion");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "importacion.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar externamente con XLSX · 1" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(String(fetchMock.mock.calls[1][0])).toContain("/completado-externo/exportar");
    expect(JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body))).toEqual({ recipe_ids: ["REC601-A"], scope: "IMPORTACION", import_id: "IMPWEB-1" });
    expect(createUrl).toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("XLSX descargado · 1 recetas · hostai-completado-recetas-IMPWEB-1.xlsx");
  });

  it("reutiliza el batch externo visible y bloquea un segundo clic mientras prepara el XLSX", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    imported.importacion.completado_recetas_activo = {
      batch_id: "RECIPE-BATCH-EXISTING", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ["REC601-A"], resultados: [], selecciones: {}, selecciones_individuales: {}, preview: null, cola: [],
      progreso: { total: 1, analizadas: 1, exitosas: 1, fallidas: 0, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 2 },
    };
    const exported = {
      ...response, contenido_base64: btoa("xlsx"), filename: "hostai-completado-recetas-IMPWEB-1.xlsx",
      tipo_mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", recetas_exportadas: 1,
    };
    let releaseExport!: (value: Response) => void;
    const pendingExport = new Promise<Response>((resolve) => { releaseExport = resolve; });
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockImplementationOnce(() => pendingExport);
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:existing-batch");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    const clickDownload = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "importacion.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    const button = await screen.findByRole("button", { name: "Completar externamente con XLSX · 1" });

    fireEvent.click(button);
    fireEvent.click(button);
    expect(screen.getByRole("button", { name: "Preparando XLSX…" })).toBeDisabled();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    releaseExport({ ok: true, status: 200, json: async () => exported } as Response);

    expect(await screen.findByText(/XLSX descargado · 1 recetas/)).toHaveTextContent(exported.filename);
    expect(screen.getByRole("button", { name: "Revisar propuestas externas · 1 recetas" })).toBeInTheDocument();
    expect(clickDownload).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls.some((call) => /completado-(ia\/iniciar|externo\/importar)/.test(String(call[0])))).toBe(false);
  });

  it("muestra el error de exportación y permite reintentar el CTA externo", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({
        ok: false, status: 503,
        json: async () => ({
          ok: false, version: "1.0", api_version: "1.0", request_id: "REQ-XLSX-ERROR",
          modo_seguro: true, datos_reales_modificados: false,
          error: { status: 503, code: "xlsx_export_failed", message: "No se pudo generar el XLSX." },
        }),
      } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "importacion.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar externamente con XLSX · 1" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo generar el XLSX");
    expect(screen.getByRole("button", { name: "Completar externamente con XLSX · 1" })).toBeEnabled();
  });

  it("distingue NO_APLICA estructurado de un campo realmente ausente en la ficha provisional", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const regenerationState = {
      estado: "NO_APLICA", estado_campo: "NO_APLICA", origen: "IA_PROPUESTA", fuente: "ARCHIVO_EXTERNO",
      confianza: 0.91, motivo: "La receta se sirve fría.", estado_revision: "REQUIERE_REVISION_HUMANA", confirmado: false,
    };
    const defrostState = {
      estado: "NO_APLICA", estado_campo: "NO_APLICA", origen: "IA_PROPUESTA", fuente: "ARCHIVO_EXTERNO",
      confianza: 0.88, motivo: "La receta no se congela.", estado_revision: "REQUIERE_REVISION_HUMANA", confirmado: false,
    };
    const result = {
      recipe_id: "REC601-A", nombre: "Agua de jamaica", estado: "CON_PROPUESTAS",
      datos_propuestos_ia: { regeneracion: { estado: "NO_APLICA" }, tiempo_descongelacion: { estado: "NO_APLICA" } },
      datos_propuestos_seguros_masivo: {},
      datos_requieren_revision_individual: { regeneracion: { estado: "NO_APLICA" }, tiempo_descongelacion: { estado: "NO_APLICA" } },
      metadatos_propuestas: { regeneracion: regenerationState, tiempo_descongelacion: defrostState },
      campos_pendientes_no_proponibles: [],
      completitud: { estados_campos: { regeneracion: "NO_APLICA", tiempo_descongelacion: "NO_APLICA", conservacion: "PENDIENTE" }, no_aplica: ["regeneracion", "tiempo_descongelacion"] },
      proyeccion_provisional: {
        estado: "PROVISIONAL", datos_reales_modificados: false,
        completitud: { estados_campos: { regeneracion: "NO_APLICA", tiempo_descongelacion: "NO_APLICA", conservacion: "PENDIENTE" }, no_aplica: ["regeneracion", "tiempo_descongelacion"] },
        ficha_tecnica: {
          estado: "PROVISIONAL", persistida: false, tiempos: { total: null }, conservacion: null,
          regeneracion: null, tiempo_descongelacion: null,
          estados_campos_operativos: { regeneracion: regenerationState, tiempo_descongelacion: defrostState },
          produccion: { indicaciones: {} },
        },
        escandallo: null,
      },
    };
    imported.importacion.completado_recetas_activo = {
      batch_id: "RECIPE-BATCH-NO-APLICA", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ["REC601-A"], resultados: [result], selecciones: {}, selecciones_individuales: {}, preview: null,
      cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }],
      progreso: { total: 1, analizadas: 1, exitosas: 1, fallidas: 0, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 2 },
    };
    spyOnImportFetch().mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "importacion.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Revisar propuestas externas · 1 recetas" }));

    const projection = screen.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
    const valueFor = (label: string) => within(projection).getByText(label, { selector: "dt" }).nextElementSibling;
    expect(valueFor("Regeneración")).toHaveTextContent("No aplica");
    expect(valueFor("Tiempo de descongelación")).toHaveTextContent("No aplica");
    expect(valueFor("Conservación")).toHaveTextContent("Sin dato");
    expect(valueFor("Regeneración")).toHaveTextContent("IA_PROPUESTA · ARCHIVO_EXTERNO");
    expect(valueFor("Regeneración")).toHaveTextContent("Confianza: 91%");
    expect(valueFor("Regeneración")).toHaveTextContent("Motivo: La receta se sirve fría.");
    expect(valueFor("Regeneración")).toHaveTextContent("Estado de revisión: REQUIERE_REVISION_HUMANA");
    expect(valueFor("Tiempo de descongelación")).toHaveTextContent("Confianza: 88%");
  });

  it("distingue una receta realmente sin nombre sin inventar uno desde su identificador", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-SIN-NOMBRE";
    imported.importacion.resumen.recetas_completables_ia = 1;
    imported.importacion.completado_recetas_activo = {
      batch_id: "RECIPE-BATCH-SIN-NOMBRE", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ["REC601-SIN-NOMBRE"], selecciones: {}, selecciones_individuales: {}, preview: null,
      progreso: { total: 1, analizadas: 1, exitosas: 1, fallidas: 0, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 1 },
      cola: [{ recipe_id: "REC601-SIN-NOMBRE", estado: "CON_PROPUESTAS" }],
      resultados: [{
        recipe_id: "REC601-SIN-NOMBRE", nombre: "", estado: "CON_PROPUESTAS",
        datos_propuestos_ia: { elaboracion: "Preparar." },
        datos_propuestos_seguros_masivo: { elaboracion: "Preparar." },
        datos_requieren_revision_individual: {}, campos_pendientes_no_proponibles: [],
      }],
    };
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => imported } as Response);
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: "Revisar propuestas externas · 1 recetas" }));
    const summary = screen.getByText(/Receta sin nombre · CON_PROPUESTAS/);
    expect(summary).not.toHaveTextContent("Receta 1");
    fireEvent.click(summary);
    expect(within(summary.closest("details") as HTMLElement).getByText("REC601-SIN-NOMBRE")).toBeInTheDocument();
  });

  it("mantiene visible la reimportación XLSX con un batch externo activo y reemplaza sus propuestas sin confirmar", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    imported.importacion.resumen.recetas_completables_ia = 1;
    const activeBatch: any = {
      batch_id: "RECIPE-BATCH-ACTIVO", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      archivo_externo: { nombre: "lote-anterior.xlsx", tamano: 21000, sha256: "fedcba9876543210" },
      recipe_ids: ["REC601-A"], selecciones: {}, selecciones_individuales: {}, preview: null,
      progreso: { total: 1, analizadas: 1, exitosas: 1, fallidas: 0, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 2 },
      cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }],
      resultados: [{
        recipe_id: "REC601-A", nombre: "Salsa verde", estado: "CON_PROPUESTAS",
        datos_propuestos_ia: { elaboracion: "Mezclar." }, datos_propuestos_seguros_masivo: { elaboracion: "Mezclar." },
        datos_requieren_revision_individual: {}, campos_pendientes_no_proponibles: [],
      }],
    };
    imported.importacion.completado_recetas_activo = activeBatch;
    const replacementBatch = {
      ...activeBatch,
      batch_id: "RECIPE-BATCH-REIMPORTADO",
      progreso: { ...activeBatch.progreso, propuestas: 3 },
      resultados: [{ ...activeBatch.resultados[0], datos_propuestos_ia: { elaboracion: "Mezclar.", observaciones: "Servir fría." }, datos_propuestos_seguros_masivo: { elaboracion: "Mezclar.", observaciones: "Servir fría." } }],
    };
    const external = {
      ...response, datos_reales_modificados: false,
      archivo: { nombre: "completado-real.xlsx", tamano: 22000, sha256: "abc123def4567890" },
      validacion: {
        filas_recibidas: 1, filas_con_propuestas: 1, filas_utiles: 1, filas_requieren_revision: 1, filas_rechazadas: 0,
        campos: { recibidos: 4, utiles: 3, requieren_revision: 0, rechazados: 1, bloqueados_criticos: 0 },
        referencias_precio: { filas_recibidas: 2, referencias_utiles: 1, pendientes: 1, rechazadas: 0, duplicadas: 0, datos_reales_modificados: false },
        filas: [{
          fila: 2, recipe_id: "REC601-A", estado: "UTIL_Y_REQUIERE_REVISION", errores: [], avisos: [], requiere_revision: true,
          rechazos_detallados: [{ campo: "categoria", estado: "RECHAZADO", motivos: ["EXISTING_VALUE"], mensajes: ["categoria: El campo ya tiene un valor; deje vacía su columna *_propuesto para no sobrescribirlo."] }],
        }],
      },
      batch: replacementBatch,
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => external } as Response);
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    expect(await screen.findByRole("button", { name: "Revisar propuestas externas · 1 recetas" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Importar XLSX completado" })).toBeVisible();
    expect(screen.getByText(/Archivo procesado:/)).toHaveTextContent("lote-anterior.xlsx");
    expect(screen.getByText(/Archivo procesado:/)).toHaveTextContent("fedcba987654");
    const input = screen.getByLabelText("Seleccionar XLSX completado");
    expect(input).toHaveAttribute("accept", ".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    const completed = new File(["xlsx"], "completado-real.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    Object.defineProperty(completed, "arrayBuffer", { value: async () => new TextEncoder().encode("xlsx").buffer });
    fireEvent.change(input, { target: { files: [completed] } });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("XLSX completado aceptado · 3 propuestas · sin cambios en datos reales")).toBeVisible();
    expect(screen.getByText(/Archivo procesado:/)).toHaveTextContent("completado-real.xlsx");
    expect(screen.getByText(/Filas recibidas: 1/)).toHaveTextContent("Con propuestas utilizables: 1");
    expect(screen.getByText(/Referencias externas:/)).toHaveTextContent("1 filas válidas · 1 identidades reutilizables · 1 pendientes · 0 rechazadas");
    expect(screen.getByText(/Referencias externas:/)).toHaveTextContent("nunca modifican precios reales");
    fireEvent.click(screen.getByText("Ver filas que necesitan atención"));
    expect(screen.getByText(/categoria: El campo ya tiene un valor/)).toBeVisible();
    expect(screen.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toHaveTextContent("Propuestas generadas: 3");
    expect(String(fetchMock.mock.calls[1][0])).toContain("/completado-externo/importar");
    const body = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(body).toMatchObject({ import_id: "IMPWEB-1", recipe_ids: ["REC601-A"] });
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/confirmar"))).toBe(false);
  });

  it("aísla selección segura por receta y permite volver al batch externo desde el resumen", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].servings = null;
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const critical = {
      tiempo_pasivo: "90", vida_util_refrigerado: "24 horas", puede_congelarse: false,
      regeneracion: "Servir fría", tiempo_total: "120", puede_refrigerarse: true,
      tiempo_activo: "30", alergenos: ["crustáceos"], tiempo_descongelacion: { estado: "NO_APLICA" },
    };
    const safe = { elaboracion: "Mezclar.", observaciones: "Mantener refrigerada." };
    const projection = {
      estado: "PROVISIONAL", datos_reales_modificados: false,
      completitud: {
        documental: { porcentaje: 55 }, propuesta: { porcentaje: 100 }, confirmada: { porcentaje: 60 }, pendientes: [],
        no_aplica: ["tiempo_descongelacion"],
      },
      ficha_tecnica: {
        estado: "PROVISIONAL", persistida: false, rendimiento: 10, unidad_rendimiento: "raciones", raciones: 10,
        tiempos: { total: "120 minutos" }, conservacion: "24 horas", regeneracion: "Servir fría",
        produccion: { indicaciones: { produccion_maxima: 20, personal_recomendado: 1 } }, campos_pendientes: [],
      },
      escandallo: {
        estado_coste: "PARCIAL", coste_total: null, coste_total_parcial: 11.63, coste_por_racion: null,
        ingredientes_sin_coste: 1, ingredientes_sin_conversion: 0,
        lineas_datos_propuestos: 3, precios_referencia: 3, completitud_coste_porcentaje: 75,
        ingredientes_pendientes_coste: ["Agua"], lineas: [{
          nombre_original: "Flor de hibiscus", precio_unitario: 15.9, unidad_precio: "kg",
          precio_provisional: true, proveedor_precio: "Herbolínea",
          referencia_precio_externa: { producto: "Flor de Jamaica 1 kg", tienda_referencia: "Herbolínea" },
        }, {
          nombre_original: "Limones", precio_unitario: 2.79, unidad_precio: "kg",
          precio_provisional: true, proveedor_precio: "Alcampo",
          referencia_precio_externa: { producto: "Limones malla 1 kg", tienda_referencia: "Alcampo" },
        }, {
          nombre_original: "Azúcar", precio_unitario: 0.89, unidad_precio: "kg",
          precio_provisional: true, proveedor_precio: "Alcampo",
          referencia_precio_externa: { producto: "Azúcar blanco 1 kg", tienda_referencia: "Alcampo" },
        }, { nombre_original: "Agua", precio_unitario: null }],
      },
    };
    const item = {
      recipe_id: "REC601-A", nombre: "Salsa", estado: "CON_PROPUESTAS",
      datos_propuestos_ia: { ...safe, ...critical },
      datos_propuestos_seguros_masivo: safe,
      datos_requieren_revision_individual: critical,
      metadatos_propuestas: Object.fromEntries(Object.keys({ ...safe, ...critical }).map((field) => [field, { origen: "IA_PROPUESTA", confianza: 0.9, motivo: "Contexto de menú", estado_revision: "REQUIERE_REVISION_HUMANA", ...(field === "tiempo_descongelacion" ? { estado_campo: "NO_APLICA" } : {}) }])),
      completitud: projection.completitud,
      proyeccion_provisional: projection,
      campos_pendientes_no_proponibles: [],
    };
    const batch: any = {
      batch_id: "RECIPE-BATCH-EXTERNAL", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ["REC601-A"], resultados: [item], selecciones: {}, selecciones_individuales: { "REC601-A": critical }, preview: null,
      cola: [{ recipe_id: "REC601-A", estado: "CON_PROPUESTAS" }],
      progreso: { total: 30, analizadas: 30, exitosas: 30, fallidas: 0, pendientes: 0, con_propuestas: 30, necesitan_usuario: 0, ya_completas: 0, propuestas: 120 },
    };
    const external = {
      ...response,
      archivo: { nombre: "completado-30.xlsx", tamano: 21708, sha256: "bd21abcdef1234567890" },
      validacion: { filas_recibidas: 30, filas_con_propuestas: 30, filas_utiles: 30, filas_requieren_revision: 30, filas_rechazadas: 0, campos: { recibidos: 340, utiles: 83, requieren_revision: 257, rechazados: 0, bloqueados_criticos: 0 }, filas: [{ fila: 2, recipe_id: "REC601-A", estado: "UTIL_Y_REQUIERE_REVISION", errores: [], avisos: [], tiene_propuestas_utiles: true, requiere_revision: true }] },
      batch,
    };
    const selected = { ...response, ...batch, selecciones: { "REC601-A": safe }, selecciones_individuales: {}, preview: null };
    const preview = {
      ...selected, estado: "PREVIEW",
      preview: {
        fingerprint: "preview-external", recetas_afectadas: 1, cambios_a_aplicar: 2,
        items: [{
          recipe_id: "REC601-A", nombre: "Salsa", cambios: safe,
          proposal_source: { fuente: "ARCHIVO_EXTERNO", origen_externo: "HUMANO" },
          proyeccion_provisional: projection,
          detalle_cambios: Object.entries(safe).map(([campo, valor]) => ({ campo, valor_actual: null, valor_propuesto: valor, procedencia: { fuente: "ARCHIVO_EXTERNO", origen_externo: "HUMANO" }, clasificacion: "SELECCION_MASIVA", sobrescribe: false, completa: true })),
        }],
      },
    };
    const selectedCritical = { ...selected, preview: null, selecciones_individuales: { "REC601-A": { alergenos: ["crustáceos"] } } };
    const previewCritical = {
      ...selectedCritical, estado: "PREVIEW",
      preview: {
        fingerprint: "preview-external-critical", recetas_afectadas: 1, cambios_a_aplicar: 3,
        items: [{
          recipe_id: "REC601-A", nombre: "Salsa", cambios: { ...safe, alergenos: ["crustáceos"] },
          detalle_cambios: [
            ...Object.entries(safe).map(([campo, valor]) => ({ campo, valor_actual: null, valor_propuesto: valor, procedencia: { fuente: "ARCHIVO_EXTERNO", origen_externo: "HUMANO" }, clasificacion: "SELECCION_MASIVA", sobrescribe: false, completa: true })),
            { campo: "alergenos", valor_actual: [], valor_propuesto: ["crustáceos"], procedencia: { fuente: "ARCHIVO_EXTERNO", origen_externo: "HUMANO" }, clasificacion: "REVISION_INDIVIDUAL", sobrescribe: false, completa: true },
          ],
        }],
      },
    };
    const selectedSafeAgain = { ...selected, preview: null };
    const previewSafeAgain = { ...preview, preview: { ...preview.preview, fingerprint: "preview-external-safe-again" } };
    const exported = {
      ...response, contenido_base64: btoa("xlsx"), filename: "hostai-completado-recetas-IMPWEB-1.xlsx",
      tipo_mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", recetas_exportadas: 1,
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => exported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => external } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => selected } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => preview } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => selectedCritical } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => previewCritical } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => selectedSafeAgain } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => previewSafeAgain } as Response);
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn() });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:completion-flow");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const source = new File(["x"], "importacion.xlsx");
    Object.defineProperty(source, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [source] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar externamente con XLSX · 1" }));
    fireEvent.change(await screen.findByLabelText("Origen de las propuestas externas"), { target: { value: "HUMANO" } });
    const completed = new File(["xlsx"], "completado.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    Object.defineProperty(completed, "arrayBuffer", { value: async () => new TextEncoder().encode("xlsx").buffer });
    fireEvent.change(screen.getByLabelText("Seleccionar XLSX completado"), { target: { files: [completed] } });

    expect(await screen.findByText(/Filas recibidas: 30/)).toHaveTextContent("Con propuestas utilizables: 30");
    expect(screen.getByText(/Filas recibidas: 30/)).toHaveTextContent("Requieren revisión: 30");
    expect(screen.getByText(/Campos seguros: 83/)).toHaveTextContent("Operativos agrupables: 0");
    expect(screen.getByText(/Campos seguros: 83/)).toHaveTextContent("Críticos individuales: 257");
    expect(screen.getByText(/Archivo procesado:/)).toHaveTextContent("completado-30.xlsx");
    expect(screen.getByText(/Archivo procesado:/)).toHaveTextContent("bd21abcdef12");
    expect(screen.getByText(/Analizadas: 30 \/ 30/)).not.toHaveTextContent("0 / 0");
    expect(screen.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toBeInTheDocument();
    expect(screen.getByText("Completitud operativa").parentElement).toHaveTextContent("Documento: 55%");
    expect(screen.getByText("Completitud operativa").parentElement).toHaveTextContent("Con propuestas IA: 100%");
    expect(screen.getByText("Completitud operativa").parentElement).toHaveTextContent("Confirmado: 60%");
    expect(screen.getByText("Completitud operativa").parentElement).toHaveTextContent("Resueltos como NO_APLICA: 1");
    expect(screen.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toHaveTextContent("tiempo_descongelacion: NO_APLICA");
    expect(screen.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toHaveTextContent("confianza 90%");
    expect(screen.getByText("Ficha técnica provisional").parentElement).toHaveTextContent("Solo lectura");
    expect(screen.getByText("Escandallo provisional").parentElement).toHaveTextContent("PARCIAL");
    expect(screen.getByText("Escandallo provisional").parentElement).toHaveTextContent("Coste total provisional conocido: 11.63");
    expect(screen.getByText("Escandallo provisional").parentElement).toHaveTextContent("Cobertura: 75%");
    expect(screen.getByText("Escandallo provisional").parentElement).toHaveTextContent("4 líneas · 3 con datos propuestos · 3 con precio de referencia");
    expect(screen.getByText("Escandallo provisional").parentElement).toHaveTextContent("Ingredientes pendientes de coste: Agua");
    expect(screen.getByText("Escandallo provisional").parentElement).not.toHaveTextContent("No calculable");
    expect(screen.getByRole("list", { name: "Referencias externas usadas en el escandallo" })).toHaveTextContent("Herbolínea");
    expect(screen.getByRole("list", { name: "Referencias externas usadas en el escandallo" })).toHaveTextContent("REFERENCIA_EXTERNA provisional");
    expect(screen.getAllByText("IA_PROPUESTA").length).toBeGreaterThan(0);
    expect(String(fetchMock.mock.calls[1][0])).toContain("/completado-externo/exportar");
    expect(String(fetchMock.mock.calls[2][0])).toContain("/completado-externo/importar");
    const importBody = JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body));
    expect(importBody).toMatchObject({ recipe_ids: ["REC601-A"], import_id: "IMPWEB-1", origen_propuesta: "HUMANO" });
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/completado-ia/iniciar"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Aceptar propuestas seguras de esta receta" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    const safePayload = JSON.parse(String((fetchMock.mock.calls[3][1] as RequestInit).body));
    expect(safePayload.selections).toEqual({ "REC601-A": safe });
    expect(safePayload.individual_selections).toEqual({});
    expect(String(fetchMock.mock.calls[3][0])).toContain("/seleccion");
    expect(String(fetchMock.mock.calls[4][0])).toContain("/preview");
    expect(screen.getByText(/2 propuestas seguras seleccionadas/)).toHaveTextContent("Aún no se ha escrito ningún dato");
    const previewRegion = screen.getByRole("region", { name: "Preview consolidado" });
    expect(previewRegion).toHaveTextContent("Vista previa de cambios");
    expect(previewRegion).toHaveTextContent("ARCHIVO_EXTERNO · HUMANO");
    expect(previewRegion).toHaveTextContent("Selección masiva");
    expect(previewRegion).toHaveTextContent("Cambios a aplicar: 2");
    const previewProjection = within(previewRegion).getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
    expect(previewProjection).toHaveTextContent("Estado: PARCIAL");
    expect(previewProjection).toHaveTextContent("Coste total provisional conocido: 11.63");
    expect(previewProjection).toHaveTextContent("3 con precio de referencia");
    expect(previewProjection).not.toHaveTextContent("SIN_COSTE");
    expect(previewProjection).not.toHaveTextContent("No calculable");
    for (const field of Object.keys(critical)) expect(previewRegion).not.toHaveTextContent(field);
    expect(screen.queryByRole("button", { name: "Aceptar propuestas seguras de todas" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Volver a propuestas" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Validar y seleccionar este campo" }).find((button) => button.parentElement?.textContent?.includes("alergenos"))!);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(7));
    expect(JSON.parse(String((fetchMock.mock.calls[5][1] as RequestInit).body)).individual_selections).toEqual({ "REC601-A": { alergenos: ["crustáceos"] } });
    expect(screen.getByRole("region", { name: "Preview consolidado" })).toHaveTextContent("Cambios a aplicar: 3");

    fireEvent.click(screen.getByRole("button", { name: "Volver a propuestas" }));
    fireEvent.click(screen.getByRole("button", { name: "Usar solo propuestas seguras de esta receta" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(9));
    expect(JSON.parse(String((fetchMock.mock.calls[7][1] as RequestInit).body)).individual_selections).toEqual({});
    expect(screen.getByRole("region", { name: "Preview consolidado" })).toHaveTextContent("Cambios a aplicar: 2");

    fireEvent.click(screen.getByRole("button", { name: "Volver al resumen" }));
    const reopen = await screen.findByRole("button", { name: "Revisar propuestas externas · 30 recetas" });
    fireEvent.click(reopen);
    expect(screen.getByRole("region", { name: "Preview consolidado" })).toHaveTextContent("Cambios a aplicar: 2");
    fireEvent.click(screen.getByRole("button", { name: "Volver a propuestas" }));
    expect(screen.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toHaveTextContent("2 propuestas seguras seleccionadas");
    expect(fetchMock).toHaveBeenCalledTimes(9);
  });

  it("identifica la plantilla vacía y muestra el archivo efectivamente procesado", async () => {
    const imported: any = structuredClone(response);
    imported.importacion.borrador.recipes[0].procedure = [];
    imported.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const external = {
      ...response,
      archivo: { nombre: "plantilla-vacia.xlsx", tamano: 15884, sha256: "f693abcdef1234567890" },
      validacion: {
        filas_recibidas: 1, filas_con_propuestas: 0, filas_utiles: 0, filas_requieren_revision: 1, filas_rechazadas: 0,
        campos: { recibidos: 0, utiles: 0, requieren_revision: 0, rechazados: 0, bloqueados_criticos: 0 },
        filas: [{ fila: 2, recipe_id: "REC601-A", estado: "REQUIERE_REVISION", errores: [], avisos: ["SIN_PROPUESTAS_RECIBIDAS"], requiere_revision: true }],
      },
      batch: {
        batch_id: "RECIPE-BATCH-EMPTY", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
        recipe_ids: [], resultados: [], selecciones: {}, selecciones_individuales: {}, cola: [],
        progreso: { total: 0, analizadas: 0, exitosas: 0, fallidas: 0, pendientes: 0, con_propuestas: 0, necesitan_usuario: 0, ya_completas: 0, propuestas: 0 },
      },
    };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => imported } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({
        ...response, contenido_base64: btoa("xlsx"), filename: "hostai-completado-recetas-IMPWEB-1.xlsx",
        tipo_mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", recetas_exportadas: 1,
      }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => external } as Response);
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:blank-flow");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const source = new File(["x"], "importacion.xlsx");
    Object.defineProperty(source, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [source] } });
    fireEvent.click(await screen.findByRole("button", { name: "Completar externamente con XLSX · 1" }));
    const blank = new File(["xlsx"], "plantilla-vacia.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    Object.defineProperty(blank, "arrayBuffer", { value: async () => new TextEncoder().encode("xlsx").buffer });
    fireEvent.change(await screen.findByLabelText("Seleccionar XLSX completado"), { target: { files: [blank] } });

    expect(await screen.findByRole("alert")).toHaveTextContent("no contiene valores en las columnas *_propuesto");
    expect(screen.getByText(/Archivo procesado:/)).toHaveTextContent("plantilla-vacia.xlsx");
  });

  it("consolida ingredientes nuevos, exige preview y confirmación de alta, y enlaza todas sus apariciones", async () => {
    const fixture: any = structuredClone(response);
    const ingredient = {
      ...structuredClone(fixture.importacion.borrador.recipes[0].ingredients[0]),
      id: "ING-NUEVO-1", original_text: "50 g estragón fresco", quantity_raw: "50", quantity: 50,
      unit_raw: "g", unit: "g", name_raw: "Estragón fresco", normalized_name: "estragon fresco",
      article_id: null, article_candidates: [], relation_status: "SIN_RELACIONAR", confidence: 0,
      validation_errors: [],
    };
    const recipeA = { ...structuredClone(fixture.importacion.borrador.recipes[0]), id: "REC-NUEVA-A", title: "Salsa A", ingredients: [ingredient] };
    const recipeB = { ...structuredClone(recipeA), id: "REC-NUEVA-B", title: "Salsa B", ingredients: [{ ...ingredient, id: "ING-NUEVO-2", unit_raw: "kg", unit: "kg" }] };
    fixture.importacion.borrador.recipes = [recipeA, recipeB];
    fixture.importacion.borrador.article_decisions = [];
    fixture.importacion.borrador.catalogo = { articulos: [], proveedores: [], relaciones: [] };
    fixture.importacion.resolucion_identidad = {
      recetas: { total: 2, ya_canonicas: 0, ya_conocidas_legacy: 0, nuevas_reales: 2, posibles_variantes: 0, requiere_revision: 0,
        grupos: { ya_canonicas: [], ya_conocidas_legacy: [], nuevas_reales: [], posibles_variantes: [], requieren_revision: [] } },
      articulos: { total: 0, ya_existentes: 0, nuevos_reales: 0, requieren_revision: 0 },
      variantes: { apariciones: 0, grupos: 0, duplicados_exactos_colapsados: 0, grupos_requieren_decision: 0, items: [] },
    };
    fixture.importacion.resumen.ingredientes_sin_relacionar = 2;
    fixture.importacion.resumen.ingredientes_nuevos = 2;
    const createdArticle = { nombre: "Estragón fresco", codigo: "ART-ESTRAGON-TEST", unidad_base: "g", unidad_compra: "g", estado: "PENDIENTE_DE_COMPLETAR", precio: null, proveedor: "" };
    let patchBody: any = null;
    const fetchMock = spyOnImportFetch().mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/articulos?")) return { ok: true, status: 200, json: async () => ({ ...response, catalogo: { items: [], total: 0, page: 1, page_size: 20, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      if (url.endsWith("/catalogo/preview")) {
        const request = JSON.parse(String(init?.body));
        expect(request.payload.precio).toBeUndefined();
        expect(request.payload.proveedor).toBeUndefined();
        return { ok: true, status: 200, json: async () => ({ ...response, preview_token: "ARTICLE-PREVIEW", propuesto: { ...createdArticle, ...request.payload }, requiere_confirmacion: true }) } as Response;
      }
      if (url.endsWith("/catalogo/confirmar")) return { ok: true, status: 200, json: async () => ({ ...response, datos_reales_modificados: true, registro: createdArticle, idempotente: false }) } as Response;
      if (url.endsWith("/borrador") && init?.method === "PATCH") {
        patchBody = JSON.parse(String(init.body));
        const linkedDraft = structuredClone(fixture.importacion.borrador);
        linkedDraft.draft_version = 2; linkedDraft.version = 2;
        linkedDraft.recipes = patchBody.recipes;
        return { ok: true, status: 200, json: async () => ({ ...response, borrador: linkedDraft, datos_reales_modificados: false }) } as Response;
      }
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: "Revisar artículos · 1" }));
    const candidates = screen.getByRole("region", { name: "Ingredientes nuevos y artículos candidatos" });
    expect(candidates).toHaveTextContent("Ingredientes nuevos · 1");
    expect(candidates).toHaveTextContent("2 apariciones");
    fireEvent.click(within(candidates).getByRole("button", { name: "Preparar alta autorizada" }));
    fireEvent.click(await within(candidates).findByRole("button", { name: "Revisar y guardar" }));

    expect(await within(candidates).findByRole("region", { name: "Vista previa" })).toHaveTextContent("PENDIENTE_DE_COMPLETAR");
    expect(patchBody).toBeNull();
    fireEvent.click(within(candidates).getByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(patchBody).not.toBeNull());
    const linked = patchBody.recipes.flatMap((recipe: any) => recipe.ingredients);
    expect(linked).toHaveLength(2);
    expect(linked.every((item: any) => item.article_id === "ART-ESTRAGON-TEST" && item.relation_status === "RELACIONADO")).toBe(true);
    expect(await screen.findByText("Todos los ingredientes nuevos ya tienen un artículo vinculado.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Exportar y enriquecer artículos incompletos" })).toHaveAttribute("href", "/articulos?panel=referencias");
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith("/catalogo/confirmar"))).toHaveLength(1);
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/importaciones/IMPWEB-1/confirmar"))).toBe(false);
  });

  it("recupera un alta cuyo response se perdió y enlaza sin crear un duplicado", async () => {
    const fixture: any = structuredClone(response);
    const ingredient = {
      ...structuredClone(fixture.importacion.borrador.recipes[0].ingredients[0]),
      id: "ING-RECUPERAR", name_raw: "Estragón fresco", normalized_name: "estragon fresco",
      quantity_raw: "50", unit_raw: "g", unit: "g", article_id: null,
      article_candidates: [], relation_status: "SIN_RELACIONAR", validation_errors: [],
    };
    fixture.importacion.borrador.recipes = [{
      ...structuredClone(fixture.importacion.borrador.recipes[0]), id: "REC-RECUPERAR", title: "Salsa recuperada", ingredients: [ingredient],
    }];
    fixture.importacion.borrador.catalogo = { articulos: [], proveedores: [], relaciones: [] };
    fixture.importacion.borrador.article_decisions = [];
    fixture.importacion.resumen.ingredientes_sin_relacionar = 1;
    fixture.importacion.resumen.ingredientes_nuevos = 1;
    let patchBody: any = null;
    const fetchMock = spyOnImportFetch().mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/articulos?")) {
        const code = new URL(url).searchParams.get("q") || "";
        return { ok: true, status: 200, json: async () => ({ ...response, catalogo: { items: [{ id: code, codigo: code, nombre: "Estragón fresco", estado: "PENDIENTE_DE_COMPLETAR", con_stock: false, tiene_ficha_tecnica: false }], total: 1, page: 1, page_size: 20, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      }
      if (url.endsWith("/borrador") && init?.method === "PATCH") {
        patchBody = JSON.parse(String(init.body));
        return { ok: true, status: 200, json: async () => ({ ...response, borrador: { ...fixture.importacion.borrador, draft_version: 2, version: 2, recipes: patchBody.recipes }, datos_reales_modificados: false }) } as Response;
      }
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: "Revisar artículos · 1" }));
    const candidates = screen.getByRole("region", { name: "Ingredientes nuevos y artículos candidatos" });
    fireEvent.click(within(candidates).getByRole("button", { name: "Preparar alta autorizada" }));
    const recovery = await within(candidates).findByRole("button", { name: /Enlazar artículo existente/ });
    expect(candidates).toHaveTextContent("ya existe con el código esperado");
    fireEvent.click(recovery);
    await waitFor(() => expect(patchBody).not.toBeNull());
    expect(patchBody.recipes[0].ingredients[0].article_id).toMatch(/^ART-ESTRAGON-FRESCO-/);
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/catalogo/preview"))).toBe(false);
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/catalogo/confirmar"))).toBe(false);
  });

  it("selecciona operativas agrupadas en una sola acción sin confirmar ni escribir", async () => {
    const fixture: any = structuredClone(response);
    fixture.importacion.borrador.recipes[0].procedure = [];
    fixture.importacion.borrador.recipes[0].servings = null;
    fixture.importacion.borrador.recipes[0].selected_canonical_recipe_id = "REC601-A";
    const grouped = { tiempo_total: "45 minutos", numero_raciones: 8 };
    const item = {
      recipe_id: "REC601-A", nombre: "Salsa", estado: "CON_PROPUESTAS",
      datos_propuestos_ia: { ...grouped, alergenos: ["gluten"] },
      datos_propuestos_seguros_masivo: {}, datos_operativos_agrupables: grouped,
      datos_requieren_revision_individual: { alergenos: ["gluten"] },
      campos_pendientes_no_proponibles: [],
    };
    const batch: any = {
      batch_id: "RECIPE-BATCH-GROUP", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ["REC601-A"], resultados: [item], selecciones: {}, selecciones_agrupadas: {}, selecciones_individuales: {},
      progreso: { total: 1, analizadas: 1, exitosas: 1, fallidas: 0, pendientes: 0, con_propuestas: 1, necesitan_usuario: 0, ya_completas: 0, propuestas: 3 },
    };
    fixture.importacion.completado_recetas_activo = batch;
    fixture.importacion.resumen.recetas_completables_ia = 1;
    const selected = { ...response, ...batch, selecciones_agrupadas: { "REC601-A": grouped } };
    const preview = { ...response, ...selected, estado: "PREVIEW", preview: { fingerprint: "grouped", recetas_afectadas: 1, cambios_a_aplicar: 2, items: [{ recipe_id: "REC601-A", nombre: "Salsa", cambios: grouped, detalle_cambios: Object.entries(grouped).map(([campo, valor_propuesto]) => ({ campo, valor_actual: null, valor_propuesto, clasificacion: "REVISION_AGRUPADA", sobrescribe: false, completa: true })) }] } };
    const fetchMock = spyOnImportFetch()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => fixture } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => selected } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => preview } as Response);
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: "Revisar propuestas externas · 1 recetas" }));
    fireEvent.click(screen.getByRole("button", { name: "Revisar y seleccionar operativas provisionales · 2" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const payload = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(payload.grouped_selections).toEqual({ "REC601-A": grouped });
    expect(payload.individual_selections).toEqual({});
    expect(screen.getByText(/2 operativas agrupadas/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/confirmar"))).toBe(false);
  });

  it("muestra resumen production-ready y filtra excepciones del lote sin abrir recetas", async () => {
    const fixture: any = structuredClone(response);
    const baseRecipe = fixture.importacion.borrador.recipes[0];
    fixture.importacion.borrador.recipes = ["REC-READY", "REC-BLOCKED"].map((id, index) => ({
      ...structuredClone(baseRecipe), id: `DRAFT-MASS-${index}`, title: index ? "Receta bloqueada" : "Agua de jamaica",
      procedure: [], servings: null, yield_value: null, selected_canonical_recipe_id: id,
    }));
    const baseItem = {
      estado: "CON_PROPUESTAS", datos_propuestos_ia: { elaboracion: "Preparar." },
      datos_propuestos_seguros_masivo: { elaboracion: "Preparar." },
      datos_operativos_agrupables: {},
      datos_requieren_revision_individual: {}, campos_pendientes_no_proponibles: [],
      completitud: { production_ready_provisional: true, production_ready_confirmed: false, pendientes: [], no_aplica: ["regeneracion"], production_ready: { bloqueos_provisionales: [] } },
      estado_operativo: "PRODUCTION_READY_PROVISIONAL",
      excepciones: { bloqueada: false, no_production_ready: false, criticos: false, baja_confianza: false, pendientes: false, no_aplica: true, error: false, precios_proveedores: false, imposible_estimar: false },
    };
    const batch: any = {
      batch_id: "RECIPE-BATCH-MASS", estado: "PROPUESTAS_LISTAS", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ["REC-READY", "REC-BLOCKED"], selecciones: {}, selecciones_agrupadas: {}, selecciones_individuales: {}, preview: null,
      progreso: { total: 2, analizadas: 2, exitosas: 2, fallidas: 0, pendientes: 0, con_propuestas: 2, necesitan_usuario: 0, ya_completas: 0, propuestas: 2 },
      resumen_masivo: { recetas_procesadas: 52, production_ready_provisional: 1, production_ready_confirmed: 0, recetas_sin_excepciones_operativas_relevantes: 1, campos_operativos_agrupables: 12, campos_criticos_individuales: 4, criticos_pendientes: 1, articulos_precios_pendientes: 1, baja_confianza: 1, escandallos_provisionales: 0, escandallos_parciales: 1, escandallos_sin_coste: 1, errores: 2, imposibles_estimar: 1, no_aplica: 1, datos_reales_modificados: false },
      resultados: [
        { ...baseItem, recipe_id: "REC-READY", nombre: "Agua de jamaica" },
        { ...baseItem, recipe_id: "REC-BLOCKED", nombre: "Receta bloqueada", estado_operativo: "CON_PROPUESTAS", completitud: { production_ready_provisional: false, production_ready_confirmed: false, pendientes: ["unidad_tanda"], no_aplica: [], production_ready: { bloqueos_provisionales: ["unidad_tanda"] } }, excepciones: { bloqueada: true, no_production_ready: true, criticos: true, baja_confianza: true, pendientes: true, no_aplica: false, error: false, precios_proveedores: true, imposible_estimar: true } },
      ],
    };
    fixture.importacion.completado_recetas_activo = batch;
    fixture.importacion.resumen.recetas_completables_ia = 2;
    spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => fixture } as Response);
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: "Revisar propuestas externas · 2 recetas" }));
    const summary = screen.getByRole("region", { name: "Resumen masivo production-ready" });
    expect(summary).toHaveTextContent("Recetas procesadas52");
    expect(summary).toHaveTextContent("Production-ready provisional1");
    expect(summary).toHaveTextContent("Recetas con críticos pendientes1");
    expect(summary).toHaveTextContent("Campos operativos agrupables12");
    expect(summary).toHaveTextContent("Baja confianza relevante1");
    fireEvent.change(screen.getByLabelText("Filtrar recetas del lote"), { target: { value: "NO_PRODUCTION_READY" } });
    expect(screen.getByText(/Receta bloqueada · CON_PROPUESTAS/)).toBeInTheDocument();
    expect(screen.queryByText(/Agua de jamaica · PRODUCTION_READY_PROVISIONAL/)).not.toBeInTheDocument();
    expect(screen.getByText("Mostrando 1 de 2 recetas.")).toBeInTheDocument();
  });

  it("busca por nombre o ID sin diacríticos en revisión y preview sin alterar el batch", async () => {
    const fixture: any = structuredClone(response);
    const ids = Array.from({ length: 52 }, (_, index) => `REC601-${String(index + 1).padStart(6, "0")}`);
    const names: Record<string, string> = {
      "REC601-000007": "Agua de jamaica",
      "REC601-000008": "Puré de patata",
      "REC601-000009": "Salmorejo cordobés",
      "REC601-000010": "Crema de calabaza",
      "REC601-000011": "Crema de puerros",
      "REC601-000012": "Crema catalana",
    };
    const baseDraft = fixture.importacion.borrador.recipes[0];
    fixture.importacion.borrador.recipes = ids.map((recipeId, index) => ({
      ...structuredClone(baseDraft), id: `DRAFT-SEARCH-${index + 1}`, title: names[recipeId] ?? `Receta ${index + 1}`,
      procedure: [], servings: null, yield_value: null, selected_canonical_recipe_id: recipeId,
    }));
    const results = ids.map((recipeId, index) => ({
      recipe_id: recipeId, nombre: names[recipeId] ?? `Receta ${index + 1}`, estado: "CON_PROPUESTAS",
      estado_operativo: "PRODUCTION_READY_PROVISIONAL", datos_propuestos_ia: { tiempo_total: "45 minutos" },
      datos_propuestos_seguros_masivo: {}, datos_operativos_agrupables: { tiempo_total: "45 minutos" },
      datos_requieren_revision_individual: {}, campos_pendientes_no_proponibles: [],
      excepciones: { bloqueada: false, no_production_ready: false, criticos: false, baja_confianza: false, pendientes: false, no_aplica: false, error: false, precios_proveedores: false, imposible_estimar: false },
    }));
    const previewItems = results.map((item) => ({
      recipe_id: item.recipe_id, nombre: item.nombre, cambios: { tiempo_total: "45 minutos" },
      detalle_cambios: [{ campo: "tiempo_total", valor_actual: null, valor_propuesto: "45 minutos", clasificacion: "REVISION_AGRUPADA", sobrescribe: false, completa: true }],
    }));
    const batch: any = {
      batch_id: "RECIPE-BATCH-SEARCH", estado: "PREVIEW", modo_generacion: "ARCHIVO_EXTERNO",
      recipe_ids: ids, resultados: results, selecciones: {},
      selecciones_agrupadas: { "REC601-000007": { tiempo_total: "45 minutos" } }, selecciones_individuales: {},
      progreso: { total: 52, analizadas: 52, exitosas: 52, fallidas: 0, pendientes: 0, con_propuestas: 52, necesitan_usuario: 0, ya_completas: 0, propuestas: 52 },
      preview: { fingerprint: "search", recetas_afectadas: 52, cambios_a_aplicar: 52, items: previewItems },
    };
    fixture.importacion.completado_recetas_activo = batch;
    fixture.importacion.resumen.recetas_completables_ia = 52;
    const fetchMock = spyOnImportFetch().mockResolvedValue({ ok: true, status: 200, json: async () => fixture } as Response);
    sessionStorage.setItem("hostai.active_import_session_id", "IMPWEB-1");
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: "Revisar propuestas externas · 52 recetas" }));
    const search = screen.getByLabelText("Buscar receta por nombre o ID");
    const clear = screen.getByRole("button", { name: "Limpiar" });
    const preview = screen.getByRole("region", { name: "Preview consolidado" });
    expect(within(preview).getAllByRole("article")).toHaveLength(52);
    expect(screen.getByText("Mostrando 52 de 52 recetas.")).toBeInTheDocument();

    fireEvent.change(search, { target: { value: "  AGUA  " } });
    const filteredPreviewRecipes = within(preview).getAllByRole("article");
    expect(filteredPreviewRecipes).toHaveLength(1);
    expect(filteredPreviewRecipes[0]).toHaveAttribute("data-recipe-view", "preview");
    expect(filteredPreviewRecipes[0]).toHaveAttribute("data-recipe-id", "REC601-000007");
    expect(within(preview).getByRole("heading", { name: "Agua de jamaica" })).toBeVisible();
    expect(within(preview).queryByRole("heading", { name: "Crema de calabaza" })).not.toBeInTheDocument();
    expect(screen.getByText("Mostrando 1 de 52 recetas.")).toBeInTheDocument();

    fireEvent.change(search, { target: { value: "REC601-000007" } });
    expect(within(preview).getByRole("heading", { name: "Agua de jamaica" })).toBeVisible();
    fireEvent.change(search, { target: { value: "pure" } });
    expect(within(preview).getByRole("heading", { name: "Puré de patata" })).toBeVisible();
    fireEvent.change(search, { target: { value: "no-existe" } });
    expect(screen.getByText("No se encontraron recetas con ese nombre o ID.")).toBeVisible();

    fireEvent.click(clear);
    expect(within(preview).getAllByRole("article")).toHaveLength(52);
    fireEvent.click(within(preview).getByRole("button", { name: "Volver a propuestas" }));
    fireEvent.change(search, { target: { value: "cordobes" } });
    expect(screen.getByText(/Salmorejo cordobés · PRODUCTION_READY_PROVISIONAL/)).toBeVisible();
    expect(screen.getByText(/Salmorejo cordobés · PRODUCTION_READY_PROVISIONAL/)).toHaveTextContent("REC601-000009");
    expect(screen.queryByText(/Agua de jamaica · PRODUCTION_READY_PROVISIONAL/)).not.toBeInTheDocument();
    fireEvent.keyDown(search, { key: "Escape" });
    expect(screen.getByText("Mostrando 52 de 52 recetas.")).toBeInTheDocument();
    expect(screen.getByText(/1 operativas agrupadas/)).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/confirmar"))).toBe(false);
  });
});
