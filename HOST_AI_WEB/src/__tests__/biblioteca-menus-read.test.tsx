import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

const envelope = { ok: true, version: "1", api_version: "v1", request_id: "READ-MENU", modo_seguro: true, datos_reales_modificados: false };
const menu = { id: "MENU601-000010", codigo: "MENU-BODA", nombre: "MENU BODA", estado: "ACTIVO", estado_operativo: "OPERATIVO", version: 1, comensales: 100, observaciones: "", coste_total: 0, coste_por_comensal: 0, coste_completo: false, lineas_sin_coste: 1, advertencias: [], incidencias: [], origen: "BORONAT", modelo_biblioteca: "MENU_601", secciones: [{ id: "SEC-001", nombre: "Otros", orden: 0, elaboraciones: [{ elaboracion_id: "REC601-000043", elaboracion_nombre: "Tabla de quesos", referencia_canonica: "REC601-000043", tipo_referencia: "RECETA", cantidad: 1, coste_por_comensal: null }] }] };

describe("Menús canónicos en Biblioteca", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("navega Recetas → Menús → detalle → receta canónica", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/biblioteca/elaboraciones") && !url.includes("REC601-000043")) return { ok: true, status: 200, json: async () => ({ ...envelope, elaboraciones: { items: [], page: 1, page_size: 20, total: 0, total_pages: 1, filters: { estados: [], categorias: [] }, capabilities: {} } }) } as Response;
      if (url.endsWith("/api/v1/menus")) return { ok: true, status: 200, json: async () => ({ ...envelope, menus: [menu], total: 1, resumen: { borradores: 0, activos: 1, archivados: 0 } }) } as Response;
      if (url.endsWith("/api/v1/menus/MENU601-000010")) return { ok: true, status: 200, json: async () => ({ ...envelope, menu }) } as Response;
      return { ok: true, status: 200, json: async () => ({ ...envelope, elaboracion: { id: "REC601-000043", codigo: "TABLA-QUESOS", nombre: "Tabla de quesos", categoria: "", estado: "COMPLETO", tiene_receta: true, tiene_escandallo: false, tiene_ficha_tecnica: false, tiene_fotografia: false, tiene_documentos: false, tiene_produccion: false, tiene_relaciones_menu_evento: true, coste_total: null, coste_por_racion: null, rendimiento: 10, unidad_rendimiento: "raciones", raciones: 10, receta: { ingredientes: [], pasos: [], temperaturas: [], tecnicas: [] }, ficha_tecnica: { estado: "", origen: "", persistida: false, identificacion: {}, ingredientes: [], proceso: { pasos: [] }, tiempos: {}, temperaturas: [], utensilios: [], produccion: { indicaciones: {}, ordenes: [], necesidades: [], historial: [] }, documentos: [], campos_pendientes: [] }, alergenos: [], produccion: { indicaciones: {}, ordenes: [], necesidades: [], historial: [] }, documentos: [], imagenes: [], versiones: [], menus: [{ menu_id: "MENU601-000010", nombre: "MENU BODA" }], eventos: [], historial: [], pendientes: [], avisos: [] } }) } as Response;
    });
    render(<MemoryRouter initialEntries={["/biblioteca/recetas"]}><App /></MemoryRouter>);
    const menusLink = (await screen.findAllByRole("link", { name: "Menús" })).find((link) => link.getAttribute("href") === "/biblioteca/menus");
    expect(menusLink).toBeDefined(); fireEvent.click(menusLink!);
    expect(await screen.findByText("MENU BODA")).toBeInTheDocument();
    expect(screen.getByText("MENU601-000010")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "Ver menú" }));
    const recipeLink = await screen.findByRole("link", { name: "REC601-000043" });
    expect(recipeLink).toHaveAttribute("href", "/biblioteca/elaboraciones/REC601-000043?tab=receta");
    fireEvent.click(recipeLink);
    expect(await screen.findByRole("heading", { name: "Tabla de quesos" })).toBeInTheDocument();
    expect(screen.getByLabelText("Usada en menús")).toHaveTextContent("MENU BODA · MENU601-000010");
  });
});
