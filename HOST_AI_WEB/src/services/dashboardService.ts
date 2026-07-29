import { hostAiApiClient } from "../api/client";

export const dashboardService = {
  load() {
    return hostAiApiClient.getDashboard();
  },
};
