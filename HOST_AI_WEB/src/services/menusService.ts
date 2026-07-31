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
  needs: (id: string) => hostAiApiClient.getMenuNeeds(id),
  createPurchaseProposal: (id: string) => hostAiApiClient.createMenuPurchaseProposal(id),
  updatePurchaseProposal: (menuId: string, proposalId: string, input: Record<string, unknown>) => hostAiApiClient.updateMenuPurchaseProposal(menuId, proposalId, input),
  createDraftOrders: (menuId: string, proposalId: string, version: number) => hostAiApiClient.createMenuDraftOrders(menuId, proposalId, version),
};
