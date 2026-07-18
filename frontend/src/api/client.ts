/**
 * Typed API client. The tenant is resolved server-side from the request host
 * (subdomain) — the frontend never sends a tenant id (CLAUDE.md §3).
 *
 * The API host mirrors the page host, so on `greenfield-high.localhost:5173` the
 * client talks to `greenfield-high.localhost:8000` and every request is
 * automatically scoped to that school's schema. On the apex host it hits the
 * public (onboarding) API.
 */
import { log } from "@/lib/logger";

const API_PORT = "8000";
const APEX_HOSTS = new Set(["localhost", "127.0.0.1", "app", "www"]);

/** Subdomain label for the current page, or null on the apex host. */
export function currentSlug(): string | null {
  const parts = window.location.hostname.split(".");
  // e.g. greenfield-high.localhost -> ["greenfield-high", "localhost"]
  if (parts.length >= 2 && !APEX_HOSTS.has(parts[0])) return parts[0];
  return null;
}

export function isTenantHost(): boolean {
  return currentSlug() !== null;
}

/** Base API URL derived from the page host (override with VITE_API_BASE_URL). */
export function apiBase(): string {
  const override = import.meta.env.VITE_API_BASE_URL;
  if (override) return override;
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:${API_PORT}/api/v1`;
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API ${status}`);
  }

  /** First human-readable message from a DRF error body. */
  get detail(): string {
    const b = this.body as Record<string, unknown> | null;
    if (!b) return "Something went wrong.";
    if (typeof b.detail === "string") return b.detail;
    const first = Object.values(b)[0];
    if (Array.isArray(first)) return String(first[0]);
    return typeof first === "string" ? first : "Something went wrong.";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const started = performance.now();
  log.info(`API → ${method} ${path}`, { action: "api_request", method });

  const res = await fetch(`${apiBase()}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken") ?? "",
      ...init.headers,
    },
    ...init,
  });

  const ms = Math.round(performance.now() - started);
  const line = `API ← ${method} ${path} ${res.status} (${ms}ms)`;

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    if (res.status >= 500) log.error(line, { action: "api_response", entity: res.status });
    else log.warn(line, { action: "api_response", entity: res.status });
    throw new ApiError(res.status, body);
  }
  log.info(line, { action: "api_response", entity: res.status });
  return (res.status === 204 ? undefined : await res.json()) as T;
}

async function requestForm<T>(path: string, form: FormData, method = "PATCH"): Promise<T> {
  // No Content-Type header — the browser sets the multipart boundary itself.
  log.info(`API → ${method} ${path} (multipart)`, { action: "api_request", method });
  const res = await fetch(`${apiBase()}${path}`, {
    method,
    credentials: "include",
    headers: { "X-CSRFToken": getCookie("csrftoken") ?? "" },
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    log.warn(`API ← ${method} ${path} ${res.status}`, { action: "api_response", entity: res.status });
    throw new ApiError(res.status, body);
  }
  log.info(`API ← ${method} ${path} ${res.status}`, { action: "api_response", entity: res.status });
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  patchForm: <T>(path: string, form: FormData) => requestForm<T>(path, form),
  postForm: <T>(path: string, form: FormData) => requestForm<T>(path, form, "POST"),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  /** Absolute URL for file downloads (auth via session cookie). */
  fileUrl: (path: string) => `${apiBase()}${path}`,
};
