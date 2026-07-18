import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { students } from "@/api/resources";
import { Button, Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { log } from "@/lib/logger";

const DRAFT_KEY = "sfms:student-draft";

const GRADES = [
  "Nursery", "LKG", "UKG",
  ...Array.from({ length: 12 }, (_, i) => `Grade ${i + 1}`),
];

const EMPTY = {
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "",
  nationality: "",
  email: "",
  phone: "",
  home_address: "",
  guardian_name: "",
  guardian_phone: "",
  grade: "",
  section: "",
  enrollment_date: "",
  program: "",
  status: "active",
  previous_school: "",
  notes: "",
};

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

function Section({
  icon,
  tint,
  title,
  subtitle,
  children,
}: {
  icon: React.ReactNode;
  tint: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
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
  const [form, setForm] = useState({ ...EMPTY });
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [drafted, setDrafted] = useState(false);
  const photoRef = useRef<HTMLInputElement>(null);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  // Restore a saved draft on mount.
  useEffect(() => {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (raw) {
      try {
        setForm({ ...EMPTY, ...JSON.parse(raw) });
      } catch {
        /* ignore malformed draft */
      }
    }
  }, []);

  function pickPhoto(file: File) {
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  function saveDraft() {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(form));
    setDrafted(true);
    setTimeout(() => setDrafted(false), 2500);
  }

  function validate(): boolean {
    const req: (keyof typeof form)[] = ["first_name", "last_name", "date_of_birth", "gender", "email", "grade", "enrollment_date"];
    const next: Record<string, string> = {};
    req.forEach((k) => {
      if (!form[k]) next[k] = "Required";
    });
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function submit() {
    setError("");
    if (!validate()) return;
    setSaving(true);
    try {
      const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ""));
      const created = await students.create(payload);
      if (photoFile) await students.uploadPhoto(created.id, photoFile);
      localStorage.removeItem(DRAFT_KEY);
      log.info("student added", { entity: created.id, action: "add_student" });
      navigate(`/students/${created.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        setErrors(err.body as Record<string, string>);
      }
      setError(err instanceof ApiError ? err.detail : "Could not save the student.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">
            <Link to="/students" className="hover:text-brand">Students</Link> ›{" "}
            <span className="text-brand">Add New Student</span>
          </p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Add New Student</h1>
          <p className="mt-1 text-slate-500">Fill in the details below to register a new student.</p>
        </div>
        <Link to="/students" className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
          ← Back to Students
        </Link>
      </div>

      {error && <Toast tone="error" message={error} />}

      {/* Personal Information */}
      <Section icon={<PersonIcon className="h-5 w-5 text-brand" />} tint="bg-brand-light" title="Personal Information" subtitle="Basic student identity details">
        <div className="mb-5 flex items-center gap-4">
          <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-400">
            {photoPreview ? <img src={photoPreview} alt="preview" className="h-full w-full object-cover" /> : "📷"}
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">Student Photo</p>
            <p className="text-xs text-slate-500">Upload a profile picture (JPG, PNG max 2MB)</p>
            <input ref={photoRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && pickPhoto(e.target.files[0])} />
            <button type="button" onClick={() => photoRef.current?.click()} className="mt-1 text-sm font-semibold text-brand hover:underline">
              ⬆ Upload Photo
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <Labeled label="First name" required error={errors.first_name}>
            <TextInput placeholder="e.g. Emma" value={form.first_name} onChange={(e) => set("first_name", e.target.value)} />
          </Labeled>
          <Labeled label="Last name" required error={errors.last_name}>
            <TextInput placeholder="e.g. Johnson" value={form.last_name} onChange={(e) => set("last_name", e.target.value)} />
          </Labeled>
          <Labeled label="Date of birth" required error={errors.date_of_birth}>
            <TextInput type="date" value={form.date_of_birth} onChange={(e) => set("date_of_birth", e.target.value)} />
          </Labeled>
          <Labeled label="Gender" required error={errors.gender}>
            <Select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </Select>
          </Labeled>
          <Labeled label="Nationality">
            <TextInput placeholder="e.g. American" value={form.nationality} onChange={(e) => set("nationality", e.target.value)} />
          </Labeled>
          <Labeled label="Student ID">
            <TextInput placeholder="Auto-generated" disabled className="opacity-60" />
          </Labeled>
        </div>
      </Section>

      {/* Contact Information */}
      <Section icon={<ContactIcon className="h-5 w-5 text-emerald-600" />} tint="bg-emerald-50" title="Contact Information" subtitle="How to reach the student and their guardian">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Labeled label="Email address" required error={errors.email}>
            <TextInput type="email" placeholder="student@email.com" value={form.email} onChange={(e) => set("email", e.target.value)} />
          </Labeled>
          <Labeled label="Phone number">
            <TextInput placeholder="+1 (555) 000-0000" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          </Labeled>
          <Labeled label="Home address" full>
            <TextInput placeholder="Street address, city, state, zip code" value={form.home_address} onChange={(e) => set("home_address", e.target.value)} />
          </Labeled>
          <Labeled label="Parent / guardian name">
            <TextInput placeholder="e.g. Robert Johnson" value={form.guardian_name} onChange={(e) => set("guardian_name", e.target.value)} />
          </Labeled>
          <Labeled label="Guardian phone">
            <TextInput placeholder="+1 (555) 000-0000" value={form.guardian_phone} onChange={(e) => set("guardian_phone", e.target.value)} />
          </Labeled>
        </div>
      </Section>

      {/* Academic Information */}
      <Section icon={<BookIcon className="h-5 w-5 text-brand" />} tint="bg-brand-light" title="Academic Information" subtitle="Enrollment and course details">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <Labeled label="Grade / year" required error={errors.grade}>
            <Select value={form.grade} onChange={(e) => set("grade", e.target.value)}>
              <option value="">Select grade</option>
              {GRADES.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </Select>
          </Labeled>
          <Labeled label="Section / class">
            <TextInput placeholder="e.g. Section A" value={form.section} onChange={(e) => set("section", e.target.value)} />
          </Labeled>
          <Labeled label="Enrollment date" required error={errors.enrollment_date}>
            <TextInput type="date" value={form.enrollment_date} onChange={(e) => set("enrollment_date", e.target.value)} />
          </Labeled>
          <Labeled label="Program / major">
            <TextInput placeholder="e.g. Science & Technology" value={form.program} onChange={(e) => set("program", e.target.value)} />
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
            <TextInput placeholder="e.g. Westview High School" value={form.previous_school} onChange={(e) => set("previous_school", e.target.value)} />
          </Labeled>
          <Labeled label="Notes / additional information" full>
            <TextArea placeholder="Any special notes, medical conditions, or additional information…" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
          </Labeled>
        </div>
      </Section>

      {/* Footer action bar */}
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm sm:flex-row sm:justify-between">
        <p className="text-sm text-slate-500">
          {drafted ? "✓ Draft saved" : "Fields marked with * are required"}
        </p>
        <div className="flex gap-2">
          <Button type="button" variant="ghost" onClick={() => navigate("/students")}>Cancel</Button>
          <Button type="button" variant="ghost" onClick={saveDraft}>Save Draft</Button>
          <Button type="button" onClick={submit} disabled={saving}>
            {saving ? "Saving…" : "＋ Add Student"}
          </Button>
        </div>
      </div>
    </div>
  );
}
