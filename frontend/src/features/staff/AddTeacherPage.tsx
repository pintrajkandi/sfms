import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { departments, teachers } from "@/api/resources";
import type { TeacherClass } from "@/api/types";
import { DatePicker } from "@/components/DatePicker";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { log } from "@/lib/logger";

const STATUSES = [
  { value: "active", label: "Active", dot: "bg-emerald-500" },
  { value: "inactive", label: "Inactive", dot: "bg-slate-300" },
  { value: "on_leave", label: "On Leave", dot: "bg-brand" },
  { value: "available", label: "Available", dot: "bg-slate-300" },
];
const CLASSES = [...Array.from({ length: 12 }, (_, i) => `Grade ${i + 1}`)];
const ROLES = ["Class Teacher", "Subject Teacher", "Assistant Teacher", "Coordinator"];
const YEARS = ["2024-2025", "2025-2026", "2023-2024"];

const EMPTY = {
  first_name: "", last_name: "", email: "", phone: "", gender: "", date_of_birth: "",
  address: "", status: "active",
  employee_id: "", department: "", joining_date: "", employment_type: "",
  years_of_experience: "", qualification: "", bio: "",
  base_salary: "0.00", hra: "0.00", medical_allowance: "0.00", other_allowance: "0.00",
  pay_frequency: "monthly",
  pf_amount: "0.00", tds_amount: "0.00", other_deduction: "0.00",
  account_holder_name: "", bank_name: "", account_number: "", branch: "", ifsc_code: "",
};

type Icon = { className?: string };
const PersonIcon = ({ className = "h-5 w-5" }: Icon) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 20a8 8 0 0 1 16 0" /></svg>
);
const CaseIcon = ({ className = "h-5 w-5" }: Icon) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
);
const ScreenIcon = ({ className = "h-5 w-5" }: Icon) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 20h8M12 16v4" /></svg>
);
const TrendIcon = ({ className = "h-5 w-5" }: Icon) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 17l6-6 4 4 7-7M14 8h6v6" /></svg>
);

function Section({ icon, tint, title, action, children }: { icon: React.ReactNode; tint: string; title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${tint}`}>{icon}</span>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function AddTeacherPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const [form, setForm] = useState({ ...EMPTY });
  const [classes, setClasses] = useState<TeacherClass[]>([{ class_name: "", role_in_class: "", academic_year: "2024-2025" }]);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const photoRef = useRef<HTMLInputElement>(null);
  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const num = (v: string) => Number.parseFloat(v || "0") || 0;
  const netSalary = formatMoney(
    (num(form.base_salary) + num(form.hra) + num(form.medical_allowance) + num(form.other_allowance)
      - num(form.pf_amount) - num(form.tds_amount) - num(form.other_deduction)).toFixed(2),
  );

  const deptList = useQuery({ queryKey: ["departments"], queryFn: () => departments.list() });
  const teacherList = useQuery({ queryKey: ["teachers"], queryFn: () => teachers.list() });
  const existing = useQuery({
    queryKey: ["teacher", id],
    queryFn: () => teachers.get(id!),
    enabled: isEdit,
  });

  useEffect(() => {
    if (!existing.data) return;
    const t = existing.data as unknown as Record<string, unknown>;
    setForm((f) => {
      const next = { ...f };
      (Object.keys(EMPTY) as (keyof typeof EMPTY)[]).forEach((k) => {
        const v = t[k];
        if (v !== null && v !== undefined) next[k] = String(v);
      });
      return next;
    });
    const rows = (existing.data.classes ?? []) as TeacherClass[];
    if (rows.length) setClasses(rows.map((r) => ({ class_name: r.class_name, role_in_class: r.role_in_class ?? "", academic_year: r.academic_year ?? "2024-2025" })));
  }, [existing.data]);

  function pickPhoto(file: File) {
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  function setClass(i: number, k: keyof TeacherClass, v: string) {
    setClasses((cs) => cs.map((c, j) => (j === i ? { ...c, [k]: v } : c)));
  }

  function validate(): boolean {
    const req: (keyof typeof form)[] = ["first_name", "last_name"];
    const next: Record<string, string> = {};
    req.forEach((k) => !form[k] && (next[k] = "Required"));
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function submit() {
    setError("");
    if (!validate()) return;
    setSaving(true);
    try {
      const scalars = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== "")) as Record<string, unknown>;
      if (form.years_of_experience) scalars.years_of_experience = Number(form.years_of_experience);
      const payload = { ...scalars, classes: classes.filter((c) => c.class_name) };
      const saved = isEdit ? await teachers.update(id!, payload) : await teachers.create(payload);
      if (photoFile) await teachers.uploadPhoto(saved.id, photoFile);
      log.info(isEdit ? "teacher updated" : "teacher added", { entity: saved.id, action: isEdit ? "edit_teacher" : "add_teacher" });
      navigate("/payouts");
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") setErrors(err.body as Record<string, string>);
      setError(err instanceof ApiError ? err.detail : "Could not save the teacher.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Banner header */}
      <div className="flex flex-col gap-2 rounded-2xl bg-brand-gradient px-6 py-5 text-white sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate("/payouts")} className="text-sm font-medium text-white/80 hover:text-white">← Back</button>
          <div className="border-l border-white/30 pl-4">
            <h1 className="text-2xl font-bold">{isEdit ? "Edit Teacher" : "Add New Teacher"}</h1>
            <p className="text-sm text-white/80">{isEdit ? "Update the teacher's details." : "Fill in the details to register a new teacher."}</p>
          </div>
        </div>
        <span className="text-sm font-medium text-white/90">👥 Teacher Management</span>
      </div>

      {error && <Toast tone="error" message={error} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-6 lg:col-span-2">
          <Section icon={<PersonIcon className="h-5 w-5 text-brand" />} tint="bg-brand-light" title="Personal Information">
            <div className="mb-5 flex flex-col items-center">
              <button type="button" onClick={() => photoRef.current?.click()} className="relative">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-slate-50 text-slate-300">
                  {photoPreview ? <img src={photoPreview} alt="preview" className="h-full w-full object-cover" /> : <PersonIcon className="h-10 w-10" />}
                </div>
                <span className="absolute bottom-0 right-0 flex h-8 w-8 items-center justify-center rounded-full bg-brand text-white">📷</span>
              </button>
              <input ref={photoRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && pickPhoto(e.target.files[0])} />
              <p className="mt-2 text-xs text-slate-500">Upload profile photo (optional)</p>
            </div>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="First name" required error={errors.first_name}>
                <TextInput placeholder="e.g. Sarah" value={form.first_name} onChange={(e) => set("first_name", e.target.value)} />
              </Labeled>
              <Labeled label="Last name" required error={errors.last_name}>
                <TextInput placeholder="e.g. Johnson" value={form.last_name} onChange={(e) => set("last_name", e.target.value)} />
              </Labeled>
              <Labeled label="Email address" error={errors.email}>
                <TextInput type="email" placeholder="teacher@school.edu" value={form.email} onChange={(e) => set("email", e.target.value)} />
              </Labeled>
              <Labeled label="Phone number">
                <TextInput placeholder="+1 (555) 000-0000" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
              </Labeled>
              <Labeled label="Gender">
                <Select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </Select>
              </Labeled>
              <Labeled label="Date of birth">
                <DatePicker value={form.date_of_birth} onChange={(v) => set("date_of_birth", v)} minYear={1950} maxYear={new Date().getFullYear()} placeholder="Select birth date" />
              </Labeled>
              <Labeled label="Address" full>
                <TextInput placeholder="Street, City, State, ZIP" value={form.address} onChange={(e) => set("address", e.target.value)} />
              </Labeled>
            </div>
          </Section>

          <Section icon={<CaseIcon className="h-5 w-5 text-emerald-600" />} tint="bg-emerald-50" title="Professional Details">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Employee ID" error={errors.employee_id}>
                <TextInput className="bg-slate-50 text-slate-500" placeholder="Auto-generated on save" value={form.employee_id} readOnly />
              </Labeled>
              <Labeled label="Department">
                {deptList.data && deptList.data.results.length > 0 ? (
                  <Select value={form.department} onChange={(e) => set("department", e.target.value)}>
                    <option value="">Select department</option>
                    {deptList.data.results.map((d) => <option key={d.id} value={d.name}>{d.name}</option>)}
                  </Select>
                ) : (
                  <TextInput placeholder="Add departments in Settings → Departments" value={form.department} onChange={(e) => set("department", e.target.value)} />
                )}
              </Labeled>
              <Labeled label="Joining date" error={errors.joining_date}>
                <DatePicker value={form.joining_date} onChange={(v) => set("joining_date", v)} minYear={2000} placeholder="Select joining date" />
              </Labeled>
              <Labeled label="Employment type">
                <Select value={form.employment_type} onChange={(e) => set("employment_type", e.target.value)}>
                  <option value="">Select type</option>
                  <option value="full_time">Full-time</option>
                  <option value="part_time">Part-time</option>
                  <option value="contract">Contract</option>
                  <option value="visiting">Visiting</option>
                </Select>
              </Labeled>
              <Labeled label="Years of experience">
                <TextInput type="number" placeholder="e.g. 5" value={form.years_of_experience} onChange={(e) => set("years_of_experience", e.target.value)} />
              </Labeled>
              <Labeled label="Qualification">
                <TextInput placeholder="e.g. M.Ed, B.Sc" value={form.qualification} onChange={(e) => set("qualification", e.target.value)} />
              </Labeled>
              <Labeled label="Bio / about" full>
                <TextArea placeholder="Brief description about the teacher…" value={form.bio} onChange={(e) => set("bio", e.target.value)} />
              </Labeled>
            </div>
          </Section>

          <Section
            icon={<ScreenIcon className="h-5 w-5 text-brand" />}
            tint="bg-brand-light"
            title="Classes Assigned"
            action={
              <button type="button" onClick={() => setClasses((c) => [...c, { class_name: "", role_in_class: "", academic_year: "2024-2025" }])} className="text-sm font-semibold text-brand hover:underline">
                + Add Class
              </button>
            }
          >
            <div className="space-y-3">
              {classes.map((c, i) => (
                <div key={i} className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_1fr_auto]">
                  <Select value={c.class_name} onChange={(e) => setClass(i, "class_name", e.target.value)}>
                    <option value="">Select class</option>
                    {CLASSES.map((g) => <option key={g} value={g}>{g}</option>)}
                  </Select>
                  <Select value={c.role_in_class} onChange={(e) => setClass(i, "role_in_class", e.target.value)}>
                    <option value="">Select role</option>
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </Select>
                  <Select value={c.academic_year} onChange={(e) => setClass(i, "academic_year", e.target.value)}>
                    {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
                  </Select>
                  <button type="button" onClick={() => setClasses((cs) => cs.filter((_, j) => j !== i))} className="rounded-lg bg-rose-50 px-3 text-rose-500 hover:bg-rose-100" aria-label="Remove class">🗑</button>
                </div>
              ))}
            </div>
          </Section>

          <Section icon={<TrendIcon className="h-5 w-5 text-emerald-600" />} tint="bg-emerald-50" title="Salary Structure (monthly, ₹)">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-400">Earnings</p>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Basic" error={errors.base_salary}>
                <TextInput placeholder="0.00" value={form.base_salary} onChange={(e) => set("base_salary", e.target.value)} />
              </Labeled>
              <Labeled label="HRA">
                <TextInput placeholder="0.00" value={form.hra} onChange={(e) => set("hra", e.target.value)} />
              </Labeled>
              <Labeled label="Medical allowance">
                <TextInput placeholder="0.00" value={form.medical_allowance} onChange={(e) => set("medical_allowance", e.target.value)} />
              </Labeled>
              <Labeled label="Other allowance">
                <TextInput placeholder="0.00" value={form.other_allowance} onChange={(e) => set("other_allowance", e.target.value)} />
              </Labeled>
            </div>
            <p className="mb-3 mt-6 text-xs font-bold uppercase tracking-wide text-slate-400">Deductions</p>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <Labeled label="PF">
                <TextInput placeholder="0.00" value={form.pf_amount} onChange={(e) => set("pf_amount", e.target.value)} />
              </Labeled>
              <Labeled label="TDS">
                <TextInput placeholder="0.00" value={form.tds_amount} onChange={(e) => set("tds_amount", e.target.value)} />
              </Labeled>
              <Labeled label="Other deductions">
                <TextInput placeholder="0.00" value={form.other_deduction} onChange={(e) => set("other_deduction", e.target.value)} />
              </Labeled>
            </div>
            <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 text-sm">
              <span className="font-medium text-slate-600">Estimated net (monthly)</span>
              <span className="text-lg font-bold text-brand">{netSalary}</span>
            </div>
          </Section>

          <Section icon={<CaseIcon className="h-5 w-5 text-brand" />} tint="bg-brand-light" title="Bank Account Details">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Account holder name">
                <TextInput placeholder="e.g. Sarah Johnson" value={form.account_holder_name} onChange={(e) => set("account_holder_name", e.target.value)} />
              </Labeled>
              <Labeled label="Account number" error={errors.account_number}>
                <TextInput inputMode="numeric" placeholder="e.g. 50100123456789" value={form.account_number} onChange={(e) => set("account_number", e.target.value.replace(/\D/g, ""))} />
              </Labeled>
              <Labeled label="Bank name">
                <TextInput placeholder="e.g. HDFC Bank" value={form.bank_name} onChange={(e) => set("bank_name", e.target.value)} />
              </Labeled>
              <Labeled label="Branch">
                <TextInput placeholder="e.g. MG Road, Bengaluru" value={form.branch} onChange={(e) => set("branch", e.target.value)} />
              </Labeled>
              <Labeled label="IFSC code" full error={errors.ifsc_code}>
                <TextInput maxLength={11} placeholder="e.g. HDFC0001234" value={form.ifsc_code} onChange={(e) => set("ifsc_code", e.target.value.toUpperCase().slice(0, 11))} />
              </Labeled>
            </div>
          </Section>

          {/* Submit button at the end of the form */}
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <button type="button" onClick={() => navigate("/payouts")} className="rounded-xl border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50">
              Cancel
            </button>
            <button type="button" onClick={submit} disabled={saving} className="rounded-xl bg-brand-gradient px-8 py-3 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
              {saving ? "Saving…" : isEdit ? "✓ Save Changes" : "＋ Add Teacher"}
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-base font-semibold text-slate-900">Teacher Status</h2>
            <div className="grid grid-cols-2 gap-3">
              {STATUSES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => set("status", s.value)}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                    form.status === s.value ? "border-brand bg-brand-light font-semibold text-brand-dark" : "border-slate-200 text-slate-600"
                  }`}
                >
                  <span className={`h-2.5 w-2.5 rounded-full ${s.dot}`} />
                  {s.label}
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h2 className="mb-1 text-base font-semibold text-slate-900">Net salary</h2>
            <p className="text-xs text-slate-400">Earnings − deductions (monthly)</p>
            <p className="mt-3 text-2xl font-bold text-brand">{netSalary}</p>
          </section>

          <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">Teachers</h2>
              <span className="text-xs text-slate-400">{teacherList.data?.count ?? 0}</span>
            </div>
            <div className="max-h-80 space-y-1 overflow-y-auto">
              {teacherList.data?.results.map((t) => (
                <Link
                  key={t.id}
                  to={`/teachers/${t.id}/edit`}
                  className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-slate-50 ${String(t.id) === id ? "bg-brand-light" : ""}`}
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium text-slate-800">{t.full_name}</span>
                    <span className="block truncate text-xs text-slate-400">{t.employee_id}{t.department ? ` · ${t.department}` : ""}</span>
                  </span>
                  <span className="text-xs text-brand">Edit</span>
                </Link>
              ))}
              {teacherList.data?.results.length === 0 && <p className="px-3 py-2 text-sm text-slate-400">No teachers yet.</p>}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
