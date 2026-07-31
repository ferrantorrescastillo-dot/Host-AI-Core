import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { App } from "../ui/App";

const envelope = { ok: true, version: "1.0", api_version: "v1", request_id: "req-menu", modo_seguro: true, datos_reales_modificados: false };
const menu = {
  id: "MENU601-000001", codigo: "MEN-DEGUSTACION", nombre: "Menú degustación",
  estado: "BORRADOR", estado_operativo: "OPERATIVO", version: 1,
  comensales: 10, observaciones: "", coste_total: 40, coste_por_comensal: 4,
  coste_completo: true, lineas_sin_coste: 0, advertencias: [],
  incidencias: [], creado_en: null, actualizado_en: null,
  secciones: [{ id: "SEC-001", nombre: "Principal", orden: 0, elaboraciones: [] }],
};
const oldElaboration = {
  id: "REC-ANTIGUA", codigo: "REC-ANTIGUA", nombre: "Ceviche de corvina", categoria: "Entrantes",
  tipo: "Elaboración", estado: "OPERATIVA", rendimiento: 10, unidad_rendimiento: "raciones", coste_por_racion: 3.25,
  tiene_receta: true, tiene_escandallo: true, tiene_ficha_tecnica: true, tiene_fotografia: false,
  tiene_documentos: false, tiene_produccion: false, tiene_relaciones_menu_evento: false,
};
const recentElaboration = { ...oldElaboration, id: "REC-NUEVA", codigo: "REC-NUEVA", nombre: "Salsa de cava", categoria: "Salsas", coste_por_racion: null, tiene_escandallo: false };

describe("Selector de elaboraciones de Menús", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("busca en la Biblioteca pública, selecciona varias, evita duplicados y guarda orden", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/biblioteca/elaboraciones")) return { ok: true, status: 200, json: async () => ({
        ...envelope, elaboraciones: { items: [oldElaboration, recentElaboration], page: 1, page_size: 10, total: 2, total_pages: 1,
          filters: { estados: ["OPERATIVA"], categorias: ["Entrantes", "Salsas"] }, capabilities: {} },
      }) } as Response;
      if (init?.method === "POST") return { ok: true, status: 201, json: async () => ({ ...envelope, menu: { ...menu, secciones: [{ ...menu.secciones[0], elaboraciones: [
        { elaboracion_id: oldElaboration.id, elaboracion_nombre: oldElaboration.nombre, cantidad: 1, coste_por_racion: 3.25, coste_linea_por_comensal: 3.25, coste_linea_total: 32.5, coste_por_comensal: 3.25, estado_coste: "DISPONIBLE" },
        { elaboracion_id: recentElaboration.id, elaboracion_nombre: recentElaboration.nombre, cantidad: 1, coste_por_racion: null, coste_linea_por_comensal: null, coste_linea_total: null, coste_por_comensal: null, estado_coste: "SIN_COSTE", motivo_coste_no_disponible: "La elaboraciÃ³n no tiene escandallo." },
      ] }], coste_total: 32.5, coste_por_comensal: 3.25, coste_completo: false, lineas_sin_coste: 1, advertencias: ["La elaboraciÃ³n no tiene escandallo."] } }) } as Response;
      return { ok: true, status: 200, json: async () => ({ ...envelope, menus: [menu], total: 1, resumen: { borradores: 1, activos: 0, archivados: 0 } }) } as Response;
    });

    render(<MemoryRouter initialEntries={["/menus"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Menú degustación")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Nuevo menú" }));
    fireEvent.change(screen.getByLabelText("Nombre del menú"), { target: { value: "Menú nuevo" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Añadir elaboración" })[1]);
    expect(await screen.findByRole("dialog", { name: "Seleccionar elaboraciones" })).toBeInTheDocument();
    expect(await screen.findByText("Ceviche de corvina")).toBeInTheDocument();
    expect(screen.getByText((text) => text.includes("3,25") && text.includes("ración"))).toBeInTheDocument();
    expect(screen.getByText((text) => text.includes("Salsa de cava"))).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Buscar elaboraciones para menú"), { target: { value: "corvina" } });
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("q=corvina"))).toBe(true));
    const addButtons = screen.getAllByRole("button", { name: "Añadir" });
    fireEvent.click(addButtons[0]); fireEvent.click(addButtons[1]);
    expect(screen.getAllByRole("button", { name: "Ya añadida" })).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "Cerrar" }));
    fireEvent.click(screen.getByRole("button", { name: "Subir Salsa de cava" }));
    fireEvent.click(screen.getByRole("button", { name: "Guardar menú" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(true));
    expect(await screen.findByText("Coste parcial")).toBeInTheDocument();
    expect(screen.getAllByText((text) => text.includes("3,25") && text.includes("comensal")).length).toBeGreaterThan(0);
    expect(screen.getByText((text) => text.includes("Sin escandallo"))).toBeInTheDocument();
    expect(screen.queryByText((text) => text.includes("0,00") && text.includes("/raciÃ³n"))).not.toBeInTheDocument();
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST")?.[1] as RequestInit;
    const body = JSON.parse(String(post.body));
    expect(body.secciones[1].elaboraciones.map((item: { elaboracion_id: string }) => item.elaboracion_id)).toEqual(["REC-NUEVA", "REC-ANTIGUA"]);
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/api/v1/menus/elaboraciones"))).toBe(false);
  });

  it("muestra error controlado sin inventar menús", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: false, status: 503, json: async () => ({ ...envelope, ok: false, error: { code: "menus_unavailable", message: "Menús no disponibles." } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/menus"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Menús no disponibles.")).toBeInTheDocument();
  });
});
