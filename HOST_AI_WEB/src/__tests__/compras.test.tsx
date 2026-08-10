import userEvent from "@testing-library/user-event";
import {
  cleanup,
  render,
  screen,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function payload(
  compras: unknown[],
  extras: Record<string, unknown> = {},
) {
  return {
    ok: true,
    version: "6.1",
    api_version: "1.0",
    request_id: "REQ-COMPRAS-1",
    modo_seguro: true,
    datos_reales_modificados: false,
    dashboard: {
      modulos: {
        compras: {
          estado: compras.length ? "datos_disponibles" : "sin_datos",
          total: compras.length,
          items: compras,
          propuestas: [],
          proveedores: [],
          historial: [],
          ...extras,
        },
      },
    },
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/compras"]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Compras", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("muestra carga, resumen y compras del endpoint público real", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () =>
        payload(
          [
            {
              id: "NEC-1",
              nombre: "Tomate triturado",
              prioridad: 3,
              estado: "pendiente",
              fecha_necesaria: "2026-08-03",
            },
          ],
          {
            propuestas: [
              {
                id: "PROP-1",
                producto: "Tomate pera",
                comprar: 5,
                unidad: "kg",
                estado: "pendiente",
                proveedor_sugerido: "Proveedor Uno",
              },
            ],
            proveedores: [
              {
                id: "PROV-1",
                nombre: "Proveedor Uno",
                estado: "activo",
                email: "compras@proveedor.test",
              },
            ],
            historial: [
              {
                id: "COMPRA-1",
                producto: "Cebolla",
                cantidad: 2,
                unidad: "kg",
                proveedor: "Proveedor Uno",
                creado_en: "2026-07-28T10:00:00",
              },
            ],
          },
        ),
    } as Response);

    renderPage();

    expect(screen.getByText("Cargando compras...")).toBeInTheDocument();
    const item = await screen.findByText("Tomate triturado");
    const row = item.closest("li");
    expect(row).not.toBeNull();
    expect(
      within(row as HTMLElement).getByText("Estado: Pendiente"),
    ).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-COMPRAS-1")).toBeInTheDocument();
    expect(screen.getByText("Tomate pera")).toBeInTheDocument();
    expect(screen.getAllByText("Proveedor Uno").length).toBeGreaterThan(0);
    expect(screen.getByText("Cebolla")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/dashboard"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra el estado vacío", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => payload([]),
    } as Response);

    renderPage();

    expect(
      await screen.findByText("No hay necesidades de compra pendientes."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No hay propuestas de compra pendientes."),
    ).toBeInTheDocument();
    expect(screen.getByText("No hay proveedores activos.")).toBeInTheDocument();
    expect(screen.getByText("No hay compras registradas.")).toBeInTheDocument();
  });

  it("muestra error y reintenta la carga", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({
          ok: false,
          version: "6.1",
          api_version: "1.0",
          request_id: "REQ-COMPRAS-ERROR",
          modo_seguro: true,
          datos_reales_modificados: false,
          error: { message: "Compras no disponible temporalmente." },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => payload([]),
      } as Response);

    renderPage();

    expect(
      await screen.findByText("Compras no disponible temporalmente."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Request ID: REQ-COMPRAS-ERROR"),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(
      await screen.findByText("No hay necesidades de compra pendientes."),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("abre, edita y guarda un borrador manteniendolo sin enviar", async () => {
    const dashboard = payload([], { pedidos: [{ id: "PED-1", proveedor: "Proveedor A", estado: "borrador", lineas: [{ nombre: "Patata", cantidad: 2, unidad: "kg" }], importe_estimado: 6 }] });
    const draft = { id: "PED-1", proveedor: "Proveedor A", estado: "borrador", lineas: [{ id: "LIN-1", nombre: "Patata", cantidad: 2, unidad: "kg", precio_unitario: 3 }], importe_estimado: 6, creado_en: "2026-08-07T10:00:00", actualizado_en: "2026-08-07T10:00:00", origen: { tipo: "menu", id: "MENU-1", version: 3, propuesta_id: "PROP-1" } };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => dashboard } as Response;
      if (init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        return { ok: true, json: async () => ({ ...dashboard, borrador: { ...draft, ...body, importe_estimado: body.lineas.reduce((sum: number, line: { cantidad: number; precio_unitario: number }) => sum + line.cantidad * line.precio_unitario, 0) }, revision: { valido: true, errores_bloqueantes: [], advertencias: [] } }) } as Response;
      }
      return { ok: true, json: async () => ({ ...dashboard, borrador: draft, revision: { valido: true, errores_bloqueantes: [], advertencias: [] } }) } as Response;
    });

    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "Abrir borrador" }));
    expect(await screen.findByText(/Menú origen: MENU-1 · versión 3/)).toBeInTheDocument();
    const quantity = screen.getByLabelText("Cantidad 1");
    await userEvent.clear(quantity);
    await userEvent.type(quantity, "4");
    await userEvent.click(screen.getByRole("button", { name: "Añadir línea" }));
    expect(screen.getAllByRole("group")).toHaveLength(2);
    await userEvent.click(screen.getAllByRole("button", { name: "Eliminar línea" })[1]);
    await userEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));
    expect(await screen.findByText("Borrador guardado y validado.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar y crear pedido" })).toBeEnabled();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/compras/borradores/PED-1"), expect.objectContaining({ method: "PATCH" }));
  });

  it("revisa, confirma una vez y muestra el pedido preparado", async () => {
    const dashboard = payload([], { pedidos: [{ id: "PED-2", proveedor: "Proveedor A", estado: "borrador", lineas: [{ nombre: "Patata", cantidad: 2, unidad: "kg" }], importe_estimado: 6 }] });
    const draft = { id: "PED-2", proveedor: "Proveedor A", estado: "borrador", lineas: [{ id: "LIN-2", articulo_id: "ART-1", nombre: "Patata", cantidad: 2, unidad: "kg", precio_unitario: 3 }], importe_estimado: 6, creado_en: "2026-08-07T10:00:00", actualizado_en: "2026-08-07T10:00:00", origen: { tipo: "menu", id: "MENU-1", version: 3, propuesta_id: "PROP-1" } };
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => dashboard } as Response;
      if (url.endsWith("/confirmar") && init?.method === "POST") {
        await gate;
        return { ok: true, json: async () => ({ ...dashboard, pedido: { ...draft, estado: "preparado", confirmado_en: "2026-08-07T11:00:00" }, borrador: { ...draft, estado: "preparado" }, idempotente: false, advertencias: [], stock_modificado: false, inventario_modificado: false, recepciones_creadas: 0 }) } as Response;
      }
      return { ok: true, json: async () => ({ ...dashboard, borrador: draft, revision: { valido: true, errores_bloqueantes: [], advertencias: [{ code: "price_pending", field: "precio", message: "Advertencia informativa" }] } }) } as Response;
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);

    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "Abrir borrador" }));
    expect(await screen.findByRole("heading", { name: "Revisión final" })).toBeInTheDocument();
    expect(screen.getByText("Advertencia informativa")).toBeInTheDocument();
    const button = screen.getByRole("button", { name: "Confirmar y crear pedido" });
    await userEvent.click(button);
    await userEvent.click(button);
    expect(screen.getByText("Creando pedido...")).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/confirmar"))).toHaveLength(1);
    release();
    expect(await screen.findByText("Pedido creado correctamente en estado preparado.")).toBeInTheDocument();
    expect(screen.getByText("Pedido:")).toBeInTheDocument();
    expect(screen.getByText("Estado preparado: pendiente de recepción.")).toBeInTheDocument();
    expect(screen.queryByText(/No se ha creado recepción/)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver pedido" })).toHaveAttribute("href", "#pedido-PED-2");
    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining("Proveedor A con 1 líneas"));
  });

  it("crea un pedido manual buscando proveedor y artículo, calcula total y lo deja recepcionable", async () => {
    const provider = { id: "PROV-PAU", nombre: "PAU GAVALDA", estado: "activo" };
    const line = { id: "LIN-MANUAL", articulo_id: "ART-PATATA", nombre: "Patata Monalisa", cantidad: 1, unidad: "kg", precio_unitario: 2, observaciones: "" };
    const draft = { id: "PED-MANUAL", proveedor: provider.nombre, estado: "borrador", fecha: "2026-08-10", referencia: "REF-1", observaciones: "", lineas: [line], importe_estimado: 2, creado_en: "2026-08-10T10:00:00", actualizado_en: "2026-08-10T10:00:00", origen: { tipo: "manual", id: "compras", version: 1, propuesta_id: "" } };
    let orderState: "none" | "draft" | "prepared" = "none";
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => payload([], { proveedores: [provider], pedidos: orderState === "none" ? [] : [{ ...draft, estado: orderState === "draft" ? "borrador" : "preparado" }] }) } as Response;
      if (url.includes("/api/v1/articulos?") && init?.method === "GET") return { ok: true, json: async () => ({ ...payload([]), catalogo: { items: [{ id: "ART-PATATA", codigo: "ART-PATATA", nombre: "Patata Monalisa", precio: 2, unidad: "kg", estado: "activo", con_stock: false, tiene_ficha_tecnica: false }], total: 1, page: 1, page_size: 20, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      if (url.endsWith("/api/v1/articulos/ART-PATATA")) return { ok: true, json: async () => ({ ...payload([]), articulo: { id: "ART-PATATA", codigo: "ART-PATATA", nombre: "Patata Monalisa", unidad_compra: "kg", unidad_base: "kg", precio: 2, proveedores: [{ id: provider.id, nombre: provider.nombre, preferente: true, precio: 2, unidad: "kg" }] } }) } as Response;
      if (url.endsWith("/api/v1/compras/borradores") && init?.method === "POST") { orderState = "draft"; return { ok: true, json: async () => ({ ...payload([]), borrador: draft, revision: { valido: true, errores_bloqueantes: [], advertencias: [] }, stock_modificado: false }) } as Response; }
      if (url.endsWith(`/borradores/${draft.id}/confirmar`)) { orderState = "prepared"; return { ok: true, json: async () => ({ ...payload([]), pedido: { ...draft, estado: "preparado" }, borrador: { ...draft, estado: "preparado" }, idempotente: false, advertencias: [], stock_modificado: false, inventario_modificado: false, recepciones_creadas: 0 }) } as Response; }
      if (url.endsWith(`/borradores/${draft.id}`)) return { ok: true, json: async () => ({ ...payload([]), borrador: draft, revision: { valido: true, errores_bloqueantes: [], advertencias: [] } }) } as Response;
      throw new Error(`URL inesperada ${url}`);
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "Nuevo pedido" }));
    await userEvent.type(screen.getByLabelText("Buscar proveedor"), "PAU");
    await userEvent.click(screen.getByRole("button", { name: provider.nombre }));
    await userEvent.type(screen.getByLabelText("Buscar artículo"), "Patata");
    await userEvent.click(screen.getByRole("button", { name: "Añadir artículo" }));
    await userEvent.click(await screen.findByRole("button", { name: /Patata Monalisa · ART-PATATA/ }));
    expect(await screen.findByText("Total pedido: 2,00 €")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Guardar borrador" }));
    await userEvent.click(await screen.findByRole("button", { name: "Abrir borrador" }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmar y crear pedido" }));
    expect(await screen.findByRole("button", { name: `Registrar recepción de ${draft.id}` })).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("stock"))).toBe(false);
  });

  it("adjunta, muestra y quita un albarán sin tocar Stock", async () => {
    const order = { id: "PED-DOC", proveedor: "Proveedor A", estado: "preparado", lineas: [{ nombre: "Patata", cantidad: 1, unidad: "kg" }], importe_estimado: 2 };
    const baseReception = { id: "REC-DOC", reception_id: "REC-DOC", order_id: order.id, proveedor: order.proveedor, fecha: "2026-08-10", referencia: "", estado: "BORRADOR", actualizado_en: "v1", lineas: [{ order_line_id: "LIN-1", article_id: "ART-1", article_name: "Patata", ordered_quantity: 1, previously_received: 0, pending_quantity: 1, received_quantity: 1, unit: "kg", canonical_unit: "kg", stock_quantity: 1, order_price: 2, received_price: null, lot: "", expiry: "", location: "", observations: "", incidences: [] }], incidencias: [], observaciones: "", confirmable: true, documento: null };
    const document = { document_id: "DOC-1", nombre: "ALB-123.pdf", tipo_mime: "application/pdf", tamano: 20, fecha_subida: "2026-08-10T10:00:00", usuario: "web", proveedor: order.proveedor, order_id: order.id, reception_id: baseReception.id, referencia: "", fecha_albaran: "", observaciones: "", checksum_sha256: "abc", estado: "PENDIENTE_REVISION" };
    let attached = false;
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => payload([], { pedidos: [order] }) } as Response;
      if (url.endsWith(`/pedidos/${order.id}/recepciones`)) return { ok: true, json: async () => ({ ...payload([]), recepcion: baseReception, stock_modificado: false }) } as Response;
      if (url.endsWith(`/recepciones/${baseReception.id}/documento`) && init?.method === "POST") { const body = JSON.parse(String(init.body)); if (body.nombre.endsWith(".exe")) return { ok: false, status: 400, json: async () => ({ ...payload([]), ok: false, error: { code: "unsupported_document_format", message: "Formato de documento no admitido." } }) } as Response; attached = true; return { ok: true, json: async () => ({ ...payload([]), recepcion: { ...baseReception, documento: document, document_id: document.document_id }, documento: document, stock_modificado: false }) } as Response; }
      if (url.endsWith(`/recepciones/${baseReception.id}/documento`) && init?.method === "DELETE") { attached = false; return { ok: true, json: async () => ({ ...payload([]), recepcion: baseReception, stock_modificado: false }) } as Response; }
      throw new Error(`URL inesperada ${url}`);
    });
    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: `Registrar recepción de ${order.id}` }));
    const invalid = new File(["bad"], "malware.exe", { type: "application/octet-stream" });
    Object.defineProperty(invalid, "arrayBuffer", { value: async () => new TextEncoder().encode("bad").buffer });
    await userEvent.upload(screen.getByLabelText("Adjuntar albarán"), invalid, { applyAccept: false });
    expect(await screen.findByText("Formato de documento no admitido.")).toBeInTheDocument();
    const file = new File(["%PDF fake"], document.nombre, { type: document.tipo_mime });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("%PDF fake").buffer });
    await userEvent.upload(screen.getByLabelText("Adjuntar albarán"), file);
    expect(await screen.findByText(document.nombre)).toBeInTheDocument();
    expect(screen.getByText("Estado: Pendiente de revisión")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ver documento" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Continuar recepción" })).toHaveAttribute("href", "#lineas-recepcion");
    await userEvent.click(screen.getByRole("button", { name: "Quitar documento" }));
    expect(await screen.findByLabelText("Adjuntar albarán")).toBeInTheDocument();
    expect(attached).toBe(false);
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("stock"))).toBe(false);
  });
});
