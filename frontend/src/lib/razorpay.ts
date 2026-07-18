/**
 * Razorpay Checkout loader + minimal typed surface.
 *
 * The Checkout script is injected once and cached; subsequent calls resolve
 * immediately. We never bundle the SDK — it must be loaded from Razorpay's CDN
 * so the hosted checkout stays in sync. No `any`: the surface is described with
 * explicit interfaces (CLAUDE.md §6).
 */
import { log } from "@/lib/logger";

const CHECKOUT_SRC = "https://checkout.razorpay.com/v1/checkout.js";

/** Response passed to the success `handler` by Razorpay Checkout. */
export interface RazorpaySuccessResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

/** Payload for the `payment.failed` event. */
export interface RazorpayFailureResponse {
  error: {
    code: string;
    description: string;
    reason?: string;
    metadata?: { order_id?: string; payment_id?: string };
  };
}

export interface RazorpayPrefill {
  name?: string;
  email?: string;
  contact?: string;
}

export interface RazorpayOptions {
  key: string;
  order_id: string;
  amount: number;
  currency: string;
  name: string;
  description?: string;
  handler: (response: RazorpaySuccessResponse) => void;
  prefill?: RazorpayPrefill;
  theme?: { color?: string };
}

export interface RazorpayInstance {
  open(): void;
  on(event: "payment.failed", cb: (response: RazorpayFailureResponse) => void): void;
}

export interface RazorpayConstructor {
  new (options: RazorpayOptions): RazorpayInstance;
}

declare global {
  interface Window {
    Razorpay?: RazorpayConstructor;
  }
}

let loader: Promise<boolean> | null = null;

/** Inject the Checkout script once. Resolves true when ready, false on error. */
export function loadRazorpay(): Promise<boolean> {
  if (typeof window !== "undefined" && window.Razorpay) return Promise.resolve(true);
  if (loader) return loader;

  loader = new Promise<boolean>((resolve) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${CHECKOUT_SRC}"]`);
    const script = existing ?? document.createElement("script");
    script.src = CHECKOUT_SRC;
    script.async = true;
    script.addEventListener("load", () => resolve(Boolean(window.Razorpay)));
    script.addEventListener("error", () => {
      log.warn("Razorpay checkout script failed to load", { action: "razorpay_load" });
      loader = null; // allow a retry on the next click
      resolve(false);
    });
    if (!existing) document.body.appendChild(script);
  });

  return loader;
}
