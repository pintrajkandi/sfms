import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { collections, payments } from "@/api/resources";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/form";
import { formatMoney } from "@/lib/money";

const DONUT = ["#2563EB", "#818CF8", "#34D399", "#60A5FA", "#FBBF24", "#F87171"];
const monthShort = (k: string) =>
  new Date(`${k}-01T00:00:00`).toLocaleDateString("en-US", { month: "short" });

export function DashboardPage() {
  const dash = useQuery({ queryKey: ["collection-dashboard"], queryFn: () => collections.dashboard() });
  const recent = useQuery({ queryKey: ["recent-payments"], queryFn: () => payments.recent() });
  const d = dash.data;

  const barData = (d?.monthly ?? []).map((m) => ({
    name: monthShort(m.month),
    Collected: Number(m.collected),
    Pending: Number(m.pending),
  }));
  const pieData = (d?.category_breakdown ?? []).map((c) => ({ name: c.fee_type, value: Number(c.amount) }));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">Fee collection overview</p>
        </div>
        <Link to="/fee-collection" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
          + New Payment
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi icon="💰" label="Total Collected" value={formatMoney(d?.total_collected ?? "0")} hint="+12.4% vs last month" tone="emerald" />
        <Kpi icon="⏰" label="Pending Dues" value={formatMoney(d?.pending_dues ?? "0")} hint={`${d?.total_students ? d.total_students - (d.paid_students ?? 0) : 0} students overdue`} tone="rose" />
        <Kpi icon="🎓" label="Total Students" value={`${d?.total_students ?? 0}`} hint={`${d?.paid_students ?? 0} paid`} tone="emerald" />
        <Kpi icon="✓" label="Collection Rate" value={`${d?.collection_rate_percent ?? 0}%`} hint="Target: 90%" tone="brand" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="text-base font-semibold text-slate-900">Monthly Fee Collection</h2>
          <p className="mb-4 text-sm text-slate-500">Collected vs Pending</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
              <Tooltip formatter={(v: number) => formatMoney(v.toFixed(2))} />
              <Bar dataKey="Collected" stackId="a" fill="#2563EB" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Pending" stackId="a" fill="#C7D2FE" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-slate-900">Fee Category Breakdown</h2>
          <p className="mb-2 text-sm text-slate-500">By fee type</p>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData.length ? pieData : [{ name: "None", value: 1 }]} dataKey="value" innerRadius={50} outerRadius={80} paddingAngle={2}>
                {pieData.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => formatMoney(v.toFixed(2))} />
            </PieChart>
          </ResponsiveContainer>
          <ul className="mt-2 space-y-1 text-sm">
            {d?.category_breakdown.slice(0, 6).map((c, i) => (
              <li key={c.fee_type} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: DONUT[i % DONUT.length] }} />
                  {c.fee_type}
                </span>
                <span className="font-medium text-slate-700">{c.percent}%</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* Recent + Quick actions + Upcoming */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-0 lg:col-span-2">
          <div className="flex items-center justify-between px-6 py-4">
            <h2 className="text-base font-semibold">Recent Payments</h2>
            <Link to="/fee-collection" className="text-sm font-semibold text-brand hover:underline">View All</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-semibold">Student</th>
                  <th className="px-6 py-3 font-semibold">Class</th>
                  <th className="px-6 py-3 font-semibold">Fee Type</th>
                  <th className="px-6 py-3 font-semibold">Amount</th>
                  <th className="px-6 py-3 text-right font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {recent.data?.results.slice(0, 6).map((p) => (
                  <tr key={p.id}>
                    <td className="px-6 py-3 font-medium text-slate-800">{p.student_name}</td>
                    <td className="px-6 py-3 text-slate-500">{p.student_grade || "—"}</td>
                    <td className="px-6 py-3 text-slate-600">{p.fee_type || "—"}</td>
                    <td className="px-6 py-3 font-semibold">{formatMoney(p.amount, p.currency)}</td>
                    <td className="px-6 py-3 text-right"><StatusBadge status={p.invoice_status} /></td>
                  </tr>
                ))}
                {recent.data?.results.length === 0 && (
                  <tr><td colSpan={5} className="px-6 py-4 text-slate-400">No payments yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="space-y-6">
          <Card>
            <h2 className="mb-4 text-base font-semibold">Quick Actions</h2>
            <div className="space-y-2">
              <Link to="/fee-collection" className="flex items-center gap-3 rounded-lg bg-brand-light px-4 py-2.5 text-sm font-semibold text-brand-dark">⊕ Record New Payment</Link>
              <Link to="/students/new" className="flex items-center gap-3 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">👤 Add Student</Link>
              <Link to="/settings" className="flex items-center gap-3 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">✈ Send Fee Reminders</Link>
              <Link to="/finance" className="flex items-center gap-3 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">📄 Generate Report</Link>
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-base font-semibold">Upcoming Due Dates</h2>
            <div className="space-y-3">
              {d?.upcoming.map((u) => (
                <div key={u.invoice} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 flex-col items-center justify-center rounded-lg bg-slate-100 text-xs">
                      <span className="font-bold text-slate-700">{new Date(u.due_date).getDate()}</span>
                      <span className="text-[10px] text-slate-400">{new Date(u.due_date).toLocaleDateString("en", { month: "short" })}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{u.student}</p>
                      <p className="text-xs text-slate-400">{formatMoney(u.amount)} due</p>
                    </div>
                  </div>
                  <span className={`text-xs font-semibold ${u.days <= 7 ? "text-rose-500" : "text-amber-500"}`}>{u.days} days</span>
                </div>
              ))}
              {d && d.upcoming.length === 0 && <p className="text-sm text-slate-400">No upcoming dues.</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Kpi({ icon, label, value, hint, tone }: { icon: string; label: string; value: string; hint: string; tone: "brand" | "rose" | "emerald" }) {
  const color = tone === "rose" ? "text-rose-500" : tone === "emerald" ? "text-emerald-600" : "text-brand";
  return (
    <Card>
      <div className="flex items-start justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
        <span className="text-lg">{icon}</span>
      </div>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      <p className={`mt-1 text-xs ${color}`}>↗ {hint}</p>
    </Card>
  );
}
