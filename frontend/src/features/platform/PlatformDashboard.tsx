import { useQuery } from "@tanstack/react-query";
import { platform } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/form";
import { formatMoney } from "@/lib/money";

function Kpi({ label, value, hint, tone = "brand" }: { label: string; value: string; hint?: string; tone?: string }) {
  const tones: Record<string, string> = { brand: "text-brand", emerald: "text-emerald-600", amber: "text-amber-600", rose: "text-rose-600", slate: "text-slate-900" };
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tones[tone]}`}>{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-400">{hint}</p>}
    </Card>
  );
}

export function PlatformDashboard() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["platform-metrics"], queryFn: () => platform.metrics(), retry: false });

  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Platform" subtitle="Cross-school operator metrics" />
        <Card><p className="text-slate-500">Platform metrics are restricted to platform administrators.</p></Card>
      </div>
    );
  }

  const maxGrowth = Math.max(1, ...(data?.growth ?? []).map((g) => g.new_schools));

  return (
    <div className="space-y-6">
      <PageHeader title="Platform" subtitle="Cross-school operator metrics (all schools)" />
      {isLoading && <p className="text-slate-500">Loading…</p>}
      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Kpi label="Total Schools" value={String(data.total_schools)} hint={`${data.archived_schools} archived`} tone="brand" />
            <Kpi label="Active Schools" value={String(data.active_schools)} hint={`${data.trial_schools} on trial`} tone="emerald" />
            <Kpi label="Paid Schools" value={String(data.paid_schools)} hint={`${data.trial_schools} on trial`} tone="slate" />
            <Kpi label="Renewals due (30d)" value={String(data.renewals_due_30d)} tone="amber" />
            <Kpi label="MRR (subscriptions)" value={formatMoney(data.mrr)} hint={`ARR ${formatMoney(data.arr)}`} tone="emerald" />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 text-base font-semibold text-slate-800">New schools / month</h2>
              <div className="space-y-2">
                {data.growth.map((g) => (
                  <div key={g.month} className="flex items-center gap-3">
                    <span className="w-16 text-xs text-slate-500">{g.month}</span>
                    <div className="h-3 flex-1 rounded-full bg-slate-100">
                      <div className="h-3 rounded-full bg-brand-gradient" style={{ width: `${(g.new_schools / maxGrowth) * 100}%` }} />
                    </div>
                    <span className="w-8 text-right text-sm font-semibold text-slate-700">{g.new_schools}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="mb-4 text-base font-semibold text-slate-800">Plan distribution</h2>
              <table className="w-full text-sm">
                <tbody className="divide-y divide-slate-50">
                  {data.plan_mix.map((p) => (
                    <tr key={p.plan}>
                      <td className="py-2 font-medium text-slate-800">{p.plan}</td>
                      <td className="py-2 text-right text-slate-600">{p.count} school{p.count === 1 ? "" : "s"}</td>
                    </tr>
                  ))}
                  {data.plan_mix.length === 0 && <tr><td className="py-2 text-slate-400">No schools yet.</td></tr>}
                </tbody>
              </table>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
