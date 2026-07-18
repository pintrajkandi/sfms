/**
 * Frontend logger — THREE LEVELS ONLY: info / warn / error (CLAUDE.md §9).
 *
 * Logs are shipped to the backend (`/client-logs/`) and printed in the backend
 * container's stdout, so the full activity trail shows up in `docker compose logs`
 * — NOT the browser console. Never log secrets or full PII.
 */
type Level = "info" | "warn" | "error";

interface Context {
  action?: string;
  entity?: string | number;
  method?: string;
  [key: string]: unknown;
}

interface Entry extends Context {
  level: Level;
  message: string;
  url: string;
  ts: string;
}

// Inlined (not imported from api/client) to avoid a circular import.
function logApiBase(): string {
  const override = import.meta.env.VITE_API_BASE_URL;
  if (override) return override;
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:8000/api/v1`;
}

const buffer: Entry[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

function flush(useKeepalive = false): void {
  if (buffer.length === 0) return;
  const logs = buffer.splice(0, buffer.length);
  // Raw fetch (NOT the api client) so shipping never logs itself → no loop.
  fetch(`${logApiBase()}/client-logs/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ logs }),
    keepalive: useKeepalive,
  }).catch(() => {
    /* dev log sink is best-effort; drop on failure */
  });
}

function emit(level: Level, message: string, ctx?: Context): void {
  buffer.push({
    level,
    message,
    url: window.location.pathname + window.location.search,
    ts: new Date().toISOString(),
    ...ctx,
  });
  if (flushTimer == null) {
    flushTimer = setTimeout(() => {
      flushTimer = null;
      flush();
    }, 400);
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => flush(true));
}

export const log = {
  info: (message: string, ctx?: Context) => emit("info", message, ctx),
  warn: (message: string, ctx?: Context) => emit("warn", message, ctx),
  error: (message: string, ctx?: Context) => emit("error", message, ctx),
};
