export class ApiError extends Error {
  notes: string[];
  status: number;
  constructor(message: string, status: number, notes: string[] = []) {
    super(message);
    this.status = status;
    this.notes = notes;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new ApiError("Cannot reach the backend. Start it with: uvicorn backend.app.main:app --port 8000", 0);
  }
  if (!res.ok) {
    let detail = res.statusText, notes: string[] = [];
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      notes = body.notes ?? [];
    } catch { /* non-JSON error */ }
    throw new ApiError(detail, res.status, notes);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T,>(p: string) => request<T>(p),
  post: <T,>(p: string, body?: unknown) => request<T>(p, { method: "POST", body: JSON.stringify(body ?? {}) }),
  put: <T,>(p: string, body: unknown) => request<T>(p, { method: "PUT", body: JSON.stringify(body) }),
};
