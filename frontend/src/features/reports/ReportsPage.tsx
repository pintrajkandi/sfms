import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { collections, ledgers, payments, payouts, students } from "@/api/resources";
import type { Student } from "@/api/types";
import { Card } from "@/components/Card";
import { PageHeader, Select } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

type ReportKey =
  | "defaulters"
  | "risk"
  | "payouts"
  | "payments"
  | "collection-analysis"
  | "student-ledger"
  | "parent-ledger"
  | "students";

const REPORTS: { key: ReportKey; title: string; desc: string; icon: string }[] = [
  { key: "defaulters", title: "Defaulters & Aging", desc: "Outstanding fees bucketed by how overdue they are.", icon: "⏳" },
  { key: "risk", title: "Predictive Risk", desc: "Students ranked by likelihood of not paying on time.", icon: "🔮" },
  { key: "payouts", title: "Teacher Payouts", desc: "Salary & incentive payouts, filter by status.", icon: "💸" },
  { key: "payments", title: "Payments Ledger", desc: "Every recorded payment for the period.", icon: "🧾" },
  { key: "collection-analysis", title: "Collection Analysis", desc: "Collections by class, by employee and by method.", icon: "📊" },
  { key: "student-ledger", title: "Student Ledger", desc: "One student's billed-vs-paid running statement.", icon: "📒" },
  { key: "parent-ledger", title: "Parent Ledger", desc: "Combined statement across a family's children.", icon: "👨‍👩‍👧" },
  { key: "students", title: "Student Directory", desc: "Full student roster with contact & class details.", icon: "👥" },
];

const PAYOUT_STATUS = ["all", "processed", "submitted", "rejected"];
const PAYOUT_LABEL: Record<string, string> = { processed: "Paid", submitted: "Pending", rejected: "Rejected" };

const AGING = ["all", "current", "1-30", "31-60", "61-90", "90+"];
const BANDS = ["all", "high", "medium", "low"];

function DownloadButtons({ csv, xlsx }: { csv: () => void; xlsx: () => void }) {
  return (
    <div className="flex gap-2">
      <button onClick={csv} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">⬇ CSV</button>
      <button onClick={xlsx} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">⬇ Excel</button>
    </div>
  );
}

function go(url: string) {
  window.location.href = url;
}

function downloadCsv(name: string, headers: string[], rows: (string | number)[][]) {
  const esc = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
  const body = [headers, ...rows].map((r) => r.map(esc).join(",")).join("\n");
  const blob = new Blob([body], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${name}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function DefaultersReport() {
  const [bucket, setBucket] = useState("all");
  const { data, isLoading } = useQuery({ queryKey: ["rep-defaulters"], queryFn: () => collections.defaulters() });
  const rows = useMemo(
    () => (data?.defaulters ?? []).filter((d) => bucket === "all" || d.bucket === bucket),
    [data, bucket],
  );

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-44">
          <label className="mb-1 block text-sm font-medium text-slate-700">Aging bucket</label>
          <Select value={bucket} onChange={(e) => setBucket(e.target.value)}>
            {AGING.map((b) => <option key={b} value={b}>{b === "all" ? "All buckets" : b}</option>)}
          </Select>
        </div>
        <DownloadButtons
          csv={() => go(collections.defaultersExportUrl("csv"))}
          xlsx={() => go(collections.defaultersExportUrl("xlsx"))}
        />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Defaulters" value={String(data?.count ?? 0)} />
        <Stat label="Total outstanding" value={formatMoney(data?.total_outstanding ?? "0")} tone="text-rose-600" />
        <Stat label="Shown" value={String(rows.length)} />
      </div>
      <Table
        loading={isLoading}
        empty="🎉 No defaulters — everyone's paid up."
        head={["Student", "Class", "Outstanding", "Days Overdue", "Oldest Due", "Bucket"]}
        rows={rows.map((d) => [
          <span key="s"><span className="font-medium text-slate-800">{d.student}</span> <span className="font-mono text-xs text-slate-400">{d.student_id}</span></span>,
          d.grade || "—",
          <span key="o" className="font-semibold text-rose-600">{formatMoney(d.outstanding)}</span>,
          d.days_overdue,
          formatDate(d.oldest_due),
          d.bucket,
        ])}
      />
    </>
  );
}

function RiskReport() {
  const [band, setBand] = useState("all");
  const { data, isLoading } = useQuery({ queryKey: ["rep-risk"], queryFn: () => collections.risk() });
  const rows = useMemo(
    () => (data?.at_risk ?? []).filter((r) => band === "all" || r.risk_band === band),
    [data, band],
  );
  const bandBadge: Record<string, string> = {
    high: "bg-rose-50 text-rose-600", medium: "bg-amber-50 text-amber-700", low: "bg-slate-100 text-slate-500",
  };

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-44">
          <label className="mb-1 block text-sm font-medium text-slate-700">Risk band</label>
          <Select value={band} onChange={(e) => setBand(e.target.value)}>
            {BANDS.map((b) => <option key={b} value={b}>{b === "all" ? "All bands" : b}</option>)}
          </Select>
        </div>
        <DownloadButtons
          csv={() => downloadCsv("predictive-risk", ["Student", "Student ID", "Class", "Outstanding", "Risk Score", "Band", "Days Overdue", "Recommended Action"], rows.map((r) => [r.student, r.student_id, r.grade, r.outstanding, r.risk_score, r.risk_band, r.days_overdue, r.recommended_action]))}
          xlsx={() => downloadCsv("predictive-risk", ["Student", "Student ID", "Class", "Outstanding", "Risk Score", "Band", "Days Overdue", "Recommended Action"], rows.map((r) => [r.student, r.student_id, r.grade, r.outstanding, r.risk_score, r.risk_band, r.days_overdue, r.recommended_action]))}
        />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="High risk" value={String(data?.counts.high ?? 0)} tone="text-rose-600" />
        <Stat label="Medium" value={String(data?.counts.medium ?? 0)} tone="text-amber-600" />
        <Stat label="Low" value={String(data?.counts.low ?? 0)} />
        <Stat label="At-risk total" value={formatMoney(String(data?.total_at_risk ?? 0))} />
      </div>
      <Table
        loading={isLoading}
        empty="No at-risk students right now."
        head={["Student", "Class", "Outstanding", "Score", "Band", "Recommended Action"]}
        rows={rows.map((r) => [
          <span key="s"><span className="font-medium text-slate-800">{r.student}</span> <span className="font-mono text-xs text-slate-400">{r.student_id}</span></span>,
          r.grade || "—",
          formatMoney(r.outstanding),
          r.risk_score,
          <span key="b" className={`rounded-full px-2 py-0.5 text-xs font-medium ${bandBadge[r.risk_band]}`}>{r.risk_band}</span>,
          <span key="a" className="text-slate-500">{r.recommended_action}</span>,
        ])}
      />
    </>
  );
}

function PayoutsReport() {
  const [status, setStatus] = useState("all");
  const { data, isLoading } = useQuery({ queryKey: ["rep-payouts"], queryFn: () => payouts.list() });
  const rows = useMemo(
    () => (data?.results ?? []).filter((p) => status === "all" || p.status === status),
    [data, status],
  );
  const paidTotal = rows.filter((p) => p.status === "processed").reduce((s, p) => s + Number(p.net_amount), 0);

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-44">
          <label className="mb-1 block text-sm font-medium text-slate-700">Status</label>
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            {PAYOUT_STATUS.map((s) => <option key={s} value={s}>{s === "all" ? "All" : PAYOUT_LABEL[s] ?? s}</option>)}
          </Select>
        </div>
        <DownloadButtons
          csv={() => downloadCsv("teacher-payouts", ["Teacher", "Period", "Type", "Days Present", "Days Absent", "Deductions", "Deduction Reason", "Net", "Status"], rows.map((p) => [p.teacher_name, p.pay_period, p.pay_type, p.days_present ?? "", p.days_absent ?? "", p.deductions, p.deduction_reason, p.net_amount, PAYOUT_LABEL[p.status] ?? p.status]))}
          xlsx={() => downloadCsv("teacher-payouts", ["Teacher", "Period", "Type", "Days Present", "Days Absent", "Deductions", "Deduction Reason", "Net", "Status"], rows.map((p) => [p.teacher_name, p.pay_period, p.pay_type, p.days_present ?? "", p.days_absent ?? "", p.deductions, p.deduction_reason, p.net_amount, PAYOUT_LABEL[p.status] ?? p.status]))}
        />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Payouts" value={String(rows.length)} />
        <Stat label="Paid total" value={formatMoney(paidTotal.toFixed(2))} tone="text-emerald-600" />
      </div>
      <Table
        loading={isLoading}
        empty="No payouts recorded yet."
        head={["Teacher", "Period", "Type", "Present / Absent", "Net", "Status"]}
        rows={rows.map((p) => [
          <span key="t" className="font-medium text-slate-800">{p.teacher_name}</span>,
          p.pay_period,
          <span key="ty" className="capitalize">{p.pay_type.replace("_", " ")}</span>,
          `${p.days_present ?? "—"} / ${p.days_absent ?? "—"}`,
          <span key="n" className="font-semibold text-emerald-600">{formatMoney(p.net_amount, p.currency)}</span>,
          PAYOUT_LABEL[p.status] ?? p.status,
        ])}
      />
    </>
  );
}

function PaymentsReport() {
  const [term, setTerm] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["rep-payments"], queryFn: () => payments.recent() });
  const rows = useMemo(() => {
    const t = term.trim().toLowerCase();
    const all = data?.results ?? [];
    if (!t) return all;
    return all.filter((p) => (p.student_name ?? "").toLowerCase().includes(t) || (p.reference ?? "").toLowerCase().includes(t));
  }, [data, term]);
  const total = rows.reduce((s, p) => s + Number(p.amount), 0);

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-64">
          <label className="mb-1 block text-sm font-medium text-slate-700">Search student / reference</label>
          <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="e.g. Priya, TXN123" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none" />
        </div>
        <DownloadButtons csv={() => go(collections.paymentsExportUrl("csv"))} xlsx={() => go(collections.paymentsExportUrl("xlsx"))} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Payments" value={String(rows.length)} />
        <Stat label="Collected" value={formatMoney(total.toFixed(2))} tone="text-emerald-600" />
      </div>
      <Table
        loading={isLoading}
        empty="No payments recorded yet."
        head={["Date", "Student", "Class", "Fee Type", "Method", "Amount"]}
        rows={rows.map((p) => [
          formatDate(p.paid_at),
          <span key="s"><span className="font-medium text-slate-800">{p.student_name}</span></span>,
          p.student_grade || "—",
          p.fee_type || "—",
          <span key="m" className="capitalize">{(p.method || "—").replace("_", " ")}</span>,
          <span key="a" className="font-semibold text-emerald-600">{formatMoney(p.amount, p.currency)}</span>,
        ])}
      />
    </>
  );
}

function StudentsReport() {
  const [term, setTerm] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["rep-students", term], queryFn: () => students.search(term) });
  const rows = data?.results ?? [];

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-64">
          <label className="mb-1 block text-sm font-medium text-slate-700">Search student</label>
          <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Name, ID or phone…" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none" />
        </div>
        <DownloadButtons csv={() => go(students.exportUrl("csv"))} xlsx={() => go(students.exportUrl("xlsx"))} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Students" value={String(data?.count ?? rows.length)} />
      </div>
      <Table
        loading={isLoading}
        empty="No students match."
        head={["Student", "Class / Section", "Guardian", "Phone", "Status"]}
        rows={rows.map((s) => [
          <span key="s"><span className="font-medium text-slate-800">{s.full_name}</span> <span className="font-mono text-xs text-slate-400">{s.student_id}</span></span>,
          `${s.grade || "—"}${s.section ? " · " + s.section : ""}`,
          s.guardian_name || "—",
          s.guardian_phone || s.phone || "—",
          <span key="st" className="capitalize">{s.status}</span>,
        ])}
      />
    </>
  );
}

function CollectionAnalysisReport() {
  const { data, isLoading } = useQuery({ queryKey: ["collection-breakdown"], queryFn: () => collections.breakdown() });
  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!data) return null;

  const block = (title: string, rows: { key: string; count: number; total: string }[]) => (
    <div>
      <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-500">{title}</h3>
      <Table
        empty="No collections yet."
        head={[title.replace("By ", ""), "Receipts", "Collected"]}
        rows={rows.map((r) => [
          <span key="k" className="font-medium capitalize text-slate-800">{r.key.replace("_", " ")}</span>,
          String(r.count),
          <span key="t" className="font-semibold text-emerald-600">{formatMoney(r.total)}</span>,
        ])}
      />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-slate-50 px-4 py-3">
        <span className="text-sm text-slate-500">Total collected · </span>
        <span className="text-lg font-bold text-emerald-600">{formatMoney(data.total)}</span>
      </div>
      {block("By Class", data.by_class)}
      {block("By Employee", data.by_employee)}
      {block("By Method", data.by_method)}
    </div>
  );
}

function LedgerReport({ mode }: { mode: "student" | "parent" }) {
  const [term, setTerm] = useState("");
  const [picked, setPicked] = useState<Student | null>(null);
  const search = useQuery({ queryKey: ["ledger-student-search", term], queryFn: () => students.search(term), enabled: !picked });
  const { data, isLoading } = useQuery({
    queryKey: ["ledger", mode, picked?.id],
    queryFn: () => (mode === "student" ? ledgers.student(picked!.id) : ledgers.parent(picked!.id)),
    enabled: Boolean(picked),
  });

  if (!picked) {
    return (
      <div className="space-y-3">
        <div className="w-72">
          <label className="mb-1 block text-sm font-medium text-slate-700">Find student</label>
          <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Name, ID or phone…" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none" />
        </div>
        <div className="divide-y divide-slate-50 rounded-xl border border-slate-100">
          {(search.data?.results ?? []).slice(0, 10).map((s) => (
            <button key={s.id} onClick={() => setPicked(s)} className="flex w-full items-center justify-between px-4 py-2 text-left text-sm hover:bg-slate-50">
              <span className="font-medium text-slate-800">{s.full_name} <span className="font-mono text-xs text-slate-400">{s.student_id}</span></span>
              <span className="text-xs text-slate-400">{s.grade}{s.section ? " · " + s.section : ""}</span>
            </button>
          ))}
          {search.data?.results.length === 0 && <p className="px-4 py-3 text-slate-400">No students match.</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button onClick={() => setPicked(null)} className="text-sm font-semibold text-brand hover:underline">← Change {mode === "parent" ? "family" : "student"}</button>
      {isLoading && <p className="text-slate-500">Loading…</p>}
      {data && (
        <>
          <div className="rounded-xl bg-slate-50 px-4 py-3">
            {mode === "student" ? (
              <p className="font-semibold text-slate-800">{data.student?.name} · {data.student?.grade}{data.student?.section ? " · " + data.student?.section : ""}</p>
            ) : (
              <p className="font-semibold text-slate-800">Guardian: {data.guardian?.name || "—"} · {data.students?.length} child(ren)</p>
            )}
            <p className="text-sm text-slate-500">Billed {formatMoney(data.total_billed)} · Paid {formatMoney(data.total_paid)} · <span className={Number(data.outstanding) > 0 ? "font-semibold text-rose-600" : "font-semibold text-emerald-600"}>Outstanding {formatMoney(data.outstanding)}</span></p>
          </div>
          <Table
            loading={false}
            empty="No transactions for this student yet."
            head={mode === "parent" ? ["Date", "Student", "Particulars", "Debit", "Credit", "Balance"] : ["Date", "Particulars", "Debit", "Credit", "Balance"]}
            rows={data.lines.map((l) => {
              const cells = [
                l.date,
                l.particulars,
                l.debit !== "0.00" ? formatMoney(l.debit) : "—",
                l.credit !== "0.00" ? formatMoney(l.credit) : "—",
                formatMoney(l.balance),
              ];
              return mode === "parent" ? [l.date, l.student ?? "—", ...cells.slice(1)] : cells;
            })}
          />
        </>
      )}
    </div>
  );
}

function Stat({ label, value, tone = "text-slate-800" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-xl border border-slate-100 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-lg font-bold ${tone}`}>{value}</p>
    </div>
  );
}

function Table({ head, rows, loading, empty }: { head: string[]; rows: React.ReactNode[][]; loading?: boolean; empty: string }) {
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[640px] text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>{head.map((h) => <th key={h} className="px-4 py-2 font-semibold">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {rows.map((r, i) => (
            <tr key={i} className="hover:bg-slate-50">
              {r.map((c, j) => <td key={j} className="px-4 py-2 align-top text-slate-600">{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {loading && <p className="px-4 py-4 text-slate-500">Loading…</p>}
      {!loading && rows.length === 0 && <p className="px-4 py-4 text-emerald-600">{empty}</p>}
    </div>
  );
}

export function ReportsPage() {
  const [active, setActive] = useState<ReportKey>("defaulters");
  const meta = REPORTS.find((r) => r.key === active)!;

  return (
    <div className="space-y-6">
      <PageHeader title="Reports" subtitle="Filter, preview and download school reports (₹ INR)" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
        {/* Report catalog */}
        <div className="space-y-2">
          {REPORTS.map((r) => (
            <button
              key={r.key}
              onClick={() => setActive(r.key)}
              className={`flex w-full items-start gap-3 rounded-xl border px-4 py-3 text-left transition ${
                active === r.key ? "border-brand bg-brand-light" : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <span className="text-xl">{r.icon}</span>
              <span>
                <span className={`block text-sm font-semibold ${active === r.key ? "text-brand-dark" : "text-slate-800"}`}>{r.title}</span>
                <span className="block text-xs text-slate-400">{r.desc}</span>
              </span>
            </button>
          ))}
        </div>

        {/* Selected report */}
        <Card>
          <div className="mb-4">
            <h2 className="text-base font-semibold text-slate-900">{meta.title}</h2>
            <p className="text-sm text-slate-500">{meta.desc}</p>
          </div>
          {active === "defaulters" && <DefaultersReport />}
          {active === "risk" && <RiskReport />}
          {active === "payouts" && <PayoutsReport />}
          {active === "payments" && <PaymentsReport />}
          {active === "collection-analysis" && <CollectionAnalysisReport />}
          {active === "student-ledger" && <LedgerReport mode="student" />}
          {active === "parent-ledger" && <LedgerReport mode="parent" />}
          {active === "students" && <StudentsReport />}
        </Card>
      </div>
    </div>
  );
}
