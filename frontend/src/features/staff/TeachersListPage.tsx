import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { teachers } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/form";
import { formatMoney } from "@/lib/money";

const statusBadge: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700",
  on_leave: "bg-amber-50 text-amber-700",
  inactive: "bg-slate-100 text-slate-600",
  resigned: "bg-rose-50 text-rose-600",
};

export function TeachersListPage() {
  const navigate = useNavigate();
  const [term, setTerm] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["teachers"], queryFn: () => teachers.list() });

  const rows = useMemo(() => {
    const all = data?.results ?? [];
    const q = term.trim().toLowerCase();
    if (!q) return all;
    return all.filter(
      (t) =>
        t.full_name.toLowerCase().includes(q) ||
        t.employee_id.toLowerCase().includes(q) ||
        (t.email || "").toLowerCase().includes(q) ||
        (t.phone || "").toLowerCase().includes(q) ||
        (t.department || "").toLowerCase().includes(q),
    );
  }, [data, term]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teachers"
        subtitle="All teaching staff"
        actions={
          <Link to="/teachers/new" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
            + Add Teacher
          </Link>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search by name, employee ID, email, phone…"
          className="w-full max-w-md rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
        />
        <span className="text-sm text-slate-500">{rows.length} teachers</span>
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[820px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Employee ID</th>
              <th className="px-6 py-3 font-semibold">Name</th>
              <th className="px-6 py-3 font-semibold">Department</th>
              <th className="px-6 py-3 font-semibold">Email</th>
              <th className="px-6 py-3 font-semibold">Phone</th>
              <th className="px-6 py-3 text-right font-semibold">Base Salary</th>
              <th className="px-6 py-3 text-right font-semibold">Status</th>
              <th className="px-6 py-3 font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {rows.map((t) => (
              <tr key={t.id} className="cursor-pointer hover:bg-slate-50" onClick={() => navigate(`/teachers/${t.id}/edit`)}>
                <td className="px-6 py-3 font-mono text-xs text-slate-600">{t.employee_id}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{t.full_name}</td>
                <td className="px-6 py-3 text-slate-600">{t.department || "—"}</td>
                <td className="px-6 py-3 text-slate-600">{t.email || "—"}</td>
                <td className="px-6 py-3 text-slate-600">{t.phone || "—"}</td>
                <td className="px-6 py-3 text-right font-semibold text-slate-700">{formatMoney(t.base_salary, t.currency)}</td>
                <td className="px-6 py-3 text-right">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusBadge[t.status] ?? "bg-slate-100 text-slate-600"}`}>
                    {(t.status || "—").replace("_", " ")}
                  </span>
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-right">
                  <Link to={`/teachers/${t.id}/edit`} onClick={(e) => e.stopPropagation()} className="text-xs font-semibold text-brand hover:underline">Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {!isLoading && rows.length === 0 && <p className="px-6 py-4 text-slate-400">No teachers found.</p>}
      </Card>
    </div>
  );
}
