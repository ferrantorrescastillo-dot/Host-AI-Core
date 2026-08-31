import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SearchField } from "../ui/components/SearchField";

afterEach(cleanup);

function Harness({ onClear = () => undefined }: { onClear?: () => void }) {
  const [value, setValue] = useState("");
  return <SearchField value={value} onChange={setValue} onClear={onClear} placeholder="Buscar registros..." ariaLabel="Buscar registros" />;
}

describe("SearchField", () => {
  it("permite buscar, limpiar y conserva una etiqueta accesible", () => {
    const onClear = vi.fn();
    render(<Harness onClear={onClear} />);
    const input = screen.getByRole("searchbox", { name: "Buscar registros" });
    fireEvent.change(input, { target: { value: "SARDA" } });
    expect(input).toHaveValue("SARDA");
    fireEvent.click(screen.getByRole("button", { name: "Limpiar buscar registros" }));
    expect(input).toHaveValue("");
    expect(onClear).toHaveBeenCalledOnce();
  });

  it("limpia con Escape para navegación por teclado", () => {
    render(<Harness />);
    const input = screen.getByRole("searchbox", { name: "Buscar registros" });
    fireEvent.change(input, { target: { value: "borrador" } });
    fireEvent.keyDown(input, { key: "Escape" });
    expect(input).toHaveValue("");
  });
});
