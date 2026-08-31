import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "../ui/App";

const styles = readFileSync(resolve(process.cwd(), "src/ui/styles.css"), "utf8");

describe("layout inmersivo del Chat", () => {
  beforeEach(() => {
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: () => undefined,
    });
  });
  it("conserva los componentes del chat dentro del área dedicada", () => {
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    expect(screen.getByTestId("app-shell")).toContainElement(screen.getByLabelText("Chat operativo de Host AI"));
    expect(screen.getByLabelText("Conversación")).toHaveClass("chat-log");
    expect(screen.getByLabelText("Mensaje para Host AI").closest("form")).toHaveClass("chat-composer");
    expect(screen.getByRole("link", { name: "Chat" })).toHaveAttribute("aria-current", "page");
  });

  it("define una sola zona de scroll, altura completa y anchuras diferenciadas", () => {
    expect(styles).toMatch(/\.app-shell:has\(\.chat-page\)[^{]*\{[^}]*height:\s*100dvh[^}]*overflow:\s*hidden/s);
    expect(styles).toMatch(/\.chat-page\s*\{[^}]*width:\s*100%[^}]*height:\s*100%[^}]*overflow:\s*hidden/s);
    expect(styles).toMatch(/\.chat-log\s*\{[^}]*overflow-y:\s*auto/s);
    expect(styles).toMatch(/\.chat-markdown\s*>\s*:not\(\.chat-table-wrap\):not\(pre\)[^{]*\{[^}]*52rem/s);
    expect(styles).toMatch(/\.chat-table-wrap\s*\{[^}]*max-width:\s*100%/s);
    expect(styles).toMatch(/\.chat-composer\s*\{[^}]*width:\s*min\(100%,\s*64rem\)/s);
  });

  it("mantiene políticas responsive específicas para tablet y móvil", () => {
    expect(styles).toContain("@media (max-width: 900px)");
    expect(styles).toContain("grid-template-rows: auto minmax(0, 1fr)");
    expect(styles).toContain("@media (max-width: 600px)");
    expect(styles).toContain("env(safe-area-inset-bottom)");
  });
});
