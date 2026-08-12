import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (_input, init) => ({ ok: true, json: async () => init?.method === "PATCH" ? ({ ...envelope, datos_reales_modificados: true, mensaje: "Artículo actualizado correctamente.", articulo: { ...detail, unidad_base: "kg", unidad_compra: "saco", cantidad_formato: 10, proveedor: "Huerta Sur", operatividad: { stock: true, compras: true, escandallos: true } } }) : ({ ...envelope, articulo: detail }) }) as Response);
    render(<MemoryRouter initialEntries={["/articulos/ART-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Editar artículo" }));
    await userEvent.selectOptions(screen.getByLabelText("Unidad base"), "kg");
    await userEvent.type(screen.getByLabelText("Unidad de compra"), "saco");
    await userEvent.type(screen.getByLabelText("Cantidad por formato"), "10");
    await userEvent.selectOptions(screen.getByLabelText("Proveedor preferente"), "Huerta Sur");
    await userEvent.click(screen.getByRole("button", { name: "Guardar artículo" }));
    await screen.findByText("10 kg");
    expect(screen.getAllByText("Sí").length).toBe(3);
    const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === "PATCH");
    expect(String(patchCall?.[0])).toContain("/articulos/ART-001");
    expect(JSON.parse(String(patchCall?.[1]?.body)).unidad_base).toBe("kg");
  });

  it("muestra el error de validación devuelto al guardar", async () => {
    const detail = { ...item, unidad_base: null, precio_incluye_iva: false, alergenos: [], stock_detalle: { cantidad: null, unidad: null, lotes: [] }, proveedores: [], precios: [], documentos: [], ficha_tecnica: null, recetas: [], escandallos: [], historial: [], operatividad: { stock: false, compras: false, escandallos: false }, edicion: { unidades_base: ["kg"], proveedores: [] } };
    vi.spyOn(global, "fetch").mockImplementation(async (_input, init) => init?.method === "PATCH" ? ({ ok: false, status: 400, json: async () => ({ ...envelope, ok: false, error: { message: "El precio debe ser mayor que cero." } }) } as Response) : ({ ok: true, json: async () => ({ ...envelope, articulo: detail }) } as Response));
    render(<MemoryRouter initialEntries={["/articulos/ART-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Editar artículo" }));
    await userEvent.selectOptions(screen.getByLabelText("Unidad base"), "kg");
    await userEvent.click(screen.getByRole("button", { name: "Guardar artículo" }));
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
});
