import { clearSession, getToken } from "./auth";
import type { ApiError } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(status: number, payload: ApiError["error"]) {
    super(payload.message);
    this.code = payload.code;
    this.status = status;
    this.details = payload.details;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
  query?: Record<string, string | number | undefined | null>;
};

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(path.startsWith("http") ? path : `${API_URL}${path}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.auth !== false) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method || "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      clearSession();
    }
    const error = (payload as ApiError | null)?.error || {
      code: "REQUEST_FAILED",
      message: "Something went wrong. Please try again.",
    };
    throw new ApiClientError(response.status, error);
  }

  return (payload?.data ?? payload) as T;
}

export const api = {
  get: <T>(path: string, query?: RequestOptions["query"], auth = true) =>
    apiRequest<T>(path, { method: "GET", query, auth }),
  post: <T>(path: string, body?: unknown, auth = true) =>
    apiRequest<T>(path, { method: "POST", body, auth }),
  put: <T>(path: string, body?: unknown, auth = true) =>
    apiRequest<T>(path, { method: "PUT", body, auth }),
  patch: <T>(path: string, body?: unknown, auth = true) =>
    apiRequest<T>(path, { method: "PATCH", body, auth }),
  delete: <T>(path: string, auth = true) => apiRequest<T>(path, { method: "DELETE", auth }),
};
