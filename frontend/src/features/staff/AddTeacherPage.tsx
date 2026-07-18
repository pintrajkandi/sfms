import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { teachers } from "@/api/resources";
import type { TeacherClass } from "@/api/types";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
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
  base_salary: "0.00", pay_frequency: "monthly", last_increment_date: "",
  increment_percent: "", next_increment_due: "", increment_reason: "",
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
  const [form, setForm] = useState({ ...EMPTY });
  const [classes, setClasses] = useState<TeacherClass[]>([{ class_name: "", role_in_class: "", academic_year: "2024-2025" }]);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const photoRef = useRef<HTMLInputElement>(null);
  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  function pickPhoto(file: File) {
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  function setClass(i: number, k: keyof TeacherClass, v: string) {
    setClasses((cs) => cs.map((c, j) => (j === i ? { ...c, [k]: v } : c)));
  }

  function validate(): boolean {
    const req: (keyof typeof form)[] = ["first_name", "last_name", "email", "employee_id", "joining_date", "base_salary", "increment_percent"];
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
      const created = await teachers.create(payload);
      if (photoFile) await teachers.uploadPhoto(created.id, photoFile);
      log.info("teacher added", { entity: created.id, action: "add_teacher" });
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
            <h1 className="text-2xl font-bold">Add New Teacher</h1>
            <p className="text-sm text-white/80">Fill in the details to register a new teacher.</p>
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
              <Labeled label="Email address" required error={errors.email}>
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
                <TextInput type="date" value={form.date_of_birth} onChange={(e) => set("date_of_birth", e.target.value)} />
              </Labeled>
              <Labeled label="Address" full>
                <TextInput placeholder="Street, City, State, ZIP" value={form.address} onChange={(e) => set("address", e.target.value)} />
              </Labeled>
            </div>
          </Section>

          <Section icon={<CaseIcon className="h-5 w-5 text-emerald-600" />} tint="bg-emerald-50" title="Professional Details">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Employee ID" required error={errors.employee_id}>
                <TextInput placeholder="e.g. TCH-2024-001" value={form.employee_id} onChange={(e) => set("employee_id", e.target.value)} />
              </Labeled>
              <Labeled label="Department">
                <TextInput placeholder="e.g. Mathematics" value={form.department} onChange={(e) => set("department", e.target.value)} />
              </Labeled>
              <Labeled label="Joining date" required error={errors.joining_date}>
                <TextInput type="date" value={form.joining_date} onChange={(e) => set("joining_date", e.target.value)} />
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

          <Section icon={<TrendIcon className="h-5 w-5 text-emerald-600" />} tint="bg-emerald-50" title="Salary & Increment">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Base salary" required error={errors.base_salary}>
                <TextInput placeholder="0.00" value={form.base_salary} onChange={(e) => set("base_salary", e.target.value)} />
              </Labeled>
              <Labeled label="Pay frequency">
                <Select value={form.pay_frequency} onChange={(e) => set("pay_frequency", e.target.value)}>
                  <option value="monthly">Monthly</option>
                  <option value="biweekly">Bi-weekly</option>
                  <option value="weekly">Weekly</option>
                  <option value="annual">Annual</option>
                </Select>
              </Labeled>
              <Labeled label="Last increment date">
                <TextInput type="date" value={form.last_increment_date} onChange={(e) => set("last_increment_date", e.target.value)} />
              </Labeled>
              <Labeled label="Increment %" required error={errors.increment_percent}>
                <TextInput type="number" placeholder="e.g. 10" value={form.increment_percent} onChange={(e) => set("increment_percent", e.target.value)} />
              </Labeled>
              <Labeled label="Next increment due">
                <TextInput type="date" value={form.next_increment_due} onChange={(e) => set("next_increment_due", e.target.value)} />
              </Labeled>
              <Labeled label="Increment reason">
                <TextInput placeholder="e.g. Annual review, promotion" value={form.increment_reason} onChange={(e) => set("increment_reason", e.target.value)} />
              </Labeled>
            </div>
          </Section>
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
            <h2 className="mb-4 text-base font-semibold text-slate-900">Quick Actions</h2>
            <div className="space-y-2">
              <button type="button" onClick={submit} disabled={saving} className="w-full rounded-lg bg-brand-gradient py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
                {saving ? "Saving…" : "＋ Add Teacher"}
              </button>
              <button type="button" disabled className="w-full cursor-not-allowed rounded-lg border border-slate-200 py-2.5 text-sm font-medium text-slate-400">
                Edit Teacher
              </button>
              <button type="button" disabled className="w-full cursor-not-allowed rounded-lg border border-slate-200 py-2.5 text-sm font-medium text-slate-400">
                Remove Teacher
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
