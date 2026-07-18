/**
 * Public Parent Portal (CLAUDE.md §3/§6/§9).
 *
 * Standalone (NOT the staff AppShell) — parents are not staff. A 3-step flow:
 *   1. Find your child   → request an OTP (never leaks whether the pair matched)
 *   2. Enter code        → verify OTP → receive an X-Parent-Token
 *   3. Dashboard         → fee summary, breakdown, history + online payment
 *
 * The token lives in component state only; every data call injects it via the
 * portal client's `X-Parent-Token` header.
 */
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/api/client";
import { portal } from "@/api/portal";
import type {
  ParentInvoice,
  RazorpayConfig,
  StudentFeeSummary,
} from "@/api/types";
import { Button, StatusBadge, TextInput, Toast } from "@/components/form";
import { loadRazorpay } from "@/lib/razorpay";
import { log } from "@/lib/logger";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

type Step = "find" | "code" | "dashboard";

type ToastState = { message: string; tone: "success" | "error" } | null;

function feeIcon(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("tuition")) return "🏛";
  if (n.includes("lab")) return "🧪";
  if (n.includes("transport")) return "🚌";
  if (n.includes("librar")) return "📗";
  if (n.includes("sport")) return "⚽";
  if (n.includes("exam")) return "📝";
  return "💰";
}

function Wordmark() {
  return (
    <div className="flex items-center gap-3">
      <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient text-lg text-white">
        ⚡
      </span>
      <div>
        <p className="text-lg font-bold text-slate-900">Fee Ledger</p>
        <p className="text-xs text-slate-500">Parent Portal</p>
      </div>
    </div>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-md">{children}</div>
    </div>
  );
}

export function ParentPortal() {
  const [step, setStep] = useState<Step>("find");
  const [studentId, setStudentId] = useState("");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [token, setToken] = useState("");
  const [studentName, setStudentName] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  async function onRequestOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await portal.requestOtp(studentId.trim(), phone.trim());
      log.info("Parent OTP requested", { action: "portal_request_otp", entity: studentId.trim() });
      setStep("code");
    } catch {
      // Never leak match/no-match; treat everything as "if it matches, sent".
      setStep("code");
    } finally {
      setBusy(false);
    }
  }

  async function onVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const result = await portal.verifyOtp(studentId.trim(), phone.trim(), otp.trim());
      log.info("Parent OTP verified", { action: "portal_verify_otp", entity: result.student_id });
      setToken(result.token);
      setStudentName(result.student_name);
      setStep("dashboard");
    } catch (err) {
      const detail =
        err instanceof ApiError && err.status === 400
          ? "That code is invalid or expired. Please try again."
          : err instanceof ApiError
            ? err.detail
            : "Could not verify the code. Please try again.";
      log.warn("Parent OTP verification failed", { action: "portal_verify_otp", entity: studentId.trim() });
      setError(detail);
    } finally {
      setBusy(false);
    }
  }

  async function onResend() {
    setError(null);
    setOtp("");
    setBusy(true);
    try {
      await portal.requestOtp(studentId.trim(), phone.trim());
    } catch {
      /* silent — same no-leak policy as step 1 */
    } finally {
      setBusy(false);
      setToast({ message: "If the details match, a new code has been sent.", tone: "success" });
    }
  }

  if (step === "find") {
    return (
      <Shell>
        <div className="rounded-2xl border border-slate-100 bg-white p-8 shadow-sm">
          <Wordmark />
          <h1 className="mt-6 text-xl font-bold text-slate-900">Find your child</h1>
          <p className="mt-1 text-sm text-slate-500">
            Enter your child's Student ID and your registered phone number to receive a
            verification code.
          </p>
          <form onSubmit={onRequestOtp} className="mt-6 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Student ID</label>
              <TextInput
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                placeholder="e.g. STU-00123"
                required
                autoComplete="off"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Guardian Phone
              </label>
              <TextInput
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Registered phone number"
                inputMode="tel"
                required
                autoComplete="tel"
              />
            </div>
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? "Sending…" : "Send code"}
            </Button>
          </form>
        </div>
        <p className="mt-4 text-center text-xs text-slate-400">
          Secure fee payments · Powered by Fee Ledger
        </p>
      </Shell>
    );
  }

  if (step === "code") {
    return (
      <Shell>
        <div className="rounded-2xl border border-slate-100 bg-white p-8 shadow-sm">
          <Wordmark />
          <h1 className="mt-6 text-xl font-bold text-slate-900">Enter code</h1>
          <p className="mt-1 text-sm text-slate-500">
            If the details match, a code has been sent to the registered phone number.
          </p>
          <form onSubmit={onVerifyOtp} className="mt-6 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Verification code
              </label>
              <TextInput
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="6-digit code"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                className="tracking-[0.4em]"
              />
            </div>
            {error && <Toast message={error} tone="error" />}
            {toast && <Toast message={toast.message} tone={toast.tone} />}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? "Verifying…" : "Verify & continue"}
            </Button>
          </form>
          <div className="mt-4 flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={() => {
                setStep("find");
                setError(null);
                setToast(null);
              }}
              className="text-slate-500 hover:text-slate-700"
            >
              ← Change details
            </button>
            <button
              type="button"
              onClick={() => void onResend()}
              disabled={busy}
              className="font-semibold text-brand hover:opacity-80 disabled:opacity-50"
            >
              Resend code
            </button>
          </div>
        </div>
      </Shell>
    );
  }

  return <ParentDashboard token={token} studentName={studentName} />;
}

function ParentDashboard({ token, studentName }: { token: string; studentName: string }) {
  const [fees, setFees] = useState<StudentFeeSummary | null>(null);
  const [invoices, setInvoices] = useState<ParentInvoice[]>([]);
  const [config, setConfig] = useState<RazorpayConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [payingId, setPayingId] = useState<number | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  const refetch = useCallback(async () => {
    const [feesData, invoicesData] = await Promise.all([
      portal.fees(token),
      portal.invoices(token),
    ]);
    setFees(feesData);
    setInvoices(invoicesData);
  }, [token]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    (async () => {
      try {
        const [feesData, invoicesData, cfg] = await Promise.all([
          portal.fees(token),
          portal.invoices(token),
          portal.razorpayConfig().catch(() => null),
        ]);
        if (!active) return;
        setFees(feesData);
        setInvoices(invoicesData);
        setConfig(cfg);
      } catch (err) {
        if (!active) return;
        const detail = err instanceof ApiError ? err.detail : "Could not load your fee details.";
        log.error("Parent dashboard load failed", { action: "portal_dashboard" });
        setToast({ message: detail, tone: "error" });
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token]);

  async function payInvoice(invoice: ParentInvoice) {
    setPayingId(invoice.id);
    setToast(null);
    try {
      const ready = await loadRazorpay();
      if (!ready || !window.Razorpay) {
        log.warn("Razorpay checkout unavailable", { action: "portal_pay", entity: invoice.id });
        setToast({ message: "Could not load the payment gateway. Please retry.", tone: "error" });
        return;
      }

      const order = await portal.payOrder(token, invoice.id);
      log.info("Parent payment order created", {
        action: "portal_pay_order",
        entity: invoice.id,
        method: order.order_id,
      });

      const rzp = new window.Razorpay({
        key: order.key_id,
        order_id: order.order_id,
        amount: order.amount,
        currency: order.currency,
        name: "Fee Ledger",
        description: invoice.invoice_number,
        theme: { color: "#2563EB" },
        handler: (resp) => {
          void (async () => {
            try {
              const result = await portal.payVerify(token, {
                invoice: invoice.id,
                razorpay_order_id: resp.razorpay_order_id,
                razorpay_payment_id: resp.razorpay_payment_id,
                razorpay_signature: resp.razorpay_signature,
              });
              log.info("Parent payment verified", {
                action: "portal_pay_verify",
                entity: invoice.id,
                method: result.status,
              });
              await refetch();
              setToast({ message: "Payment received. Your balance is updated.", tone: "success" });
            } catch (err) {
              const detail = err instanceof ApiError ? err.detail : "Verification failed.";
              log.error("Parent payment verification failed", {
                action: "portal_pay_verify",
                entity: invoice.id,
              });
              setToast({ message: detail, tone: "error" });
            }
          })();
        },
      });

      rzp.on("payment.failed", (resp) => {
        log.warn("Parent payment failed", {
          action: "portal_pay",
          entity: invoice.id,
          method: resp.error.code,
        });
        setToast({ message: `Payment failed: ${resp.error.description}`, tone: "error" });
      });

      rzp.open();
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        log.warn("Razorpay not configured", { action: "portal_pay", entity: invoice.id });
        setToast({ message: "Online payment is not available right now.", tone: "error" });
      } else {
        const detail = err instanceof ApiError ? err.detail : "Could not start the payment.";
        log.error("Parent checkout error", { action: "portal_pay", entity: invoice.id });
        setToast({ message: detail, tone: "error" });
      }
    } finally {
      setPayingId(null);
    }
  }

  const payable = invoices.filter((inv) => Number(inv.balance) > 0);
  const canPay = Boolean(config?.enabled) && payable.length > 0;

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center justify-between">
          <Wordmark />
        </div>

        <div className="rounded-2xl bg-brand-gradient p-6 text-white shadow-sm">
          <p className="text-sm text-white/80">Welcome</p>
          <h1 className="mt-1 text-2xl font-bold">{studentName}</h1>
          <p className="mt-1 text-sm text-white/80">Here is your fee summary and payment history.</p>
        </div>

        {toast && <Toast message={toast.message} tone={toast.tone} />}

        {loading || !fees ? (
          <p className="text-sm text-slate-500">Loading your fee details…</p>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">Total Fee</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{formatMoney(fees.total_fee)}</p>
              </div>
              <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">Amount Paid</p>
                <p className="mt-1 text-2xl font-bold text-emerald-600">{formatMoney(fees.paid)}</p>
                <p className="mt-1 text-xs text-emerald-600">✓ {fees.progress_percent}% paid</p>
              </div>
              <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">Outstanding</p>
                <p className="mt-1 text-2xl font-bold text-rose-600">{formatMoney(fees.outstanding)}</p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700">Fee Payment Progress</span>
                <span className="font-semibold text-brand">{fees.progress_percent}%</span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-brand-gradient"
                  style={{ width: `${fees.progress_percent}%` }}
                />
              </div>
              <div className="mt-2 flex justify-between text-xs text-slate-400">
                <span>Paid: {formatMoney(fees.paid)}</span>
                <span>Remaining: {formatMoney(fees.outstanding)}</span>
              </div>
            </div>

            {canPay && (
              <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
                <h2 className="text-base font-semibold text-slate-900">Pay your dues</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Secure online payment for outstanding invoices.
                </p>
                <div className="mt-4 space-y-3">
                  {payable.map((inv) => (
                    <div
                      key={inv.id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-4"
                    >
                      <div>
                        <p className="text-sm font-semibold text-slate-800">
                          Invoice #{inv.invoice_number}
                        </p>
                        <p className="text-xs text-slate-400">
                          Due {formatDate(inv.due_date)} · Balance {formatMoney(inv.balance)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={inv.status} />
                        <Button
                          type="button"
                          onClick={() => void payInvoice(inv)}
                          disabled={payingId !== null}
                        >
                          {payingId === inv.id ? "Opening…" : "Pay Now"}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
              <h2 className="px-6 py-4 text-base font-semibold text-slate-900">Fee Breakdown</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Fee Type</th>
                      <th className="px-6 py-3 text-right font-semibold">Amount</th>
                      <th className="px-6 py-3 text-right font-semibold">Paid</th>
                      <th className="px-6 py-3 text-right font-semibold">Balance</th>
                      <th className="px-6 py-3 text-right font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {fees.fee_breakdown.map((row) => (
                      <tr key={row.fee_type}>
                        <td className="px-6 py-3 font-medium text-slate-800">
                          {feeIcon(row.fee_type)} {row.fee_type}
                        </td>
                        <td className="px-6 py-3 text-right">{formatMoney(row.amount)}</td>
                        <td className="px-6 py-3 text-right text-emerald-600">
                          {formatMoney(row.paid)}
                        </td>
                        <td
                          className={`px-6 py-3 text-right ${
                            Number(row.balance) > 0 ? "text-rose-600" : "text-slate-400"
                          }`}
                        >
                          {formatMoney(row.balance)}
                        </td>
                        <td className="px-6 py-3 text-right">
                          <StatusBadge status={row.status} />
                        </td>
                      </tr>
                    ))}
                    {fees.fee_breakdown.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 text-slate-400">
                          No fees billed yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
              <h2 className="mb-3 text-base font-semibold text-slate-900">Payment History</h2>
              <div className="space-y-3">
                {fees.payment_history.map((p, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                        ✓
                      </span>
                      <div>
                        <p className="text-sm font-medium text-slate-800">{p.fee_type || "Payment"}</p>
                        <p className="text-xs text-slate-400">
                          Receipt #{p.receipt} · {formatDate(p.paid_at)}
                        </p>
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-emerald-600">
                      +{formatMoney(p.amount)}
                    </span>
                  </div>
                ))}
                {fees.payment_history.length === 0 && (
                  <p className="text-sm text-slate-400">No payments recorded.</p>
                )}
              </div>
            </div>
          </>
        )}

        <p className="text-center text-xs text-slate-400">
          Secure fee payments · Powered by Fee Ledger
        </p>
      </div>
    </div>
  );
}
