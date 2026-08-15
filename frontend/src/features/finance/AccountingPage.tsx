import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { accounting, type Account } from "@/api/resources";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, Select, TextInput, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";

type Tab = "coa" | "trial" | "pnl" | "bs" | "ledger" | "daybook";
const TABS: { key: Tab; label: string }[] = [
  { key: "coa", label: "Chart of Accounts" },
  { key: "trial", label: "Trial Balance" },
  { key: "pnl", label: "Profit & Loss" },
  { key: "bs", label: "Balance Sheet" },
  { key: "ledger", label: "General Ledger" },
  { key: "daybook", label: "Day Book" },
];

const TYPE_BADGE: Record<string, string> = {
  asset: "bg-brand-light text-brand-dark",
  liability: "bg-amber-50 text-amber-700",
  equity: "bg-indigo-50 text-indigo-700",
  income: "bg-emerald-50 text-emerald-700",
  expense: "bg-rose-50 text-rose-600",
};

function ChartOfAccounts() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["accounts"], queryFn: () => accounting.accounts() });
  const [form, setForm] = useState({ code: "", name: "", type: "expense" });
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);
  const invalidate = () => qc.invalidateQueries({ queryKey: ["accounts"] });
  const fail = (e: unknown) => setToast({ msg: e instanceof ApiError ? e.detail : "Something went wrong.", tone: "error" });

  const add = useMutation({
    mutationFn: () => accounting.createAccount(form),
    onSuccess: () => { setForm({ code: "", name: "", type: "expense" }); invalidate(); },
    onError: fail,
  });
  const remove = useMutation({ mutationFn: (id: number) => accounting.removeAccount(id), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); if (form.code && form.name) add.mutate(); }}>
        <Labeled label="Code"><TextInput value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="e.g. 5300" /></Labeled>
        <Labeled label="Account name"><TextInput value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Utilities" /></Labeled>
        <Labeled label="Type">
          <Select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
            {["asset", "liability", "equity", "income", "expense"].map((t) => <option key={t} value={t}>{t}</option>)}
          </Select>
        </Labeled>
        <Button type="submit" disabled={add.isPending || !form.code || !form.name}>Add account</Button>
      </form>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Code</th><th className="px-4 py-2">Name</th><th className="px-4 py-2">Type</th><th className="px-4 py-2"></th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((a: Account) => (
              <tr key={a.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-slate-700">{a.code}</td>
                <td className="px-4 py-2 font-medium text-slate-800">{a.name}</td>
                <td className="px-4 py-2"><span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${TYPE_BADGE[a.type]}`}>{a.type}</span></td>
                <td className="px-4 py-2 text-right">
                  {a.is_system ? <span className="text-xs text-slate-300">system</span>
                    : <button onClick={() => remove.mutate(a.id)} className="text-xs text-rose-600 hover:underline">Delete</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatementTable({ head, rows }: { head: string[]; rows: (string | JSX.Element)[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>{head.map((h, i) => <th key={h} className={`px-4 py-2 ${i > 0 ? "text-right" : ""}`}>{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => <td key={j} className={`px-4 py-2 ${j > 0 ? "text-right" : ""}`}>{c}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TrialBalanceView() {
  const { data, isLoading } = useQuery({ queryKey: ["trial-balance"], queryFn: () => accounting.trialBalance() });
  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!data) return null;
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">As of {data.as_of} · {data.balanced ? <span className="font-medium text-emerald-600">Balanced ✓</span> : <span className="font-medium text-rose-600">Out of balance</span>}</p>
      <StatementTable
        head={["Account", "Debit", "Credit"]}
        rows={[
          ...data.rows.map((r) => [`${r.code} · ${r.name}`, r.debit !== "0.00" ? formatMoney(r.debit!) : "—", r.credit !== "0.00" ? formatMoney(r.credit!) : "—"]),
          [<span key="t" className="font-bold">Total</span>, <span key="d" className="font-bold">{formatMoney(data.total_debit)}</span>, <span key="c" className="font-bold">{formatMoney(data.total_credit)}</span>],
        ]}
      />
    </div>
  );
}

/** Month → { since: 'YYYY-MM-01', until: last day } for the date-windowed reports. */
function monthRange(month: string): { since: string; until: string } | undefined {
  if (!month) return undefined;
  const [y, m] = month.split("-").map(Number);
  const last = new Date(y, m, 0).getDate();
  return { since: `${month}-01`, until: `${month}-${String(last).padStart(2, "0")}` };
}

function MonthFilter({ month, setMonth }: { month: string; setMonth: (m: string) => void }) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <Labeled label="Filter by month">
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand-ring/40"
        />
      </Labeled>
      <button
        type="button"
        onClick={() => setMonth("")}
        disabled={!month}
        className="pb-2 text-sm text-slate-500 hover:text-slate-700 disabled:opacity-0"
      >
        Clear (all time)
      </button>
    </div>
  );
}

function ProfitLossView() {
  const [month, setMonth] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["pnl", month],
    queryFn: () => accounting.profitLoss(monthRange(month)),
  });
  const profit = data ? Number(data.net_profit) >= 0 : true;
  return (
    <div className="space-y-5">
      <MonthFilter month={month} setMonth={setMonth} />
      {isLoading && <p className="text-slate-500">Loading…</p>}
      {!isLoading && data && (
        <>
      <div>
        <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-emerald-700">Income</h3>
        <StatementTable head={["Account", "Amount"]} rows={[...data.income.map((r) => [`${r.code} · ${r.name}`, formatMoney(r.amount!)]), [<span key="t" className="font-semibold">Total Income</span>, <span key="a" className="font-semibold text-emerald-600">{formatMoney(data.total_income)}</span>]]} />
      </div>
      <div>
        <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-rose-600">Expense</h3>
        <StatementTable head={["Account", "Amount"]} rows={[...data.expense.map((r) => [`${r.code} · ${r.name}`, formatMoney(r.amount!)]), [<span key="t" className="font-semibold">Total Expense</span>, <span key="a" className="font-semibold text-rose-600">{formatMoney(data.total_expense)}</span>]]} />
      </div>
      <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
        <span className="font-bold text-slate-900">Net {profit ? "Profit" : "Loss"}</span>
        <span className={`text-lg font-bold ${profit ? "text-emerald-600" : "text-rose-600"}`}>{formatMoney(data.net_profit)}</span>
      </div>
        </>
      )}
    </div>
  );
}

function BalanceSheetView() {
  const { data, isLoading } = useQuery({ queryKey: ["balance-sheet"], queryFn: () => accounting.balanceSheet() });
  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!data) return null;
  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-500">As of {data.as_of} · {data.balanced ? <span className="font-medium text-emerald-600">Balanced ✓</span> : <span className="font-medium text-rose-600">Out of balance</span>}</p>
      <div>
        <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-brand-dark">Assets</h3>
        <StatementTable head={["Account", "Amount"]} rows={[...data.assets.map((r) => [`${r.code} · ${r.name}`, formatMoney(r.amount!)]), [<span key="t" className="font-semibold">Total Assets</span>, <span key="a" className="font-semibold">{formatMoney(data.total_assets)}</span>]]} />
      </div>
      <div>
        <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-amber-700">Liabilities</h3>
        <StatementTable head={["Account", "Amount"]} rows={[...data.liabilities.map((r) => [`${r.code} · ${r.name}`, formatMoney(r.amount!)]), [<span key="t" className="font-semibold">Total Liabilities</span>, <span key="a" className="font-semibold">{formatMoney(data.total_liabilities)}</span>]]} />
      </div>
      <div>
        <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-indigo-700">Equity</h3>
        <StatementTable head={["Account", "Amount"]} rows={[...data.equity.map((r) => [`${r.code} · ${r.name}`, formatMoney(r.amount!)]), [<span key="t" className="font-semibold">Total Equity</span>, <span key="a" className="font-semibold">{formatMoney(data.total_equity)}</span>]]} />
      </div>
    </div>
  );
}

function GeneralLedgerView() {
  const { data: accts } = useQuery({ queryKey: ["accounts"], queryFn: () => accounting.accounts() });
  const [code, setCode] = useState("1010");
  const { data, isLoading } = useQuery({ queryKey: ["gl", code], queryFn: () => accounting.generalLedger(code) });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="w-72">
          <label className="mb-1 block text-sm font-medium text-slate-700">Account</label>
          <Select value={code} onChange={(e) => setCode(e.target.value)}>
            {accts?.results.map((a) => <option key={a.id} value={a.code}>{a.code} · {a.name}</option>)}
          </Select>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setCode("1000")} className={`rounded-lg border px-3 py-2 text-sm font-medium ${code === "1000" ? "border-brand bg-brand-light text-brand-dark" : "border-slate-200 text-slate-600"}`}>Cash Book</button>
          <button type="button" onClick={() => setCode("1010")} className={`rounded-lg border px-3 py-2 text-sm font-medium ${code === "1010" ? "border-brand bg-brand-light text-brand-dark" : "border-slate-200 text-slate-600"}`}>Bank Book</button>
        </div>
      </div>
      {isLoading ? <p className="text-slate-500">Loading…</p> : (
        <>
          <StatementTable
            head={["Date", "Narration", "Debit", "Credit", "Balance"]}
            rows={(data?.lines ?? []).map((l) => [l.date, l.narration || "—", l.debit !== "0.00" ? formatMoney(l.debit) : "—", l.credit !== "0.00" ? formatMoney(l.credit) : "—", formatMoney(l.balance)])}
          />
          {data && data.lines.length === 0 && <p className="py-3 text-slate-400">No entries for this account yet.</p>}
          {data?.closing_balance && data.lines.length > 0 && (
            <p className="text-right text-sm font-semibold">Closing balance: {formatMoney(data.closing_balance)}</p>
          )}
        </>
      )}
    </div>
  );
}

function DayBookView() {
  const [month, setMonth] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["day-book", month],
    queryFn: () => accounting.dayBook(monthRange(month)),
  });
  return (
    <div className="space-y-4">
      <MonthFilter month={month} setMonth={setMonth} />
      {isLoading && <p className="text-slate-500">Loading…</p>}
      {!isLoading && data && (
        <>
      <p className="text-sm text-slate-500">Posted journal entries, newest first · Total {formatMoney(data.total_debit)}</p>
      {data.entries.length === 0 && (
        <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-4 py-8 text-center text-slate-400">
          No journal entries yet. Record a payment, expense or payout and it appears here automatically.
        </p>
      )}
      <div className="space-y-3">
        {data.entries.map((e) => (
          <div key={e.id} className="rounded-xl border border-slate-100">
            <div className="flex items-center justify-between border-b border-slate-50 px-4 py-2 text-sm">
              <span className="font-medium text-slate-700">{e.narration || `Entry #${e.id}`}</span>
              <span className="text-slate-400">{e.date}</span>
            </div>
            <table className="w-full text-sm">
              <tbody>
                {e.lines.map((l, i) => (
                  <tr key={i} className="border-t border-slate-50 first:border-0">
                    <td className="px-4 py-1.5 text-slate-600">{l.account}</td>
                    <td className="px-4 py-1.5 text-right">{l.debit !== "0.00" ? formatMoney(l.debit) : ""}</td>
                    <td className="px-4 py-1.5 text-right">{l.credit !== "0.00" ? formatMoney(l.credit) : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
        </>
      )}
    </div>
  );
}

export function AccountingPage() {
  const [tab, setTab] = useState<Tab>("coa");
  return (
    <div className="space-y-6">
      <PageHeader title="Accounting" subtitle="Chart of accounts, journals and financial statements (₹ INR)" />
      <div className="flex flex-wrap gap-2 border-b border-slate-100">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t.key ? "border-brand text-brand" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            {t.label}
          </button>
        ))}
      </div>
      <Card>
        {tab === "coa" && <ChartOfAccounts />}
        {tab === "trial" && <TrialBalanceView />}
        {tab === "pnl" && <ProfitLossView />}
        {tab === "bs" && <BalanceSheetView />}
        {tab === "ledger" && <GeneralLedgerView />}
        {tab === "daybook" && <DayBookView />}
      </Card>
    </div>
  );
}
