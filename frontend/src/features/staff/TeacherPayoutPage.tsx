import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "@/api/client";
import { payouts, teachers } from "@/api/resources";
import type { Payout, PayoutStatus, Teacher } from "@/api/types";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { MonthPicker } from "@/components/MonthPicker";
import { alertError } from "@/lib/alerts";
import { formatMoney } from "@/lib/money";

const readonly = "bg-slate-50 text-slate-600";

// Approval stages removed — a submitted payout is paid or rejected in one step.
const NEXT: Partial<Record<PayoutStatus, { to: PayoutStatus; label: string }>> = {
  submitted: { to: "processed", label: "Mark as Paid" },
  hod_approved: { to: "processed", label: "Mark as Paid" },
  finance_approved: { to: "processed", label: "Mark as Paid" },
};

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

const q = (v: string) => (Number.parseFloat(v || "0") || 0).toFixed(2);

const EMPTY = {
  teacher: "", pay_type: "salary", pay_period: "",
  base_amount: "0.00", bonus_amount: "0.00", deductions: "0.00",
  days_present: "", days_absent: "",
  payment_method: "bank_transfer", payment_reference: "", notes: "",
};

export function TeacherPayoutPage() {
  const qc = useQueryClient();
  const teacherList = useQuery({ queryKey: ["teachers"], queryFn: () => teachers.list() });
  const payoutList = useQuery({ queryKey: ["payouts"], queryFn: () => payouts.list() });
  const [form, setForm] = useState({ ...EMPTY });
  const [reasons, setReasons] = useState<string[]>([""]);
  const [teacherQuery, setTeacherQuery] = useState("");
  const [teacherOpen, setTeacherOpen] = useState(false);
  const [error, setError] = useState("");
  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }));

  const selected: Teacher | undefined = teacherList.data?.results.find((t) => String(t.id) === form.teacher);
  const teacherMatches = useMemo(() => {
    const term = teacherQuery.trim().toLowerCase();
    const all = teacherList.data?.results ?? [];
    if (!term) return all.slice(0, 8);
    return all
      .filter((t) => t.full_name.toLowerCase().includes(term) || (t.employee_id ?? "").toLowerCase().includes(term))
      .slice(0, 8);
  }, [teacherQuery, teacherList.data]);
  const net = q(String(Number(q(form.base_amount)) + Number(q(form.bonus_amount)) - Number(q(form.deductions))));

  const rows = payoutList.data?.results ?? [];
  const totalBudget = rows.reduce((s, p) => s + Number(p.net_amount), 0);
  const pending = rows.filter((p) => !["processed", "rejected"].includes(p.status)).length;
  const paidPayouts = rows.filter((p) => p.status === "processed");
  const paidCount = paidPayouts.length;
  const paidTotal = paidPayouts.reduce((s, p) => s + Number(p.net_amount), 0);

  function pickTeacher(t: Teacher) {
    const earnings = (Number(t.base_salary) + Number(t.hra) + Number(t.medical_allowance) + Number(t.other_allowance)).toFixed(2);
    const deduct = (Number(t.pf_amount) + Number(t.tds_amount) + Number(t.other_deduction)).toFixed(2);
    setForm((f) => ({ ...f, teacher: String(t.id), base_amount: earnings, deductions: deduct }));
    setTeacherQuery(t.full_name);
    setTeacherOpen(false);
  }

  function resetForm() {
    setForm({ ...EMPTY });
    setReasons([""]);
    setTeacherQuery("");
  }

  const create = useMutation({
    mutationFn: () =>
      payouts.create({
        teacher: Number(form.teacher),
        pay_type: form.pay_type || "salary",
        pay_period: form.pay_period,
        base_amount: q(form.base_amount),
        bonus_amount: q(form.bonus_amount),
        deductions: q(form.deductions),
        days_present: form.days_present === "" ? null : Number(form.days_present),
        days_absent: form.days_absent === "" ? null : Number(form.days_absent),
        deduction_reason: reasons.map((r) => r.trim()).filter(Boolean).join("; "),
        payment_method: form.payment_method,
        payment_reference: form.payment_reference,
        notes: form.notes,
      }),
    onSuccess: () => {
      setError("");
      resetForm();
      qc.invalidateQueries({ queryKey: ["payouts"] });
    },
    onError: (e) => {
      const msg = e instanceof ApiError ? e.detail : "Could not submit payout.";
      // Duplicate pay-period (and any other rejection) surfaces as a SweetAlert.
      void alertError("Payout not created", msg);
      setError(msg);
    },
  });

  const transition = useMutation({
    mutationFn: ({ id, to }: { id: number; to: string }) => payouts.transition(id, to),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payouts"] }),
    onError: (e) => setError(e instanceof ApiError ? e.detail : "Transition not allowed."),
  });

  const canSubmit =
    Boolean(form.teacher) &&
    Boolean(form.pay_period) &&
    Number(q(form.base_amount)) + Number(q(form.bonus_amount)) > 0;

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="flex flex-col gap-4 rounded-2xl bg-brand-gradient px-8 py-6 text-white sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-white/70">Finance Department</p>
          <h1 className="mt-1 text-3xl font-bold">Teacher Payout Form</h1>
          <p className="text-sm text-white/80">Submit and process teacher salary &amp; incentive payouts.</p>
        </div>
        <div className="flex gap-3">
          <div className="rounded-xl bg-white/15 px-5 py-3 text-center">
            <p className="text-xs text-white/70">Total Budget</p>
            <p className="text-lg font-bold">{formatMoney(totalBudget.toFixed(2))}</p>
          </div>
          <div className="rounded-xl bg-white/15 px-5 py-3 text-center">
            <p className="text-xs text-white/70">Pending</p>
            <p className="text-lg font-bold">{pending}</p>
          </div>
        </div>
      </div>

      {error && <Toast tone="error" message={error} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Form */}
        <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-2">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">New Payout Entry</h2>
              <p className="text-sm text-slate-500">Fill in teacher and payment details</p>
            </div>
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">◷ Draft</span>
          </div>

          <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-400">Teacher Information</p>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Labeled label="Full name" required>
              <div className="relative">
                <TextInput
                  placeholder="Search teacher by name or ID…"
                  value={teacherQuery}
                  onChange={(e) => { setTeacherQuery(e.target.value); setTeacherOpen(true); if (form.teacher) set("teacher", ""); }}
                  onFocus={() => setTeacherOpen(true)}
                />
                {teacherOpen && teacherMatches.length > 0 && (
                  <div className="absolute z-30 mt-1 max-h-60 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg">
                    {teacherMatches.map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => pickTeacher(t)}
                        className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50"
                      >
                        <span className="font-medium text-slate-800">{t.full_name}</span>
                        <span className="text-xs text-slate-400">{t.employee_id}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {selected && (
                <Link to={`/teachers/${selected.id}/edit`} className="mt-1 inline-block text-xs font-semibold text-brand hover:underline">
                  Edit {selected.full_name}'s details →
                </Link>
              )}
            </Labeled>
            <Labeled label="Employee ID" required>
              <TextInput className={readonly} readOnly value={selected?.employee_id ?? ""} placeholder="e.g. TCH-2024-001" />
            </Labeled>
            <Labeled label="Department">
              <TextInput className={readonly} readOnly value={selected?.department ?? ""} placeholder="—" />
            </Labeled>
            <Labeled label="Email address">
              <TextInput className={readonly} readOnly value={selected?.email ?? ""} placeholder="teacher@school.edu" />
            </Labeled>
          </div>

          <p className="mb-3 mt-6 text-xs font-bold uppercase tracking-wide text-slate-400">Payout Details</p>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Labeled label="Payout type" required>
              <Select value={form.pay_type} onChange={(e) => set("pay_type", e.target.value)}>
                <option value="">Select type</option>
                <option value="salary">Salary</option>
                <option value="bonus">Bonus / Incentive</option>
                <option value="reimbursement">Reimbursement</option>
              </Select>
            </Labeled>
            <Labeled label="Pay period" required>
              <MonthPicker value={form.pay_period} onChange={(v) => set("pay_period", v)} placeholder="Select pay month" />
            </Labeled>
            <Labeled label="Base amount (₹)" required>
              <TextInput placeholder="0.00" value={form.base_amount} onChange={(e) => set("base_amount", e.target.value)} />
            </Labeled>
            <Labeled label="Bonus / incentive (₹)">
              <TextInput placeholder="0.00" value={form.bonus_amount} onChange={(e) => set("bonus_amount", e.target.value)} />
            </Labeled>
            <Labeled label="Deductions (₹)">
              <TextInput placeholder="0.00" value={form.deductions} onChange={(e) => set("deductions", e.target.value)} />
            </Labeled>
            <Labeled label="Payment method" required>
              <Select value={form.payment_method} onChange={(e) => { set("payment_method", e.target.value); set("payment_reference", ""); }}>
                <option value="">Select method</option>
                <option value="bank_transfer">Bank Transfer / Account</option>
                <option value="upi">UPI</option>
                <option value="cheque">Cheque</option>
                <option value="cash">Cash</option>
              </Select>
            </Labeled>
            {form.payment_method === "cheque" && (
              <Labeled label="Cheque number" required>
                <TextInput placeholder="e.g. 004521" value={form.payment_reference} onChange={(e) => set("payment_reference", e.target.value)} />
              </Labeled>
            )}
            {form.payment_method === "upi" && (
              <Labeled label="UPI ID / reference" required>
                <TextInput placeholder="e.g. teacher@okhdfc" value={form.payment_reference} onChange={(e) => set("payment_reference", e.target.value)} />
              </Labeled>
            )}
            {form.payment_method === "bank_transfer" && (
              <Labeled label="Credited to account">
                <TextInput className={readonly} readOnly value={selected ? `${selected.bank_name} ${selected.account_number ? "•••• " + selected.account_number.slice(-4) : ""}`.trim() : ""} placeholder="Select teacher for account details" />
              </Labeled>
            )}
          </div>

          <p className="mb-3 mt-6 text-xs font-bold uppercase tracking-wide text-slate-400">Attendance &amp; Deduction Reasons</p>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Labeled label="Days present">
              <TextInput type="number" placeholder="e.g. 24" value={form.days_present} onChange={(e) => set("days_present", e.target.value)} />
            </Labeled>
            <Labeled label="Days absent">
              <TextInput type="number" placeholder="e.g. 2" value={form.days_absent} onChange={(e) => set("days_absent", e.target.value)} />
            </Labeled>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm font-medium text-slate-700">Reasons for deductions</label>
              <div className="space-y-2">
                {reasons.map((r, i) => (
                  <div key={i} className="flex gap-2">
                    <TextInput
                      placeholder="e.g. 2 days loss of pay"
                      value={r}
                      onChange={(e) => setReasons((rs) => rs.map((x, j) => (j === i ? e.target.value : x)))}
                    />
                    {reasons.length > 1 && (
                      <button type="button" onClick={() => setReasons((rs) => rs.filter((_, j) => j !== i))} className="rounded-lg bg-rose-50 px-3 text-rose-500 hover:bg-rose-100" aria-label="Remove reason">🗑</button>
                    )}
                  </div>
                ))}
              </div>
              <button type="button" onClick={() => setReasons((rs) => [...rs, ""])} className="mt-2 text-sm font-semibold text-brand hover:underline">+ Add reason</button>
            </div>
          </div>

          <p className="mb-3 mt-6 text-xs font-bold uppercase tracking-wide text-slate-400">Bank Details</p>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Labeled label="Account holder">
              <TextInput className={readonly} readOnly value={selected?.account_holder_name ?? ""} placeholder="—" />
            </Labeled>
            <Labeled label="Bank name">
              <TextInput className={readonly} readOnly value={selected?.bank_name ?? ""} placeholder="e.g. HDFC Bank" />
            </Labeled>
            <Labeled label="Branch">
              <TextInput className={readonly} readOnly value={selected?.branch ?? ""} placeholder="—" />
            </Labeled>
            <Labeled label="IFSC code">
              <TextInput className={readonly} readOnly value={selected?.ifsc_code ?? ""} placeholder="e.g. HDFC0001234" />
            </Labeled>
            <Labeled label="Notes / remarks" full>
              <TextArea placeholder="Add any additional notes or justification for this payout…" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
            </Labeled>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button onClick={() => create.mutate()} disabled={!canSubmit || create.isPending} className="rounded-xl bg-brand-gradient px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
              ➤ {create.isPending ? "Submitting…" : "Submit Payout"}
            </button>
            <button onClick={resetForm} className="rounded-xl border border-slate-200 px-6 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">
              ↺ Clear
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-slate-900">🧮 Payout Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Base Amount</span><span className="font-semibold">{formatMoney(q(form.base_amount))}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Bonus / Incentive</span><span className="font-semibold text-emerald-600">+ {formatMoney(q(form.bonus_amount))}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Deductions</span><span className="font-semibold text-rose-500">− {formatMoney(q(form.deductions))}</span></div>
              <div className="mt-2 flex justify-between border-t border-slate-100 pt-3"><span className="font-bold text-slate-900">Net Payout</span><span className="text-lg font-bold text-brand">{formatMoney(net)}</span></div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-slate-900">📊 Payout Status</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-amber-50 px-4 py-3">
                <p className="text-xs font-medium text-amber-700">Pending</p>
                <p className="text-2xl font-bold text-amber-700">{pending}</p>
              </div>
              <div className="rounded-xl bg-emerald-50 px-4 py-3">
                <p className="text-xs font-medium text-emerald-700">Paid</p>
                <p className="text-lg font-bold text-emerald-700">{formatMoney(paidTotal.toFixed(2))}</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-slate-400">Payouts are paid in a single step — no multi-stage approval.</p>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-slate-900">↻ Recent Payouts</h3>
            <div className="space-y-3">
              {payoutList.data?.results.slice(0, 5).map((p: Payout) => (
                <div key={p.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{p.teacher_name}</p>
                    <p className="mt-0.5 flex items-center gap-2 text-xs capitalize text-slate-400">
                      {p.pay_type.replace("_", " ")}
                      <span className={`rounded-full px-2 py-0.5 font-medium ${STATUS_BADGE[p.status] ?? "bg-slate-100 text-slate-500"}`}>
                        {STATUS_LABEL[p.status] ?? p.status}
                      </span>
                    </p>
                    {NEXT[p.status] && (
                      <div className="mt-1 flex gap-2">
                        <button onClick={() => transition.mutate({ id: p.id, to: NEXT[p.status]!.to })} className="text-xs font-semibold text-brand hover:underline">{NEXT[p.status]!.label}</button>
                        <button onClick={() => transition.mutate({ id: p.id, to: "rejected" })} className="text-xs font-semibold text-rose-500 hover:underline">Reject</button>
                      </div>
                    )}
                  </div>
                  <span className="text-sm font-bold text-emerald-600">{formatMoney(p.net_amount, p.currency)}</span>
                </div>
              ))}
              {payoutList.data?.results.length === 0 && <p className="text-sm text-slate-400">No payouts yet.</p>}
            </div>
            <Link to="/teachers/new" className="mt-4 block text-sm font-semibold text-brand hover:underline">Add teacher →</Link>
          </div>
        </div>
      </div>

      {/* Payments made (processed payouts) */}
      <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-900">Payments Made</h3>
          <span className="text-sm text-slate-400">{paidCount} paid · {formatMoney(paidTotal.toFixed(2))}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2 font-semibold">Teacher</th>
                <th className="px-4 py-2 font-semibold">Period</th>
                <th className="px-4 py-2 font-semibold">Type</th>
                <th className="px-4 py-2 font-semibold">Present / Absent</th>
                <th className="px-4 py-2 font-semibold">Method</th>
                <th className="px-4 py-2 font-semibold">Reference</th>
                <th className="px-4 py-2 text-right font-semibold">Net Paid</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {paidPayouts.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-4 py-2 font-medium text-slate-800">{p.teacher_name}</td>
                  <td className="px-4 py-2 text-slate-600">{p.pay_period}</td>
                  <td className="px-4 py-2 capitalize text-slate-600">{p.pay_type.replace("_", " ")}</td>
                  <td className="px-4 py-2 text-slate-600">{p.days_present ?? "—"} / {p.days_absent ?? "—"}</td>
                  <td className="px-4 py-2 capitalize text-slate-600">{(p.payment_method || "—").replace("_", " ")}</td>
                  <td className="px-4 py-2 text-slate-600">{p.payment_reference || "—"}</td>
                  <td className="px-4 py-2 text-right font-semibold text-emerald-600">{formatMoney(p.net_amount, p.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {paidPayouts.length === 0 && <p className="px-4 py-4 text-slate-400">No payments made yet. Submit a payout and mark it as paid.</p>}
        </div>
      </div>
    </div>
  );
}
