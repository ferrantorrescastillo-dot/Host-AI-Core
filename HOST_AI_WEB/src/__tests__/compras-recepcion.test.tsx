import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../ui/App";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("guarda la cantidad visible antes de confirmar una recepción parcial y evita doble confirmación", async () => {
  const envelope = { ok: true, version: "6", api_version: "1", request_id: "REQ", modo_seguro: true, datos_reales_modificados: false };
  const dashboard = { ...envelope, dashboard: { modulos: { compras: { estado: "datos_disponibles", total: 0, items: [], propuestas: [], proveedores: [], historial: [], pedidos: [{ id: "PED-3", proveedor: "Proveedor A", estado: "preparado", lineas: [{ nombre: "Patata", cantidad: 10, unidad: "kg" }], importe_estimado: 20 }] } } } };
  const draft = { id: "REC-1", reception_id: "REC-1", order_id: "PED-3", proveedor: "Proveedor A", fecha: "2026-08-10", referencia: "", actualizado_en: "2026-08-10T10:00:00", estado: "BORRADOR", observaciones: "", confirmable: true, incidencias: [], lineas: [{ order_line_id: "LIN-1", article_id: "ART-1", article_name: "Patata", ordered_quantity: 10, previously_received: 0, pending_quantity: 10, received_quantity: 10, unit: "kg", order_price: 2, received_price: null, lot: "", expiry: "", location: "", observations: "", incidences: [] }] };
  let saved: any = draft; let release!: () => void; const gate = new Promise<void>((resolve) => { release = resolve; });
  const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => dashboard } as Response;
    if (url.endsWith("/api/v1/stock/ubicaciones")) return { ok: true, json: async () => ({ ...envelope, ubicaciones: ["Congelador", "Cámara", "Seco", "Bodega", "Limpieza"].map((nombre) => ({ id: nombre, nombre })) }) } as Response;
    if (url.includes("/pedidos/PED-3/recepciones")) return { ok: true, json: async () => ({ ...envelope, recepcion: draft, stock_modificado: false }) } as Response;
    if (url.endsWith("/recepciones/REC-1") && init?.method === "PATCH") { const body = JSON.parse(String(init.body)); const issue = { code: "DIFERENCIA_CANTIDAD", message: "Pendiente 10 y recibido ahora 6.", bloqueante: false }; saved = { ...draft, lineas: body.lineas.map((line: Record<string, unknown>) => ({ ...line, incidences: [issue] })), incidencias: [issue] }; return { ok: true, json: async () => ({ ...envelope, recepcion: saved, stock_modificado: false }) } as Response; }
    if (url.endsWith("/recepciones/REC-1/confirmar")) { const body = JSON.parse(String(init?.body)); saved = { ...draft, referencia: body.referencia, observaciones: body.observaciones, lineas: body.lineas }; await gate; return { ok: true, json: async () => ({ ...envelope, recepcion: { ...saved, estado: "CONFIRMADA", confirmable: false }, idempotente: false, stock_modificado: true }) } as Response; }
    throw new Error(`URL inesperada ${url}`);
  });
  vi.spyOn(window, "confirm").mockReturnValue(true);
  render(<MemoryRouter initialEntries={["/compras"]}><App /></MemoryRouter>);
  await userEvent.click(await screen.findByRole("button", { name: /Registrar.*PED-3/ }));
  expect(await screen.findByText(/Pedido: 10 kg/)).toHaveTextContent(/Ya recibido: 0 kg.*Pendiente: 10 kg/);
  const quantity = screen.getByLabelText("Cantidad recibida 1"); await userEvent.clear(quantity); await userEvent.type(quantity, "6");
  await userEvent.type(screen.getByLabelText("Precio recibido 1"), "2.25");
  await userEvent.type(screen.getByLabelText("Lote 1"), "LOTE-VISIBLE");
  await userEvent.type(screen.getByLabelText("Caducidad 1"), "2026-12-31");
  await userEvent.selectOptions(screen.getByLabelText("Ubicación 1"), "Cámara");
  await userEvent.type(screen.getByLabelText("Observaciones recepción 1"), "Caja revisada");
  const confirm = screen.getByRole("button", { name: /Confirmar/ }); await userEvent.click(confirm); await userEvent.click(confirm);
  const confirmCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/recepciones/REC-1/confirmar"));
  const body = JSON.parse(String(confirmCall?.[1]?.body));
  expect(body.actualizado_en).toBe(draft.actualizado_en);
  expect(body.lineas[0]).toMatchObject({ received_quantity: 6, received_price: 2.25, lot: "LOTE-VISIBLE", expiry: "2026-12-31", location: "Cámara", observations: "Caja revisada" });
  expect(fetchMock.mock.calls.some(([, options]) => options?.method === "PATCH")).toBe(false);
  expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/recepciones/REC-1/confirmar"))).toHaveLength(1);
  release();
  await waitFor(() => expect(screen.getAllByRole("status").some((item) => item.textContent?.includes("CONFIRMADA"))).toBe(true));
});

it("tras confirmar un pedido lo muestra y permite abrir su recepción sin modificar Stock", async () => {
  const envelope = { ok: true, version: "6", api_version: "1", request_id: "REQ", modo_seguro: true, datos_reales_modificados: false };
  const line = { id: "LIN-PAU", articulo_id: "ART000238", nombre: "Patata Monalisa", cantidad: 0.25, unidad: "kg", precio_unitario: 2 };
  const order = { id: "PED-PAU", proveedor: "PAU GAVALDA", estado: "borrador", lineas: [line], importe_estimado: 0.5, creado_en: "2026-08-10T13:00:04", actualizado_en: "2026-08-10T13:00:04", origen: { tipo: "menu", id: "MENU601-000003", version: 1, propuesta_id: "PROP-1" } };
  const module = (pedidos: unknown[]) => ({ ...envelope, dashboard: { modulos: { compras: { estado: "datos_disponibles", total: 0, items: [], propuestas: [], proveedores: [], historial: [], pedidos } } } });
  const reception = { id: "REC-PAU", reception_id: "REC-PAU", order_id: order.id, proveedor: order.proveedor, fecha: "2026-08-10", referencia: "", estado: "BORRADOR", observaciones: "", confirmable: true, incidencias: [], lineas: [{ order_line_id: line.id, article_id: line.articulo_id, article_name: line.nombre, ordered_quantity: 0.25, previously_received: 0, pending_quantity: 0.25, received_quantity: 0.25, unit: "kg", order_price: 2, received_price: null, lot: "", expiry: "", location: "", observations: "", incidences: [] }] };
  let prepared = false;
  const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/api/v1/dashboard")) return { ok: true, json: async () => module([{ ...order, estado: prepared ? "preparado" : "borrador" }]) } as Response;
    if (url.endsWith("/api/v1/stock/ubicaciones")) return { ok: true, json: async () => ({ ...envelope, ubicaciones: ["Congelador", "Cámara", "Seco", "Bodega", "Limpieza"].map((nombre) => ({ id: nombre, nombre })) }) } as Response;
    if (url.endsWith(`/borradores/${order.id}/confirmar`)) { prepared = true; return { ok: true, json: async () => ({ ...envelope, pedido: { ...order, estado: "preparado" }, borrador: { ...order, estado: "preparado" }, idempotente: false, advertencias: [], stock_modificado: false, inventario_modificado: false, recepciones_creadas: 0 }) } as Response; }
    if (url.endsWith(`/borradores/${order.id}`)) return { ok: true, json: async () => ({ ...envelope, borrador: order, revision: { valido: true, errores_bloqueantes: [], advertencias: [] } }) } as Response;
    if (url.endsWith(`/pedidos/${order.id}/recepciones`)) return { ok: true, json: async () => ({ ...envelope, recepcion: reception, stock_modificado: false }) } as Response;
    throw new Error(`URL inesperada ${url}`);
  });
  vi.spyOn(window, "confirm").mockReturnValue(true);
  render(<MemoryRouter initialEntries={["/compras"]}><App /></MemoryRouter>);
  await userEvent.click(await screen.findByRole("button", { name: "Abrir borrador" }));
  await userEvent.click(await screen.findByRole("button", { name: "Confirmar y crear pedido" }));
  const receive = await screen.findByRole("button", { name: `Registrar recepción de ${order.id}` });
  await userEvent.click(receive);
  expect(await screen.findByRole("heading", { name: `Recepción ${reception.id}` })).toBeInTheDocument();
  expect(screen.getByText(/Pedido: 0.25 kg.*Ya recibido: 0 kg.*Pendiente: 0.25 kg/)).toBeInTheDocument();
  expect(fetchMock.mock.calls.some(([url, init]) => String(url).includes("stock") && init?.method !== "GET")).toBe(false);
});

it("mantiene Registrar recepción para pedidos parciales y la retira al completarlos", async () => {
  const envelope = { ok: true, version: "6", api_version: "1", request_id: "REQ", modo_seguro: true, datos_reales_modificados: false };
  vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...envelope, dashboard: { modulos: { compras: { estado: "datos_disponibles", total: 0, items: [], propuestas: [], proveedores: [], historial: [], pedidos: [
    { id: "PED-PARCIAL", proveedor: "PAU GAVALDA", estado: "parcialmente_recibido", lineas: [{ nombre: "Patata Monalisa", cantidad: 0.25, unidad: "kg" }], importe_estimado: 0.5 },
    { id: "PED-COMPLETO", proveedor: "PAU GAVALDA", estado: "recibido", lineas: [{ nombre: "Patata Monalisa", cantidad: 0.25, unidad: "kg" }], importe_estimado: 0.5 },
  ] } } } }) } as Response);
  render(<MemoryRouter initialEntries={["/compras"]}><App /></MemoryRouter>);
  expect(await screen.findByRole("button", { name: "Registrar recepción de PED-PARCIAL" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Registrar recepción de PED-COMPLETO" })).not.toBeInTheDocument();
});
