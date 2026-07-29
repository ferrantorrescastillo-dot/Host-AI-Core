import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
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

    expect(await screen.findByText("Prioridad del dia")).toBeInTheDocument();
    expect(screen.getByText("Evento activo")).toBeInTheDocument();
    expect(screen.getByText("Pendientes")).toBeInTheDocument();
    expect(screen.getByText("Riesgos")).toBeInTheDocument();
    expect(screen.getByText("Recomendaciones")).toBeInTheDocument();
    expect(screen.getByText("Workflows preparados")).toBeInTheDocument();
    expect(screen.getByText(/Datos reales modificados: no/i)).toBeInTheDocument();
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

    expect(await screen.findByText("Error de dashboard")).toBeInTheDocument();
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

    expect(await screen.findByText("No hay informacion operativa disponible.")).toBeInTheDocument();
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

    expect(await screen.findByText("Error de dashboard")).toBeInTheDocument();
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

    expect(await screen.findByText("Codigo exacto P-123")).toBeInTheDocument();
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

    expect(await screen.findByText("Alerta tecnica de seguridad")).toBeInTheDocument();
  });
});
