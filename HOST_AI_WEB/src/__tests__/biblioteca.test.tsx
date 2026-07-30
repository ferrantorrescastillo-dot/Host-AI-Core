import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

const base = { ok: true, version: "1.0", api_version: "1.0", request_id: "LIB-1", modo_seguro: true, datos_reales_modificados: false };
const item = { id: "REC601-1", codigo: "SALSA", nombre: "Salsa de tomate", categoria: "Salsas", tipo: "Elaboración", estado: "PENDIENTE_DE_COMPLETAR", rendimiento: 10, unidad_rendimiento: "raciones", raciones: 10, coste_total: 8.5, coste_por_racion: 0.85, tiene_receta: true, tiene_escandallo: true, tiene_ficha_tecnica: false, tiene_fotografia: false, tiene_documentos: false, tiene_produccion: false, tiene_relaciones_menu_evento: false, completitud: 80 };
const list = { ...base, elaboraciones: { items: [item], page: 1, page_size: 20, total: 1, total_pages: 1, filters: { estados: ["OPERATIVA"], categorias: ["Salsas"] }, capabilities: {} } };
const ingredient = { articulo_id: "ART-001", codigo: "ART-001", nombre_articulo: "Tomate pera", unidad_base: "kg", nombre_original: "Tomate pera", cantidad_texto: "2 kg", cantidad: 2, unidad: "kg", merma: 5, coste_unitario: 4, unidad_precio: "kg", origen_precio: "historico_compras", fecha_precio: "2026-07-24", factor_conversion: 1, cantidad_utilizada: 2, cantidad_con_merma: 2.1, coste_linea: 8, coste_con_merma: 8, estado_coste: "DISPONIBLE", motivo_sin_coste: null, estado_relacion: "relacionado" };
const ingredientWithoutPrice = { articulo_id: "ART-002", codigo: "ART-002", nombre_articulo: "Sal", unidad_base: null, nombre_original: "Sal", cantidad_texto: "20 g", cantidad: 20, unidad: "g", merma: 0, coste_unitario: null, unidad_precio: null, origen_precio: "no_disponible", fecha_precio: null, factor_conversion: null, cantidad_utilizada: 20, cantidad_con_merma: null, coste_linea: null, coste_con_merma: null, estado_coste: "SIN_PRECIO", motivo_sin_coste: "Sin precio vigente", estado_relacion: "relacionado" };
const ingredientWithoutConversion = { articulo_id: "ART-003", articulo_codigo: "ART-003", codigo: "ART-003", nombre_articulo: "Gamba paella", unidad_base: null, nombre_original: "Gamba paella", cantidad_texto: "0.19 kg", cantidad: 0.19, unidad: "kg", merma: 0, coste_unitario: 10.5, unidad_precio: null, origen_precio: "catalogo_articulos", fecha_precio: null, factor_conversion: null, cantidad_utilizada: 0.19, cantidad_con_merma: 0.19, coste_linea: null, coste_con_merma: null, estado_coste: "CONVERSION_NO_DISPONIBLE", motivo_sin_coste: "Conversión no disponible", estado_relacion: "relacionado" };
const detail = {
  ...item,
  descripcion: null,
  actualizado_en: null,
  receta: { ingredientes: [ingredient], procedimiento: null, pasos: [], temperaturas: [], tecnicas: [], rendimiento: 10, unidad_rendimiento: "raciones", raciones: 10 },
  escandallo: { estado: "PARCIAL", estado_coste: "PARCIAL", lineas: [ingredient, ingredientWithoutPrice, ingredientWithoutConversion], coste_total: null, coste_total_parcial: 8, coste_por_racion: null, rendimiento: 10, ingredientes_sin_coste: 1, ingredientes_sin_conversion: 1, desactualizado: false, incidencias: [] },
  ficha_tecnica: {
    estado: "EN_CONSTRUCCION", origen: "proyeccion_datos_existentes", persistida: false,
    identificacion: {}, descripcion: null, ingredientes: [ingredient],
    proceso: { procedimiento: null, pasos: [] }, tiempos: { activo: null, pasivo: null, total: null },
    temperaturas: [], rendimiento: 10, unidad_rendimiento: "raciones", raciones: 10,
    escandallo: { estado: "PARCIAL", estado_coste: "PARCIAL", lineas: [ingredient, ingredientWithoutPrice, ingredientWithoutConversion], coste_total: null, coste_total_parcial: 8, coste_por_racion: null, rendimiento: 10, ingredientes_sin_coste: 1, ingredientes_sin_conversion: 1, desactualizado: false, incidencias: [] },
    alergenos: [], conservacion: null, caducidad: null, regeneracion: null, presentacion: null,
    utensilios: [], produccion: { indicaciones: { produccion_minima: null, produccion_maxima: null, personal_recomendado: null, recursos: [], notas: null }, ordenes: [], necesidades: [], historial: [] },
    documentos: [], version: null, actualizado_en: null,
    campos_pendientes: ["Procedimiento", "Conservación", "Coste por ración"],
  },
  alergenos: [], conservacion: null, regeneracion: null,
  produccion: { indicaciones: { produccion_minima: null, produccion_maxima: null, personal_recomendado: null, recursos: [], notas: null }, ordenes: [], necesidades: [], historial: [] },
  documentos: [], imagenes: [], versiones: [], menus: [], eventos: [], historial: [],
  pendientes: ["Procedimiento", "Conservación"], avisos: ["Ficha técnica en construcción.", "Sin documentos asociados."],
};

describe("Biblioteca Culinaria", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });
  it("navega al resumen y muestra métricas reales", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, biblioteca: { estado: "datos_disponibles", total_elaboraciones: 1, sin_receta: 0, sin_escandallo: 0, sin_ficha_tecnica: 0, con_documentos: 0, capacidades: {} } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Biblioteca" })).toBeInTheDocument();
    expect(screen.getByText("Cada dato se introduce una sola vez y se reutiliza en todo el sistema.")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/biblioteca", expect.objectContaining({ method: "GET" }));
  });
  it("lista, busca y filtra elaboraciones en backend", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => list } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Salsa de tomate")).toBeInTheDocument();
    expect(screen.getByText("Pendiente de completar")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Buscar elaboraciones"), { target: { value: "tomate" } });
    await waitFor(() => expect(global.fetch).toHaveBeenLastCalledWith(expect.stringContaining("q=tomate"), expect.anything()));
    expect(screen.queryByText(/\bAP\b/)).not.toBeInTheDocument();
  });
  it("muestra receta, enlace al artículo, escandallo y ficha técnica parcial", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: detail }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Salsa de tomate" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Tomate pera" })).toHaveAttribute("href", "/articulos/ART-001");
    expect(screen.getByText("Sin procedimiento estructurado.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Escandallo" }));
    expect(screen.getByText("Sin coste por ración")).toBeInTheDocument();
    expect(screen.getByText("8.00 €")).toBeInTheDocument();
    expect(screen.getByText(/Histórico de compras/)).toBeInTheDocument();
    expect(screen.getAllByText("Sin precio vigente")).toHaveLength(2);
    expect(screen.getByText("10.50 €")).toBeInTheDocument();
    expect(screen.getByText("Conversión no disponible")).toBeInTheDocument();
    expect(screen.getByText(/Coste incompleto/)).toBeInTheDocument();
    expect(screen.queryByText("0.00 €")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Ficha técnica" }));
    expect(screen.getByText("Ficha técnica en construcción")).toBeInTheDocument();
    expect(screen.getAllByText("Procedimiento").length).toBeGreaterThan(0);
    expect(screen.queryByText(/\bA\.?P\.?\b/)).not.toBeInTheDocument();
  });
  it("abre resumen directo, estados vacíos e historial sin inventar", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: detail }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Resumen operativo" })).toBeInTheDocument();
    expect(screen.getByText("Ficha técnica en construcción.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Producción" }));
    expect(screen.getByText("No hay registros de producción asociados.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Documentos" }));
    expect(screen.getByText("No hay documentos asociados a esta elaboración.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Historial" }));
    expect(screen.getByText("No hay historial estructurado disponible.")).toBeInTheDocument();
  });
  it("distingue elaboración inexistente de un error de red", async () => {
    const mock = vi.spyOn(global, "fetch").mockResolvedValueOnce({ ok: false, status: 404, json: async () => ({ ...base, ok: false, error: { message: "Elaboración no encontrada." } }) } as Response);
    const first = render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/NO-EXISTE"]}><App /></MemoryRouter>);
    expect(await screen.findByText("La elaboración no existe.")).toBeInTheDocument();
    expect(screen.getByText("Elaboración no encontrada.")).toBeInTheDocument();
    first.unmount();
    mock.mockRejectedValueOnce(new TypeError("network"));
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1"]}><App /></MemoryRouter>);
    expect(await screen.findByText("No se pudo cargar la elaboración.")).toBeInTheDocument();
    expect(screen.getByText("No se pudo conectar con la API.")).toBeInTheDocument();
  });
  it("cubre vistas globales, vacío y error", async () => {
    const mock = vi.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true, json: async () => ({ ...list, elaboraciones: { ...list.elaboraciones, items: [], total: 0, total_pages: 0 } }) } as Response);
    const first = render(<MemoryRouter initialEntries={["/biblioteca/recetas"]}><App /></MemoryRouter>);
    expect(await screen.findByText("No hay recetas para los filtros seleccionados.")).toBeInTheDocument();
    first.unmount();
    mock.mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ ...base, ok: false, error: { message: "Biblioteca no disponible." } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/escandallos"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Biblioteca no disponible.")).toBeInTheDocument();
  });
});
