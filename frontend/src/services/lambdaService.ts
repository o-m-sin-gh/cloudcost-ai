import { api } from "./api";
import type { Analysis, Connection, Inventory, LambdaFn, Metrics } from "../types";

export const lambdaService = {
  connection: () => api.get<Connection>("/aws/connection"),
  functions: () => api.get<Inventory>("/lambda/functions"),
  detail: (name: string) =>
    api.get<{ function: LambdaFn; metrics: Metrics; analysis: Analysis | null; data_source: string }>(`/lambda/${encodeURIComponent(name)}`),
};
