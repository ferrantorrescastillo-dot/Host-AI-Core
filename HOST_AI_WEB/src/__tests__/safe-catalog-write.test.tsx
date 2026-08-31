import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { hostAiApiClient } from "../api/client";
import { articulosService } from "../services/articulosService";
import { SafeCatalogWritePanel } from "../ui/components/SafeCatalogWritePanel";

afterEach(cleanup);

describe("SafeCatalogWritePanel", () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it("prepara y cancela un alta sin ejecutar confirmación", async () => {
    const preview = vi.spyOn(hostAiApiClient, "previewCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "TOKEN", propuesto: { nombre: "Evento seguro", fecha: "2030-01-01", pax: 20 }, requiere_confirmacion: true });
    const confirm = vi.spyOn(hostAiApiClient, "confirmCatalogCrud"); const cancel = vi.fn();
    render(<SafeCatalogWritePanel domain="EVENTO" operation="CREAR" onCancel={cancel} onConfirmed={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Evento seguro" } });
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2030-01-01" } });
    fireEvent.change(screen.getByLabelText("PAX"), { target: { value: "20" } });
    fireEvent.click(screen.getByRole("button", { name: "Revisar y guardar" }));
    await screen.findByRole("heading", { name: "Vista previa" });
    expect(preview).toHaveBeenCalledOnce(); expect(confirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" })); expect(cancel).toHaveBeenCalledOnce();
  });

  it("confirma una receta una sola vez aunque se pulse dos veces", async () => {
    vi.spyOn(hostAiApiClient, "previewCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "TOKEN", propuesto: { nombre: "Salsa", codigo: "SALSA", numero_raciones: 2, ingredientes: ["sal"], cantidades: ["2 g"] }, requiere_confirmacion: true });
    let resolve!: (value: any) => void; const confirm = vi.spyOn(hostAiApiClient, "confirmCatalogCrud").mockImplementation(() => new Promise((done) => { resolve = done; }));
    render(<SafeCatalogWritePanel domain="RECETA" operation="CREAR" onCancel={vi.fn()} onConfirmed={vi.fn()} />);
    for (const [label, value] of [["Nombre", "Salsa"], ["Código", "SALSA"], ["Rendimiento / raciones", "2"], ["Ingredientes (uno por línea: nombre | cantidad unidad)", "sal | 2 g"]]) fireEvent.change(screen.getByLabelText(label), { target: { value } });
    fireEvent.click(screen.getByRole("button", { name: "Revisar y guardar" })); await screen.findByRole("heading", { name: "Vista previa" });
    const button = screen.getByRole("button", { name: "Confirmar" }); fireEvent.click(button); fireEvent.click(button);
    expect(confirm).toHaveBeenCalledOnce(); resolve({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: true, registro: { id: "REC-1" }, idempotente: false });
    await waitFor(() => expect(button).not.toHaveTextContent("Confirmando"));
  });

  it("archiva mediante preview y permite cancelar sin escribir", async () => {
    const preview = vi.spyOn(hostAiApiClient, "previewCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "ARCH", propuesto: { id: "REC-1", nombre: "Salsa", estado: "ARCHIVADA" }, requiere_confirmacion: true });
    const confirm = vi.spyOn(hostAiApiClient, "confirmCatalogCrud"); const cancel = vi.fn();
    render(<SafeCatalogWritePanel domain="RECETA" operation="ARCHIVAR" entityId="REC-1" onCancel={cancel} onConfirmed={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Revisar archivado" }));
    expect(await screen.findByText("Se va a archivar esta receta.")).toBeInTheDocument();
    expect(preview).toHaveBeenCalledWith("RECETA", "ARCHIVAR", {}, "REC-1");
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(cancel).toHaveBeenCalledOnce(); expect(confirm).not.toHaveBeenCalled();
  });

  it("busca candidatos reales y conserva nombre culinario y article_id elegido", async () => {
    vi.spyOn(hostAiApiClient, "getArticulos").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [
      { id: "ART-JS", codigo: "ART-JS", nombre: "Jamón serrano reserva", unidad: "kg", proveedor: "Proveedor A", estado: "ACTIVO", con_stock: false, tiene_ficha_tecnica: false },
      { id: "ART-JI", codigo: "ART-JI", nombre: "Jamón ibérico", unidad: "kg", proveedor: "Proveedor B", estado: "ACTIVO", con_stock: false, tiene_ficha_tecnica: false },
    ], total: 2, page: 1, page_size: 10, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } });
    const preview = vi.spyOn(hostAiApiClient, "previewCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "T", propuesto: {}, requiere_confirmacion: true });
    render(<SafeCatalogWritePanel domain="RECETA" operation="CREAR" onCancel={vi.fn()} onConfirmed={vi.fn()} />);
    for (const [label, value] of [["Nombre", "Croquetas"], ["Código", "REC-CROQ"], ["Rendimiento / raciones", "10"], ["Ingredientes (uno por línea: nombre | cantidad unidad)", "Jamón curado | 200 g"], ["Procedimiento", "Mezclar"]]) fireEvent.change(screen.getByLabelText(label), { target: { value } });
    fireEvent.click(screen.getByRole("button", { name: "Buscar artículo" })); fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByText("Pendiente de confirmar. Candidatos encontrados:")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /Jamón serrano reserva/ })).not.toBeChecked();
    fireEvent.click(screen.getByRole("radio", { name: /Jamón ibérico/ }));
    fireEvent.click(screen.getByRole("button", { name: "Revisar y guardar" }));
    await waitFor(() => expect(preview).toHaveBeenCalled());
    const sent = preview.mock.calls[0][2] as any;
    expect(sent.ingredientes).toEqual(["Jamón curado"]);
    expect(sent.ingredientes_estructurados[0]).toMatchObject({ nombre: "Jamón curado", article_id: "ART-JI", estado: "RESUELTO" });
  });

  it("crea un artículo ausente, lo relee y lo deja seleccionado en la receta", async () => {
    const article = { id: "ART-HARINA-ESPECIAL", codigo: "ART-HARINA-ESPECIAL", nombre: "Harina especial X", unidad: "kg", estado: "ACTIVO", con_stock: false, tiene_ficha_tecnica: false };
    const reads = vi.spyOn(hostAiApiClient, "getArticulos")
      .mockResolvedValueOnce({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } })
      .mockResolvedValueOnce({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [article], total: 1, page: 1, page_size: 10, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } });
    vi.spyOn(hostAiApiClient, "previewCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "ARTICLE", propuesto: article, requiere_confirmacion: true });
    vi.spyOn(hostAiApiClient, "confirmCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: true, registro: article, idempotente: false });
    render(<SafeCatalogWritePanel domain="RECETA" operation="CREAR" onCancel={vi.fn()} onConfirmed={vi.fn()} />);
    for (const [label, value] of [["Nombre", "Masa"], ["Código", "REC-MASA"], ["Rendimiento / raciones", "4"], ["Ingredientes (uno por línea: nombre | cantidad unidad)", "Harina especial X | 1 kg"]]) fireEvent.change(screen.getByLabelText(label), { target: { value } });
    fireEvent.click(screen.getByRole("button", { name: "Buscar artículo" })); fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Crear artículo “Harina especial X”" }));
    const articlePanel = screen.getByLabelText("Nuevo articulo");
    fireEvent.change(within(articlePanel).getByLabelText("Unidad base"), { target: { value: "kg" } });
    fireEvent.click(within(articlePanel).getByRole("button", { name: "Revisar y guardar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(screen.getByText(/Vinculado a: Harina especial X/)).toBeInTheDocument());
    expect(reads).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("radio", { name: /Harina especial X/ })).toBeChecked();
  });
  it("completa un borrador inline con IA sin escribir", async () => {
    vi.spyOn(hostAiApiClient, "getArticulos").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } });
    const proposal = vi.spyOn(hostAiApiClient, "proposeArticleDraft").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, datos_propuestos_ia: { familia: "Setas", unidad_compra: "kg", cantidad_formato: 500, unidad_formato: "g", observaciones: "Producto fresco" }, campos_descartados: ["precio", "proveedor", "stock"] });
    const preview = vi.spyOn(hostAiApiClient, "previewCatalogCrud"); const confirm = vi.spyOn(hostAiApiClient, "confirmCatalogCrud");
    render(<SafeCatalogWritePanel domain="RECETA" operation="CREAR" onCancel={vi.fn()} onConfirmed={vi.fn()} />);
    for (const [label, value] of [["Nombre", "Crema"], ["Código", "REC-CREMA"], ["Rendimiento / raciones", "4"], ["Ingredientes (uno por línea: nombre | cantidad unidad)", "Champiñones | 1 kg"]]) fireEvent.change(screen.getByLabelText(label), { target: { value } });
    fireEvent.click(screen.getByRole("button", { name: "Buscar artículo" })); fireEvent.click(screen.getByRole("button", { name: "Buscar" })); fireEvent.click(await screen.findByRole("button", { name: /Crear artículo/ }));
    const panel = screen.getByLabelText("Nuevo articulo"); fireEvent.change(within(panel).getByLabelText("Unidad base"), { target: { value: "kg" } }); fireEvent.click(within(panel).getByRole("button", { name: "Completar campos con IA" }));
    await waitFor(() => expect(proposal).toHaveBeenCalledWith(expect.objectContaining({ unidad_base: "kg" }), expect.objectContaining({ ingrediente_original: "Champiñones", receta_nombre: "Crema", receta_id: "REC-CREMA", cantidad_receta: "1", unidad_receta: "kg" })));
    expect(preview).not.toHaveBeenCalled(); expect(confirm).not.toHaveBeenCalled();
    const proposalPanel = within(panel).getByLabelText("IA para borrador de artículo"); expect(within(proposalPanel).queryByText(/^precio$/i)).not.toBeInTheDocument(); expect(within(proposalPanel).queryByText(/^proveedor$/i)).not.toBeInTheDocument(); expect(within(proposalPanel).queryByText(/^stock$/i)).not.toBeInTheDocument();
    fireEvent.click(within(panel).getAllByRole("button", { name: "Aceptar" })[0]); expect(preview).not.toHaveBeenCalled(); expect(within(panel).getByLabelText("Unidad base")).toHaveValue("kg");
  });

  /* Retirado: la búsqueda web de precios ya no forma parte del producto.
  it("busca precio sobre el borrador inline sin crear y confirma la referencia por separado", async () => {
    const candidate = { tipo: "PRECIO_REFERENCIA_WEB", origen: "WEB", producto: "Cava cocina X", tienda_referencia: "Makro", precio_comercial: 3, cantidad_formato: 750, unidad_formato: "ml", precio_normalizado: 4, unidad_normalizada: "l", url: "https://makro.example/cava", consultado_en: "2026-08-27T10:00:00+02:00", autoridad: "REFERENCIA_NO_REAL" };
    const article = { id: "ART-CAVA", codigo: "ART-CAVA", nombre: "Cava para cocinar" };
    const search = vi.spyOn(articulosService, "searchWebPrices").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, consulta: "cava cocinar", candidatos: [candidate], total: 1 });
    const referencePreview = vi.spyOn(articulosService, "previewWebPrice").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "WEB", referencia_propuesta: candidate });
    const referenceConfirm = vi.spyOn(articulosService, "confirmWebPrice").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: true, referencia: candidate });
    vi.spyOn(articulosService, "get").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, articulo: article as any });
    const createPreview = vi.spyOn(hostAiApiClient, "previewCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, preview_token: "CREATE", propuesto: article, requiere_confirmacion: true });
    const createConfirm = vi.spyOn(hostAiApiClient, "confirmCatalogCrud").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: true, registro: article, idempotente: false });
    const onConfirmed = vi.fn();
    render(<SafeCatalogWritePanel domain="ARTICULO" operation="CREAR" initial={{ nombre: "Cava para cocinar", codigo: "ART-CAVA", unidad_base: "l", cantidad_formato: 750, unidad_formato: "ml" }} onCancel={vi.fn()} onConfirmed={onConfirmed} />);
    fireEvent.click(screen.getByRole("button", { name: "Buscar precio online" }));
    expect(await screen.findByText(/Cava cocina X · Makro/)).toBeInTheDocument();
    expect(search).toHaveBeenCalledWith(expect.objectContaining({ article_name: "Cava para cocinar", usage_context: "ingrediente para cocinar" }));
    expect(createPreview).not.toHaveBeenCalled(); expect(createConfirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Usar esta referencia" }));
    expect(screen.getByText(/todavía no guardada/)).toBeInTheDocument();
    expect(createPreview).not.toHaveBeenCalled(); expect(referencePreview).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Revisar y guardar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
    expect(await screen.findByRole("heading", { name: "PRECIO DE REFERENCIA WEB" })).toBeInTheDocument();
    expect(referencePreview).toHaveBeenCalledWith("ART-CAVA", candidate); expect(referenceConfirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar referencia" }));
    await waitFor(() => expect(referenceConfirm).toHaveBeenCalledWith("ART-CAVA", candidate, "WEB"));
    expect(onConfirmed).toHaveBeenCalledWith(article);
  }); */

  it("no ofrece búsqueda web al crear un artículo sin precio", () => {
    render(<SafeCatalogWritePanel domain="ARTICULO" operation="CREAR" initial={{ nombre: "Cava para cocinar", codigo: "ART-CAVA" }} onCancel={vi.fn()} onConfirmed={vi.fn()} />);
    expect(screen.queryByRole("button", { name: "Buscar precio online" })).not.toBeInTheDocument();
  });
});
