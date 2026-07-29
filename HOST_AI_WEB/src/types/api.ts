export type ApiEnvelopeBase = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
};

export type ApiError = {
  status?: number;
  code?: string;
  message?: string;
};

export type DashboardPayload = {
  estado_general?: string;
  prioridad?: unknown;
  pendientes?: unknown[];
  riesgos?: unknown[];
  recomendaciones?: unknown[];
  evento_activo?: unknown;
  workflows?: unknown[];
};

export type DashboardResponse = ApiEnvelopeBase & {
  dashboard?: DashboardPayload;
  error?: ApiError;
};

export type ChatResponse = ApiEnvelopeBase & {
  respuesta?: string;
  chat?: Record<string, unknown>;
  contexto?: Record<string, unknown>;
  error?: ApiError;
};
