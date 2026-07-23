import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { payments } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const methodBadge: Record<string, string> = {
  cash: "bg-emerald-50 text-emerald-700",
  bank_transfer: "bg-brand-light text-brand-dark",
  upi: "bg-indigo-50 text-indigo-700",
  cheque: "bg-amber-50 text-amber-700",
  card: "bg-slate-100 text-slate-600",
};

export function FeeCollectionsListPage() {
  const [term, setTerm] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["fee-collections", term],
    queryFn: () => payments.search(term),
  });

  const rows = data?.results ?? [];
  const total = rows.reduce((s, p) => s + Number(p.amount), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fee Collections"
        subtitle="Search and review students who have paid their fees"
        actions={
          <Link to="/fee-collection/new" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
            + Collect Fee
          </Link>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search by student name, ID or reference…"
          className="w-full max-w-md rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
        />
        <span className="text-sm text-slate-500">{rows.length} payments · <span className="font-semibold text-emerald-600">{formatMoney(total.toFixed(2))}</span> collected</span>
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[820px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Date</th>
              <th className="px-6 py-3 font-semibold">Student</th>
              <th className="px-6 py-3 font-semibold">Class</th>
              <th className="px-6 py-3 font-semibold">Fee Type</th>
              <th className="px-6 py-3 font-semibold">Method</th>
              <th className="px-6 py-3 font-semibold">Reference</th>
              <th className="px-6 py-3 text-right font-semibold">Amount</th>
              <th className="px-6 py-3 font-semibold">Invoice</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {rows.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50">
                <td className="px-6 py-3 whitespace-nowrap text-slate-500">{formatDate(p.paid_at)}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{p.student_name}</td>
                <td className="px-6 py-3 text-slate-600">{p.student_grade || "—"}</td>
                <td className="px-6 py-3 text-slate-600">{p.fee_type || "—"}</td>
                <td className="px-6 py-3">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${methodBadge[p.method] ?? "bg-slate-100 text-slate-600"}`}>
                    {(p.method || "—").replace("_", " ")}
                  </span>
                </td>
                <td className="px-6 py-3 text-slate-500">{p.reference || "—"}</td>
                <td className="px-6 py-3 text-right font-semibold text-emerald-600">{formatMoney(p.amount, p.currency)}</td>
                <td className="px-6 py-3 whitespace-nowrap">
                  <Link to={`/invoices/${p.invoice}`} className="text-xs font-semibold text-brand hover:underline">Invoice</Link>
                  <Link to={`/receipts/${p.id}`} className="ml-3 text-xs font-semibold text-brand hover:underline">Receipt</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {!isLoading && rows.length === 0 && <p className="px-6 py-4 text-slate-400">No payments found.</p>}
      </Card>
    </div>
  );
}
