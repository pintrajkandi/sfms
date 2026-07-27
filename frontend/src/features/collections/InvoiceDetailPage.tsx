import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { invoices, payments, razorpay, settings, students } from "@/api/resources";
import { ApiError } from "@/api/client";
import type { Invoice } from "@/api/types";
import { Toast } from "@/components/form";
import { loadRazorpay } from "@/lib/razorpay";
import { log } from "@/lib/logger";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const CAT_COLORS: Record<string, string> = {
  academic: "bg-blue-50 text-blue-600",
  facility: "bg-purple-50 text-purple-600",
  "extra-curricular": "bg-orange-50 text-orange-600",
  science: "bg-teal-50 text-teal-600",
  transport: "bg-amber-50 text-amber-700",
  examination: "bg-rose-50 text-rose-600",
};
const catColor = (c: string) => CAT_COLORS[c?.toLowerCase()] ?? "bg-slate-100 text-slate-600";

const METHOD_LABELS: Record<string, string> = {
  card: "Credit Card",
  bank_transfer: "Bank Transfer",
  paypal: "PayPal",
  cash: "Cash",
  upi: "UPI",
  cheque: "Cheque",
};

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-1 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}

export function InvoiceDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();

  const invoiceQ = useQuery({ queryKey: ["invoice", id], queryFn: () => invoices.get(id) });
  const inv = invoiceQ.data;

  const razorpayConfigQ = useQuery({
    queryKey: ["razorpay-config"],
    queryFn: () => razorpay.config(),
  });

  const [paying, setPaying] = useState(false);
  const [toast, setToast] = useState<{ message: string; tone: "success" | "error" } | null>(null);

  async function payOnline(invoice: Invoice) {
    setPaying(true);
    setToast(null);
    try {
      const ready = await loadRazorpay();
      if (!ready || !window.Razorpay) {
        setToast({ message: "Could not load the payment gateway. Please retry.", tone: "error" });
        log.warn("Razorpay checkout unavailable", { action: "razorpay_pay", entity: invoice.id });
        return;
      }

      const order = await razorpay.createOrder(invoice.id);
      log.info("Razorpay order created", {
        action: "razorpay_order",
        entity: invoice.id,
        method: order.order_id,
      });

      const rzp = new window.Razorpay({
        key: order.key_id,
        order_id: order.order_id,
        amount: order.amount,
        currency: order.currency,
        name: "YukiCares",
        description: invoice.invoice_number,
        theme: { color: "#2563EB" },
        handler: (resp) => {
          void (async () => {
            try {
              const result = await razorpay.verify({
                invoice: invoice.id,
                razorpay_order_id: resp.razorpay_order_id,
                razorpay_payment_id: resp.razorpay_payment_id,
                razorpay_signature: resp.razorpay_signature,
              });
              log.info("Razorpay payment verified", {
                action: "razorpay_verify",
                entity: invoice.id,
                method: String(result.payment_id),
              });
              await queryClient.invalidateQueries({ queryKey: ["invoice", id] });
              await queryClient.invalidateQueries({ queryKey: ["invoice-payments", id] });
              setToast({ message: "Payment received. Receipt updated.", tone: "success" });
            } catch (err) {
              const detail = err instanceof ApiError ? err.detail : "Verification failed.";
              log.error("Razorpay verification failed", {
                action: "razorpay_verify",
                entity: invoice.id,
              });
              setToast({ message: detail, tone: "error" });
            }
          })();
        },
      });

      rzp.on("payment.failed", (resp) => {
        log.warn("Razorpay payment failed", {
          action: "razorpay_pay",
          entity: invoice.id,
          method: resp.error.code,
        });
        setToast({ message: `Payment failed: ${resp.error.description}`, tone: "error" });
      });

      rzp.open();
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        log.warn("Razorpay not configured", { action: "razorpay_pay", entity: invoice.id });
        setToast({ message: "Online payments are not configured for this school.", tone: "error" });
      } else {
        const detail = err instanceof ApiError ? err.detail : "Could not start the payment.";
        log.error("Razorpay checkout error", { action: "razorpay_pay", entity: invoice.id });
        setToast({ message: detail, tone: "error" });
      }
    } finally {
      setPaying(false);
    }
  }

  const studentQ = useQuery({
    queryKey: ["invoice-student", inv?.student],
    queryFn: () => students.get(inv!.student),
    enabled: !!inv?.student,
  });
  const settingsQ = useQuery({ queryKey: ["settings"], queryFn: () => settings.get() });
  const paymentsQ = useQuery({
    queryKey: ["invoice-payments", id],
    queryFn: () => payments.list(Number(id)),
    enabled: !!inv,
  });

  if (invoiceQ.isLoading || !inv) return <p className="text-slate-500">Loading invoice…</p>;

  const student = studentQ.data;
  const school = settingsQ.data?.results[0];
  const payment = paymentsQ.data?.results[0];
  const cur = inv.currency;
  const discountPct =
    Number(inv.subtotal) > 0 ? Math.round((Number(inv.discount_amount) / Number(inv.subtotal)) * 100) : 0;
  const isPaid = inv.status === "paid";
  const canPayOnline = Boolean(razorpayConfigQ.data?.enabled) && Number(inv.balance) > 0;

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      {/* Action bar (hidden on print) */}
      <div className="flex items-center justify-between print:hidden">
        <h1 className="text-xl font-bold text-brand">{school?.name ?? "YukiCares"}</h1>
        <div className="flex gap-2">
          {canPayOnline && (
            <button
              onClick={() => void payOnline(inv)}
              disabled={paying}
              className="rounded-xl bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {paying ? "Opening…" : "💳 Pay Online"}
            </button>
          )}
          <button onClick={() => window.print()} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark">
            🖨 Print Receipt
          </button>
          <button onClick={() => window.print()} className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            ⬇ Download PDF
          </button>
        </div>
      </div>

      {toast && (
        <div className="print:hidden">
          <Toast message={toast.message} tone={toast.tone} />
        </div>
      )}

      {/* Receipt */}
      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {/* Gradient header */}
        <div className="bg-brand-gradient p-8 text-white">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                {school?.logo ? (
                  <img src={school.logo} alt="School logo" className="h-11 w-11 rounded-xl bg-white/90 object-contain p-1" />
                ) : (
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/20 text-lg">🏫</span>
                )}
                <span className="text-2xl font-bold">{school?.name ?? "YukiCares"}</span>
              </div>
              <p className="mt-3 text-sm font-medium text-white/90">
                {[school?.street_address, school?.city, school?.state_province].filter(Boolean).join(", ") || "School Fee Management System"}
              </p>
              <p className="text-sm text-white/70">
                {[school?.primary_phone, school?.official_email].filter(Boolean).join(" · ") || "—"}
              </p>
            </div>
            <div className="text-right">
              <span className="inline-flex items-center gap-1 rounded-lg bg-white/20 px-3 py-1.5 text-sm font-semibold">
                🧾 INVOICE #{inv.invoice_number}
              </span>
              <p className="mt-3 text-sm text-white/80">📅 Issue Date: <span className="font-semibold text-white">{formatDate(inv.issue_date)}</span></p>
              <p className="text-sm text-white/80">⏰ Due Date: <span className="font-semibold text-white">{formatDate(inv.due_date)}</span></p>
              <span className={`mt-2 inline-flex rounded-full px-3 py-0.5 text-xs font-semibold uppercase ${isPaid ? "bg-emerald-400 text-emerald-900" : "bg-amber-300 text-amber-900"}`}>
                {isPaid ? "✓ Paid" : inv.status}
              </span>
            </div>
          </div>
        </div>

        {/* Student + School details */}
        <div className="grid grid-cols-1 gap-5 p-6 md:grid-cols-2">
          <div className="rounded-xl border border-slate-100 p-5">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand">👤 Student Details</p>
            <div className="mb-4 flex items-center gap-3">
              <div className="h-11 w-11 overflow-hidden rounded-full bg-slate-100">
                {student?.photo && <img src={student.photo} alt="" className="h-full w-full object-cover" />}
              </div>
              <div>
                <p className="font-bold text-slate-900">{inv.student_name}</p>
                <p className="text-xs text-slate-500">Student ID: {student?.student_id ?? "—"}</p>
              </div>
            </div>
            <Row label="Class" value={`${student?.grade || "—"}${student?.section ? ` — ${student.section}` : ""}`} />
            <Row label="Academic Year" value={inv.academic_year_label || "—"} />
            <Row label="Section" value={student?.section || "—"} />
            <Row label="Status" value={<span className="capitalize">{student?.status || "—"}</span>} />
          </div>

          <div className="rounded-xl border border-slate-100 p-5">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand">🏫 School Details</p>
            <p className="font-bold text-slate-900">{school?.name ?? "—"}</p>
            <p className="mb-4 text-xs text-slate-500">
              {school?.affiliation_board ? `Affiliated with ${school.affiliation_board}` : "—"}
              {school?.established_year ? ` · Est. ${school.established_year}` : ""}
            </p>
            <Row label="Reg. No." value={school?.registration_number || "—"} />
            <Row label="Parent / Guardian" value={student?.guardian_name || "—"} />
            <Row label="Contact" value={school?.primary_phone || "—"} />
          </div>
        </div>

        {/* Fee breakdown */}
        <div className="px-6 pb-2">
          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">Fee Breakdown</p>
          <div className="overflow-hidden rounded-xl">
            <table className="w-full text-sm">
              <thead className="bg-slate-800 text-left text-xs uppercase tracking-wide text-white">
                <tr>
                  <th className="px-4 py-3 font-semibold">#</th>
                  <th className="px-4 py-3 font-semibold">Description</th>
                  <th className="px-4 py-3 font-semibold">Category</th>
                  <th className="px-4 py-3 text-center font-semibold">Qty</th>
                  <th className="px-4 py-3 text-right font-semibold">Unit Price</th>
                  <th className="px-4 py-3 text-right font-semibold">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {inv.lines.map((l, i) => (
                  <tr key={l.id}>
                    <td className="px-4 py-3 text-slate-400">{String(i + 1).padStart(2, "0")}</td>
                    <td className="px-4 py-3 font-semibold text-slate-800">{l.description || l.fee_type_name}</td>
                    <td className="px-4 py-3">
                      {l.fee_type_category && (
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${catColor(l.fee_type_category)}`}>{l.fee_type_category}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">{l.quantity}</td>
                    <td className="px-4 py-3 text-right">{formatMoney(l.unit_price, cur)}</td>
                    <td className="px-4 py-3 text-right font-bold text-slate-900">{formatMoney(l.amount, cur)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Totals */}
        <div className="flex justify-end px-6 py-4">
          <div className="w-full max-w-sm space-y-2">
            <div className="flex justify-between text-sm"><span className="text-slate-500">Subtotal</span><span className="font-semibold">{formatMoney(inv.subtotal, cur)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-slate-500">Discount{discountPct ? ` (${discountPct}%)` : ""}</span><span className="font-semibold text-emerald-600">− {formatMoney(inv.discount_amount, cur)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-slate-500">Late Fee</span><span className="font-semibold">{formatMoney(inv.late_fee_amount, cur)}</span></div>
            <div className="mt-2 flex items-center justify-between rounded-xl bg-brand px-5 py-3 text-white">
              <span className="font-semibold">{isPaid ? "Total Amount Paid" : "Total Due"}</span>
              <span className="text-xl font-bold">{formatMoney(inv.total, cur)}</span>
            </div>
          </div>
        </div>

        {/* Payment info + signature */}
        <div className="grid grid-cols-1 gap-5 bg-slate-50 p-6 md:grid-cols-2">
          <div className="rounded-xl border border-slate-100 bg-white p-5">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand">💳 Payment Information</p>
            <Row label="Payment Method" value={payment ? METHOD_LABELS[payment.method] ?? payment.method : "—"} />
            <Row label="Transaction ID" value={payment?.reference || "—"} />
            <Row label="Payment Date" value={payment ? formatDate(payment.paid_at) : "—"} />
            <Row label="Status" value={<span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${isPaid ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{isPaid ? "✓ Confirmed" : inv.status}</span>} />
          </div>
          <div className="rounded-xl border border-slate-100 bg-white p-5">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand">✍ Authorized Signature</p>
            <p className="text-sm italic text-slate-400">This is a computer-generated receipt and does not require a physical signature unless stamped.</p>
            <div className="mt-6 border-t border-dashed border-slate-200 pt-2 text-sm">
              <p className="font-bold text-slate-800">{school?.name ?? "—"}</p>
              <p className="text-xs text-slate-500">Accounts Office</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-800 px-6 py-4 text-center text-xs text-slate-300">
          <p>Generated by <span className="font-semibold text-white">YukiCares</span> — Smart School Fee Management</p>
          <p className="mt-1 text-slate-400">This receipt is valid only with the official seal of {school?.name ?? "the school"}.</p>
        </div>
      </div>
    </div>
  );
}
