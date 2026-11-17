import { api } from "./api";
import type { AppSettings, CostAnalysis, OptRecord, Recommendations, ReportFile } from "../types";

export const recommendationService = {
  list: (refresh = false) => api.get<Recommendations>(`/recommendations?refresh=${refresh}`),
  cost: () => api.get<CostAnalysis>("/cost-analysis"),
};

export const optimizationService = {
  history: () => api.get<OptRecord[]>("/optimization/history"),
  dryRun: (function_name: string, target_memory_mb?: number) =>
    api.post<OptRecord>("/optimization/dry-run", { function_name, target_memory_mb }),
  approve: (record_id: string) => api.post<OptRecord>("/optimization/approve", { record_id }),
  reject: (record_id: string) => api.post<OptRecord>("/optimization/reject", { record_id }),
  apply: (record_id: string) => api.post<OptRecord>("/optimization/apply", { record_id }),
  verify: (record_id: string) => api.post<OptRecord>("/optimization/verify", { record_id }),
  rollback: (record_id: string) => api.post<OptRecord>("/optimization/rollback", { record_id }),
};

export const reportService = {
  list: () => api.get<ReportFile[]>("/reports"),
  generate: () => api.post<ReportFile[]>("/reports/generate"),
};

export const settingsService = {
  get: () => api.get<AppSettings>("/settings"),
  update: (b: Partial<Pick<AppSettings, "region" | "lookback_days" | "min_monthly_savings_usd">>) =>
    api.put<AppSettings>("/settings", b),
};
