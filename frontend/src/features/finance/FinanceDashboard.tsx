import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { finance } from "@/api/resources";
import { Card } from "@/components/Card";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const DONUT = ["#818CF8", "#34D399", "#FBBF24", "#F87171", "#60A5FA", "#A78BFA"];
const monthShort = (k: string) =>
  new Date(`${k}-01T00:00:00`).toLocaleDateString("en-US", { month: "short" });

export function FinanceDashboard() {
  const q = useQuery({ queryKey: ["finance-dashboard"], queryFn: () => finance.dashboard() });
  const d = q.data;

  const bars = (d?.monthly ?? []).map((m) => ({ name: monthShort(m.month), Income: Number(m.income), Expenses: Number(m.expense) }));
  const trend = (d?.net_savings_trend ?? []).map((t) => ({ name: monthShort(t.month), balance: Number(t.balance) }));
  const totalExp = Number(d?.total_expense ?? 0);
  const pie = (d?.expense_breakdown ?? []).map((e) => ({
    name: e.category, value: Number(e.total),
    percent: totalExp > 0 ? Math.round((Number(e.total) / totalExp) * 100) : 0,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Financial Overview</h1>
        <p className="text-sm text-slate-500">Income, expenses and savings across recent months</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl bg-brand-gradient p-5 text-white">
          <p className="text-sm text-white/80">Total Balance</p>
          <p className="mt-1 text-2xl font-bold">{formatMoney(d?.total_balance ?? "0")}</p>
          <p className="mt-1 text-xs text-white/70">net savings</p>
        </div>
        <Kpi label="Total Income" value={formatMoney(d?.total_income ?? "0")} tone="emerald" />
        <Kpi label="Total Expenses" value={formatMoney(d?.total_expense ?? "0")} tone="rose" />
        <Kpi label="Savings Rate" value={`${d?.savings_rate_percent ?? 0}%`} tone="brand" />
      </div>

      {/* Income vs Expenses + Expense Breakdown */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="text-base font-semibold text-slate-900">Income vs Expenses</h2>
          <p className="mb-4 text-sm text-slate-500">Monthly comparison</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={bars}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
              <Tooltip formatter={(v: number) => formatMoney(v.toFixed(2))} />
              <Legend />
              <Bar dataKey="Income" fill="#34D399" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Expenses" fill="#F87171" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-slate-900">Expense Breakdown</h2>
          <p className="mb-2 text-sm text-slate-500">By category</p>
          <ResponsiveContainer width="100%" height={190}>
            <PieChart>
              <Pie data={pie.length ? pie : [{ name: "None", value: 1, percent: 0 }]} dataKey="value" innerRadius={48} outerRadius={78} paddingAngle={2}>
                {pie.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => formatMoney(v.toFixed(2))} />
            </PieChart>
          </ResponsiveContainer>
          <ul className="mt-2 space-y-1 text-sm">
            {pie.slice(0, 6).map((c, i) => (
              <li key={c.name} className="flex items-center justify-between">
                <span className="flex items-center gap-2 capitalize text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: DONUT[i % DONUT.length] }} />
                  {c.name}
                </span>
                <span className="font-medium text-slate-700">{formatMoney(c.value.toFixed(2))} · {c.percent}%</span>
              </li>
            ))}
            {pie.length === 0 && <li className="text-slate-400">No expenses recorded.</li>}
          </ul>
        </Card>
      </div>

      {/* Net Savings Trend + Recent Transactions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Net Savings Trend</h2>
              <p className="text-sm text-slate-500">Running balance</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-600">{formatMoney(d?.net_savings ?? "0")}</span>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={trend}>
              <defs>
                <linearGradient id="sav" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4F46E5" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#4F46E5" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
              <Tooltip formatter={(v: number) => formatMoney(v.toFixed(2))} />
              <Area type="monotone" dataKey="balance" stroke="#4F46E5" strokeWidth={2} fill="url(#sav)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-4 text-base font-semibold text-slate-900">Recent Transactions</h2>
          <div className="space-y-3">
            {d?.recent_transactions.map((t, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${t.direction === "in" ? "bg-emerald-50" : "bg-rose-50"}`}>
                    {t.direction === "in" ? "↓" : "↑"}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{t.title}</p>
                    <p className="text-xs text-slate-400">{formatDate(t.date)} · {t.category}</p>
                  </div>
                </div>
                <span className={`text-sm font-semibold ${t.direction === "in" ? "text-emerald-600" : "text-rose-500"}`}>
                  {t.direction === "in" ? "+" : "−"}{formatMoney(t.amount)}
                </span>
              </div>
            ))}
            {d && d.recent_transactions.length === 0 && <p className="text-sm text-slate-400">No transactions yet.</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Kpi({ label, value, tone }: { label: string; value: string; tone: "emerald" | "rose" | "brand" }) {
  const color = tone === "rose" ? "text-rose-500" : tone === "emerald" ? "text-emerald-600" : "text-brand";
  return (
    <Card>
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
    </Card>
  );
}
