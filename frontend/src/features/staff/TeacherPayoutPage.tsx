import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "@/api/client";
import { payouts, teachers } from "@/api/resources";
import type { Payout, PayoutStatus, Teacher } from "@/api/types";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";

const readonly = "bg-slate-50 text-slate-600";

const NEXT: Partial<Record<PayoutStatus, { to: PayoutStatus; label: string }>> = {
  submitted: { to: "hod_approved", label: "HOD approve" },
  hod_approved: { to: "finance_approved", label: "Finance approve" },
  finance_approved: { to: "processed", label: "Process" },
};

const STEPS: { key: PayoutStatus; label: string; sub: string }[] = [
  { key: "submitted", label: "Form Submitted", sub: "Completed by Admin" },
  { key: "hod_approved", label: "HOD Review", sub: "Awaiting approval" },
  { key: "finance_approved", label: "Finance Review", sub: "Pending" },
  { key: "processed", label: "Payment Processed", sub: "Pending" },
];

const q = (v: string) => (Number.parseFloat(v || "0") || 0).toFixed(2);

const EMPTY = {
  teacher: "", pay_type: "", pay_period: "",
  base_amount: "0.00", bonus_amount: "0.00", deductions: "0.00",
  payment_method: "", notes: "",
};

export function TeacherPayoutPage() {
  const qc = useQueryClient();
  const teacherList = useQuery({ queryKey: ["teachers"], queryFn: () => teachers.list() });
  const payoutList = useQuery({ queryKey: ["payouts"], queryFn: () => payouts.list() });
  const [form, setForm] = useState({ ...EMPTY });
  const [error, setError] = useState("");
  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }));

  const selected: Teacher | undefined = teacherList.data?.results.find((t) => String(t.id) === form.teacher);
  const net = q(String(Number(q(form.base_amount)) + Number(q(form.bonus_amount)) - Number(q(form.deductions))));

  const totalBudget = (payoutList.data?.results ?? []).reduce((s, p) => s + Number(p.net_amount), 0);
  const pending = (payoutList.data?.results ?? []).filter((p) => !["processed", "rejected"].includes(p.status)).length;

  function pickTeacher(id: string) {
    const t = teacherList.data?.results.find((x) => String(x.id) === id);
    setForm((f) => ({ ...f, teacher: id, base_amount: t?.base_salary ?? f.base_amount }));
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
        payment_method: form.payment_method,
        notes: form.notes,
      }),
    onSuccess: () => {
      setError("");
      setForm({ ...EMPTY });
      qc.invalidateQueries({ queryKey: ["payouts"] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.detail : "Could not submit payout."),
  });

  const transition = useMutation({
    mutationFn: ({ id, to }: { id: number; to: string }) => payouts.transition(id, to),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payouts"] }),
    onError: (e) => setError(e instanceof ApiError ? e.detail : "Transition not allowed."),
  });

  const canSubmit = form.teacher && form.pay_type && form.pay_period && Number(form.base_amount) > 0;

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
              <Select value={form.teacher} onChange={(e) => pickTeacher(e.target.value)}>
                <option value="">Select teacher</option>
                {teacherList.data?.results.map((t) => (
                  <option key={t.id} value={t.id}>{t.full_name}</option>
                ))}
              </Select>
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
              <TextInput type="month" value={form.pay_period} onChange={(e) => set("pay_period", e.target.value)} />
            </Labeled>
            <Labeled label="Base amount ($)" required>
              <TextInput placeholder="0.00" value={form.base_amount} onChange={(e) => set("base_amount", e.target.value)} />
            </Labeled>
            <Labeled label="Bonus / incentive ($)">
              <TextInput placeholder="0.00" value={form.bonus_amount} onChange={(e) => set("bonus_amount", e.target.value)} />
            </Labeled>
            <Labeled label="Deductions ($)">
              <TextInput placeholder="0.00" value={form.deductions} onChange={(e) => set("deductions", e.target.value)} />
            </Labeled>
            <Labeled label="Payment method" required>
              <Select value={form.payment_method} onChange={(e) => set("payment_method", e.target.value)}>
                <option value="">Select method</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="cheque">Cheque</option>
                <option value="cash">Cash</option>
              </Select>
            </Labeled>
          </div>

          <p className="mb-3 mt-6 text-xs font-bold uppercase tracking-wide text-slate-400">Bank Details</p>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Labeled label="Bank name">
              <TextInput className={readonly} readOnly value={selected?.bank_name ?? ""} placeholder="e.g. Chase Bank" />
            </Labeled>
            <Labeled label="Account number">
              <TextInput className={readonly} readOnly value={selected?.bank_name ? "•••• •••• ••••" : ""} placeholder="XXXX XXXX XXXX" />
            </Labeled>
            <Labeled label="Routing / IFSC number" full>
              <TextInput className={readonly} readOnly value={selected?.routing_code ?? ""} placeholder="e.g. 021000021" />
            </Labeled>
            <Labeled label="Notes / remarks" full>
              <TextArea placeholder="Add any additional notes or justification for this payout…" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
            </Labeled>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button onClick={() => create.mutate()} disabled={!canSubmit || create.isPending} className="rounded-xl bg-brand-gradient px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
              ➤ {create.isPending ? "Submitting…" : "Submit Payout"}
            </button>
            <button onClick={() => setForm({ ...EMPTY })} className="rounded-xl border border-slate-200 px-6 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">
              💾 Save as Draft
            </button>
            <button onClick={() => setForm({ ...EMPTY })} className="rounded-xl border border-slate-200 px-4 py-2.5 text-slate-500 hover:bg-slate-50">↺</button>
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
            <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-slate-900">👥 Approval Steps</h3>
            <ol className="space-y-4">
              {STEPS.map((s, i) => (
                <li key={s.key} className="flex items-start gap-3">
                  <span className={`mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-xs ${i === 0 ? "bg-brand text-white" : i === 1 ? "bg-amber-100 text-amber-600" : "bg-slate-100 text-slate-400"}`}>
                    {i === 0 ? "✓" : i === 1 ? "◷" : "•"}
                  </span>
                  <div>
                    <p className={`text-sm font-semibold ${i <= 1 ? "text-slate-800" : "text-slate-400"}`}>{s.label}</p>
                    <p className="text-xs text-slate-400">{s.sub}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-slate-900">↻ Recent Payouts</h3>
            <div className="space-y-3">
              {payoutList.data?.results.slice(0, 5).map((p: Payout) => (
                <div key={p.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{p.teacher_name}</p>
                    <p className="text-xs capitalize text-slate-400">{p.pay_type.replace("_", " ")} · {p.status.replace("_", " ")}</p>
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
    </div>
  );
}
