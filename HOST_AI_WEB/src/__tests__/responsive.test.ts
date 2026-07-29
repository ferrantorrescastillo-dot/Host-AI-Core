import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";

describe("responsive basico", () => {
  it("incluye media query para movil", () => {
    const cssPath = path.resolve(__dirname, "../ui/styles.css");
    const css = fs.readFileSync(cssPath, "utf8");
    expect(css.includes("@media (max-width: 900px)")).toBe(true);
    expect(css.includes("grid-template-columns: 1fr;")).toBe(true);
  });
});
