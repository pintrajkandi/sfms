import { useQuery } from "@tanstack/react-query";
import { subscription } from "@/api/resources";
import { formatMoney } from "@/lib/money";

const INCLUDED = [
  "Students, classes & sections",
  "Fee collection, invoices & receipts",
  "Payments, refunds & payment plans",
  "Double-entry accounting & statements",
  "Payroll, expenses & inventory",
  "Transport, reports & audit log",
];

export function SubscriptionTab() {
  const { data, isLoading } = useQuery({ queryKey: ["subscription"], queryFn: () => subscription.get() });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-900">Subscription</h2>
        <p className="text-sm text-slate-500">Your current plan and usage.</p>
      </div>

      {isLoading && <p className="text-slate-500">Loading…</p>}

      {data && (
        <>
          <div className="rounded-2xl border border-slate-100 bg-brand-gradient px-6 py-6 text-white">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-white/70">Current plan</p>
                <p className="mt-1 text-3xl font-bold">{data.plan.name}</p>
                <p className="text-sm text-white/80">{data.plan.description}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">
                  {data.is_free ? "Free" : `${formatMoney(data.plan.price_monthly, data.plan.currency)}`}
                </p>
                {!data.is_free && <p className="text-sm text-white/70">/ {data.plan.interval}</p>}
                <span className="mt-2 inline-block rounded-full bg-white/15 px-3 py-1 text-xs font-medium capitalize">{data.status}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-100 px-5 py-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Students</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {data.student_count}
                <span className="text-base font-medium text-slate-400"> / {data.max_students === 0 ? "∞" : data.max_students}</span>
              </p>
            </div>
            <div className="rounded-xl border border-slate-100 px-5 py-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Renews</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{data.renews_at ?? "—"}</p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-100 p-5">
            <h3 className="text-sm font-semibold text-slate-800">Included</h3>
            <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {INCLUDED.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                  <span className="text-emerald-500">✓</span> {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-5 py-4 text-sm text-slate-500">
            You're on the <span className="font-semibold text-slate-700">Free</span> plan — every feature is included at no cost. Paid plans with higher limits and priority support are coming soon.
          </div>
        </>
      )}
    </div>
  );
}
