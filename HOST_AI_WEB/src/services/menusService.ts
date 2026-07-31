import { hostAiApiClient } from "../api/client";
import type { MenuInput } from "../types/menus";

export const menusService = {
  list: () => hostAiApiClient.getMenus(),
  get: (id: string) => hostAiApiClient.getMenu(id),
  elaborations: () => hostAiApiClient.getMenuElaborations(),
  create: (input: MenuInput) => hostAiApiClient.createMenu(input),
  update: (id: string, input: MenuInput) => hostAiApiClient.updateMenu(id, input),
  archive: (id: string, version: number) => hostAiApiClient.archiveMenu(id, version),
};
