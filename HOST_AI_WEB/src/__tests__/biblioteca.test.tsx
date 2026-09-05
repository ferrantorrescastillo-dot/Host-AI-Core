import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { App } from "../ui/App";

const base = { ok: true, version: "1.0", api_version: "1.0", request_id: "LIB-1", modo_seguro: true, datos_reales_modificados: false };
const item = { id: "REC601-1", codigo: "SALSA", nombre: "Salsa de tomate", categoria: "Salsas", tipo: "Elaboración", estado: "PENDIENTE_DE_COMPLETAR", rendimiento: 10, unidad_rendimiento: "raciones", raciones: 10, coste_total: 8.5, coste_por_racion: 0.85, tiene_receta: true, tiene_escandallo: true, tiene_ficha_tecnica: false, tiene_fotografia: false, tiene_documentos: false, tiene_produccion: false, tiene_relaciones_menu_evento: false, completitud: 80 };
const list = { ...base, elaboraciones: { items: [item], page: 1, page_size: 20, total: 1, total_pages: 1, filters: { estados: ["OPERATIVA"], categorias: ["Salsas"] }, capabilities: {} } };
const ingredient = { articulo_id: "ART-001", articulo_codigo: "ART-001", articulo_nombre: "Tomate pera", codigo: "ART-001", nombre_articulo: "Tomate pera", unidad_base: "kg", nombre_original: "Tomate pera", cantidad_texto: "500 g", cantidad: 500, unidad: "g", cantidad_receta: 500, unidad_receta: "g", merma: 5, coste_unitario: 4, precio_unitario: 4, precio_original: 4, unidad_precio_original: "kg", precio_aplicado: 4, unidad_precio_aplicado: "kg", unidad_precio: "kg", origen_precio: "historico_compras", clasificacion_precio: "REAL", fecha_precio: "2026-07-24", tipo_conversion: "metrica", factor_conversion: 0.001, cantidad_utilizada: 500, cantidad_con_merma: 525, coste_linea: 2, coste_con_merma: 2, estado_coste: "DISPONIBLE", motivo_sin_coste: null, estado_relacion: "relacionado" };
const ingredientWithoutPrice = { articulo_id: "ART-002", codigo: "ART-002", nombre_articulo: "Sal", unidad_base: null, nombre_original: "Sal", cantidad_texto: "20 g", cantidad: 20, unidad: "g", merma: 0, coste_unitario: null, unidad_precio: null, origen_precio: "no_disponible", fecha_precio: null, factor_conversion: null, cantidad_utilizada: 20, cantidad_con_merma: null, coste_linea: null, coste_con_merma: null, estado_coste: "SIN_PRECIO", motivo_sin_coste: "Sin precio vigente", estado_relacion: "relacionado" };
const ingredientWithoutConversion = { articulo_id: "ART-003", articulo_codigo: "ART-003", codigo: "ART-003", nombre_articulo: "Gamba paella", unidad_base: null, nombre_original: "Gamba paella", cantidad_texto: "0.19 kg", cantidad: 0.19, unidad: "kg", cantidad_receta: 0.19, unidad_receta: "kg", merma: 0, coste_unitario: 10.5, precio_original: 10.5, unidad_precio_original: "u", precio_aplicado: 10.5, unidad_precio_aplicado: "u", unidad_precio: "u", origen_precio: "catalogo_articulos", fecha_precio: null, tipo_conversion: "no_disponible", factor_conversion: null, cantidad_utilizada: 0.19, cantidad_con_merma: 0.19, coste_linea: null, coste_con_merma: null, estado_coste: "CONVERSION_NO_DISPONIBLE", motivo_sin_coste: "Conversión no disponible", estado_relacion: "relacionado" };
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
    expect(screen.getAllByText("Pendiente de completar").length).toBeGreaterThanOrEqual(4);
    expect(screen.getByLabelText("Indicadores de la elaboración")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Descripción" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Conservación" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Alérgenos" })).toBeInTheDocument();
    expect(screen.getByText("Sin alérgenos confirmados")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Escandallo" }));
    expect(screen.getByLabelText("Indicadores del escandallo")).toBeInTheDocument();
    expect(screen.getByText("Revisión económica pendiente")).toBeInTheDocument();
    expect(screen.getByText("Sin coste por ración")).toBeInTheDocument();
    expect(screen.getByText(/Coste incompleto · 8.00 € calculados/)).toBeInTheDocument();
    expect(screen.getByText(/Histórico de compras/)).toBeInTheDocument();
    expect(screen.getAllByText("Sin precio vigente")).toHaveLength(1);
    expect(screen.getByText(/4.00 € \/ kg/)).toBeInTheDocument();
    expect(screen.getByText(/Métrica g → kg · factor 0.001/)).toBeInTheDocument();
    expect(screen.getByText(/10.50 € \/ u/)).toBeInTheDocument();
    expect(screen.getByText("Conversión no disponible")).toBeInTheDocument();
    expect(screen.queryByText("Sin precio vigente", { selector: "td:first-child" })).not.toBeInTheDocument();
    expect(screen.getByText(/Coste incompleto/)).toBeInTheDocument();
    expect(screen.queryByText("0.00 €")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Ficha técnica" }));
    expect(screen.getByText("Ficha técnica en construcción")).toBeInTheDocument();
    expect(screen.getAllByText("Procedimiento").length).toBeGreaterThan(0);
    expect(screen.queryByText(/\bA\.?P\.?\b/)).not.toBeInTheDocument();
  });
  it("presenta como pendiente el rendimiento técnico desconocido y nunca como cero raciones", async () => {
    const unknownYield = {
      ...detail,
      rendimiento: null, raciones: null, coste_por_racion: null,
      motivo_coste_no_disponible: "Pendiente de rendimiento.",
      receta: { ...detail.receta, rendimiento: null, raciones: null, unidad_rendimiento: null },
      escandallo: { ...detail.escandallo, rendimiento: null, coste_por_racion: null },
      ficha_tecnica: {
        ...detail.ficha_tecnica, rendimiento: null, raciones: null,
        campos_pendientes: [...detail.ficha_tecnica.campos_pendientes, "Rendimiento"],
      },
      pendientes: [...detail.pendientes, "Rendimiento"],
    };
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true, json: async () => ({ ...base, elaboracion: unknownYield }),
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Resumen operativo" })).toBeInTheDocument();
    expect(screen.getAllByText("Rendimiento pendiente").length).toBeGreaterThan(0);
    expect(screen.getByText("No informadas")).toBeInTheDocument();
    expect(screen.queryByText(/0\s+raciones/i)).not.toBeInTheDocument();
    expect(screen.getAllByText("Rendimiento").length).toBeGreaterThan(0);
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
  it("muestra rendimiento físico teórico como sugerencia READ parcial", async () => {
    const withTheoretical = {
      ...detail,
      receta: {
        ...detail.receta,
        rendimiento: 7,
        unidad_rendimiento: "u",
        rendimiento_neto: null,
        rendimiento_fisico_teorico: {
          estado: "PARCIAL", cantidad: 1.4, unidad: "kg",
          estado_confirmacion: "SUGERIDO",
          magnitudes: { masa: { cantidad: 1.4, unidad: "kg" } },
          ingredientes_incluidos: [{ nombre: "Base", cantidad_original: 1.4, unidad_original: "kg", dimension: "masa", cantidad_normalizada: 1.4, unidad_normalizada: "kg" }],
          ingredientes_excluidos: [{ articulo_id: "ART-HUEVO", nombre: "Huevos", cantidad: 7, unidad: "u", motivo: "UNIDAD_DISCRETA_SIN_EQUIVALENCIA_FISICA" }],
          por_unidad: { cantidad: 0.2, unidad: "kg/u", estado_confirmacion: "SUGERIDO", calculo_parcial: true },
          incidencias: [{ codigo: "CALCULO_PARCIAL", detalle: "Existen ingredientes sin magnitud física convertible." }],
          datos_reales_modificados: false,
        },
      },
    };
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: withTheoretical, permisos: { confirmar_rendimiento: false } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Rendimiento físico teórico" })).toBeInTheDocument();
    expect(screen.getByText("Estado económico")).toBeInTheDocument();
    expect(screen.getByText(/Estado del rendimiento físico:/)).toBeInTheDocument();
    expect(screen.getByText("1.4 kg")).toBeInTheDocument();
    expect(screen.getByText(/200 g\/u \(cálculo parcial\)/)).toBeInTheDocument();
    expect(screen.getByText(/Estimación parcial: no incluye 1 ingrediente/)).toBeInTheDocument();
    expect(screen.getByText("Ingredientes no convertibles: 1")).toBeInTheDocument();
    expect(screen.getByText(/no sustituye el rendimiento neto confirmado/i)).toBeInTheDocument();
  });

  it("usa el rendimiento teórico parcial como propuesta sin preview ni persistencia", async () => {
    const withProposal = {
      ...detail,
      receta: {
        ...detail.receta,
        rendimiento: 7,
        unidad_rendimiento: "u",
        rendimiento_neto: null,
        rendimiento_fisico_teorico: {
          estado: "PARCIAL", cantidad: 1.276, unidad: "kg", estado_confirmacion: "SUGERIDO",
          magnitudes: { masa: { cantidad: 1.276, unidad: "kg" } },
          ingredientes_incluidos: [{ nombre: "Base", cantidad_original: 1.276, unidad_original: "kg", dimension: "masa", cantidad_normalizada: 1.276, unidad_normalizada: "kg" }],
          ingredientes_excluidos: [{ articulo_id: "ART-HUEVO", nombre: "Huevos", cantidad: 7, unidad: "u", motivo: "UNIDAD_DISCRETA_SIN_EQUIVALENCIA_FISICA" }],
          por_unidad: { cantidad: 0.18228571428571427, unidad: "kg/u", estado_confirmacion: "SUGERIDO", calculo_parcial: true },
          incidencias: [{ codigo: "CALCULO_PARCIAL" }], datos_reales_modificados: false,
        },
      },
    };
    const mock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/rendimiento/preview")) return { ok: true, json: async () => ({
        ...base, estado: "LISTO_PARA_CONFIRMAR", escandallo_id: "REC601-1",
        rendimiento_declarado: { cantidad: 7, unidad: "u" }, rendimiento_neto_actual: null,
        rendimiento_neto_propuesto: { cantidad: 1.276, unidad: "kg", estado: "CONFIRMADO", origen: { tipo: "USUARIO", actor_id: "USR" } },
        modo_entrada: "TOTAL", propuesta_origen: "TEORICO_PARCIAL", version_esperada: "v1", preview_token: "TOKEN-PROPUESTA",
        requiere_confirmacion: true, incidencias: [], datos_reales_modificados: false,
      }) } as Response;
      if (init?.method === "POST") throw new Error("No debe existir otra escritura");
      return { ok: true, json: async () => ({ ...base, elaboracion: withProposal, permisos: { confirmar_rendimiento: true } }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    expect(await screen.findByText(/182 g\/u \(cálculo parcial\)/)).toBeInTheDocument();
    expect(screen.getByText(/Estimación parcial: no incluye 1 ingrediente/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Usar como propuesta" }));
    expect(screen.getByRole("radio", { name: "Rendimiento neto total" })).toBeChecked();
    expect(screen.getByLabelText("Cantidad de rendimiento neto")).toHaveValue("1,276");
    expect(screen.getByLabelText("Unidad de rendimiento neto")).toHaveValue("kg");
    expect(screen.queryByLabelText("Vista previa del rendimiento")).not.toBeInTheDocument();
    expect(screen.getByText(/Estimación parcial: no incluye 1 ingrediente/)).toBeInTheDocument();
    expect(mock.mock.calls.filter(([input]) => String(input).includes("/biblioteca/elaboraciones/REC601-1")).length).toBe(1);
    fireEvent.change(screen.getByLabelText("Cantidad de rendimiento neto"), { target: { value: "1,3" } });
    expect(screen.getByLabelText("Cantidad de rendimiento neto")).toHaveValue("1,3");
    expect(screen.getByText("Valor editado a partir de una propuesta teórica parcial.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Usar como propuesta" }));
    fireEvent.click(screen.getByRole("button", { name: "Vista previa" }));
    await screen.findByLabelText("Vista previa del rendimiento");
    expect(screen.getByText(/Esta propuesta procede de una estimación teórica parcial/)).toBeInTheDocument();
    expect(screen.getByText("Huevos — 7 u")).toBeInTheDocument();
    const confirmButton = screen.getByRole("button", { name: "Confirmar rendimiento" });
    expect(confirmButton).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: /Confirmo que este valor corresponde/ }));
    expect(confirmButton).toBeEnabled();
    const previewCall = mock.mock.calls.find(([called]) => String(called).endsWith("/rendimiento/preview"));
    expect(JSON.parse(String(previewCall?.[1]?.body))).toMatchObject({ cantidad: 1.276, unidad: "kg", modo: "TOTAL", propuesta_origen: "TEORICO_PARCIAL" });
    expect(mock.mock.calls.some(([called]) => String(called).endsWith("/rendimiento/confirmar"))).toBe(false);
    fireEvent.click(screen.getByRole("radio", { name: "Peso o volumen por unidad" }));
    expect(screen.queryByLabelText("Vista previa del rendimiento")).not.toBeInTheDocument();
    expect(screen.queryByText(/propuesta teórica parcial/i)).not.toBeInTheDocument();
  });

  it("oculta la propuesta para rendimiento no calculable o multidimensional", async () => {
    const theoreticalBase = { estado_confirmacion: "SUGERIDO", ingredientes_incluidos: [], ingredientes_excluidos: [], por_unidad: null, incidencias: [], datos_reales_modificados: false };
    const cases = [
      { estado: "NO_CALCULABLE", cantidad: null, unidad: null, magnitudes: {} },
      { estado: "COMPLETO", cantidad: null, unidad: null, magnitudes: { masa: { cantidad: 1, unidad: "kg" }, volumen: { cantidad: 1, unidad: "l" } } },
    ];
    for (const theoretical of cases) {
      const current = { ...detail, receta: { ...detail.receta, rendimiento_fisico_teorico: { ...theoreticalBase, ...theoretical } } };
      const mock = vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: current, permisos: { confirmar_rendimiento: true } }) } as Response);
      const view = render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
      await screen.findByRole("heading", { name: "Rendimiento físico teórico" });
      expect(screen.queryByRole("button", { name: "Usar como propuesta" })).not.toBeInTheDocument();
      view.unmount();
      mock.mockRestore();
    }
  });

  it("ofrece una estimación teórica completa de una única magnitud", async () => {
    const complete = { ...detail, receta: { ...detail.receta, rendimiento_fisico_teorico: {
      estado: "COMPLETO", cantidad: 1, unidad: "kg", estado_confirmacion: "SUGERIDO",
      magnitudes: { masa: { cantidad: 1, unidad: "kg" } }, ingredientes_incluidos: [], ingredientes_excluidos: [],
      por_unidad: null, incidencias: [], datos_reales_modificados: false,
    } } };
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/rendimiento/preview")) return { ok: true, json: async () => ({
        ...base, estado: "LISTO_PARA_CONFIRMAR", escandallo_id: "REC601-1",
        rendimiento_declarado: { cantidad: 10, unidad: "raciones" }, rendimiento_neto_actual: null,
        rendimiento_neto_propuesto: { cantidad: 1, unidad: "kg", estado: "CONFIRMADO", origen: { tipo: "USUARIO", actor_id: "USR" } },
        modo_entrada: "TOTAL", propuesta_origen: "TEORICO_COMPLETO", version_esperada: "v1", preview_token: "TOKEN-COMPLETO",
        requiere_confirmacion: true, incidencias: [], datos_reales_modificados: false,
      }) } as Response;
      return { ok: true, json: async () => ({ ...base, elaboracion: complete, permisos: { confirmar_rendimiento: true } }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Estimación teórica basada en todos los ingredientes.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Usar como propuesta" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Usar como propuesta" }));
    fireEvent.click(screen.getByRole("button", { name: "Vista previa" }));
    expect(await screen.findByText("Esta propuesta procede de una estimación teórica. Revísala antes de confirmar.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar rendimiento" })).toBeEnabled();
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

  it("previsualiza 0,18 kg por unidad, confirma 1,26 kg y refresca el READ", async () => {
    const editable = {
      ...detail,
      receta: {
        ...detail.receta,
        rendimiento: 7,
        unidad_rendimiento: "u",
        estado_rendimiento: "IMPORTADO",
        origen_rendimiento: { tipo: "EXCEL" },
        rendimiento_neto: null,
      },
    };
    const confirmed = {
      ...editable,
      receta: {
        ...editable.receta,
        rendimiento_neto: {
          cantidad: 1.26, unidad: "kg", estado: "CONFIRMADO",
          origen: { tipo: "USUARIO", actor_id: "USR-CHEF", fecha: "2026-08-14T10:00:00Z" },
        },
      },
    };
    const mock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/rendimiento/preview")) return { ok: true, json: async () => ({
        ...base, estado: "LISTO_PARA_CONFIRMAR", escandallo_id: "REC601-1",
        rendimiento_declarado: { cantidad: 7, unidad: "u" }, rendimiento_neto_actual: null,
        rendimiento_neto_propuesto: { cantidad: 1.26, unidad: "kg", estado: "CONFIRMADO", origen: { tipo: "USUARIO", actor_id: "USR-CHEF" } },
        modo_entrada: "POR_UNIDAD", version_esperada: "v1", preview_token: "TOKEN-1",
        requiere_confirmacion: true, incidencias: [], datos_reales_modificados: false,
      }) } as Response;
      if (url.endsWith("/rendimiento/confirmar")) return { ok: true, json: async () => ({
        ...base, estado: "CONFIRMADO", escandallo_id: "REC601-1",
        rendimiento_declarado: { cantidad: 7, unidad: "u" },
        rendimiento_neto: confirmed.receta.rendimiento_neto, idempotente: false,
        datos_reales_modificados: true,
      }) } as Response;
      const isRefresh = mock.mock.calls.filter(([called]) => String(called).includes("/elaboraciones/REC601-1")).length > 1;
      return { ok: true, json: async () => ({ ...base, elaboracion: isRefresh ? confirmed : editable, permisos: { confirmar_rendimiento: true } }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    expect((await screen.findAllByText("No confirmado", { selector: "dd" })).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByLabelText("Peso o volumen por unidad"));
    fireEvent.click(screen.getByRole("button", { name: "Vista previa" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Introduce una cantidad mayor que cero.");
    fireEvent.change(screen.getByLabelText("Cantidad de rendimiento neto"), { target: { value: "0,18" } });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Vista previa" }));
    expect(await screen.findByText(/0,18 kg por unidad → 1.26 kg totales/)).toBeInTheDocument();
    expect(screen.getByText(/USR-CHEF/)).toBeInTheDocument();
    const previewCall = mock.mock.calls.find(([called]) => String(called).endsWith("/rendimiento/preview"));
    expect(JSON.parse(String(previewCall?.[1]?.body))).toMatchObject({ cantidad: 0.18, unidad: "kg", modo: "POR_UNIDAD" });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar rendimiento" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Rendimiento confirmado correctamente.");
    expect(screen.getByText("1.26 kg")).toBeInTheDocument();
    const confirmCall = mock.mock.calls.find(([called]) => String(called).endsWith("/rendimiento/confirmar"));
    expect(JSON.parse(String(confirmCall?.[1]?.body))).toMatchObject({ cantidad: 0.18, unidad: "kg", modo: "POR_UNIDAD", preview_token: "TOKEN-1" });
  });

  it("mantiene la ficha en READ cuando falta escandallos:write", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ...base, elaboracion: detail, permisos: { confirmar_rendimiento: false },
    }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    expect(await screen.findByText(/No tienes permiso para confirmar/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Vista previa" })).not.toBeInTheDocument();
  });

  it("abre desde cero y acepta 0,18 por unidad sin validar ni mostrar error automáticamente", async () => {
    const fresh = {
      ...detail,
      receta: {
        ...detail.receta,
        rendimiento: 7,
        unidad_rendimiento: "u",
        rendimiento_neto: null,
      },
    };
    const mock = vi.spyOn(global, "fetch").mockImplementation(async (_input, init) => {
      if (init?.method === "POST") throw new Error("No debe existir POST antes de Vista previa");
      return { ok: true, json: async () => ({
        ...base, elaboracion: fresh, permisos: { confirmar_rendimiento: true },
      }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Salsa de tomate" });
    fireEvent.click(screen.getByLabelText("Peso o volumen por unidad"));
    fireEvent.change(screen.getByLabelText("Cantidad de rendimiento neto"), { target: { value: "0,18" } });
    fireEvent.change(screen.getByLabelText("Unidad de rendimiento neto"), { target: { value: "kg" } });

    expect(screen.getByLabelText("Cantidad de rendimiento neto")).toHaveValue("0,18");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByText(/Cantidad no v[aá]lida/i)).not.toBeInTheDocument();
    const detailCalls = mock.mock.calls.filter(([input]) => String(input).includes("/biblioteca/elaboraciones/REC601-1"));
    expect(detailCalls).toHaveLength(1);
    expect(detailCalls[0]?.[1]?.method).toBe("GET");
  });

  it("muestra el error saneado y descarta una vista previa obsoleta", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/rendimiento/preview")) return { ok: true, json: async () => ({
        ...base, estado: "LISTO_PARA_CONFIRMAR", escandallo_id: "REC601-1",
        rendimiento_declarado: { cantidad: 10, unidad: "raciones" }, rendimiento_neto_actual: null,
        rendimiento_neto_propuesto: { cantidad: 1, unidad: "kg", estado: "CONFIRMADO", origen: { tipo: "USUARIO", actor_id: "USR" } },
        modo_entrada: "TOTAL", version_esperada: "v1", preview_token: "OLD", requiere_confirmacion: true,
        incidencias: [],
      }) } as Response;
      if (String(input).endsWith("/rendimiento/confirmar")) return { ok: false, status: 409, json: async () => ({
        ...base, ok: false, error: { code: "stale_or_invalid_preview", message: "La vista previa ya no corresponde al estado actual." },
      }) } as Response;
      return { ok: true, json: async () => ({ ...base, elaboracion: detail, permisos: { confirmar_rendimiento: true } }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Salsa de tomate" });
    fireEvent.change(screen.getByLabelText("Cantidad de rendimiento neto"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Vista previa" }));
    await screen.findByLabelText("Vista previa del rendimiento");
    fireEvent.click(screen.getByRole("button", { name: "Confirmar rendimiento" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("La vista previa ya no corresponde al estado actual.");
    expect(screen.queryByLabelText("Vista previa del rendimiento")).not.toBeInTheDocument();
  });

  it("muestra una relacion canonica como subelaboracion", async () => {
    const childLine = {
      tipo_componente: "ELABORACION", articulo_id: null,
      escandallo_hijo_id: "REC-CREMA", referencia_elaboracion: "Crema fixture",
      nombre_original: "Crema fixture", cantidad: 0.18, unidad: "kg", merma: 0,
      precio_aplicado: 14, origen_precio: "escandallo_hijo", coste_linea: 2,
      estado_coste: "COSTE_SUBELABORACION_RESUELTO",
      estado_relacion: "elaboracion_relacionada",
    };
    const parent = {
      ...detail,
      id: "REC-PADRE-CREMA", codigo: "REC-PADRE-CREMA", nombre: "Padre crema fixture",
      escandallo: { ...detail.escandallo, lineas: [childLine], coste_total: 2, coste_total_parcial: null, estado_coste: "DISPONIBLE" },
    };
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: parent }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC-PADRE-CREMA?tab=escandallo"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Padre crema fixture" })).toBeInTheDocument();
    expect(screen.getByText("Escandallo hijo")).toBeInTheDocument();
    expect(screen.getByText("Subelaboración")).toBeInTheDocument();
    expect(screen.queryByText("Sin relacionar")).not.toBeInTheDocument();
    expect(screen.getAllByText("2.00 €").length).toBeGreaterThan(0);
  });

  it("distingue campos pendientes de propuestas IA no guardadas", async () => {
    const withProposals = {
      ...detail,
      alergenos: null,
      conservacion: null,
      receta: {
        ...detail.receta,
        procedimiento: null,
        procedimiento_propuesto_ia: "Pochar cebolla 10 min y enfriar.",
        ingredientes_propuestos_no_registrados: ["Sal", "Pimienta"],
        alergenos_posibles: ["Huevo"],
        conservacion_propuesta_ia: "Refrigerado 48 h",
        temperaturas_propuestas_ia: ["Servicio a 65 ºC"],
        tiempos_estimados_ia: { total: "25 min" },
        observaciones_propuestas_ia: "Terminar con hierbas frescas.",
      },
    };
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: withProposals }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Salsa de tomate" })).toBeInTheDocument();
    expect(screen.getAllByText("Pendiente de completar").length).toBeGreaterThan(0);
    expect(screen.getByText("Propuesta IA (no guardada)")).toBeInTheDocument();
    expect(screen.getByText("Pochar cebolla 10 min y enfriar.")).toBeInTheDocument();
    expect(screen.getByText("Posibles alérgenos a revisar")).toBeInTheDocument();
    expect(screen.getByText("Conservación propuesta (orientativa)")).toBeInTheDocument();
    expect(screen.getByText("Ingredientes propuestos no registrados")).toBeInTheDocument();
    expect(screen.getByText("Sal")).toBeInTheDocument();
    expect(screen.getByText("Pimienta")).toBeInTheDocument();
  });

  it("genera, revisa, confirma y relee propuestas IA desde la ruta real de receta", async () => {
    let persisted = false;
    let resolveConfirm!: () => void;
    const currentDetail = () => persisted ? {
      ...detail,
      receta: { ...detail.receta, procedimiento: "Pochar el tomate, triturar y enfriar.", procedimiento_propuesto_ia: null },
      pendientes: ["Conservación"],
      procedencia_campos: { elaboracion: { tipo: "IA", actor_id: "CHEF", estado_revision: "PENDIENTE_REVISION" } },
    } : { ...detail, receta: { ...detail.receta, procedimiento: null }, pendientes: ["Elaboración paso a paso", "Vida útil refrigerado"] };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input); const method = String(init?.method || "GET");
      if (url.endsWith("/api/v1/biblioteca/elaboraciones/REC601-1") && method === "GET") return { ok: true, json: async () => ({ ...base, elaboracion: currentDetail() }) } as Response;
      if (url.endsWith("/documentacion/propuesta")) return { ok: true, json: async () => ({ ...base, datos_propuestos_ia: { elaboracion: "Pochar el tomate, triturar y enfriar.", vida_util_refrigerado: "Conservar refrigerado un máximo de 48 h." }, campos_faltantes_motor: ["Elaboración paso a paso", "Vida útil refrigerado"], generado_ahora: true }) } as Response;
      if (url.endsWith("/documentacion/preview")) return { ok: true, json: async () => ({ ...base, preview_token: "AI-PREVIEW", cambios_seleccionados: { elaboracion: "Pochar el tomate, triturar y enfriar." }, requiere_confirmacion: true }) } as Response;
      if (url.endsWith("/documentacion/confirmar")) return new Promise<Response>((resolve) => {
        resolveConfirm = () => { persisted = true; resolve({ ok: true, json: async () => ({ ...base, estado: "CONFIRMADO", campos_confirmados: ["elaboracion"], idempotente: false, datos_reales_modificados: true, lectura_posterior_verificada: true, receta: currentDetail() }) } as Response); };
      });
      throw new Error(`Unexpected request ${method} ${url}`);
    });
    const view = render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Completar con IA" }));
    expect(await screen.findByRole("heading", { name: "Propuestas IA" })).toBeInTheDocument();
    expect(screen.getAllByText("Pochar el tomate, triturar y enfriar.").length).toBeGreaterThan(0);
    const procedure = screen.getByText("Pochar el tomate, triturar y enfriar.").closest("article")!;
    await userEvent.click(within(procedure).getByRole("button", { name: "Aceptar" }));
    await userEvent.click(screen.getByRole("button", { name: "Continuar" }));
    const preview = await screen.findByLabelText("Vista previa de documentación");
    expect(preview).toHaveTextContent("Pochar el tomate, triturar y enfriar.");
    const confirmButton = within(preview).getByRole("button", { name: "Confirmar" });
    fireEvent.click(confirmButton);
    fireEvent.click(confirmButton);
    expect(await within(preview).findByRole("button", { name: "Guardando..." })).toBeDisabled();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(1);
    resolveConfirm();
    await waitFor(() => expect(screen.getByText("Origen: IA · Pendiente de revisión")).toBeInTheDocument());
    expect(screen.getByRole("status")).toHaveTextContent("Cambios guardados.");
    expect(screen.queryByLabelText("Vista previa de documentación")).not.toBeInTheDocument();
    expect(screen.getAllByText("Pochar el tomate, triturar y enfriar.").length).toBeGreaterThan(0);
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/documentacion/propuesta"))).toBe(true);
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/api/v1/biblioteca/elaboraciones/REC601-1")).length).toBeGreaterThanOrEqual(2);
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(1);
    view.rerender(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    view.rerender(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(1));
    view.unmount();
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Origen: IA · Pendiente de revisión")).toBeInTheDocument();
    expect(screen.getAllByText("Pochar el tomate, triturar y enfriar.").length).toBeGreaterThan(0);
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(1);
  });

  it("no reintenta una confirmación fallida y permite un reintento explícito", async () => {
    const incomplete = { ...detail, receta: { ...detail.receta, procedimiento: null }, pendientes: ["Elaboración paso a paso"] };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input); const method = String(init?.method || "GET");
      if (url.endsWith("/api/v1/biblioteca/elaboraciones/REC601-1") && method === "GET") return { ok: true, json: async () => ({ ...base, elaboracion: incomplete }) } as Response;
      if (url.endsWith("/documentacion/propuesta")) return { ok: true, json: async () => ({ ...base, datos_propuestos_ia: { elaboracion: "Propuesta que requiere confirmación." } }) } as Response;
      if (url.endsWith("/documentacion/preview")) return { ok: true, json: async () => ({ ...base, preview_token: "ERROR-PREVIEW", cambios_seleccionados: { elaboracion: "Propuesta que requiere confirmación." }, requiere_confirmacion: true }) } as Response;
      if (url.endsWith("/documentacion/confirmar")) return { ok: false, status: 409, json: async () => ({ ...base, ok: false, error: { code: "stale_or_invalid_preview", message: "La vista previa ya no es válida." } }) } as Response;
      throw new Error(`Unexpected request ${method} ${url}`);
    });
    const view = render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Completar con IA" }));
    const proposal = (await screen.findByText("Propuesta que requiere confirmación.")).closest("article")!;
    await userEvent.click(within(proposal).getByRole("button", { name: "Aceptar" }));
    await userEvent.click(screen.getByRole("button", { name: "Continuar" }));
    const preview = await screen.findByLabelText("Vista previa de documentación");
    await userEvent.click(within(preview).getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("La vista previa ya no es válida.");
    expect(screen.getByLabelText("Vista previa de documentación")).toBeInTheDocument();
    expect(screen.queryByText("Cambios guardados.")).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(1);
    view.rerender(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(1));
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/documentacion/confirmar"))).toHaveLength(2));
  });

  it("explica los campos que requieren información manual cuando no hay propuestas", async () => {
    const incomplete = { ...detail, receta: { ...detail.receta, procedimiento: "Procedimiento existente", tiempo_total: null }, pendientes: ["Categoría", "Producción máxima por tanda"] };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input); const method = String(init?.method || "GET");
      if (url.endsWith("/api/v1/biblioteca/elaboraciones/REC601-1") && method === "GET") return { ok: true, json: async () => ({ ...base, elaboracion: incomplete }) } as Response;
      if (url.endsWith("/documentacion/propuesta")) return { ok: true, json: async () => ({ ...base, datos_propuestos_ia: {}, campos_pendientes_no_proponibles: ["Categoría", "Producción máxima por tanda"] }) } as Response;
      throw new Error(`Unexpected request ${method} ${url}`);
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Completar con IA" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No puedo completar automáticamente estos campos: Categoría, Producción máxima por tanda. Necesitan información del usuario.");
    expect(screen.queryByText("No se generaron propuestas seguras para los campos pendientes.")).not.toBeInTheDocument();
  });

  it("el asistente no presenta un candidato como relación canónica confirmada", async () => {
    const candidate = { ...ingredient, nombre_original: "chalota", articulo_id: "ART000112", articulo_codigo: "ART000112", articulo_nombre: "Cebolla chalota", estado_relacion: "coincidencia_dudosa" };
    const current = { ...detail, receta: { ...detail.receta, ingredientes: [candidate] } };
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: current }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Completar receta" }));
    expect(screen.getByLabelText("Asistente de completitud operativa")).toHaveTextContent("Relaciones confirmadas0/1");
    expect(screen.getByLabelText("Relaciones de ingredientes")).toHaveTextContent("Sin artículo vinculado");
    expect(screen.queryByText(/Vinculado a: Cebolla chalota/)).not.toBeInTheDocument();
  });

  it("completa artículo y referencia manual desde ElaboracionDetailPage", async () => {
    const current = { ...detail, receta: { ...detail.receta, ingredientes: [ingredientWithoutPrice] } };
    let article: any = { id: "ART-002", codigo: "ART-002", nombre: "Sal", estado: "ACTIVO", con_stock: false, tiene_ficha_tecnica: false, precio: null, precios: [], familia: null, unidad_base: null, precios_referencia: [] };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input); const method = String(init?.method || "GET");
      if (url.endsWith("/biblioteca/elaboraciones/REC601-1") && method === "GET") return { ok: true, json: async () => ({ ...base, elaboracion: current }) } as Response;
      if (url.endsWith("/articulos/ART-002") && method === "GET") return { ok: true, json: async () => ({ ...base, articulo: article }) } as Response;
      if (url.endsWith("/documentacion/propuesta")) return { ok: true, json: async () => ({ ...base, datos_propuestos_ia: { familia: "Condimentos" } }) } as Response;
      if (url.endsWith("/documentacion/preview")) return { ok: true, json: async () => ({ ...base, preview_token: "AI-TOKEN" }) } as Response;
      if (url.endsWith("/documentacion/confirmar")) { article = { ...article, familia: "Condimentos" }; return { ok: true, json: async () => ({ ...base, articulo: article }) } as Response; }
      if (url.endsWith("/precio-referencia-manual/preview")) return { ok: true, json: async () => ({ ...base, preview_token: "PRICE-TOKEN", referencia_propuesta: { tipo: "PRECIO_REFERENCIA_MANUAL", origen: "USUARIO", precio_comercial: 4, cantidad_formato: 500, unidad_formato: "g", precio_normalizado: 8, unidad_normalizada: "kg", autoridad: "REFERENCIA_NO_REAL" } }) } as Response;
      if (url.endsWith("/precio-referencia-manual/confirmar")) { article = { ...article, precios_referencia: [{ tipo: "PRECIO_REFERENCIA_MANUAL", precio_normalizado: 8, unidad_normalizada: "kg" }] }; return { ok: true, json: async () => ({ ...base, articulo: article }) } as Response; }
      throw new Error(`Unexpected request ${method} ${url}`);
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Completar artículo con IA" }));
    const proposalCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/documentacion/propuesta"));
    expect(JSON.parse(String((proposalCall?.[1] as RequestInit).body)).culinary_context).toMatchObject({ ingrediente_original: ingredientWithoutPrice.nombre_original, receta_nombre: detail.nombre, receta_id: detail.codigo });
    await userEvent.click(await screen.findByRole("button", { name: "Continuar" }));
    await userEvent.click(within((await screen.findByText("PREVIEW IA")).parentElement as HTMLElement).getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByText(/Artículo completado y verificado/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Introducir referencia manual" }));
    await userEvent.type(screen.getByLabelText("Precio (€)"), "4");
    await userEvent.clear(screen.getByLabelText("Cantidad")); await userEvent.type(screen.getByLabelText("Cantidad"), "500");
    await userEvent.selectOptions(screen.getByLabelText("Unidad"), "g");
    await userEvent.click(screen.getByRole("button", { name: "Preview" }));
    expect(await screen.findByText("Precio normalizado: 8.00 €/kg")).toBeInTheDocument();
    await userEvent.click(within(screen.getByText("PRECIO DE REFERENCIA MANUAL").parentElement as HTMLElement).getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByText(/Referencia manual persistida y verificada/)).toBeInTheDocument();
  });

  /* Retirado: la búsqueda web de precios ya no forma parte del producto.
  it("busca, previsualiza y confirma una referencia web desde ElaboracionDetailPage", async () => {
    const current = { ...detail, nombre: "SALSA DE CAVA", codigo: "SALSA-DE-CAVA", receta: { ...detail.receta, ingredientes: [{ ...ingredientWithoutPrice, nombre_original: "cava", nombre_articulo: "Cava para cocinar" }] } };
    const candidate = { tipo: "PRECIO_REFERENCIA_WEB", origen: "WEB", producto: "Cava cocina X", tienda_referencia: "Makro", precio_comercial: 3, cantidad_formato: 750, unidad_formato: "ml", precio_normalizado: 4, unidad_normalizada: "l", url: "https://makro.example/cava", consultado_en: "2026-08-26T12:00:00+02:00", autoridad: "REFERENCIA_NO_REAL" };
    let article: any = { id: "ART-002", codigo: "ART-002", nombre: "Cava para cocinar", estado: "ACTIVO", con_stock: false, tiene_ficha_tecnica: false, precio: null, precios: [], familia: "Bebidas", unidad_base: "l", precios_referencia: [] };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input); const method = String(init?.method || "GET");
      if (url.endsWith("/biblioteca/elaboraciones/REC601-1") && method === "GET") return { ok: true, json: async () => ({ ...base, elaboracion: current }) } as Response;
      if (url.endsWith("/articulos/ART-002") && method === "GET") return { ok: true, json: async () => ({ ...base, articulo: article }) } as Response;
      if (url.endsWith("/precio-referencia-web/buscar")) return { ok: true, json: async () => ({ ...base, candidatos: [candidate, { ...candidate, producto: "Cava Y", tienda_referencia: "Carrefour", precio_comercial: 3.5, precio_normalizado: 4.6667, url: "https://carrefour.example/cava" }], total: 2 }) } as Response;
      if (url.endsWith("/precio-referencia-web/preview")) return { ok: true, json: async () => ({ ...base, preview_token: "WEB-TOKEN", referencia_propuesta: candidate }) } as Response;
      if (url.endsWith("/precio-referencia-web/confirmar")) { article = { ...article, precios_referencia: [candidate] }; return { ok: true, json: async () => ({ ...base, articulo: article, referencia: candidate, lectura_posterior_verificada: true }) } as Response; }
      throw new Error(`Unexpected request ${method} ${url}`);
    });
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Buscar precio online" }));
    expect(await screen.findByText("REFERENCIAS ENCONTRADAS")).toBeInTheDocument();
    expect(screen.getByText("Makro")).toBeInTheDocument();
    expect(screen.getByText("Carrefour")).toBeInTheDocument();
    const searchCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/precio-referencia-web/buscar"));
    const searchBody = JSON.parse(String((searchCall?.[1] as RequestInit).body));
    expect(searchBody.context).toMatchObject({ article_name: "Cava para cocinar", ingredient_name: "cava", usage_context: "cocina / ingrediente de receta" });
    await userEvent.click(screen.getAllByRole("button", { name: "Usar esta referencia" })[0]);
    expect(await screen.findByText("PRECIO DE REFERENCIA WEB")).toBeInTheDocument();
    expect(screen.getByText(/NO REPRESENTA UNA COMPRA REAL/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/precio-referencia-web/confirmar"))).toHaveLength(0);
    await userEvent.click(within(screen.getByText("PRECIO DE REFERENCIA WEB").parentElement as HTMLElement).getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByText(/Referencia web persistida y verificada/)).toBeInTheDocument();
    expect(screen.getByText("Proveedor/Tienda de referencia: Makro")).toBeInTheDocument();
    expect(screen.getByText(/Origen: WEB · REFERENCIA/)).toBeInTheDocument();
  }); */

  it("no ofrece búsqueda web de precios desde la receta", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: detail, permisos: { confirmar_rendimiento: true } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Salsa de tomate" });
    expect(screen.queryByRole("button", { name: "Buscar precio online" })).not.toBeInTheDocument();
  });
  it("distingue un escandallo provisional y la referencia externa de un precio confirmado", async () => {
    const referenceIngredient = {
      ...ingredient,
      origen_precio: "referencia_externa",
      clasificacion_precio: "REFERENCIA",
      precio_provisional: true,
      tienda_referencia: "Tienda externa",
    };
    const provisional = {
      ...detail,
      estado_coste: "PROVISIONAL",
      coste_completo: false,
      coste_provisional: true,
      escandallo: {
        ...detail.escandallo,
        estado_coste: "PROVISIONAL",
        coste_provisional: true,
        precios_confirmados: 0,
        precios_referencia: 1,
        completitud_coste_porcentaje: 100,
        lineas: [referenceIngredient],
        coste_total: 2,
        coste_total_parcial: null,
      },
    };
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: provisional }) } as Response);

    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=escandallo"]}><App /></MemoryRouter>);

    expect(await screen.findByText("Escandallo provisional")).toBeInTheDocument();
    expect(screen.getByText(/No es un coste real confirmado/)).toBeInTheDocument();
    expect(screen.getByText("Referencia externa · provisional")).toBeInTheDocument();
    expect(screen.getByText("Referencia externa (provisional)")).toBeInTheDocument();
    expect(screen.getByText(/Completitud del coste:/).parentElement).toHaveTextContent("100%");
  });
});
