import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";

const ROOT = path.resolve(__dirname, "..");

function walk(dir: string, found: string[] = []): string[] {
  for (const item of fs.readdirSync(dir)) {
    const full = path.join(dir, item);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      walk(full, found);
    } else if (full.endsWith(".ts") || full.endsWith(".tsx")) {
      found.push(full);
    }
  }
  return found;
}

describe("seguridad de dependencias frontend", () => {
  it("no importa Core ni rutas Python internas", () => {
    const files = walk(ROOT);
    for (const file of files) {
      const content = fs.readFileSync(file, "utf8");
      expect(content.includes("CORE/")).toBe(false);
      expect(content.includes("from CORE")).toBe(false);
      expect(content.includes("SERVICIOS/")).toBe(false);
      expect(content.includes("DATOS/")).toBe(false);
      expect(content.includes("MOTORES/")).toBe(false);
    }
  });
});
