import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { App } from "../ui/App";

const ROUTES = ["/produccion", "/stock", "/configuracion"];

describe("placeholders de modulos futuros", () => {
  it.each(ROUTES)("muestra placeholder en %s", (route) => {
    render(
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("Modulo disponible proximamente.")).toBeInTheDocument();
  });
});
