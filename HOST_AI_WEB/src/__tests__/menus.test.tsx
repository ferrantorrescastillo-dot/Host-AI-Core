import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { App } from "../ui/App";

const envelope = {
  ok: true, version: "1.0", api_version: "v1", request_id: "req-menu",
  modo_seguro: true, datos_reales_modificados: false,
};

const menu = {
  id: "MENU601-000001", codigo: "MEN-DEGUSTACION", nombre: "Menú degustación",
  estado: "BORRADOR", estado_operativo: "OPERATIVO", version: 1,
  comensales: 10, observaciones: "", coste_total: 40, coste_por_comensal: 4,
  incidencias: [], creado_en: null, actualizado_en: null,
  secciones: [{
    id: "SEC-001", nombre: "Principal", orden: 0,
    elaboraciones: [{ elaboracion_id: "REC-1", elaboracion_nombre: "Arroz", cantidad: 1, coste_por_comensal: 4 }],
  }],
};

describe("Menús inteligentes", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("lista, edita secciones y muestra costes calculados por la API", async () => {
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({
        ...envelope, menus: [menu], total: 1,
        resumen: { borradores: 1, activos: 0, archivados: 0 },
      }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({
        ...envelope, elaboraciones: [{ id: "REC-1", codigo: "REC-1", nombre: "Arroz", familia: "Principal" }], total: 1,
      }) } as Response)
      .mockResolvedValueOnce({ ok: true, status: 201, json: async () => ({ ...envelope, menu }) } as Response);

    render(<MemoryRouter initialEntries={["/menus"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Menú degustación")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Nuevo menú" }));
    fireEvent.change(screen.getByLabelText("Nombre del menú"), { target: { value: "Menú nuevo" } });
    fireEvent.change(screen.getByLabelText("Comensales"), { target: { value: "10" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Añadir elaboración" })[1]);
    fireEvent.click(screen.getByRole("button", { name: "Guardar menú" }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(3));
    expect(global.fetch).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/menus",
      expect.objectContaining({ method: "POST" }),
    );
    const request = vi.mocked(global.fetch).mock.calls[2][1] as RequestInit;
    const body = JSON.parse(String(request.body));
    expect(body.secciones[1]).toMatchObject({
      nombre: "Principal", elaboraciones: [{ elaboracion_id: "REC-1", cantidad: 1 }],
    });
    expect(await screen.findByText((text) => text.includes("Total:") && text.includes("40,00"))).toBeInTheDocument();
    expect(screen.getByText((text) => text.includes("Por comensal:") && text.includes("4,00"))).toBeInTheDocument();
  });

  it("muestra error controlado sin inventar menús", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false, status: 503, json: async () => ({
        ...envelope, ok: false, error: { code: "menus_unavailable", message: "Menús no disponibles." },
      }),
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/menus"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Menús no disponibles.")).toBeInTheDocument();
  });
});
