/**
 * Parent portal API client (CLAUDE.md §3/§6).
 *
 * The parent portal is PUBLIC — it is NOT staff-session-authed. Parents prove
 * they own a student by verifying an OTP; the backend hands back an opaque token
 * that must ride on every subsequent call as the `X-Parent-Token` header.
 *
 * These endpoints must therefore bypass the standard session/CSRF `api` client
 * (which sends cookies) and talk to the API with a plain `fetch`. The tenant is
 * still resolved server-side from the request host — we never send a tenant id.
 */
import { ApiError, apiBase } from "@/api/client";
import { log } from "@/lib/logger";
import type {
  ParentInvoice,
  ParentPayOrder,
  ParentPayVerifyResult,
  ParentVerifyResult,
  RazorpayConfig,
  RazorpayVerifyPayload,
  StudentFeeSummary,
} from "@/api/types";

async function portalFetch<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["X-Parent-Token"] = token;

  log.info(`Portal → ${method} ${path}`, { action: "portal_request", method });

  // Raw fetch — no credentials/CSRF. Auth is the X-Parent-Token header only.
  const res = await fetch(`${apiBase()}${path}`, { ...init, method, headers });
  const line = `Portal ← ${method} ${path} ${res.status}`;

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    if (res.status >= 500) log.error(line, { action: "portal_response", entity: res.status });
    else log.warn(line, { action: "portal_response", entity: res.status });
    throw new ApiError(res.status, body);
  }
  log.info(line, { action: "portal_response", entity: res.status });
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const portal = {
  /** Always resolves 200 with a generic message — never leaks whether the pair matched. */
  requestOtp: (student_id: string, phone: string) =>
    portalFetch<{ detail: string }>("/portal/request-otp/", {
      method: "POST",
      body: JSON.stringify({ student_id, phone }),
    }),

  verifyOtp: (student_id: string, phone: string, otp: string) =>
    portalFetch<ParentVerifyResult>("/portal/verify-otp/", {
      method: "POST",
      body: JSON.stringify({ student_id, phone, otp }),
    }),

  fees: (token: string) =>
    portalFetch<StudentFeeSummary>("/portal/fees/", {}, token),

  invoices: (token: string) =>
    portalFetch<ParentInvoice[]>("/portal/invoices/", {}, token),

  payOrder: (token: string, invoice: number) =>
    portalFetch<ParentPayOrder>(
      "/portal/pay/order/",
      { method: "POST", body: JSON.stringify({ invoice }) },
      token,
    ),

  payVerify: (token: string, payload: RazorpayVerifyPayload) =>
    portalFetch<ParentPayVerifyResult>(
      "/portal/pay/verify/",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    ),

  /** Public gateway config (AllowAny) — reused to decide whether to show Pay Now. */
  razorpayConfig: () =>
    portalFetch<RazorpayConfig>("/payments/razorpay/config/"),
};
