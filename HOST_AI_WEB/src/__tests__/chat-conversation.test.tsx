import { createRef } from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { AssistantMessage, ChatComposer, ChatPurchaseGroups, ChatTechnicalDetails, MarkdownContent, UserMessage } from "../ui/components/ChatConversation";

afterEach(cleanup);

describe("componentes de conversación", () => {
  it("renderiza Markdown GFM con estructura y tabla desplazable", () => {
    render(<MarkdownContent>{"## Resumen\n\n- **Stock** revisado\n\n| Artículo | Cantidad |\n| --- | ---: |\n| Patata | 4 |"}</MarkdownContent>);

    expect(screen.getByRole("heading", { name: "Resumen" })).toBeInTheDocument();
    expect(screen.getByText("Stock").tagName).toBe("STRONG");
    expect(screen.getByRole("list")).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByLabelText("Tabla desplazable")).toHaveClass("chat-table-wrap");
  });

  it("no interpreta HTML incluido en una respuesta", () => {
    const { container } = render(<MarkdownContent>{"Texto <script>alert('x')</script> seguro"}</MarkdownContent>);

    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
  });

  it("deduplica solo el enlace Markdown equivalente a la UI action", () => {
    const item = {
      id: "assistant-draft", role: "host_ai" as const,
      text: "Existe un borrador. [Abrir borrador](/compras?pedido_id=PED-DRAFT-42)\n\n[Ver proveedor](/proveedores/SARDA)",
      navigation: { to: "/compras?pedido_id=PED-DRAFT-42", label: "Abrir borrador" },
      purchaseGroups: [{
        proveedor: "SARDA", estado_pedido: "borrador",
        articulos: [{ articulo_id: "ART-1", nombre: "Azúcar", cantidad: .1, unidad: "kg" }],
        action: { type: "OPEN_ORDER" as const, label: "Abrir borrador", pedido_id: "PED-DRAFT-42" },
      }],
      operationalIncidents: [{ articulo_id: "ART-1", reason: "FORMATO_PENDIENTE" }],
    };
    const view = render(<MemoryRouter><AssistantMessage item={item} sending={false} onConfirmation={vi.fn()} onOpenNewTab={vi.fn()} /></MemoryRouter>);
    const scoped = within(view.container);

    expect(scoped.getAllByRole("link", { name: "Abrir borrador" })).toHaveLength(1);
    expect(scoped.getByRole("link", { name: "Abrir borrador" })).toHaveAttribute("href", "/compras?pedido_id=PED-DRAFT-42");
    expect(scoped.queryByText("Existe un borrador.")).not.toBeInTheDocument();
    expect(scoped.queryByRole("link", { name: "Ver proveedor" })).not.toBeInTheDocument();
    expect(scoped.getByRole("heading", { name: "Requiere tu atención" })).toBeInTheDocument();
    expect(scoped.getByText("ART-1: FORMATO_PENDIENTE")).toBeInTheDocument();
  });

  it("conserva CTA Markdown cuando no existe una UI action equivalente", () => {
    const view = render(<MarkdownContent>{"[Abrir borrador](/compras?pedido_id=PED-OTHER)"}</MarkdownContent>);
    expect(within(view.container).getByRole("link", { name: "Abrir borrador" })).toHaveAttribute("href", "/compras?pedido_id=PED-OTHER");
  });

  it("conserva la respuesta narrativa cuando no existe síntesis operativa", () => {
    const item = { id: "assistant-normal", role: "host_ai" as const, text: "Respuesta narrativa de Terra sin síntesis." };
    const view = render(<MemoryRouter><AssistantMessage item={item} sending={false} onConfirmation={vi.fn()} onOpenNewTab={vi.fn()} /></MemoryRouter>);
    expect(within(view.container).getByText("Respuesta narrativa de Terra sin síntesis.")).toBeInTheDocument();
  });

  it("mantiene los detalles técnicos plegados por defecto", () => {
    render(<ChatTechnicalDetails requestId="REQ-DETALLE" safeStatus={{ modoSeguro: true, datosRealesModificados: false }} />);

    const details = screen.getByText("Detalles").closest("details");
    expect(details).not.toHaveAttribute("open");
    expect(screen.getByText("REQ-DETALLE")).toBeInTheDocument();
  });

  it("muestra el mensaje del usuario sin Markdown", () => {
    render(<UserMessage item={{ id: "1", role: "usuario", text: "**texto literal**" }} />);

    expect(screen.getByText("**texto literal**")).toBeInTheDocument();
    expect(screen.queryByText("texto literal")).not.toBeInTheDocument();
  });

  it("limita el crecimiento automático del composer", () => {
    const textareaRef = createRef<HTMLTextAreaElement>();
    Object.defineProperty(HTMLTextAreaElement.prototype, "scrollHeight", { configurable: true, get: () => 240 });

    render(<ChatComposer value="Varias líneas" sending={false} canSend textareaRef={textareaRef} onChange={vi.fn()} onSubmit={vi.fn()} onKeyDown={vi.fn()} />);

    expect(textareaRef.current).toHaveStyle({ height: "176px", overflowY: "auto" });
    fireEvent.change(textareaRef.current!, { target: { value: "otro" } });
  });

  it("presenta compras agrupadas y acciones seguras por estado", () => {
    render(<MemoryRouter><ChatPurchaseGroups groups={[
      { proveedor: "SARDA", estado_pedido: "preparado", articulos: [{ articulo_id: "A1", nombre: "Azúcar", cantidad: .1, unidad: "kg", precio_unitario: .82, unidad_precio: "kg", coste_neto: .082 }, { articulo_id: "A2", nombre: "Maizena", cantidad: .2, unidad: "kg" }], action: { type: "OPEN_ORDER", label: "Abrir pedido", pedido_id: "PED-1" } },
      { proveedor: "PAU GAVALDA", estado_pedido: "borrador", articulos: [{ articulo_id: "A3", nombre: "Huevos", cantidad: 12, unidad: "u" }], pedido_relacionado: { pedido_id: "PED-2", estado: "borrador", lineas_relevantes: [{ articulo_id: "A3", nombre: "Huevos", cantidad_prevista: 18, unidad: "u", cubriria_necesidad: true }] }, action: { type: "OPEN_ORDER", label: "Abrir borrador", pedido_id: "PED-2" } },
      { proveedor: "PESCADO", estado_pedido: "ninguno", articulos: [{ articulo_id: "A4", nombre: "Gamba", cantidad: 1.2, unidad: "kg", formato: "caja", precio_unitario: 15, unidad_precio: "kg", coste_neto: 18 }], action: { type: "PREPARE_ORDER", label: "Preparar pedido", menu_id: "MENU-1" } },
      { proveedor: "Sin proveedor asignado", estado_pedido: "ninguno", articulos: [{ articulo_id: "A5", nombre: "Sal", cantidad: 1, unidad: "kg" }], action: null },
    ]} /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "🛒 Compra necesaria" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "SARDA" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sin proveedor asignado" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir pedido" })).toHaveAttribute("href", "/compras?pedido_id=PED-1");
    expect(screen.getByRole("link", { name: "Abrir borrador" })).toHaveAttribute("href", "/compras?pedido_id=PED-2");
    expect(screen.getByRole("link", { name: "Preparar pedido" })).toHaveAttribute("href", "/menus?menu_id=MENU-1&view=compra");
    expect(screen.getByText("Formato de compra: caja")).toBeInTheDocument();
    expect(screen.getByText(/Coste estimado: 18,00/)).toBeInTheDocument();
    expect(screen.getByText(/Precio: 0,82.*\/kg/)).toBeInTheDocument();
    expect(screen.getByText(/Coste estimado: 0,08/)).toBeInTheDocument();
    expect(screen.getByText(/no cuenta como cobertura confirmada.*cantidad prevista sería suficiente/)).toBeInTheDocument();
    expect(screen.getAllByText("Formato de compra: pendiente").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Unidad: kg/).length).toBeGreaterThan(0);
  });

  it("prioriza un único borrador relevante y separa los campos operativos", () => {
    const view = render(<MemoryRouter><ChatPurchaseGroups groups={[{
      proveedor: "SARDA", estado_pedido: "borrador",
      articulos: [{ articulo_id: "ART-AZUCAR", nombre: "Azúcar", cantidad: .1, unidad: "kg", precio_unitario: .82, unidad_precio: "kg", coste_neto: .082, formato: null }],
      pedido_relacionado: { pedido_id: "PED-0AD463508C", estado: "borrador", lineas_relevantes: [{ articulo_id: "ART-AZUCAR", nombre: "Azúcar", cantidad_prevista: .2, unidad: "kg", cubriria_necesidad: true }] },
      action: { type: "OPEN_ORDER", label: "Abrir borrador", pedido_id: "PED-0AD463508C" },
    }]} /></MemoryRouter>);

    const scoped = within(view.container);
    expect(scoped.getByText("Azúcar — faltan 0,1 kg")).toBeInTheDocument();
    expect(scoped.getByText("Unidad: kg")).toBeInTheDocument();
    expect(scoped.getByText(/Precio: 0,82.*\/kg/)).toBeInTheDocument();
    expect(scoped.getByText(/Coste estimado: 0,08/)).toBeInTheDocument();
    expect(scoped.getByText("Formato de compra: pendiente")).toBeInTheDocument();
    expect(scoped.getByText(/0,2 kg.*no cuenta como cobertura confirmada.*cantidad prevista sería suficiente/)).toBeInTheDocument();
    expect(scoped.getByRole("link", { name: "Abrir borrador" })).toHaveAttribute("href", "/compras?pedido_id=PED-0AD463508C");
    expect(scoped.queryByRole("link", { name: "Preparar pedido" })).not.toBeInTheDocument();
    expect(scoped.queryByRole("link", { name: "Abrir Compras" })).not.toBeInTheDocument();
  });
});
