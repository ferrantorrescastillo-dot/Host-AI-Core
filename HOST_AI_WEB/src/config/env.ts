const configuredApiUrl =
  import.meta.env.VITE_HOST_AI_API_BASE_URL ??
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";

export const HOST_AI_API_BASE_URL = configuredApiUrl
  .trim()
  .replace(/\/+$/, "")
  .replace(/\/api\/v1$/i, "");

export const API_VERSION = "1.0";
