import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { collections, payments } from "@/api/resources";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const methodBadge: Record<string, string> = {
  cash: "bg-emerald-50 text-emerald-700",
  bank_transfer: "bg-brand-light text-brand-dark",
  upi: "bg-indigo-50 text-indigo-700",
  cheque: "bg-amber-50 text-amber-700",
  card: "bg-slate-100 text-slate-600",
};

export function FeeCollectionDashboard() {
  const navigate = useNavigate();
  const stats = useQuery({ queryKey: ["collection-stats"], queryFn: () => collections.stats() });

  const [term, setTerm] = useState("");
  const list = useQuery({
    queryKey: ["fee-collections", term],
    queryFn: () => payments.search(term),
  });

  const st = stats.data;
  const rows = list.data?.results ?? [];
  const listedTotal = rows.reduce((s, p) => s + Number(p.amount), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Fee Collection</h1>
          <p className="text-sm text-slate-500">Collect and review student fee payments</p>
        </div>
        <Link to="/fee-collection/new" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
          + New Collection
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Total Collected" value={formatMoney(st?.total_collected ?? "0")} hint="fees received" tone="brand" />
        <Kpi label="Pending Dues" value={formatMoney(st?.pending_dues ?? "0")} hint="outstanding" tone="rose" />
        <Kpi label="Paid Students" value={`${st?.paid_students ?? 0}`} hint={`of ${st?.total_students ?? 0} total`} tone="emerald" />
        <Kpi label="Today's Collection" value={formatMoney(st?.todays_collection ?? "0")} hint={`${st?.todays_receipts ?? 0} receipts`} tone="brand" />
      </div>

      {/* Accountant breakouts */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Kpi label="Cash in Hand" value={formatMoney(st?.cash_in_hand ?? "0")} hint="net cash collected" tone="emerald" />
        <Kpi label="Bank Deposits" value={formatMoney(st?.bank_deposits ?? "0")} hint="UPI / bank / cheque / card" tone="brand" />
        <Kpi label="Yesterday's Collection" value={formatMoney(st?.yesterday_collection ?? "0")} hint="previous day" tone="brand" />
      </div>

      {/* Collected fees list */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-slate-900">Fees Collected</h2>
        <span className="text-sm text-slate-500">
          {rows.length} payments · <span className="font-semibold text-emerald-600">{formatMoney(listedTotal.toFixed(2))}</span> shown
        </span>
      </div>
      <input
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder="Search by student name, ID, receipt or reference…"
        className="w-full max-w-md rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
      />

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[860px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Date</th>
              <th className="px-6 py-3 font-semibold">Receipt No</th>
              <th className="px-6 py-3 font-semibold">Student</th>
              <th className="px-6 py-3 font-semibold">Class</th>
              <th className="px-6 py-3 font-semibold">Fee Type</th>
              <th className="px-6 py-3 font-semibold">Method</th>
              <th className="px-6 py-3 text-right font-semibold">Amount</th>
              <th className="px-6 py-3 text-right font-semibold">Status</th>
              <th className="px-6 py-3 font-semibold">Links</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {rows.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50">
                <td className="px-6 py-3 whitespace-nowrap text-slate-500">{formatDate(p.paid_at)}</td>
                <td className="px-6 py-3 font-mono text-xs text-slate-600">{p.receipt_number || "—"}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{p.student_name}</td>
                <td className="px-6 py-3 text-slate-600">{p.student_grade || "—"}</td>
                <td className="px-6 py-3 text-slate-600">{p.fee_type || "—"}</td>
                <td className="px-6 py-3">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${methodBadge[p.method] ?? "bg-slate-100 text-slate-600"}`}>
                    {(p.method || "—").replace("_", " ")}
                  </span>
                </td>
                <td className="px-6 py-3 text-right font-semibold text-emerald-600">{formatMoney(p.amount, p.currency)}</td>
                <td className="px-6 py-3 text-right"><StatusBadge status={p.invoice_status} /></td>
                <td className="px-6 py-3 whitespace-nowrap">
                  <button onClick={() => navigate(`/invoices/${p.invoice}`)} className="text-xs font-semibold text-brand hover:underline">Invoice</button>
                  <Link to={`/receipts/${p.id}`} className="ml-3 text-xs font-semibold text-brand hover:underline">Receipt</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {!list.isLoading && rows.length === 0 && <p className="px-6 py-4 text-slate-400">No payments found.</p>}
      </Card>
    </div>
  );
}

function Kpi({ label, value, hint, tone }: { label: string; value: string; hint: string; tone: "brand" | "rose" | "emerald" }) {
  const color = tone === "rose" ? "text-rose-500" : tone === "emerald" ? "text-emerald-600" : "text-brand";
  return (
    <Card>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      <p className={`mt-1 text-xs ${color}`}>{hint}</p>
    </Card>
  );
}
