import { useQuery } from "@tanstack/react-query";
import { collections } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const BUCKETS: { key: string; label: string; tone: string }[] = [
  { key: "current", label: "Current", tone: "text-slate-700" },
  { key: "1-30", label: "1–30 days", tone: "text-amber-600" },
  { key: "31-60", label: "31–60 days", tone: "text-orange-600" },
  { key: "61-90", label: "61–90 days", tone: "text-rose-500" },
  { key: "90+", label: "90+ days", tone: "text-rose-700" },
];

const bucketBadge: Record<string, string> = {
  current: "bg-slate-100 text-slate-600",
  "1-30": "bg-amber-50 text-amber-700",
  "31-60": "bg-orange-50 text-orange-700",
  "61-90": "bg-rose-50 text-rose-600",
  "90+": "bg-rose-100 text-rose-700",
};

export function DefaultersPage() {
  const { data, isLoading } = useQuery({ queryKey: ["defaulters"], queryFn: () => collections.defaulters() });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Defaulters & Aging"
        subtitle="Who owes what, by how overdue"
        actions={
          <div className="flex gap-2">
            <a href={collections.defaultersExportUrl("csv")} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">CSV</a>
            <a href={collections.defaultersExportUrl("xlsx")} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">Excel</a>
          </div>
        }
      />

      {/* Aging summary */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {BUCKETS.map((b) => (
          <Card key={b.key}>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{b.label}</p>
            <p className={`mt-1 text-lg font-bold ${b.tone}`}>{formatMoney(data?.aging[b.key] ?? "0")}</p>
          </Card>
        ))}
        <Card className="bg-brand-gradient text-white">
          <p className="text-xs font-medium uppercase tracking-wide text-white/70">Total Due</p>
          <p className="mt-1 text-lg font-bold">{formatMoney(data?.total_outstanding ?? "0")}</p>
        </Card>
      </div>

      <Card className="overflow-x-auto p-0">
        <div className="flex items-center justify-between px-6 py-4">
          <h2 className="text-base font-semibold">{data?.count ?? 0} defaulters</h2>
        </div>
        <table className="w-full min-w-[720px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Student</th>
              <th className="px-6 py-3 font-semibold">Grade</th>
              <th className="px-6 py-3 text-right font-semibold">Outstanding</th>
              <th className="px-6 py-3 text-right font-semibold">Days Overdue</th>
              <th className="px-6 py-3 font-semibold">Oldest Due</th>
              <th className="px-6 py-3 font-semibold">Invoices</th>
              <th className="px-6 py-3 text-right font-semibold">Aging</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.defaulters.map((d) => (
              <tr key={d.student_id} className="hover:bg-slate-50">
                <td className="px-6 py-3">
                  <p className="font-medium text-slate-800">{d.student}</p>
                  <p className="font-mono text-xs text-slate-400">{d.student_id}</p>
                </td>
                <td className="px-6 py-3">{d.grade || "—"}</td>
                <td className="px-6 py-3 text-right font-semibold text-rose-600">{formatMoney(d.outstanding)}</td>
                <td className="px-6 py-3 text-right">{d.days_overdue}</td>
                <td className="px-6 py-3 text-slate-500">{formatDate(d.oldest_due)}</td>
                <td className="px-6 py-3">{d.invoices}</td>
                <td className="px-6 py-3 text-right">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${bucketBadge[d.bucket] ?? "bg-slate-100"}`}>{d.bucket}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {data?.defaulters.length === 0 && <p className="px-6 py-4 text-emerald-600">🎉 No defaulters — everyone's paid up.</p>}
      </Card>
    </div>
  );
}
