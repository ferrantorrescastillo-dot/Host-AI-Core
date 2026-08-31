import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

describe("navegacion", () => {
  it("navega a dashboard", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-1",
        modo_seguro: true,
        datos_reales_modificados: false,
        dashboard: {},
      }),
    } as Response);

    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByRole("link", { name: "Dashboard" }));
    expect(
      await screen.findByRole("heading", {
        name: "Estado operativo del restaurante",
      }),
    ).toBeInTheDocument();
  });

  it("muestra 404", () => {
    render(
      <MemoryRouter initialEntries={["/desconocida"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("Pagina no encontrada")).toBeInTheDocument();
  });
});
