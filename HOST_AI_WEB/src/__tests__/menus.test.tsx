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
  }, 10_000);

  it("muestra error controlado sin inventar menús", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: false, status: 503, json: async () => ({ ...envelope, ok: false, error: { code: "menus_unavailable", message: "Menús no disponibles." } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/menus"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Menús no disponibles.")).toBeInTheDocument();
  });

  it("consulta necesidades reales y genera la propuesta con su borrador", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/necesidades")) return { ok: true, status: 200, json: async () => ({ ...envelope, necesidades: {
        menu_id: menu.id, menu_version: 1, comensales: 10, generated_at: "2026-07-31T10:00:00Z", complete: true,
        summary: { articulos: 2, cubiertos: 1, compra_necesaria: 1, sin_relacionar: 0, conversiones_pendientes: 0, candidatas_propuesta: 1 },
        warnings: [], blocking_errors: [], solo_lectura: true, datos_reales_modificados: false,
        lines: [{ articulo_id: "ART-PATATA", articulo_codigo: "ART-PATATA", articulo_nombre: "Patata", ingrediente_nombre: "Patata",
          origenes: [{ seccion: "Principal", elaboracion_id: "REC-ENS", elaboracion_nombre: "Ensaladilla", cantidad: 2.5, unidad: "kg", factor_escalado: 2.5 }],
          cantidad_necesaria: 2.5, unidad_necesaria: "kg", stock_fisico: 1, stock_reservado: 0, stock_comprometido: 0,
          stock_disponible: 1, cantidad_faltante: 1.5, unidad_stock: "kg", estado: "Parcialmente cubierto",
          proveedor_preferente: "Proveedor A", formato_compra: "saco", cantidad_propuesta_compra: 5, coste_estimado: 10, motivo_no_resuelto: null },
        { articulo_id: "ART-SAL", articulo_codigo: "ART-SAL", articulo_nombre: "Sal", ingrediente_nombre: "Sal", origenes: [],
          cantidad_necesaria: 0.1, unidad_necesaria: "kg", stock_fisico: 1, stock_reservado: 0, stock_comprometido: 0,
          stock_disponible: 1, cantidad_faltante: 0, unidad_stock: "kg", estado: "Cubierto por stock", proveedor_preferente: null,
          formato_compra: null, cantidad_propuesta_compra: 0, coste_estimado: 0, motivo_no_resuelto: null }],
      } }) } as Response;
      if (url.endsWith("/crear-pedidos") && init?.method === "POST") return { ok: true, status: 201, json: async () => ({ ...envelope,
        propuesta: { id: "MENUPROP-1", estado: "CONFIRMADA", version: 2, coste_estimado: 10, coste_completo: true, lineas: [], grupos_proveedor: [], resumen: { articulos_propuestos: 1, articulos_pendientes: 0, proveedores_pendientes: 0 }, advertencias: [], crea_pedido: false, modifica_stock: false, datos_reales_modificados: true },
        pedidos: [{ id: "PED-1", proveedor: "Proveedor B", estado: "borrador", lineas: [], importe_estimado: 14, observaciones: "Generado desde Menú" }],
        pedidos_creados: [{ id: "PED-1", proveedor: "Proveedor B", estado: "borrador", lineas: [], importe_estimado: 14, observaciones: "Generado desde Menú" }],
        lineas_incluidas: [], lineas_pendientes: [], lineas_excluidas: [], advertencias: [], errores: [], idempotente: false,
        stock_modificado: false, recepciones_creadas: 0,
      }) } as Response;
      if (url.includes("/propuesta-compra/") && init?.method === "PATCH") {
        const changed = JSON.parse(String(init.body));
        return { ok: true, status: 200, json: async () => ({ ...envelope, propuesta: { id: "MENUPROP-1", estado: "REVISADA", version: 2, coste_estimado: 10, coste_completo: true, lineas: changed.lineas, grupos_proveedor: [], resumen: { articulos_propuestos: 1, articulos_pendientes: 0, proveedores_pendientes: 0 }, advertencias: [], crea_pedido: false, modifica_stock: false, datos_reales_modificados: false } }) } as Response;
      }
      if (url.endsWith("/propuesta-compra") && init?.method === "POST") return { ok: true, status: 201, json: async () => ({ ...envelope,
        propuesta: { id: "MENUPROP-1", estado: "CONFIRMADA", version: 1, coste_estimado: 10, coste_completo: true,
          lineas: [{ id: "LINEA-001", incluir: true, articulo_id: "ART-PATATA", articulo: "Patata", cantidad_necesaria: 2.5,
            cantidad_faltante: 1.5, cantidad_final_propuesta: null, unidad_base: "kg", proveedor: null, proveedor_sugerido: { nombre: "Proveedor A" }, formato_compra: "saco",
            precio_estimado: 2, coste_estimado: 10, estado: "Parcialmente cubierto", observaciones: "", advertencia: null }],
          grupos_proveedor: [{ proveedor: "Proveedor A", lineas: [] }], resumen: { articulos_propuestos: 1, articulos_pendientes: 0, proveedores_pendientes: 0 },
          advertencias: [], crea_pedido: true, modifica_stock: false, datos_reales_modificados: true },
        pedidos_creados: [{ id: "PED-AUTO", proveedor: "Proveedor A", estado: "borrador", lineas: [], importe_estimado: 10, observaciones: "Generado desde Menú" }],
        lineas_incluidas: [], lineas_pendientes: [], lineas_excluidas: [], advertencias: [], errores: [],
      }) } as Response;
      return { ok: true, status: 200, json: async () => ({ ...envelope, menus: [menu], total: 1, resumen: { borradores: 1, activos: 0, archivados: 0 } }) } as Response;
    });

    render(<MemoryRouter initialEntries={["/menus"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByText("Menú degustación"));
    fireEvent.click(screen.getByRole("button", { name: "Calcular necesidades" }));
    expect(await screen.findByText(/2 artículos/)).toBeInTheDocument();
    expect(screen.getByText(/Falta: 1,5 kg/)).toBeInTheDocument();
    fireEvent.click(screen.getAllByText("Ver trazabilidad")[0]);
    expect(screen.getByText(/Ensaladilla: 2,5 kg/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Filtrar necesidades"), { target: { value: "cubiertos" } });
    expect(screen.getByText("Sal")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Generar propuesta de compra" }));
    expect(await screen.findByText("Propuesta CONFIRMADA")).toBeInTheDocument();
    expect(screen.getByLabelText("Revisar propuesta de compra")).toBeInTheDocument();
    expect(screen.getByText("Líneas listas para pedido: 1")).toBeInTheDocument();
    expect(screen.getByText("Líneas pendientes: 0")).toBeInTheDocument();
    expect(screen.getByText("Proveedores: 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Cantidad propuesta LINEA-001")).toHaveValue(2.5);
    expect(screen.getByLabelText("Proveedor LINEA-001")).toHaveValue("Proveedor A");
    expect(await screen.findByText("1 borradores creados")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir Compras" })).toHaveAttribute("href", "/compras");
    expect(screen.getByText("No se ha creado ningún pedido ni modificado Stock.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/propuesta-compra") && init?.method === "POST")).toBe(true);
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/crear-pedidos"))).toBe(false);
  });

  it("explica por qué no hay líneas listas y muestra un error controlado al crear", async () => {
    let releaseCreation!: () => void;
    const creationGate = new Promise<void>((resolve) => { releaseCreation = resolve; });
    const pendingLine = { id: "LINEA-PENDIENTE", incluir: true, articulo_id: "ART-PATATA", articulo: "Patata", cantidad_necesaria: 2,
      cantidad_faltante: null, cantidad_final_propuesta: null, unidad_base: "kg", proveedor: null, formato_compra: null,
      precio_estimado: null, coste_estimado: null, estado: "Stock no disponible", observaciones: "", advertencia: "Stock desconocido" };
    vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/dashboard")) return { ok: true, status: 200, json: async () => ({ ...envelope, dashboard: { modulos: { compras: { proveedores: [{ id: "PROV-A", nombre: "Proveedor A", estado: "activo" }] } } } }) } as Response;
      if (url.endsWith("/necesidades")) return { ok: true, status: 200, json: async () => ({ ...envelope, necesidades: {
        menu_id: menu.id, menu_version: 1, comensales: 10, generated_at: "2026-07-31T10:00:00Z", complete: false,
        lines: [], warnings: [], blocking_errors: [], summary: { articulos: 1, cubiertos: 0, compra_necesaria: 0, sin_relacionar: 0, conversiones_pendientes: 0, candidatas_propuesta: 1 },
        solo_lectura: true, datos_reales_modificados: false,
      } }) } as Response;
      if (url.endsWith("/propuesta-compra") && init?.method === "POST") return { ok: true, status: 201, json: async () => ({ ...envelope, propuesta: {
        id: "MENUPROP-P", estado: "BORRADOR", version: 1, coste_estimado: 0, coste_completo: false, lineas: [pendingLine], grupos_proveedor: [],
        resumen: { articulos_propuestos: 0, articulos_pendientes: 1, proveedores_pendientes: 1 }, advertencias: ["Stock desconocido"], crea_pedido: false, modifica_stock: false, datos_reales_modificados: false,
      } }) } as Response;
      if (url.includes("/propuesta-compra/") && init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        return { ok: true, status: 200, json: async () => ({ ...envelope, propuesta: { id: "MENUPROP-P", estado: "REVISADA", version: 2, coste_estimado: 0, coste_completo: false, lineas: body.lineas, grupos_proveedor: [], resumen: { articulos_propuestos: 1, articulos_pendientes: 0, proveedores_pendientes: 0 }, advertencias: [], crea_pedido: false, modifica_stock: false, datos_reales_modificados: false } }) } as Response;
      }
      if (url.endsWith("/crear-pedidos")) {
        await creationGate;
        return { ok: false, status: 500, json: async () => ({ ...envelope, ok: false, error: { code: "order_creation_failed", message: "No se pudieron crear los borradores." } }) } as Response;
      }
      return { ok: true, status: 200, json: async () => ({ ...envelope, menus: [menu], total: 1, resumen: { borradores: 1, activos: 0, archivados: 0 } }) } as Response;
    });

    render(<MemoryRouter initialEntries={["/menus"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByText("Menú degustación"));
    fireEvent.click(screen.getByRole("button", { name: "Calcular necesidades" }));
    await screen.findByText(/1 artículos/);
    fireEvent.click(screen.getByRole("button", { name: "Generar propuesta de compra" }));
    const createButton = await screen.findByRole("button", { name: "Crear borradores de pedido" });
    expect(createButton).toBeDisabled();
    expect(screen.getByText(/No hay líneas listas/)).toBeInTheDocument();
    expect(screen.getByText("Líneas pendientes: 1")).toBeInTheDocument();
    expect(screen.getByText(/^Proveedor pendiente/, { selector: "strong" })).toHaveTextContent("(1)");
    expect(screen.getByText("Requiere atención")).toBeInTheDocument();
    expect(screen.getByLabelText("Cantidad propuesta LINEA-PENDIENTE")).toHaveValue(2);
    fireEvent.click(screen.getByRole("button", { name: /Patata: Selecciona un proveedor existente/ }));
    expect(screen.getByLabelText("Proveedor LINEA-PENDIENTE")).toHaveFocus();

    fireEvent.change(screen.getByLabelText("Cantidad propuesta LINEA-PENDIENTE"), { target: { value: "3" } });
    await waitFor(() => expect(document.querySelector('option[value="Proveedor A"]')).not.toBeNull());
    fireEvent.change(screen.getByLabelText("Proveedor LINEA-PENDIENTE"), { target: { value: "Proveedor A" } });
    expect(createButton).toBeEnabled();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    fireEvent.click(createButton);
    expect((await screen.findAllByText("Creando borradores…")).length).toBeGreaterThan(0);
    expect(createButton).toBeDisabled();
    releaseCreation();
    expect(await screen.findByText("No se pudieron crear los borradores.")).toBeInTheDocument();
  });

  it("busca y relaciona un artículo existente y revalida la línea", async () => {
    const pendingLine = { id: "LINEA-SIN-ARTICULO", incluir: true, articulo_id: null, articulo: null, cantidad_necesaria: 0.5,
      cantidad_faltante: null, cantidad_final_propuesta: null, unidad_base: "kg", proveedor: null, formato_compra: null,
      precio_estimado: null, coste_estimado: null, estado: "Sin artículo relacionado", observaciones: "", advertencia: "Pendiente" };
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/necesidades")) return { ok: true, status: 200, json: async () => ({ ...envelope, necesidades: {
        menu_id: menu.id, menu_version: 1, comensales: 10, generated_at: "2026-08-07T10:00:00Z", complete: false,
        lines: [], warnings: [], blocking_errors: [], summary: { articulos: 1, cubiertos: 0, compra_necesaria: 0, sin_relacionar: 1, conversiones_pendientes: 0, candidatas_propuesta: 1 }, solo_lectura: true, datos_reales_modificados: false,
      } }) } as Response;
      if (url.endsWith("/propuesta-compra") && init?.method === "POST") return { ok: true, status: 201, json: async () => ({ ...envelope, propuesta: {
        id: "MENUPROP-ART", estado: "BORRADOR", version: 1, coste_estimado: 0, coste_completo: false, lineas: [pendingLine], grupos_proveedor: [],
        resumen: { articulos_propuestos: 0, articulos_pendientes: 1, proveedores_pendientes: 1 }, advertencias: ["Pendiente"], crea_pedido: false, modifica_stock: false, datos_reales_modificados: false,
      } }) } as Response;
      if (url.includes("/api/v1/articulos?") && init?.method === "GET") return { ok: true, status: 200, json: async () => ({ ...envelope, catalogo: {
        items: [{ id: "ART-NARANJA", codigo: "ART-NARANJA", nombre: "Naranja", proveedor: "Frutas Sur", precio: 1.8, unidad: "kg", estado: "activo", con_stock: false, tiene_ficha_tecnica: false }],
        total: 1, page: 1, page_size: 8, total_pages: 1, filtros: { familias: [], proveedores: ["Frutas Sur"], estados: ["activo"] }, capacidades: {},
      } }) } as Response;
      if (url.endsWith("/api/v1/articulos/ART-NARANJA")) return { ok: true, status: 200, json: async () => ({ ...envelope, articulo: {
        id: "ART-NARANJA", codigo: "ART-NARANJA", nombre: "Naranja", proveedor: "Frutas Sur", precio: 1.8, unidad: "kg", unidad_base: "kg", unidad_compra: "caja", estado: "activo", con_stock: false, tiene_ficha_tecnica: false,
        precio_incluye_iva: false, alergenos: [], stock_detalle: { lotes: [] }, proveedores: [{ nombre: "Frutas Sur", preferente: true }], precios: [], documentos: [], ficha_tecnica: null, recetas: [], escandallos: [], historial: [],
      } }) } as Response;
      if (url.includes("/propuesta-compra/") && init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        return { ok: true, status: 200, json: async () => ({ ...envelope, propuesta: { id: "MENUPROP-ART", estado: "REVISADA", version: 2, coste_estimado: 0.9, coste_completo: true, lineas: body.lineas, grupos_proveedor: [], resumen: { articulos_propuestos: 1, articulos_pendientes: 0, proveedores_pendientes: 0 }, advertencias: [], crea_pedido: false, modifica_stock: false, datos_reales_modificados: false } }) } as Response;
      }
      return { ok: true, status: 200, json: async () => ({ ...envelope, menus: [menu], total: 1, resumen: { borradores: 1, activos: 0, archivados: 0 } }) } as Response;
    });

    render(<MemoryRouter initialEntries={["/menus"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByText("Menú degustación"));
    fireEvent.click(screen.getByRole("button", { name: "Calcular necesidades" }));
    await screen.findByText(/1 artículos/);
    fireEvent.click(screen.getByRole("button", { name: "Generar propuesta de compra" }));
    const search = await screen.findByLabelText("Buscar artículo LINEA-SIN-ARTICULO");
    fireEvent.change(search, { target: { value: "naranja" } });
    fireEvent.click(await screen.findByRole("button", { name: /Naranja/ }));

    await waitFor(() => expect(screen.queryByLabelText("Buscar artículo LINEA-SIN-ARTICULO")).not.toBeInTheDocument());
    expect(screen.getByText("Naranja")).toBeInTheDocument();
    expect(screen.getByLabelText("Proveedor LINEA-SIN-ARTICULO")).toHaveValue("Frutas Sur");
    expect(screen.getByText("Completos").nextElementSibling).toHaveTextContent("1");
    expect(screen.getByRole("button", { name: "Crear borradores de pedido" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Guardar propuesta" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, request]) => String(url).includes("/propuesta-compra/") && request?.method === "PATCH" && String(request.body).includes("ART-NARANJA"))).toBe(true));
  });
  it("abre por enlace la propuesta creada desde Produccion", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes(`/propuesta-compra/PROP-PROD`)) return { ok: true, status: 200, json: async () => ({ ...envelope, propuesta: {
        id: "PROP-PROD", menu_id: menu.id, menu_version: 1, production_plan_id: "PLAN-1", origen: "produccion",
        estado: "BORRADOR", version: 1, coste_estimado: 0, coste_completo: false,
        lineas: [{ id: "LINEA-001", incluir: true, articulo_id: "ART-PATATA", articulo: "Patata Monalisa", cantidad_necesaria: .75, cantidad_disponible: .5, cantidad_faltante: .25, cantidad_final_propuesta: .25, unidad_base: "kg", proveedor: null, formato_compra: null, precio_estimado: null, coste_estimado: null, estado: "Compra necesaria", observaciones: "", advertencia: null }],
        grupos_proveedor: [], resumen: { articulos_propuestos: 1, articulos_pendientes: 1, proveedores_pendientes: 1 }, advertencias: [], crea_pedido: false, modifica_stock: false, datos_reales_modificados: false,
      } }) } as Response;
      return { ok: true, status: 200, json: async () => ({ ...envelope, menus: [menu], total: 1, resumen: { borradores: 1, activos: 0, archivados: 0 } }) } as Response;
    });
    render(<MemoryRouter initialEntries={[`/menus?menu_id=${menu.id}&proposal_id=PROP-PROD`]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Revisar propuesta" })).toBeInTheDocument();
    expect(screen.getByText("Patata Monalisa")).toBeInTheDocument();
    expect(screen.getByText("Disponible").nextElementSibling).toHaveTextContent("0,5 kg");
    expect(screen.getByLabelText("Cantidad propuesta LINEA-001")).toHaveValue(.25);
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/propuesta-compra/PROP-PROD"))).toBe(true);
  });
});
