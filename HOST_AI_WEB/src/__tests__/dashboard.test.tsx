import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function mockDashboard(payload: unknown, delayed = false) {
  return vi
    .spyOn(global, "fetch")
    .mockImplementation(
      () =>
        new Promise((resolve) => {
          const doResolve = () =>
            resolve({
              ok: true,
              json: async () => payload,
            } as Response);
          if (delayed) {
            setTimeout(doResolve, 20);
          } else {
            doResolve();
          }
        }),
    );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("dashboard", () => {
  it("renderiza cabecera y estado general", async () => {
    mockDashboard({
      ok: true,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-DASH-CAB",
      modo_seguro: true,
      datos_reales_modificados: false,
      dashboard: {
        estado_general: "estable",
      },
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Estado operativo del restaurante")).toBeInTheDocument();
    expect(screen.getByText("HOST AI")).toBeInTheDocument();
    expect(screen.getByText(/estado general/i)).toBeInTheDocument();
  });

  it("muestra datos cuando la respuesta es correcta", async () => {
    mockDashboard({
      ok: true,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-DASH",
      modo_seguro: true,
      datos_reales_modificados: false,
      dashboard: {
        estado_general: "estable",
        prioridad: { titulo: "Preparar produccion", justificacion: "Evento cercano" },
        pendientes: [{ codigo: "A", nombre: "Preparar mise", estado: "pendiente", prioridad: "alta" }],
        riesgos: [{ nivel: "alto", mensaje: "Falta producto", accion_recomendada: "Revisar compras" }],
        recomendaciones: ["Priorizar mise en place"],
        evento_activo: { nombre: "Boda Alba", fecha: "2026-07-31", pax: 120, estado: "abierto" },
        workflows: [{ workflow: "PRODUCCION_INTELIGENTE", estado: "preparado" }],
      },
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Prioridad del día")).toBeInTheDocument();
    expect(screen.getAllByText("Evento activo")).not.toHaveLength(0);
    expect(screen.getAllByText("Pendientes")).not.toHaveLength(0);
    expect(screen.getAllByText("Riesgos")).not.toHaveLength(0);
    expect(screen.getByText("Recomendaciones")).toBeInTheDocument();
    expect(screen.getAllByText("Workflows preparados")).not.toHaveLength(0);
    expect(
      screen.getByLabelText("Estado de seguridad"),
    ).toHaveTextContent(/Datos reales modificados:\s*No/i);
  });

  it("muestra estado de carga", () => {
    mockDashboard(
      {
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-DASH",
        modo_seguro: true,
        datos_reales_modificados: false,
        dashboard: {},
      },
      true,
    );

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("Cargando dashboard...")).toBeInTheDocument();
  });

  it("muestra error seguro", async () => {
    mockDashboard({
      ok: false,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-DASH",
      modo_seguro: true,
      datos_reales_modificados: false,
      error: { message: "No se pudo construir el dashboard en este momento." },
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("No se pudo cargar el dashboard.")).toBeInTheDocument();
    expect(screen.getByText("No se pudo construir el dashboard en este momento.")).toBeInTheDocument();
  });

  it("muestra estado vacio sin inventar datos", async () => {
    mockDashboard({
      ok: true,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-VACIO",
      modo_seguro: true,
      datos_reales_modificados: false,
      dashboard: {},
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("No hay información operativa disponible.")).toBeInTheDocument();
  });

  it("muestra request_id en error y permite reintentar", async () => {
    const spy = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ok: false,
          version: "1.0",
          api_version: "1.0",
          request_id: "REQ-ERR-1",
          modo_seguro: true,
          datos_reales_modificados: false,
          error: { message: "No se pudo construir el dashboard en este momento." },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ok: true,
          version: "1.0",
          api_version: "1.0",
          request_id: "REQ-OK-2",
          modo_seguro: true,
          datos_reales_modificados: false,
          dashboard: { estado_general: "estable" },
        }),
      } as Response);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("No se pudo cargar el dashboard.")).toBeInTheDocument();
    expect(screen.getByText(/Request ID: REQ-ERR-1/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(await screen.findByText("Estado operativo del restaurante")).toBeInTheDocument();
    expect(spy).toHaveBeenCalledTimes(2);
  });

  it("boton actualizar vuelve a consultar el endpoint", async () => {
    const spy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          version: "1.0",
          api_version: "1.0",
          request_id: "REQ-UPD",
          modo_seguro: true,
          datos_reales_modificados: false,
          dashboard: { estado_general: "estable" },
        }),
      } as Response);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Estado operativo del restaurante")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Actualizar" }));

    await waitFor(() => {
      expect(spy).toHaveBeenCalledTimes(2);
    });
  });

  it("no recalcula negocio, solo presenta datos recibidos", async () => {
    mockDashboard({
      ok: true,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-RAW",
      modo_seguro: true,
      datos_reales_modificados: false,
      dashboard: {
        prioridad: { titulo: "Codigo exacto P-123" },
        riesgos: [{ nivel: "medio", mensaje: "R-XYZ" }],
      },
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      (await screen.findAllByText("Codigo Exacto P-123")).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("R-XYZ")).toBeInTheDocument();
  });

  it("no realiza escrituras: solo GET /api/v1/dashboard", async () => {
    const spy = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-GET",
        modo_seguro: true,
        datos_reales_modificados: false,
        dashboard: { estado_general: "estable" },
      }),
    } as Response);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByText("Estado operativo del restaurante");
    const [url, init] = spy.mock.calls[0] as [string, RequestInit | undefined];
    expect(String(url)).toContain("/api/v1/dashboard");
    expect((init?.method || "GET").toUpperCase()).toBe("GET");
    expect(init?.body).toBeUndefined();
  });

  it("muestra alerta tecnica si datos_reales_modificados es true", async () => {
    mockDashboard({
      ok: true,
      version: "1.0",
      api_version: "1.0",
      request_id: "REQ-ALERTA",
      modo_seguro: false,
      datos_reales_modificados: true,
      dashboard: { estado_general: "revision" },
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Alerta técnica de seguridad")).toBeInTheDocument();
  });

  it("expone acciones concretas sin inventar WRITE para entidades canónicas", async () => {
    mockDashboard({ ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-ACTIONS", modo_seguro: true, datos_reales_modificados: false, dashboard: {
      pendientes: [
        { nombre: "Producción bloqueada", tipo_entidad: "PRODUCCION", plan_id: "PLAN-1" },
        { nombre: "Stock bajo", tipo_entidad: "STOCK_BAJO", articulo_id: "ART-1" },
        { nombre: "Aviso manual", tipo_entidad: "DESCONOCIDA", entidad_id: "X-1" },
      ],
    } });
    render(<MemoryRouter initialEntries={["/dashboard"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("link", { name: "Abrir producción" })).toHaveAttribute("href", "/produccion?plan_id=PLAN-1");
    expect(screen.getByRole("link", { name: "Preparar compra" })).toHaveAttribute("href", "/compras?article_id=ART-1");
    expect(screen.getByText("Aviso Manual").closest("li")?.querySelector("button, a")).toBeNull();
  });

  it("agrupa lotes del mismo artículo, conserva cada lote y expone recetas incompletas", async () => {
    mockDashboard({ ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-GROUPS", modo_seguro: true, datos_reales_modificados: false, dashboard: {
      pendientes: [{ nombre: "Recetas pendientes", modulo: "recetas", cantidad: 3, entidades: [
        { receta_id: "REC601-000001", nombre: "Crema catalana", estado: "PENDIENTE_DE_COMPLETAR", campos_faltantes: ["procedimiento", "conservacion"] },
        { receta_id: "REC601-000002", nombre: "Salsa romesco", estado: "PENDIENTE_DE_COMPLETAR", campos_faltantes: ["rendimiento"] },
        { receta_id: "REC601-000003", nombre: "Fondo oscuro", estado: "PENDIENTE_DE_COMPLETAR", campos_faltantes: ["alergenos"] },
      ] }],
      riesgos: [
        { tipo: "sin_ubicacion", nivel: "atencion", mensaje: "Patata tiene un lote sin ubicación", articulo_id: "ART-1", lote_id: "LOT-1", tipo_entidad: "LOTE" },
        { tipo: "sin_ubicacion", nivel: "atencion", mensaje: "Patata tiene un lote sin ubicación", articulo_id: "ART-1", lote_id: "LOT-2", tipo_entidad: "LOTE" },
      ],
    } });
    render(<MemoryRouter initialEntries={["/dashboard"]}><App /></MemoryRouter>);
    expect(await screen.findByLabelText("Recetas pendientes de completar — 3")).toBeInTheDocument();
    expect(screen.getByText("Crema catalana")).toBeInTheDocument();
    expect(screen.getByText("Salsa romesco")).toBeInTheDocument();
    expect(screen.getByText("Fondo oscuro")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Abrir receta" })[0]).toHaveAttribute("href", "/biblioteca/elaboraciones/REC601-000001?tab=receta");
    expect(screen.getAllByRole("link", { name: "Completar" })[0]).toHaveAttribute("href", "/biblioteca/elaboraciones/REC601-000001?tab=receta&complete=1");
    expect(screen.queryByRole("link", { name: "Abrir artículo" })).not.toBeInTheDocument();
    await userEvent.click(screen.getByText("2 incidencias agrupadas · ver detalle"));
    expect(screen.getAllByRole("link", { name: "Abrir lote" })).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Asignar ubicación" })).toHaveLength(2);
  });

  it("lote sin ubicación usa preview, confirmación y refresca dashboard", async () => {
    const dashboard = { ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-LOT", modo_seguro: true, datos_reales_modificados: false, dashboard: { pendientes: [{ nombre: "Lote sin ubicación", tipo_entidad: "LOTE", lote_id: "LOT-1" }] } };
    const fetch = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce({ ok: true, json: async () => dashboard } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...dashboard, ubicaciones: [{ id: "Congelador", nombre: "Congelador" }, { id: "Cámara", nombre: "Cámara" }, { id: "Seco", nombre: "Seco" }, { id: "Bodega", nombre: "Bodega" }, { id: "Limpieza", nombre: "Limpieza" }] }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...dashboard, preview_token: "opaque", lote_antes: { ubicacion: "" }, lote_despues: { ubicacion: "Bodega" }, requiere_confirmacion: true }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...dashboard, datos_reales_modificados: true, lote: { id: "LOT-1", ubicacion: "BODEGA" } }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...dashboard, dashboard: { pendientes: [] } }) } as Response);
    render(<MemoryRouter initialEntries={["/dashboard"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "Asignar ubicación" }));
    const selector = screen.getByLabelText("Ubicación canónica");
    for (const label of ["Congelador", "Cámara", "Seco", "Bodega", "Limpieza"]) expect(selector).toHaveTextContent(label);
    await userEvent.selectOptions(selector, "Bodega");
    await userEvent.click(screen.getByRole("button", { name: "Vista previa" }));
    expect(await screen.findByText(/Sin ubicación.*Bodega/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Confirmar ubicación" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(5));
    expect(screen.queryByRole("button", { name: "Asignar ubicación" })).not.toBeInTheDocument();
  });

  it("refresca completitud y contador tras confirmar una receta en la pestaña concreta", async () => {
    const response = (count: number) => ({ ok: true, version: "1", api_version: "1", request_id: `REQ-${count}`, modo_seguro: true, datos_reales_modificados: false, dashboard: { pendientes: [{ nombre: "Recetas pendientes", modulo: "recetas", cantidad: count, entidades: Array.from({ length: count }, (_, index) => ({ receta_id: `REC601-00000${index + 1}`, nombre: `Receta ${index + 1}`, campos_faltantes: ["procedimiento"] })) }] } });
    const fetch = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce({ ok: true, json: async () => response(3) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => response(2) } as Response);
    render(<MemoryRouter initialEntries={["/dashboard"]}><App /></MemoryRouter>);
    await screen.findByLabelText("Recetas pendientes de completar — 3");
    window.dispatchEvent(new MessageEvent("message", { origin: window.location.origin, data: { type: "host-ai-recipe-updated", recipe_id: "REC601-000001" } }));
    expect(await screen.findByLabelText("Recetas pendientes de completar — 2")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
