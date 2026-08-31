import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

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
  beforeEach(() => sessionStorage.clear());
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    sessionStorage.clear();
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
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => fixture } as Response);

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

  it("limpia un token expirado sin inventar un borrador", async () => {
    sessionStorage.setItem("hostai.active_import_session_id", "IMP-EXPIRADA");
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false, status: 404, json: async () => ({ ...response, ok: false, error: { code: "import_not_found", message: "No encontrada" } }),
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    expect(await screen.findByText(/No hay una importaci/)).toBeInTheDocument();
    expect(sessionStorage.getItem("hostai.active_import_session_id")).toBeNull();
    expect(screen.queryByText("ImportaciÃ³n analizada")).not.toBeInTheDocument();
  });

  it("una importaciÃ³n nueva sustituye la referencia activa anterior", async () => {
    let sequence = 0;
    vi.spyOn(global, "fetch").mockImplementation(async () => {
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
    vi.spyOn(global, "fetch").mockImplementation(async (_url, init) => {
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
    vi.spyOn(global, "fetch").mockImplementation(async (_url, init) => {
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
    vi.spyOn(global, "fetch").mockResolvedValue({
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
    vi.spyOn(global, "fetch")
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
    vi.spyOn(global, "fetch")
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

    vi.spyOn(global, "fetch")
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
    vi.spyOn(global, "fetch")
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
    fireEvent.click(screen.getByRole("checkbox"));
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    vi.spyOn(global, "fetch")
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    vi.spyOn(global, "fetch").mockResolvedValue({
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
    vi.spyOn(global, "fetch").mockResolvedValue({
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
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => withCatalog } as Response);
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
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => ux } as Response);
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
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => semantic } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "operativa.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    const summary = await screen.findByRole("region", { name: "Resumen sencillo de importación" });
    expect(summary).toHaveTextContent("2Necesitan tu decisión · decisiones");
    expect(summary).not.toHaveTextContent("40Necesitan tu decisión");
    expect(screen.getByRole("region", { name: "Necesito que decidas" })).toHaveTextContent("2 decisiones");
    expect(screen.getByRole("region", { name: "Puedes completar después" })).toHaveTextContent("3 recetas tienen datos pendientes");
    expect(screen.getByRole("button", { name: "Completar recetas con IA · 3" })).toBeEnabled();
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
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => boronat } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["fixture"], "boronat.xlsx");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), { target: { files: [file] } });

    const summary = await screen.findByRole("region", { name: "Resumen sencillo de importación" });
    expect(summary).toHaveTextContent("23Necesitan tu decisión · decisiones");
    expect(summary).not.toHaveTextContent("364Necesitan tu decisión");
    expect(screen.getByRole("region", { name: "Puedes completar después" })).toHaveTextContent("57 recetas tienen datos pendientes");
    expect(screen.getByRole("button", { name: "Completar recetas con IA · 57" })).toBeEnabled();
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
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue({
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    vi.spyOn(global, "fetch").mockImplementation(async (_url, init) => {
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
    vi.spyOn(global, "fetch").mockImplementation(async (_url, init) => {
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
    vi.spyOn(global, "fetch").mockImplementation(async (_url, init) => {
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
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => response } as Response);
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    const fetchMock = vi.spyOn(global, "fetch")
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
    vi.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true, status: 200, json: async () => analyzed } as Response);
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
    const fetchMock = vi.spyOn(global, "fetch")
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
});
