import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { collections, fees, invoices, payments, students } from "@/api/resources";
import type { Student } from "@/api/types";
import { Card } from "@/components/Card";
import { Labeled, Select, TextArea, TextInput, StatusBadge, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

const MODE_COLORS: Record<string, string> = {
  UPI: "text-emerald-600", upi: "text-emerald-600",
  Cash: "text-slate-600", cash: "text-slate-600",
  Cheque: "text-purple-600", cheque: "text-purple-600",
  card: "text-brand", bank_transfer: "text-brand", paypal: "text-brand",
};

export function FeeCollectionDashboard() {
  const navigate = useNavigate();
  const stats = useQuery({ queryKey: ["collection-stats"], queryFn: () => collections.stats() });
  const recent = useQuery({ queryKey: ["recent-payments"], queryFn: () => payments.recent() });
  const feeTypes = useQuery({ queryKey: ["fee-types"], queryFn: () => fees.types() });

  const [query, setQuery] = useState("");
  const [student, setStudent] = useState<Student | null>(null);
  const [feeType, setFeeType] = useState("");
  const [amount, setAmount] = useState("");
  const [mode, setMode] = useState("cash");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [remarks, setRemarks] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const search = useQuery({
    queryKey: ["fc-search", query],
    queryFn: () => students.search(query),
    enabled: query.length > 1 && !student,
  });
  const feesSummary = useQuery({
    queryKey: ["fc-fees", student?.id],
    queryFn: () => students.fees(student!.id),
    enabled: !!student,
  });

  async function confirm() {
    if (!student || !feeType || !amount) {
      setError("Select a student, fee category and amount.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const invoice = await invoices.create({
        student: student.id,
        lines: [{ fee_type: Number(feeType), quantity: 1, unit_price: amount }],
      });
      await payments.create({
        invoice: invoice.id,
        amount,
        method: mode,
        reference: remarks,
        paid_at: `${date}T00:00:00Z`,
        idempotency_key: crypto.randomUUID(),
      });
      navigate(`/invoices/${invoice.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not record the payment.");
    } finally {
      setSubmitting(false);
    }
  }

  const st = stats.data;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Fee Collection</h1>
          <p className="text-sm text-slate-500">Collect and manage student fee payments</p>
        </div>
        <Link to="/fee-collection/new" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
          + New Collection
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Total Collected" value={formatMoney(st?.total_collected ?? "0")} hint="fees received" tone="brand" />
        <Kpi label="Pending Dues" value={formatMoney(st?.pending_dues ?? "0")} hint="outstanding" tone="rose" />
        <Kpi label="Paid Students" value={`${st?.paid_students ?? 0}`} hint={`of ${st?.total_students ?? 0} total`} tone="emerald" />
        <Kpi label="Today's Collection" value={formatMoney(st?.todays_collection ?? "0")} hint={`${st?.todays_receipts ?? 0} receipts`} tone="brand" />
      </div>

      {/* Accountant breakouts */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Kpi label="Cash in Hand" value={formatMoney(st?.cash_in_hand ?? "0")} hint="net cash collected" tone="emerald" />
        <Kpi label="Bank Deposits" value={formatMoney(st?.bank_deposits ?? "0")} hint="UPI / bank / cheque / card" tone="brand" />
        <Kpi label="Yesterday's Collection" value={formatMoney(st?.yesterday_collection ?? "0")} hint="previous day" tone="brand" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Collect Fee panel */}
        <Card className="space-y-4">
          <h2 className="flex items-center gap-2 text-base font-semibold">💳 Collect Fee</h2>
          {error && <Toast tone="error" message={error} />}

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Student ID / Name</label>
            {!student ? (
              <>
                <TextInput placeholder="🔍 Search student…" value={query} onChange={(e) => setQuery(e.target.value)} />
                {search.data && query.length > 1 && (
                  <div className="mt-2 divide-y divide-slate-50 rounded-lg border border-slate-100">
                    {search.data.results.map((s) => (
                      <button key={s.id} onClick={() => setStudent(s)} className="flex w-full justify-between px-3 py-2 text-left text-sm hover:bg-slate-50">
                        <span className="font-medium text-slate-800">{s.full_name}</span>
                        <span className="font-mono text-xs text-slate-400">{s.student_id}</span>
                      </button>
                    ))}
                    {search.data.results.length === 0 && <p className="px-3 py-2 text-sm text-slate-400">No students found.</p>}
                  </div>
                )}
              </>
            ) : (
              <div className="rounded-xl bg-brand-light/60 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 overflow-hidden rounded-full bg-white">
                      {student.photo && <img src={student.photo} alt="" className="h-full w-full object-cover" />}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{student.full_name}</p>
                      <p className="text-xs text-slate-500">{student.grade || "—"}{student.section ? ` · ${student.section}` : ""}</p>
                    </div>
                  </div>
                  <button onClick={() => setStudent(null)} className="text-xs font-semibold text-brand hover:underline">Change</button>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div className="rounded-lg bg-white px-3 py-2">
                    <p className="text-xs text-slate-400">Outstanding</p>
                    <p className="font-bold text-rose-600">{formatMoney(feesSummary.data?.outstanding ?? "0")}</p>
                  </div>
                  <div className="rounded-lg bg-white px-3 py-2">
                    <p className="text-xs text-slate-400">Paid</p>
                    <p className="font-bold text-emerald-600">{formatMoney(feesSummary.data?.paid ?? "0")}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <Labeled label="Fee category">
            <Select value={feeType} onChange={(e) => {
              setFeeType(e.target.value);
              const ft = feeTypes.data?.results.find((f) => String(f.id) === e.target.value);
              if (ft && !amount) setAmount(ft.default_amount);
            }}>
              <option value="">Select category</option>
              {feeTypes.data?.results.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
            </Select>
          </Labeled>

          <div className="grid grid-cols-2 gap-3">
            <Labeled label="Amount">
              <TextInput placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </Labeled>
            <Labeled label="Payment mode">
              <Select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="upi">UPI</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="cheque">Cheque</option>
              </Select>
            </Labeled>
          </div>

          <Labeled label="Payment date">
            <TextInput type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </Labeled>
          <Labeled label="Remarks (optional)">
            <TextArea placeholder="Add a note…" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          </Labeled>

          <button onClick={confirm} disabled={submitting} className="w-full rounded-xl bg-brand-gradient py-3 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
            ✓ {submitting ? "Processing…" : "Confirm & Generate Receipt"}
          </button>
        </Card>

        {/* Recent Payments */}
        <Card className="p-0 lg:col-span-2">
          <div className="flex items-center justify-between px-6 py-4">
            <h2 className="flex items-center gap-2 text-base font-semibold">☰ Recent Payments</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-semibold">Student</th>
                  <th className="px-6 py-3 font-semibold">Category</th>
                  <th className="px-6 py-3 font-semibold">Amount</th>
                  <th className="px-6 py-3 font-semibold">Mode</th>
                  <th className="px-6 py-3 font-semibold">Date</th>
                  <th className="px-6 py-3 text-right font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {recent.data?.results.map((p) => (
                  <tr key={p.id} className="cursor-pointer hover:bg-slate-50" onClick={() => navigate(`/invoices/${p.invoice}`)}>
                    <td className="px-6 py-3">
                      <p className="font-medium text-slate-800">{p.student_name}</p>
                      <p className="text-xs text-slate-400">{p.student_grade || "—"}</p>
                    </td>
                    <td className="px-6 py-3 text-slate-600">{p.fee_type || "—"}</td>
                    <td className="px-6 py-3 font-semibold">{formatMoney(p.amount, p.currency)}</td>
                    <td className={`px-6 py-3 font-medium ${MODE_COLORS[p.method] ?? "text-slate-600"}`}>{p.method.replace("_", " ")}</td>
                    <td className="px-6 py-3 text-slate-500">{formatDate(p.paid_at)}</td>
                    <td className="px-6 py-3 text-right"><StatusBadge status={p.invoice_status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {recent.data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No payments yet.</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Kpi({ label, value, hint, tone }: { label: string; value: string; hint: string; tone: "brand" | "rose" | "emerald" }) {
  const color = tone === "rose" ? "text-rose-500" : tone === "emerald" ? "text-emerald-600" : "text-brand";
  return (
    <Card>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      <p className={`mt-1 text-xs ${color}`}>{hint}</p>
    </Card>
  );
}
