import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
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
      explicacion: "Propuesta generada a partir de receta «Salsa verde».",
      titulo: "Crear receta: Salsa verde",
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
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
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
    expect(screen.getByText("RECETA")).toBeInTheDocument();
    expect(screen.getByText("Crear receta: Salsa verde")).toBeInTheDocument();
    expect(screen.getAllByText("Salsa verde").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Salsa roja").length).toBeGreaterThan(0);
    expect(screen.getByText(/100 g Perejil/)).toBeInTheDocument();
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    expect(screen.getByText(/Relacionado/)).toBeInTheDocument();
    expect(screen.queryByText(/Lector Word pendiente/)).not.toBeInTheDocument();
    expect(screen.getAllByText(/Pendiente de revisión/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Ninguna propuesta ha sido aplicada/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /confirmar/i })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Revisar borrador" })).toBeInTheDocument();
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
    expect(screen.getAllByText(/puede representar una fracción/).length).toBeGreaterThan(0);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones",
      expect.objectContaining({ method: "POST" }),
    ));
    const request = vi.mocked(global.fetch).mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).toMatchObject({
      nombre: "receta.txt",
      tipo_mime: "text/plain",
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
    await screen.findByText("Revisar borrador");
    fireEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));
    expect(await screen.findByText(/Borrador guardado/)).toBeInTheDocument();
    expect(global.fetch).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones/IMPWEB-1/borrador",
      expect.objectContaining({ method: "PATCH" }),
    );
    expect(screen.queryByRole("button", { name: /confirmar/i })).not.toBeInTheDocument();
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
    await screen.findByText("Revisar borrador");
    fireEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));
    expect(await screen.findByText(/cambió en otra revisión/)).toBeInTheDocument();
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
});
