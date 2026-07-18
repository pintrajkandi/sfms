import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { invoices } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader, StatusBadge } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const FILTERS = ["", "pending", "partial", "paid", "overdue"];

export function InvoicesListPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["invoices", status],
    queryFn: () => invoices.list(status ? `?status=${status}` : ""),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Invoices" subtitle="Student fee invoices and receipts" />

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f || "all"}
            onClick={() => setStatus(f)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium capitalize ${
              status === f ? "bg-brand text-white" : "border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {f || "All"}
          </button>
        ))}
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="border-b border-slate-100 text-left text-slate-500">
            <tr>
              <th className="px-6 py-3 font-medium">Invoice #</th>
              <th className="px-6 py-3 font-medium">Student</th>
              <th className="px-6 py-3 font-medium">Total</th>
              <th className="px-6 py-3 font-medium">Balance</th>
              <th className="px-6 py-3 font-medium">Due</th>
              <th className="px-6 py-3 text-right font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((inv) => (
              <tr key={inv.id} onClick={() => navigate(`/invoices/${inv.id}`)} className="cursor-pointer hover:bg-slate-50">
                <td className="px-6 py-3 font-mono text-xs text-brand">{inv.invoice_number}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{inv.student_name}</td>
                <td className="px-6 py-3">{formatMoney(inv.total, inv.currency)}</td>
                <td className="px-6 py-3">{formatMoney(inv.balance, inv.currency)}</td>
                <td className="px-6 py-3 text-slate-500">{formatDate(inv.due_date)}</td>
                <td className="px-6 py-3 text-right"><StatusBadge status={inv.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No invoices yet.</p>}
      </Card>
    </div>
  );
}
