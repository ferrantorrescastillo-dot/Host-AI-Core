import { hostAiApiClient } from "../api/client";
import { bibliotecaService, type ElaboracionesQuery } from "./bibliotecaService";
import type { MenuInput } from "../types/menus";

export const menusService = {
  list: () => hostAiApiClient.getMenus(),
  get: (id: string) => hostAiApiClient.getMenu(id),
  elaborations: (query: ElaboracionesQuery = {}) => bibliotecaService.list(query),
  create: (input: MenuInput) => hostAiApiClient.createMenu(input),
  update: (id: string, input: MenuInput) => hostAiApiClient.updateMenu(id, input),
  archive: (id: string, version: number) => hostAiApiClient.archiveMenu(id, version),
};
