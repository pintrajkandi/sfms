import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { classes, students } from "@/api/resources";
import { Button, Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { DatePicker } from "@/components/DatePicker";
import { log } from "@/lib/logger";

const DRAFT_KEY = "sfms:student-draft";

const EMPTY = {
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "",
  email: "",
  phone: "",
  address_line: "",
  address_city: "",
  address_state: "",
  address_pin: "",
  guardian_name: "",
  guardian_relation: "",
  guardian_phone: "",
  guardian_email: "",
  grade: "",
  section: "",
  enrollment_date: "",
  status: "active",
  previous_school: "",
  notes: "",
};
type Form = typeof EMPTY;

const onlyDigits = (v: string) => v.replace(/\D/g, "").slice(0, 10);

type IconProps = { className?: string };
const PersonIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 20a8 8 0 0 1 16 0" /></svg>
);
const ContactIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="M6 16a3 3 0 0 1 6 0M15 9h3M15 13h3" /></svg>
);
const BookIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2V5Z" /><path d="M4 19a2 2 0 0 0 2 2h12" /></svg>
);

function FormSection({ icon, tint, title, subtitle, children }: {
  icon: React.ReactNode; tint: string; title: string; subtitle: string; children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${tint}`}>{icon}</span>
        <div>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

export function AddStudentPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const editing = Boolean(id);
  const [form, setForm] = useState<Form>({ ...EMPTY });
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [drafted, setDrafted] = useState(false);
  const photoRef = useRef<HTMLInputElement>(null);

  const set = (k: keyof Form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const { data: classList } = useQuery({ queryKey: ["classes"], queryFn: () => classes.list() });
  const sections = useMemo(
    () => classList?.results.find((c) => c.name === form.grade)?.sections ?? [],
    [classList, form.grade],
  );

  // Load an existing student for edit; else restore any saved draft.
  useEffect(() => {
    if (editing && id) {
      students.get(id).then((s) => {
        setForm({
          ...EMPTY,
          first_name: s.first_name, last_name: s.last_name,
          date_of_birth: s.date_of_birth ?? "", gender: s.gender,
          email: s.email, phone: s.phone, address_line: s.home_address,
          guardian_name: s.guardian_name, guardian_relation: s.guardian_relation,
          guardian_phone: s.guardian_phone, guardian_email: s.guardian_email,
          grade: s.grade, section: s.section, enrollment_date: s.enrollment_date ?? "",
          status: s.status, previous_school: s.previous_school, notes: s.notes,
        });
        if (s.photo) setPhotoPreview(s.photo);
      });
      return;
    }
    const raw = localStorage.getItem(DRAFT_KEY);
    if (raw) {
      try { setForm({ ...EMPTY, ...JSON.parse(raw) }); } catch { /* ignore */ }
    }
  }, [editing, id]);

  function pickPhoto(file: File) {
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  function validate(): boolean {
    const req: (keyof Form)[] = ["first_name", "last_name", "date_of_birth", "gender", "grade", "enrollment_date"];
    const next: Record<string, string> = {};
    req.forEach((k) => { if (!form[k]) next[k] = "Required"; });
    if (form.phone && form.phone.length !== 10) next.phone = "Enter 10 digits";
    if (form.guardian_phone && form.guardian_phone.length !== 10) next.guardian_phone = "Enter 10 digits";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function buildPayload() {
    const home_address = [
      form.address_line,
      form.address_city,
      form.address_state,
      form.address_pin && `PIN ${form.address_pin}`,
    ].filter(Boolean).join(", ");
    const { address_line, address_city, address_state, address_pin, ...rest } = form;
    void address_line; void address_city; void address_state; void address_pin;
    return Object.fromEntries(
      Object.entries({ ...rest, home_address }).filter(([, v]) => v !== ""),
    );
  }

  async function submit() {
    setError("");
    if (!validate()) return;
    setSaving(true);
    try {
      const payload = buildPayload();
      const saved = editing && id
        ? await students.update(id, payload)
        : await students.create(payload);
      if (photoFile) await students.uploadPhoto(saved.id, photoFile);
      if (!editing) localStorage.removeItem(DRAFT_KEY);
      log.info(editing ? "student updated" : "student added", { entity: saved.id, action: "save_student" });
      navigate(`/students/${saved.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        setErrors(err.body as Record<string, string>);
      }
      setError(err instanceof ApiError ? err.detail : "Could not save the student.");
    } finally {
      setSaving(false);
    }
  }

  function saveDraft() {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(form));
    setDrafted(true);
    setTimeout(() => setDrafted(false), 2500);
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">
            <Link to="/students" className="hover:text-brand">Students</Link> ›{" "}
            <span className="text-brand">{editing ? "Edit Student" : "Add New Student"}</span>
          </p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">{editing ? "Edit Student" : "Add New Student"}</h1>
          <p className="mt-1 text-slate-500">Fill in the details below.</p>
        </div>
        <Link to="/students" className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">← Back to Students</Link>
      </div>

      {error && <Toast tone="error" message={error} />}

      {/* Personal */}
      <FormSection icon={<PersonIcon className="h-5 w-5 text-brand" />} tint="bg-brand-light" title="Personal Information" subtitle="Basic student identity details">
        <div className="mb-5 flex items-center gap-4">
          <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-400">
            {photoPreview ? <img src={photoPreview} alt="preview" className="h-full w-full object-cover" /> : "📷"}
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">Student Photo</p>
            <p className="text-xs text-slate-500">JPG/PNG, max 2MB</p>
            <input ref={photoRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && pickPhoto(e.target.files[0])} />
            <button type="button" onClick={() => photoRef.current?.click()} className="mt-1 text-sm font-semibold text-brand hover:underline">⬆ Upload Photo</button>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <Labeled label="First name" required error={errors.first_name}>
            <TextInput value={form.first_name} onChange={(e) => set("first_name", e.target.value)} placeholder="e.g. Emma" />
          </Labeled>
          <Labeled label="Last name" required error={errors.last_name}>
            <TextInput value={form.last_name} onChange={(e) => set("last_name", e.target.value)} placeholder="e.g. Johnson" />
          </Labeled>
          <Labeled label="Date of birth" required error={errors.date_of_birth}>
            <DatePicker value={form.date_of_birth} onChange={(v) => set("date_of_birth", v)} minYear={1990} maxYear={new Date().getFullYear()} placeholder="Select birth date" />
          </Labeled>
          <Labeled label="Gender" required error={errors.gender}>
            <Select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </Select>
          </Labeled>
        </div>
      </FormSection>

      {/* Contact */}
      <FormSection icon={<ContactIcon className="h-5 w-5 text-emerald-600" />} tint="bg-emerald-50" title="Contact Information" subtitle="How to reach the student and guardian">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Labeled label="Email address (optional)" error={errors.email}>
            <TextInput type="email" value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="student@email.com" />
          </Labeled>
          <Labeled label="Phone number (10 digits)" error={errors.phone}>
            <TextInput inputMode="numeric" maxLength={10} value={form.phone} onChange={(e) => set("phone", onlyDigits(e.target.value))} placeholder="9876543210" />
          </Labeled>
        </div>

        {/* Address */}
        <div className="mt-5 rounded-xl bg-slate-50 p-4">
          <p className="mb-3 text-sm font-medium text-slate-700">Home address</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Labeled label="Address line" full>
              <TextArea rows={2} value={form.address_line} onChange={(e) => set("address_line", e.target.value)} placeholder="House / flat, street, area" />
            </Labeled>
            <Labeled label="City"><TextInput value={form.address_city} onChange={(e) => set("address_city", e.target.value)} placeholder="City" /></Labeled>
            <Labeled label="State"><TextInput value={form.address_state} onChange={(e) => set("address_state", e.target.value)} placeholder="State" /></Labeled>
            <Labeled label="PIN code"><TextInput inputMode="numeric" maxLength={6} value={form.address_pin} onChange={(e) => set("address_pin", e.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="560001" /></Labeled>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Labeled label="Parent / guardian name">
            <TextInput value={form.guardian_name} onChange={(e) => set("guardian_name", e.target.value)} placeholder="e.g. Robert Johnson" />
          </Labeled>
          <Labeled label="Guardian phone (10 digits)" error={errors.guardian_phone}>
            <TextInput inputMode="numeric" maxLength={10} value={form.guardian_phone} onChange={(e) => set("guardian_phone", onlyDigits(e.target.value))} placeholder="9876543210" />
          </Labeled>
        </div>
      </FormSection>

      {/* Academic */}
      <FormSection icon={<BookIcon className="h-5 w-5 text-brand" />} tint="bg-brand-light" title="Academic Information" subtitle="Class, section and enrollment">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <Labeled label="Class" required error={errors.grade}>
            <Select value={form.grade} onChange={(e) => { set("grade", e.target.value); set("section", ""); }}>
              <option value="">Select class</option>
              {classList?.results.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
            </Select>
            {classList && classList.results.length === 0 && (
              <p className="mt-1 text-xs text-amber-600">No classes yet — add them in <Link to="/classes" className="underline">Classes &amp; Sections</Link>.</p>
            )}
          </Labeled>
          <Labeled label="Section">
            <Select value={form.section} onChange={(e) => set("section", e.target.value)} disabled={!form.grade}>
              <option value="">{form.grade ? "Select section" : "Pick a class first"}</option>
              {sections.map((s) => <option key={s.id} value={s.name}>{s.name}</option>)}
            </Select>
          </Labeled>
          <Labeled label="Enrollment date" required error={errors.enrollment_date}>
            <DatePicker value={form.enrollment_date} onChange={(v) => set("enrollment_date", v)} minYear={2015} placeholder="Select date" />
          </Labeled>
          <Labeled label="Status">
            <Select value={form.status} onChange={(e) => set("status", e.target.value)}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="graduated">Graduated</option>
              <option value="transferred">Transferred</option>
              <option value="suspended">Suspended</option>
            </Select>
          </Labeled>
          <Labeled label="Previous school">
            <TextInput value={form.previous_school} onChange={(e) => set("previous_school", e.target.value)} placeholder="e.g. Westview High School" />
          </Labeled>
          <Labeled label="Notes" full>
            <TextArea value={form.notes} onChange={(e) => set("notes", e.target.value)} placeholder="Any special notes or additional information…" />
          </Labeled>
        </div>
      </FormSection>

      <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm sm:flex-row sm:justify-between">
        <p className="text-sm text-slate-500">{drafted ? "✓ Draft saved" : "Fields marked with * are required"}</p>
        <div className="flex gap-2">
          <Button type="button" variant="ghost" onClick={() => navigate("/students")}>Cancel</Button>
          {!editing && <Button type="button" variant="ghost" onClick={saveDraft}>Save Draft</Button>}
          <Button type="button" onClick={submit} disabled={saving}>
            {saving ? "Saving…" : editing ? "Save changes" : "＋ Add Student"}
          </Button>
        </div>
      </div>
    </div>
  );
}
