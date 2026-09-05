import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { App } from "../ui/App";

const envelope = { ok: true, version: "1.0", api_version: "1.0", request_id: "CAT-1", modo_seguro: true, datos_reales_modificados: false };
const item = { id: "ART-001", codigo: "ART-001", nombre: "Tomate pera", familia: "Verduras", proveedor: "Huerta Sur", precio: 2.5, unidad: "kg", estado: "ACTIVO", stock: 8, unidad_stock: "kg", con_stock: true, tiene_ficha_tecnica: false };

describe("Catálogo de artículos", () => {
  afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); });

  it("lista datos reales, busca con debounce y conserva la ruta", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...envelope, catalogo: { items: [item], total: 1, page: 1, page_size: 20, total_pages: 1, filtros: { familias: ["Verduras"], proveedores: ["Huerta Sur"], estados: ["ACTIVO"] }, capacidades: {} } }) } as Response);
    render(<MemoryRouter initialEntries={["/articulos"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Tomate pera")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Buscar artículos"), { target: { value: "tomate" } });
    await waitFor(() => expect(global.fetch).toHaveBeenLastCalledWith(expect.stringContaining("q=tomate"), expect.objectContaining({ method: "GET" })), { timeout: 1000 });
    expect(global.fetch).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/articulos?q=tomate&orden=nombre&direccion=asc&page=1&page_size=20",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("precarga y aplica q al entrar desde Chat", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...envelope, catalogo: { items: [item], total: 1, page: 1, page_size: 20, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response);
    render(<MemoryRouter initialEntries={["/articulos?q=Patata%20Monalisa"]}><App /></MemoryRouter>);
    expect(screen.getByLabelText(/Buscar art/)).toHaveValue("Patata Monalisa");
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("q=Patata+Monalisa"), expect.objectContaining({ method: "GET" })));
  });

  it("abre la ficha contextual y muestra ausencias sin inventar relaciones", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...envelope, articulo: { ...item, unidad_base: "kg", precio_incluye_iva: false, alergenos: [], stock_detalle: { cantidad: 8, unidad: "kg", lotes: [] }, proveedores: [], precios: [], documentos: [], ficha_tecnica: null, recetas: [], escandallos: [], historial: [], operatividad: { stock: true, compras: true, escandallos: true }, edicion: { unidades_base: ["kg", "g", "l", "ml", "u"], proveedores: [{ id: "PROV-1", nombre: "Huerta Sur" }] } } }) } as Response);
    render(<MemoryRouter initialEntries={["/articulos/ART-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Tomate pera" })).toBeInTheDocument();
    expect(screen.getByText("No hay relaciones verificables con recetas o escandallos.")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/articulos/ART-001"), expect.objectContaining({ method: "GET" }));
  });

  it("edita la ficha maestra, conserva el id y refresca su estado operativo", async () => {
    const detail = { ...item, unidad_base: null, unidad_compra: null, cantidad_formato: null, proveedor: null, precio: 2.5, precio_incluye_iva: false, alergenos: [], stock_detalle: { cantidad: null, unidad: null, lotes: [] }, proveedores: [], precios: [], documentos: [], ficha_tecnica: null, recetas: [], escandallos: [], historial: [], operatividad: { stock: false, compras: false, escandallos: false }, edicion: { unidades_base: ["kg", "g", "l", "ml", "u"], proveedores: [{ id: "PROV-1", nombre: "Huerta Sur" }] } };
    const updated = { ...detail, unidad_base: "kg", unidad_compra: "saco", cantidad_formato: 10, proveedor: "Huerta Sur", operatividad: { stock: true, compras: true, escandallos: true } };
    let confirmed = false;
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => { const url = String(input); if (url.endsWith("/catalogo/preview")) return { ok: true, json: async () => ({ ...envelope, preview_token: "TOKEN", propuesto: updated, requiere_confirmacion: true }) } as Response; if (url.endsWith("/catalogo/confirmar")) { confirmed = true; return { ok: true, json: async () => ({ ...envelope, datos_reales_modificados: true, registro: updated, idempotente: false }) } as Response; } return { ok: true, json: async () => ({ ...envelope, articulo: confirmed ? updated : detail }) } as Response; });
    render(<MemoryRouter initialEntries={["/articulos/ART-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Editar artículo" }));
    await userEvent.type(screen.getByLabelText("Unidad base"), "kg");
    await userEvent.type(screen.getByLabelText("Unidad de compra"), "saco");
    await userEvent.type(screen.getByLabelText("Cantidad por formato"), "10");
    await userEvent.type(screen.getByLabelText("Proveedor preferente"), "Huerta Sur");
    await userEvent.click(screen.getByRole("button", { name: "Revisar y guardar" }));
    await userEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
    await screen.findByText("10 kg");
    expect(screen.getAllByText("Sí").length).toBe(3);
    const previewCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/catalogo/preview"));
    expect(JSON.parse(String(previewCall?.[1]?.body)).payload.unidad_base).toBe("kg");
  });

  it("muestra el error de validación devuelto al guardar", async () => {
    const detail = { ...item, unidad_base: null, precio_incluye_iva: false, alergenos: [], stock_detalle: { cantidad: null, unidad: null, lotes: [] }, proveedores: [], precios: [], documentos: [], ficha_tecnica: null, recetas: [], escandallos: [], historial: [], operatividad: { stock: false, compras: false, escandallos: false }, edicion: { unidades_base: ["kg"], proveedores: [] } };
    vi.spyOn(global, "fetch").mockImplementation(async (input) => String(input).endsWith("/catalogo/preview") ? ({ ok: false, status: 422, json: async () => ({ ...envelope, ok: false, error: { message: "El precio debe ser mayor que cero." } }) } as Response) : ({ ok: true, json: async () => ({ ...envelope, articulo: detail }) } as Response));
    render(<MemoryRouter initialEntries={["/articulos/ART-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Editar artículo" }));
    await userEvent.type(screen.getByLabelText("Unidad base"), "kg");
    await userEvent.click(screen.getByRole("button", { name: "Revisar y guardar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("El precio debe ser mayor que cero.");
  });

  it("muestra estados vacío y error controlado", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true, json: async () => ({ ...envelope, catalogo: { items: [], total: 0, page: 1, page_size: 20, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response);
    const first = render(<MemoryRouter initialEntries={["/articulos"]}><App /></MemoryRouter>);
    expect(await screen.findByText("No hay artículos para los filtros seleccionados.")).toBeInTheDocument();
    first.unmount();
    fetchMock.mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ ...envelope, ok: false, error: { message: "Catálogo temporalmente no disponible." } }) } as Response);
    render(<MemoryRouter initialEntries={["/articulos"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Catálogo temporalmente no disponible.")).toBeInTheDocument();
  });

  it("abre el enriquecimiento externo por ruta, previsualiza y confirma solo referencias", async () => {
    const reference = {
      tipo: "PRECIO_REFERENCIA_WEB", origen: "IMPORTADO", producto: "Estragón fresco", tienda_referencia: "Proveedor externo",
      precio_comercial: 2.5, moneda: "EUR", cantidad_formato: 100, unidad_formato: "g",
      precio_normalizado: 25, unidad_normalizada: "kg", url: "https://example.test/estragon",
      autoridad: "REFERENCIA_NO_REAL",
    };
    let confirmed = false;
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/articulos/sin-precio")) return { ok: true, json: async () => ({ ...envelope, articulos: [{ article_id: "ART-ESTRAGON", codigo: "ART-ESTRAGON", articulo: "Estragón fresco", unidad_base: "g", unidad_compra: "g", recetas: ["REC-A"], usado_en_recetas: 1, precio_real: null, proveedor_real: null, referencia: confirmed ? reference : null, estado: confirmed ? "CON_REFERENCIA" : "SIN_PRECIO" }], total: 1, costes_derivados: [], coste_ia_usd: "0.00000000" }) } as Response;
      if (url.endsWith("/referencias-importadas/estado")) return { ok: true, json: async () => ({ ...envelope, workflow: confirmed ? { estado: "CONFIRMADO", preview: { ...envelope, formato_detectado: "CSV", listas: [{ fila: 1, article_id: "ART-ESTRAGON", articulo: "Estragón fresco", precio_real_actual: null, proveedor_real_actual: null, referencia: reference, preview_token: "REF-PREVIEW", incluir: true }], ambiguas: [], invalidas: [], resumen: { listas: 1, ambiguas: 0, invalidas: 0 }, requiere_confirmacion: true, coste_ia_usd: "0.00000000" }, updated_at: "2026-09-01T12:00:00Z" } : null }) } as Response;
      if (url.endsWith("/referencias-importadas/preview")) return { ok: true, json: async () => ({ ...envelope, formato_detectado: "CSV", listas: [{ fila: 1, article_id: "ART-ESTRAGON", articulo: "Estragón fresco", precio_real_actual: null, proveedor_real_actual: null, referencia: reference, preview_token: "REF-PREVIEW", incluir: true }], ambiguas: [], invalidas: [], resumen: { listas: 1, ambiguas: 0, invalidas: 0 }, requiere_confirmacion: true, precio_real_modificado: false, proveedor_real_modificado: false, coste_ia_usd: "0.00000000" }) } as Response;
      if (url.endsWith("/referencias-importadas/confirmar")) { confirmed = true; return { ok: true, json: async () => ({ ...envelope, datos_reales_modificados: true, confirmadas: 1, lectura_posterior_verificada: true, precio_real_modificado: false, proveedor_real_modificado: false, coste_ia_usd: "0.00000000" }) } as Response; }
      return { ok: true, json: async () => ({ ...envelope, catalogo: { items: [item], total: 1, page: 1, page_size: 20, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/articulos?panel=referencias"]}><App /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "Artículos incompletos" })).toBeInTheDocument();
    expect(screen.getByText(/no se convertirá en proveedor real/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Reimportar precio y proveedor/tienda de referencia"), { target: { value: "article_id,proveedor_referencia,precio\nART-ESTRAGON,Proveedor externo,2.50" } });
    fireEvent.click(screen.getByRole("button", { name: "Preparar vista previa" }));
    const preview = await screen.findByRole("region", { name: "Referencias a importar" });
    expect(preview).toHaveTextContent("Actual real: precio sin informar · proveedor sin informar");
    expect(preview).toHaveTextContent("proveedor/tienda Proveedor externo");
    expect(confirmed).toBe(false);
    fireEvent.click(within(preview).getByRole("button", { name: "Confirmar referencias seleccionadas" }));
    expect(await screen.findByRole("status")).toHaveTextContent("El precio y el proveedor reales siguen sin modificarse");
    const confirmCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/referencias-importadas/confirmar"));
    expect(JSON.parse(String(confirmCall?.[1]?.body)).rows).toHaveLength(1);

    cleanup();
    render(<MemoryRouter initialEntries={["/articulos?panel=referencias"]}><App /></MemoryRouter>);
    expect(await screen.findByText("VISTA PREVIA CONSERVADA · CONFIRMADA")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Referencias a importar" })).toHaveTextContent("Proveedor externo");
    expect(screen.queryByRole("button", { name: "Confirmar referencias seleccionadas" })).not.toBeInTheDocument();
  });
});
