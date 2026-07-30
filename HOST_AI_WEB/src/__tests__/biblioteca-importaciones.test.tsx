import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

const response = {
  ok: true,
  version: "1.0",
  api_version: "1.0",
  request_id: "IMP-REQ-1",
  modo_seguro: true,
  datos_reales_modificados: false,
  importacion: {
    documento: {
      id: "IMPWEB-1",
      nombre: "receta.txt",
      tipo_mime: "text/plain",
      tamano: 42,
      origen: "TEXTO",
      clasificacion: {
        tipo: "RECETA",
        confianza: { valor: 0.82, explicacion: "Marcadores detectados: receta, ingredientes." },
      },
      secciones: [],
      entidades: [],
      advertencias: [],
      contenido_almacenado: false,
    },
    resumen: { secciones: 1, entidades: 1, propuestas: 1, incidencias: 0, estado: "PENDIENTE_REVISION" },
    propuestas: [{
      id: "IMPWEB-1-PROP-001",
      tipo: "CREAR_RECETA",
      estado: "PENDIENTE_REVISION",
      confianza: { valor: 0.75, explicacion: "Receta detectada." },
      explicacion: "Propuesta generada a partir de receta «Salsa verde».",
      origen: { importacion_id: "IMPWEB-1", nombre: "receta.txt", tipo: "TEXTO" },
      datos_propuestos: {},
      persistida: false,
    }],
    solo_previsualizacion: true,
    confirmacion_disponible: false,
  },
};

describe("Importador Inteligente de Biblioteca", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("sube, clasifica y muestra propuestas sin ofrecer escritura", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => response,
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Importador Inteligente" })).toBeInTheDocument();
    const file = new File(["Receta\nIngredientes\nPerejil"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("Receta\nIngredientes\nPerejil").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });

    expect(await screen.findByText("Documento recibido")).toBeInTheDocument();
    expect(screen.getByText("RECETA")).toBeInTheDocument();
    expect(screen.getByText("Crear receta")).toBeInTheDocument();
    expect(screen.getAllByText(/Pendiente de revisión/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Ninguna propuesta ha sido aplicada/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /confirmar/i })).not.toBeInTheDocument();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/biblioteca/importaciones",
      expect.objectContaining({ method: "POST" }),
    ));
    const request = vi.mocked(global.fetch).mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).toMatchObject({
      nombre: "receta.txt",
      tipo_mime: "text/plain",
    });
  });

  it("muestra un error controlado", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        ok: false, version: "1.0", api_version: "1.0", request_id: "IMP-ERR",
        modo_seguro: true, datos_reales_modificados: false,
        error: { status: 400, code: "invalid_content", message: "Documento inválido." },
      }),
    } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/importaciones"]}><App /></MemoryRouter>);
    const file = new File(["x"], "receta.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new TextEncoder().encode("x").buffer,
    });
    fireEvent.change(screen.getByLabelText("Seleccionar documento"), {
      target: { files: [file] },
    });
    expect(await screen.findByText("No se pudo interpretar el documento.")).toBeInTheDocument();
    expect(screen.getByText("Documento inválido.")).toBeInTheDocument();
  });
});
