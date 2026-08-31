import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { App } from "../ui/App";

function last<T>(items: T[]): T {
  return items[items.length - 1];
}

function response(existencias: unknown[]) {
  return {
    ok: true,
    version: "6.1",
    api_version: "1.0",
    request_id: "REQ-STOCK-1",
    modo_seguro: true,
    datos_reales_modificados: false,
    dashboard: {
      modulos: {
        stock: {
          estado: existencias.length ? "datos_disponibles" : "sin_datos",
          total: existencias.length ? 1 : 0,
          items: existencias.length
            ? [{ tipo: "bajo_stock", nivel: "alto", mensaje: "Tomate bajo mínimo." }]
            : [],
          alertas: existencias.length
            ? [{ tipo: "bajo_stock", nivel: "alto", mensaje: "Tomate bajo mínimo." }]
            : [],
          existencias,
          lotes: existencias.length
            ? [{ id: "LOTE-1", nombre: "Tomate", cantidad: 4, unidad: "kg", ubicacion: "Cámara", caducidad: "2026-08-02" }]
            : [],
          movimientos: existencias.length
            ? [{ id: "MOV-1", tipo: "entrada", nombre: "Tomate", cantidad: 4, unidad: "kg", motivo: "Recepción" }]
            : [],
          caducidades: [],
          resumen: {
            articulos: existencias.length,
            lotes: existencias.length,
            movimientos: existencias.length,
            alertas: existencias.length,
          },
        },
      },
    },
  };
}

function renderPage() {
  return render(<MemoryRouter initialEntries={["/stock"]}><App /></MemoryRouter>);
}

describe("Stock", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("muestra existencias, lotes, movimientos y alertas del dashboard", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => response([{
        clave: "ART-TOMATE",
        nombre: "Tomate",
        cantidad: 4,
        unidad: "kg",
        familia: "Verduras",
        lotes: [{ id: "LOTE-1" }],
      }]),
    } as Response);

    renderPage();
    expect(screen.getByText("Cargando stock...")).toBeInTheDocument();
    const existencias = await screen.findByLabelText("Resumen de stock");
    expect(within(existencias).getByText("Artículos")).toBeInTheDocument();
    expect(screen.getAllByText("Tomate").length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText("Tomate bajo mínimo.")).toBeInTheDocument();
    expect(screen.getByText("Cámara")).toBeInTheDocument();
    expect(screen.getByText("Entrada · Recepción")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-STOCK-1")).toBeInTheDocument();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/dashboard"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra el estado sin datos", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => response([]),
    } as Response);
    renderPage();
    expect(await screen.findByText("No hay existencias de stock registradas.")).toBeInTheDocument();
  });

  it("muestra un error controlado y conserva request_id", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        ok: false,
        version: "6.1",
        api_version: "1.0",
        request_id: "REQ-STOCK-ERROR",
        modo_seguro: true,
        datos_reales_modificados: false,
        error: { message: "Stock no disponible temporalmente." },
      }),
    } as Response);
    renderPage();
    expect(await screen.findByText("Stock no disponible temporalmente.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-STOCK-ERROR")).toBeInTheDocument();
  });

  it("ajusta stock mediante preview y confirmación y refresca la vista", async () => {
    let saved = false;
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/articulos?")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-ART", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [{ id: "ART-PATATA", codigo: "ART-PATATA", nombre: "Patata Monalisa", unidad: "kg", estado: "activo", con_stock: false, tiene_ficha_tecnica: false }], total: 1, page: 1, page_size: 25, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      if (url.endsWith("/api/v1/stock/ubicaciones")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-LOC", modo_seguro: true, datos_reales_modificados: false, ubicaciones: [] }) } as Response;
      if (url.endsWith("/api/v1/stock/ajustes/preview")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-PREVIEW", modo_seguro: true, preview_token: "TOKEN", stock_anterior: 0, stock_resultante: 0.5, diferencia: 0.5, unidad: "kg", motivo: "Recuento", requiere_confirmacion: true, datos_reales_modificados: false }) } as Response;
      if (url.endsWith("/api/v1/stock/ajustes/confirmar")) { saved = true; return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-CONFIRM", modo_seguro: true, datos_reales_modificados: true, estado: "CONFIRMADO", idempotente: false, mensaje: "Movimiento registrado correctamente.", movimiento: { id: "MOV-2" }, stock_anterior: 0, stock_actual: 0.5 }) } as Response; }
      return { ok: true, json: async () => response(saved ? [{ clave: "ART-PATATA", articulo_id: "ART-PATATA", nombre: "Patata Monalisa", cantidad: 0.5, unidad: "kg", familia: "Verduras", lotes: [{ id: "LOTE-2" }] }] : []) } as Response;
    });
    renderPage();
    await screen.findByText("No hay existencias de stock registradas.");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Ajustar stock" })));
    await userEvent.type(last(screen.getAllByLabelText("Buscar artículo")), "Patata");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Buscar" })));
    await userEvent.selectOptions(last(await screen.findAllByLabelText("Artículo")), "ART-PATATA");
    expect(last(screen.getAllByLabelText("Artículo"))).toHaveValue("ART-PATATA");
    await userEvent.type(last(screen.getAllByLabelText("Cantidad real")), "0.5");
    await userEvent.type(last(screen.getAllByLabelText("Motivo obligatorio")), "Recuento");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Vista previa" })));
    expect(await screen.findByText("Stock anterior: 0 kg")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/stock/ajustes/confirmar"))).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "Confirmar ajuste" }));
    expect(await screen.findByText("Movimiento registrado correctamente.")).toBeInTheDocument();
    expect((await screen.findAllByText("Patata Monalisa")).length).toBeGreaterThan(0);
    expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/stock/ajustes/confirmar") && init?.method === "POST")).toBe(true);
  });

  it("muestra cero resultados sin seleccionar ni modificar Stock", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/articulos?")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-EMPTY", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 25, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      return { ok: true, json: async () => response([]) } as Response;
    });
    renderPage();
    await screen.findByText("No hay existencias de stock registradas.");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Ajustar stock" })));
    await userEvent.type(last(screen.getAllByLabelText("Buscar artículo")), "No existe");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Buscar" })));
    expect(await screen.findByText("No se encontraron artículos.")).toBeInTheDocument();
    expect(last(screen.getAllByLabelText("Artículo"))).toHaveValue("");
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/stock/movimientos"))).toBe(false);
  });

  it("muestra resultados justo debajo del buscador y limpiar restaura la vista normal", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => response([{ clave: "ART-TOMATE", articulo_id: "ART-TOMATE", nombre: "Tomate", cantidad: 4, unidad: "kg", familia: "Verduras", lotes: [{ id: "LOTE-1" }] }]) } as Response);
    renderPage();
    await screen.findByLabelText("Resumen de stock");
    const search = screen.getByLabelText("Buscar stock");
    await userEvent.type(search, "Cámara");
    const results = screen.getByLabelText("Resultados de búsqueda");
    const summary = screen.getByLabelText("Resumen de stock");
    expect(search.compareDocumentPosition(results) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(results.compareDocumentPosition(summary) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(results).getByText(/LOTE-1/)).toBeInTheDocument();
    expect(within(results).getByRole("link", { name: "Abrir" })).toHaveAttribute("href", "/stock?lote_id=LOTE-1");
    await userEvent.click(screen.getByRole("button", { name: "Limpiar buscar stock" }));
    expect(screen.queryByLabelText("Resultados de búsqueda")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Resumen de stock")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Existencias actuales" })).toBeInTheDocument();
  });

  it("muestra solo acciones canónicas: ficha, ubicación y corrección por ajuste", async () => {
    const payload = response([{ clave: "ART-TOMATE", articulo_id: "ART-TOMATE", nombre: "Tomate", cantidad: 4, unidad: "kg", familia: "Verduras", lotes: [{ id: "LOTE-1" }] }]);
    const stock = payload.dashboard.modulos.stock;
    (stock.movimientos as Array<Record<string, unknown>>) = [{ id: "MOV-1", articulo_id: "ART-TOMATE", tipo: "entrada", nombre: "Tomate", cantidad: 4, unidad: "kg", motivo: "Recepción" }];
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => payload } as Response);
    renderPage();
    await screen.findByLabelText("Resumen de stock");
    expect(screen.getByRole("link", { name: "Editar ficha" })).toHaveAttribute("href", "/articulos/ART-TOMATE?edit=1");
    expect(screen.getByRole("button", { name: "Asignar ubicación" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Corregir con ajuste" })).toHaveAttribute("href", "/stock?article_id=ART-TOMATE");
    expect(screen.queryByRole("button", { name: /eliminar|borrar|editar movimiento/i })).not.toBeInTheDocument();
  });

  it("abre detalle inmutable de movimiento, alerta, lote y ubicación con acciones reales", async () => {
    const payload = response([{ clave: "ART-TOMATE", articulo_id: "ART-TOMATE", nombre: "Tomate", cantidad: 4, unidad: "kg", familia: "Verduras", lotes: [{ id: "LOTE-1" }] }]);
    const stock = payload.dashboard.modulos.stock;
    (stock.alertas as Array<Record<string, unknown>>) = [{ tipo: "sin_ubicacion", nivel: "alto", mensaje: "Lote sin ubicación", articulo_id: "ART-TOMATE", lote_id: "LOTE-1" }];
    (stock.movimientos as Array<Record<string, unknown>>) = [{ id: "MOV-1", articulo_id: "ART-TOMATE", lote_id: "LOTE-1", tipo: "entrada", nombre: "Tomate", cantidad: 4, unidad: "kg", motivo: "Recepción", creado_en: "2026-08-25T10:00:00" }];
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/stock/ubicaciones")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-LOC", modo_seguro: true, datos_reales_modificados: false, ubicaciones: [{ id: "Cámara", nombre: "Cámara", total_lotes: 1, total_articulos: 1, lotes: [{ id: "LOTE-1", nombre: "Tomate", cantidad: 4, unidad: "kg" }] }] }) } as Response;
      if (url.endsWith("/api/v1/stock/lotes/LOTE-1")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-LOT", modo_seguro: true, datos_reales_modificados: false, lote: { id: "LOTE-1", articulo_id: "ART-TOMATE", nombre: "Tomate", cantidad: 4, unidad: "kg", ubicacion: "Cámara", fecha_entrada: "2026-08-25", origen: "Recepción", estado: "activo" }, incidencias: [], movimientos: [{ id: "MOV-1", tipo: "entrada", cantidad: 4, unidad: "kg" }], acciones: ["CAMBIAR_UBICACION", "REGISTRAR_AJUSTE"] }) } as Response;
      return { ok: true, json: async () => payload } as Response;
    });
    renderPage();
    await screen.findByLabelText("Resumen de stock");
    const movementsSection = screen.getByRole("heading", { name: "Movimientos recientes" }).closest("section")!;
    await userEvent.click(within(movementsSection).getByRole("button", { name: "Abrir" }));
    const movement = await screen.findByLabelText("Detalle del movimiento");
    expect(within(movement).getByText("Este movimiento es histórico e inmutable.")).toBeInTheDocument();
    expect(within(movement).getByRole("link", { name: "Corregir con ajuste" })).toHaveAttribute("href", "/stock?article_id=ART-TOMATE");
    await userEvent.click(screen.getByText("Lote sin ubicación"));
    expect(screen.getAllByRole("button", { name: "Asignar ubicación" }).length).toBeGreaterThan(0);
    const lotsSection = document.getElementById("stock-lotes")!.closest("section")!;
    await userEvent.click(within(lotsSection).getByRole("button", { name: "Asignar ubicación" }));
    expect(await screen.findByLabelText("Asignar ubicación")).toHaveTextContent("Movimientos relacionados");
    const locationsSection = screen.getByRole("heading", { name: "Ubicaciones" }).closest("section")!;
    await userEvent.click(within(locationsSection).getByRole("button", { name: "Abrir" }));
    expect(await screen.findByLabelText("Detalle de ubicación")).toHaveTextContent("Tomate");
  });

  it("resuelve una alerta real de ubicación sin navegación circular y verifica la relectura", async () => {
    let confirmed = false;
    const dashboard = () => {
      const payload = response([{ clave: "ART-TOMATE", articulo_id: "ART-TOMATE", nombre: "Tomate", cantidad: 5, unidad: "kg", familia: "Verduras", lotes: [{ id: "LOTE-1" }] }]);
      const stock = payload.dashboard.modulos.stock;
      stock.lotes = [{ id: "LOTE-1", nombre: "Tomate", cantidad: 5, unidad: "kg", ubicacion: confirmed ? "Cámara" : "", caducidad: "2026-09-02" }];
      stock.alertas = (confirmed ? [] : [{ tipo: "sin_ubicacion", nivel: "alto", mensaje: "Lote sin ubicación", articulo_id: "ART-TOMATE", lote_id: "LOTE-1" }]) as any;
      stock.resumen.alertas = stock.alertas.length;
      return payload;
    };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input); const method = String(init?.method || "GET");
      const envelope = { ok: true, version: "6.1", api_version: "1.0", request_id: "REQ", modo_seguro: true, datos_reales_modificados: false };
      if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => dashboard() } as Response;
      if (url.endsWith("/api/v1/stock/ubicaciones")) return { ok: true, json: async () => ({ ...envelope, ubicaciones: ["Congelador", "Cámara", "Seco", "Bodega", "Limpieza"].map((nombre) => ({ id: nombre, nombre })) }) } as Response;
      if (url.endsWith("/api/v1/stock/lotes/LOTE-1") && method === "GET") return { ok: true, json: async () => ({ ...envelope, lote: { id: "LOTE-1", articulo_id: "ART-TOMATE", nombre: "Tomate", cantidad: 5, unidad: "kg", ubicacion: confirmed ? "Cámara" : "" }, incidencias: confirmed ? [] : [{ code: "SIN_UBICACION", message: "Lote sin ubicación" }], movimientos: [], acciones: ["CAMBIAR_UBICACION"] }) } as Response;
      if (url.endsWith("/ubicacion/preview")) return { ok: true, json: async () => ({ ...envelope, preview_token: "LOCATION", lote_antes: { id: "LOTE-1", cantidad: 5, unidad: "kg", ubicacion: "" }, lote_despues: { id: "LOTE-1", cantidad: 5, unidad: "kg", ubicacion: "Cámara" }, requiere_confirmacion: true }) } as Response;
      if (url.endsWith("/ubicacion/confirmar")) { confirmed = true; return { ok: true, json: async () => ({ ...envelope, datos_reales_modificados: true, lote: { id: "LOTE-1", cantidad: 5, unidad: "kg", ubicacion: "Cámara" } }) } as Response; }
      throw new Error(`Unexpected request ${method} ${url}`);
    });
    renderPage();
    await userEvent.click(await screen.findByText("Lote sin ubicación"));
    const alerts = screen.getByRole("heading", { name: "Alertas de stock" }).closest("section")!;
    const clickedAlert = within(alerts).getByText("Lote sin ubicación").closest("details")!;
    await userEvent.click(within(clickedAlert).getByRole("button", { name: "Asignar ubicación" }));
    const panel = await screen.findByLabelText("Asignar ubicación");
    expect(clickedAlert).toContainElement(panel);
    expect(within(panel).getAllByText("Tomate").length).toBeGreaterThan(0);
    expect(within(panel).getAllByText("5 kg").length).toBeGreaterThan(0);
    expect(within(panel).getAllByRole("option").map((option) => option.textContent)).toEqual(["Seleccionar", "Congelador", "Cámara", "Seco", "Bodega", "Limpieza"]);
    await userEvent.selectOptions(within(panel).getByLabelText("Ubicación canónica"), "Cámara");
    await userEvent.click(within(panel).getByRole("button", { name: "Continuar" }));
    expect(await within(panel).findByLabelText("Vista previa de ubicación")).toHaveTextContent("Sin ubicación");
    await userEvent.click(within(panel).getByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(screen.queryByText("Lote sin ubicación")).not.toBeInTheDocument());
    expect(screen.getAllByText("Cámara").length).toBeGreaterThan(0);
    expect(screen.getAllByText("5 kg").length).toBeGreaterThan(0);
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/api/v1/stock/lotes/LOTE-1")).length).toBeGreaterThanOrEqual(2);
  });

  it("cancelar un ajuste descarta el preview y no confirma ningún WRITE", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const base = { ok: true, version: "6.1", api_version: "1.0", request_id: "REQ", modo_seguro: true, datos_reales_modificados: false };
      if (url.includes("/api/v1/articulos?")) return { ok: true, json: async () => ({ ...base, catalogo: { items: [{ id: "ART-1", codigo: "ART-1", nombre: "Tomate", unidad: "kg", estado: "activo" }], total: 1, page: 1, page_size: 25, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      if (url.endsWith("/ajustes/preview")) return { ok: true, json: async () => ({ ...base, preview_token: "TOKEN", stock_anterior: 4, stock_resultante: 3, diferencia: -1, unidad: "kg", motivo: "Recuento", requiere_confirmacion: true }) } as Response;
      if (url.endsWith("/ajustes/descartar")) return { ok: true, json: async () => ({ ...base, estado: "DESCARTADO" }) } as Response;
      if (url.endsWith("/stock/ubicaciones")) return { ok: true, json: async () => ({ ...base, ubicaciones: [] }) } as Response;
      return { ok: true, json: async () => response([]) } as Response;
    });
    renderPage(); await screen.findByText("No hay existencias de stock registradas.");
    await userEvent.click(screen.getByRole("button", { name: "Ajustar stock" }));
    await userEvent.type(screen.getByLabelText("Buscar artículo"), "Tomate"); await userEvent.click(screen.getByRole("button", { name: "Buscar" }));
    await userEvent.selectOptions(screen.getByLabelText("Artículo"), "ART-1"); await userEvent.type(screen.getByLabelText("Cantidad real"), "3"); await userEvent.type(screen.getByLabelText("Motivo obligatorio"), "Recuento");
    await userEvent.click(screen.getByRole("button", { name: "Vista previa" })); await screen.findByText("Stock anterior: 4 kg");
    await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/ajustes/descartar"))).toBe(true);
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/ajustes/confirmar"))).toBe(false);
  });
});
