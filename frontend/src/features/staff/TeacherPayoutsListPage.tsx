import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { payouts } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/form";
import { formatMoney } from "@/lib/money";

const STATUS_BADGE: Record<string, string> = {
  submitted: "bg-amber-50 text-amber-700",
  hod_approved: "bg-amber-50 text-amber-700",
  finance_approved: "bg-amber-50 text-amber-700",
  processed: "bg-emerald-50 text-emerald-700",
  rejected: "bg-rose-50 text-rose-600",
};
const STATUS_LABEL: Record<string, string> = {
  submitted: "Pending",
  hod_approved: "Pending",
  finance_approved: "Pending",
  processed: "Paid",
  rejected: "Rejected",
};

export function TeacherPayoutsListPage() {
  const navigate = useNavigate();
  const [term, setTerm] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["payouts"], queryFn: () => payouts.list() });

  const rows = useMemo(() => {
    const all = data?.results ?? [];
    const q = term.trim().toLowerCase();
    if (!q) return all;
    return all.filter(
      (p) =>
        p.teacher_name.toLowerCase().includes(q) ||
        p.pay_period.toLowerCase().includes(q) ||
        p.pay_type.toLowerCase().includes(q),
    );
  }, [data, term]);

  const total = rows.reduce((s, p) => s + Number(p.net_amount), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teacher Payouts"
        subtitle="Complete history of salary & incentive payouts"
        actions={
          <Link to="/payouts" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
            + New Payout
          </Link>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search by teacher, pay period or type…"
          className="w-full max-w-md rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
        />
        <span className="text-sm text-slate-500">
          {rows.length} payouts · <span className="font-semibold text-emerald-600">{formatMoney(total.toFixed(2))}</span> net
        </span>
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[880px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Teacher</th>
              <th className="px-6 py-3 font-semibold">Pay Period</th>
              <th className="px-6 py-3 font-semibold">Type</th>
              <th className="px-6 py-3 text-right font-semibold">Base</th>
              <th className="px-6 py-3 text-right font-semibold">Bonus</th>
              <th className="px-6 py-3 text-right font-semibold">Deductions</th>
              <th className="px-6 py-3 text-right font-semibold">Net</th>
              <th className="px-6 py-3 text-right font-semibold">Status</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {rows.map((p) => (
              <tr key={p.id} className="cursor-pointer hover:bg-slate-50" onClick={() => navigate(`/payslips/${p.id}`)}>
                <td className="px-6 py-3 font-medium text-slate-800">{p.teacher_name}</td>
                <td className="px-6 py-3 text-slate-600">{p.pay_period}</td>
                <td className="px-6 py-3 capitalize text-slate-600">{p.pay_type}</td>
                <td className="px-6 py-3 text-right text-slate-600">{formatMoney(p.base_amount, p.currency)}</td>
                <td className="px-6 py-3 text-right text-slate-600">{formatMoney(p.bonus_amount, p.currency)}</td>
                <td className="px-6 py-3 text-right text-rose-500">{formatMoney(p.deductions, p.currency)}</td>
                <td className="px-6 py-3 text-right font-semibold text-emerald-600">{formatMoney(p.net_amount, p.currency)}</td>
                <td className="px-6 py-3 text-right">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_BADGE[p.status] ?? "bg-slate-100 text-slate-600"}`}>
                    {STATUS_LABEL[p.status] ?? p.status}
                  </span>
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-right">
                  <Link to={`/payslips/${p.id}`} onClick={(e) => e.stopPropagation()} className="text-xs font-semibold text-brand hover:underline">View payslip →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {!isLoading && rows.length === 0 && <p className="px-6 py-4 text-slate-400">No payouts found.</p>}
      </Card>
    </div>
  );
}
