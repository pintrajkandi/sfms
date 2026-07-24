/**
 * Frontend error monitoring — Sentry (CLAUDE.md §10).
 *
 * Env-gated: with no `VITE_SENTRY_DSN` set, Sentry stays dormant and the app
 * behaves exactly as before (dev/local). Never ship PII (§9/§10) — we disable
 * `sendDefaultPii` and don't attach form values.
 */
import * as Sentry from "@sentry/react";

let enabled = false;

export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;
  if (!dsn) return; // dormant unless a DSN is configured
  Sentry.init({
    dsn,
    environment: (import.meta.env.VITE_SENTRY_ENVIRONMENT as string) || import.meta.env.MODE,
    sendDefaultPii: false,
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? 0.1),
    // Default integrations capture unhandled errors + promise rejections; our
    // lib/logger also forwards deliberate `error` calls via captureError().
  });
  enabled = true;
}

export function captureError(message: string, context?: Record<string, unknown>): void {
  if (!enabled) return;
  Sentry.captureException(new Error(message), { extra: context });
}

export const sentryEnabled = () => enabled;
