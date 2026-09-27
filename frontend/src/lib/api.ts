export class ApiError extends Error {
  status: number;
  payload: unknown;
  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

let csrf = "";
export function setCsrf(token: string) {
  csrf = token;
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  const method = (options.method || "GET").toUpperCase();
  if (csrf && method !== "GET") headers.set("X-CSRF-Token", csrf);
  const response = await fetch(`/api${path}`, { ...options, headers, credentials: "include" });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : detail?.message || "Request failed.";
    throw new ApiError(message, response.status, data);
  }
  return data as T;
}
