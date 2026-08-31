import {
  render,
  screen,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { App } from "../ui/App";

const ROUTES = [
  {
    route: "/configuracion",
    testId: "placeholder-configuracion",
  },
];

describe("placeholders de modulos futuros", () => {
  it.each(ROUTES)(
    "muestra placeholder en $route",
    ({ route, testId }) => {
      render(
        <MemoryRouter initialEntries={[route]}>
          <App />
        </MemoryRouter>,
      );

      const panel = screen.getByTestId(testId);

      expect(
        within(panel).getByText(
          "Modulo disponible proximamente.",
        ),
      ).toBeInTheDocument();
    },
  );
});
