import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { expenses } from "@/api/resources";
import { DatePicker } from "@/components/DatePicker";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { log } from "@/lib/logger";

const DRAFT_KEY = "sfms:expense-draft";
const CATEGORIES = ["salaries", "utilities", "maintenance", "supplies", "transport", "events", "other"];
const METHODS = ["Cash", "Card", "Bank Transfer", "UPI", "Cheque", "Company Card"];
const COST_CENTERS = ["General", "Academics", "Sports", "Events", "Maintenance", "IT", "Administration"];

// Method-specific detail captured in `payment_reference`. Methods absent here
// (e.g. Cash) need no extra input.
const METHOD_DETAIL: Record<string, { label: string; placeholder: string; digitsOnly?: number }> = {
  Card: { label: "Card last 4 digits", placeholder: "e.g. 4242", digitsOnly: 4 },
  "Company Card": { label: "Card last 4 digits", placeholder: "e.g. 4242", digitsOnly: 4 },
  Cheque: { label: "Cheque number", placeholder: "e.g. 000123" },
  UPI: { label: "UPI ID", placeholder: "e.g. name@okbank" },
  "Bank Transfer": { label: "Voucher / UTR number", placeholder: "e.g. UTR0001234" },
};

const EMPTY = {
  title: "", category: "", expense_date: "",
  amount: "0.00", currency: "INR", payment_method: "", payment_reference: "", reimbursable: false,
  vendor: "", project_cost_center: "", notes: "",
};

function Section({ icon, tint, title, children }: { icon: React.ReactNode; tint: string; title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-dashed border-slate-200 py-6 first:border-t-0 first:pt-0">
      <div className="mb-4 flex items-center gap-3">
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${tint}`}>{icon}</span>
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      </div>
      {children}
    </div>
  );
}

export function SubmitExpensePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ ...EMPTY });
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [drafted, setDrafted] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }));

  useEffect(() => {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (raw) {
      try {
        setForm({ ...EMPTY, ...JSON.parse(raw) });
      } catch {
        /* ignore */
      }
    }
  }, []);

  const required = ["title", "category", "expense_date", "amount"] as const;
  const progress = Math.round((required.filter((k) => form[k]).length / required.length) * 100);

  function saveDraft() {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(form));
    setDrafted(true);
    setTimeout(() => setDrafted(false), 2500);
  }

  function validate(): boolean {
    const next: Record<string, string> = {};
    required.forEach((k) => !form[k] && (next[k] = "Required"));
    const detail = METHOD_DETAIL[form.payment_method];
    if (detail) {
      if (!form.payment_reference) next.payment_reference = "Required";
      else if (detail.digitsOnly && form.payment_reference.length !== detail.digitsOnly)
        next.payment_reference = `Enter ${detail.digitsOnly} digits`;
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function submit() {
    setError("");
    if (!validate()) return;
    setSaving(true);
    try {
      const created = await expenses.create(form);
      if (file) await expenses.uploadReceipt(created.id, file);
      localStorage.removeItem(DRAFT_KEY);
      log.info("expense submitted", { entity: created.id, action: "submit_expense" });
      navigate("/finance");
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") setErrors(err.body as Record<string, string>);
      setError(err instanceof ApiError ? err.detail : "Could not submit the expense.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-sm text-slate-400">🏠 / New Expense</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Submit Expense</h1>
        <p className="mt-1 text-slate-500">Fill in the details below to log a new expense entry.</p>
      </div>

      {error && <Toast tone="error" message={error} />}

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {/* Progress bar */}
        <div className="h-1.5 bg-slate-100">
          <div className="h-full bg-brand-gradient transition-all" style={{ width: `${progress}%` }} />
        </div>

        <div className="p-6">
          <Section icon={<span className="text-brand">ⓘ</span>} tint="bg-brand-light" title="Basic Information">
            <Labeled label="Expense title" required error={errors.title}>
              <TextInput placeholder="e.g. Team lunch at Olive Garden" value={form.title} onChange={(e) => set("title", e.target.value)} />
            </Labeled>
            <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Category" required error={errors.category}>
                <Select value={form.category} onChange={(e) => set("category", e.target.value)}>
                  <option value="">Select category</option>
                  {CATEGORIES.map((c) => <option key={c} value={c} className="capitalize">{c}</option>)}
                </Select>
              </Labeled>
              <Labeled label="Expense date" required error={errors.expense_date}>
                <DatePicker
                  value={form.expense_date}
                  onChange={(v) => set("expense_date", v)}
                  minYear={2015}
                  maxYear={new Date().getFullYear()}
                  placeholder="Select expense date"
                />
              </Labeled>
            </div>
          </Section>

          <Section icon={<span className="text-emerald-600">₹</span>} tint="bg-emerald-50" title="Amount & Payment">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <Labeled label="Amount (₹)" required error={errors.amount}>
                <TextInput placeholder="0.00" value={form.amount} onChange={(e) => set("amount", e.target.value)} />
              </Labeled>
              <Labeled label="Currency">
                <Select value={form.currency} onChange={(e) => set("currency", e.target.value)}>
                  <option value="INR">INR — Indian Rupee</option>
                </Select>
              </Labeled>
              <Labeled label="Payment method">
                <Select
                  value={form.payment_method}
                  onChange={(e) => {
                    // Switching method invalidates any previously entered detail.
                    setForm((f) => ({ ...f, payment_method: e.target.value, payment_reference: "" }));
                  }}
                >
                  <option value="">Select method</option>
                  {METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
                </Select>
              </Labeled>
            </div>
            {METHOD_DETAIL[form.payment_method] && (
              <div className="mt-5 sm:max-w-xs">
                <Labeled label={METHOD_DETAIL[form.payment_method].label} error={errors.payment_reference}>
                  <TextInput
                    placeholder={METHOD_DETAIL[form.payment_method].placeholder}
                    value={form.payment_reference}
                    inputMode={METHOD_DETAIL[form.payment_method].digitsOnly ? "numeric" : undefined}
                    maxLength={METHOD_DETAIL[form.payment_method].digitsOnly}
                    onChange={(e) => {
                      const cfg = METHOD_DETAIL[form.payment_method];
                      const v = cfg.digitsOnly ? e.target.value.replace(/\D/g, "").slice(0, cfg.digitsOnly) : e.target.value;
                      set("payment_reference", v);
                    }}
                  />
                </Labeled>
              </div>
            )}
            <label className="mt-4 flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
              <span>
                <span className="block text-sm font-medium text-slate-800">Reimbursable Expense</span>
                <span className="block text-xs text-slate-500">Mark if this expense needs to be reimbursed</span>
              </span>
              <input type="checkbox" className="h-6 w-6 rounded border-slate-300" checked={form.reimbursable} onChange={(e) => set("reimbursable", e.target.checked)} />
            </label>
          </Section>

          <Section icon={<span className="text-amber-500">▤</span>} tint="bg-amber-50" title="Additional Details">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Vendor / merchant">
                <TextInput placeholder="e.g. Amazon, Delta Airlines" value={form.vendor} onChange={(e) => set("vendor", e.target.value)} />
              </Labeled>
              <Labeled label="Project / cost center">
                <Select value={form.project_cost_center} onChange={(e) => set("project_cost_center", e.target.value)}>
                  <option value="">Assign to project</option>
                  {COST_CENTERS.map((p) => <option key={p} value={p}>{p}</option>)}
                </Select>
              </Labeled>
              <Labeled label="Notes / description" full>
                <TextArea placeholder="Add any additional context or notes about this expense…" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
              </Labeled>
            </div>
          </Section>

          <Section icon={<span className="text-purple-600">📎</span>} tint="bg-purple-50" title="Attach Receipt">
            <button type="button" onClick={() => fileRef.current?.click()} className="flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-8 text-slate-400 hover:border-brand">
              <span className="text-3xl">☁️</span>
              <span className="mt-1 text-sm font-semibold text-slate-700">Drop files here or click to browse</span>
              <span className="text-xs">Supports JPG, PNG, PDF — Max 10MB</span>
            </button>
            <input ref={fileRef} type="file" accept="image/*,application/pdf" className="hidden" onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])} />
            {file && (
              <div className="mt-3 flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-100 text-xs font-bold text-rose-600">FILE</span>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{file.name}</p>
                    <p className="text-xs text-slate-500">{Math.round(file.size / 1024)} KB · Ready to upload</p>
                  </div>
                </div>
                <button type="button" onClick={() => setFile(null)} className="text-slate-400 hover:text-rose-500">✕</button>
              </div>
            )}
          </Section>

          {/* Footer actions */}
          <div className="mt-6 flex flex-col gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <button type="button" onClick={saveDraft} className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              💾 {drafted ? "Draft saved" : "Save as Draft"}
            </button>
            <div className="flex gap-2">
              <button type="button" onClick={() => navigate("/finance")} className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                Cancel
              </button>
              <button type="button" onClick={submit} disabled={saving} className="rounded-xl bg-brand-gradient px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
                ➤ {saving ? "Submitting…" : "Submit Expense"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
