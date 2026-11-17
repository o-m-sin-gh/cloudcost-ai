import { api } from "./api";
import type { Metrics } from "../types";

export const metricsService = {
  get: (name: string, days = 14, refresh = false) =>
    api.get<Metrics>(`/metrics/${encodeURIComponent(name)}?days=${days}&refresh=${refresh}`),
};
