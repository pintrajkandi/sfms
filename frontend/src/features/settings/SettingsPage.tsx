import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { ApiError } from "@/api/client";
import { collections, settings, type SchoolSettings, type SettingsFileField } from "@/api/resources";
import { Card } from "@/components/Card";
import { Button, Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { AcademicYearTab } from "./AcademicYearTab";
import { ClassesPage } from "./ClassesPage";
import { DepartmentsTab } from "./DepartmentsTab";
import { FeeSetupPage } from "./FeeSetupPage";
import { SubscriptionTab } from "./SubscriptionTab";
import { PushToggle } from "./PushToggle";

const TABS = [
  "School Info",
  "Branding & Logos",
  "Invoice Settings",
  "Fee Setup",
  "Classes & Sections",
  "Departments",
  "Payroll",
  "Contact Details",
  "Academic Year",
  "Notifications",
  "Subscription",
  "Security",
] as const;
type Tab = (typeof TABS)[number];

const CURRENCIES = [["INR", "INR — Indian Rupee (₹)"]];
const COUNTRIES = ["India", "United States", "United Kingdom", "United Arab Emirates", "Singapore"];

const BLANK: Partial<SchoolSettings> = {
  name: "",
  school_type: "private",
  brand_color: "#4F46E5",
  invoice_prefix: "INV",
  starting_invoice_number: 1001,
  currency: "INR",
  default_tax_rate: "0",
  payment_due_days: 30,
  country: "India",
  notify_due_reminders: true,
  notify_overdue: true,
};

const FILE_KEYS: SettingsFileField[] = ["logo", "letterhead_logo", "favicon"];

export function SettingsPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("School Info");
  const [form, setForm] = useState<Partial<SchoolSettings>>(BLANK);
  const [id, setId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    settings
      .get()
      .then((res) => {
        if (res.results.length) {
          setForm(res.results[0]);
          setId(res.results[0].id);
        }
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  const set = <K extends keyof SchoolSettings>(k: K, v: SchoolSettings[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  async function save() {
    setSaving(true);
    setMsg("");
    setErr("");
    try {
      const payload = { ...form };
      FILE_KEYS.forEach((k) => delete payload[k]); // files are uploaded separately
      const saved = id ? await settings.update(id, payload) : await settings.create(payload);
      setId(saved.id);
      setForm(saved);
      setMsg("Settings saved.");
      qc.invalidateQueries({ queryKey: ["onboarding"] });
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Could not save settings.");
    } finally {
      setSaving(false);
    }
  }

  async function upload(field: SettingsFileField, file: File) {
    if (!id) {
      setErr("Save your school profile first, then upload logos.");
      return;
    }
    try {
      const saved = await settings.uploadFile(id, field, file);
      setForm((f) => ({ ...f, [field]: saved[field] }));
      setMsg("Image uploaded.");
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Upload failed.");
    }
  }

  if (loading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">School Settings</h1>
          <p className="text-sm text-slate-500">
            Manage your school profile, branding, and system preferences.
          </p>
        </div>
        <Button onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save changes"}
        </Button>
      </div>

      {!id && (
        <div className="rounded-xl bg-brand-light px-4 py-3 text-sm text-brand-dark">
          👋 Welcome! Complete your school profile to unlock the rest of YukiCares — enter your
          school name and save to continue.
        </div>
      )}
      {msg && <Toast message={msg} />}
      {err && <Toast tone="error" message={err} />}

      <div className="flex flex-col gap-6 lg:flex-row">
        <nav className="shrink-0 lg:w-56">
          <div className="overflow-hidden rounded-xl border border-slate-100">
            <div className="bg-brand-gradient px-4 py-3 text-xs font-semibold uppercase tracking-wide text-white">
              Configuration
            </div>
            <div className="space-y-0.5 bg-white p-2">
              {TABS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`w-full rounded-lg px-4 py-2.5 text-left text-sm font-medium ${
                    tab === t ? "bg-brand-light text-brand-dark" : "text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </nav>

        <Card className="flex-1">
          {tab === "School Info" && <SchoolInfo form={form} set={set} />}
          {tab === "Branding & Logos" && <Branding form={form} set={set} onUpload={upload} />}
          {tab === "Invoice Settings" && <Invoice form={form} set={set} />}
          {tab === "Fee Setup" && <FeeSetupPage embedded />}
          {tab === "Classes & Sections" && <ClassesPage embedded />}
          {tab === "Departments" && <DepartmentsTab />}
          {tab === "Payroll" && <Payroll form={form} set={set} />}
          {tab === "Contact Details" && <Contact form={form} set={set} />}
          {tab === "Academic Year" && <AcademicYearTab />}
          {tab === "Subscription" && <SubscriptionTab />}
          {tab === "Notifications" && <Notifications form={form} set={set} />}
          {tab === "Security" && <Security />}
        </Card>
      </div>
    </div>
  );
}

type SectionProps = {
  form: Partial<SchoolSettings>;
  set: <K extends keyof SchoolSettings>(k: K, v: SchoolSettings[K]) => void;
};

function Section({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <>
      <div className="mb-5">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-500">{subtitle}</p>
      </div>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">{children}</div>
    </>
  );
}

function SchoolInfo({ form, set }: SectionProps) {
  return (
    <Section title="School Information" subtitle="Basic details about your institution">
      <Labeled label="School name" required full>
        <TextInput value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} placeholder="Springfield Academy of Excellence" />
      </Labeled>
      <Labeled label="School type">
        <Select value={form.school_type ?? "private"} onChange={(e) => set("school_type", e.target.value)}>
          <option value="public">Public</option>
          <option value="private">Private</option>
          <option value="charter">Charter</option>
          <option value="international">International</option>
        </Select>
      </Labeled>
      <Labeled label="Registration number">
        <TextInput value={form.registration_number ?? ""} onChange={(e) => set("registration_number", e.target.value)} placeholder="REG-2024-0045781" />
      </Labeled>
      <Labeled label="Established year">
        <TextInput type="number" value={form.established_year ?? ""} onChange={(e) => set("established_year", e.target.value ? Number(e.target.value) : null)} placeholder="1998" />
      </Labeled>
      <Labeled label="Affiliation / board">
        <TextInput value={form.affiliation_board ?? ""} onChange={(e) => set("affiliation_board", e.target.value)} placeholder="CBSE" />
      </Labeled>
      <Labeled label="School tagline / motto" full>
        <TextInput value={form.tagline ?? ""} onChange={(e) => set("tagline", e.target.value)} placeholder="Inspiring Minds, Shaping Futures" />
      </Labeled>
    </Section>
  );
}

function UploadTile({
  title,
  hint,
  value,
  onPick,
}: {
  title: string;
  hint: string;
  value: string | null | undefined;
  onPick: (file: File) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-slate-200 p-5 text-center">
      <div className="mb-3 flex h-16 w-16 items-center justify-center overflow-hidden rounded-xl bg-brand-light">
        {value ? <img src={value} alt={title} className="h-full w-full object-contain" /> : <span className="text-2xl">🎓</span>}
      </div>
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      <p className="mt-0.5 text-xs text-slate-500">{hint}</p>
      <input ref={ref} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && onPick(e.target.files[0])} />
      <Button type="button" variant="ghost" onClick={() => ref.current?.click()}>
        Upload
      </Button>
    </div>
  );
}

function Branding({
  form,
  set,
  onUpload,
}: SectionProps & { onUpload: (field: SettingsFileField, file: File) => void }) {
  return (
    <Section title="Branding & Logos" subtitle="Upload your school logo and letterhead assets">
      <UploadTile title="School Logo" hint="Shown in navigation & app header · PNG/SVG · max 2MB" value={form.logo} onPick={(f) => onUpload("logo", f)} />
      <UploadTile title="Invoice Letterhead Logo" hint="Printed on invoices & reports · PNG · max 5MB" value={form.letterhead_logo} onPick={(f) => onUpload("letterhead_logo", f)} />
      <UploadTile title="Favicon" hint="ICO/PNG · 32×32 or 64×64" value={form.favicon} onPick={(f) => onUpload("favicon", f)} />
      <Labeled label="Brand color">
        <div className="flex items-center gap-3">
          <input type="color" className="h-11 w-14 rounded-lg border border-slate-300" value={form.brand_color ?? "#4F46E5"} onChange={(e) => set("brand_color", e.target.value)} />
          <TextInput value={form.brand_color ?? ""} onChange={(e) => set("brand_color", e.target.value)} />
        </div>
        <p className="mt-1 text-xs text-slate-500">Used in invoices and reports.</p>
      </Labeled>
    </Section>
  );
}

function Invoice({ form, set }: SectionProps) {
  const year = new Date().getFullYear();
  const seq = String(form.starting_invoice_number ?? 1001).padStart(4, "0");
  const preview = `${form.invoice_prefix || "INV"}-${year}-${seq}`;
  return (
    <Section title="Invoice Settings" subtitle="Configure invoice numbering and payment details">
      <Labeled label="Invoice prefix" required>
        <TextInput value={form.invoice_prefix ?? ""} onChange={(e) => set("invoice_prefix", e.target.value)} placeholder="INV" />
        <p className="mt-1 text-xs text-slate-500">Preview: <span className="font-mono text-slate-700">{preview}</span></p>
      </Labeled>
      <Labeled label="Starting invoice number">
        <TextInput type="number" value={form.starting_invoice_number ?? 1001} onChange={(e) => set("starting_invoice_number", Number(e.target.value))} />
      </Labeled>
      <Labeled label="Currency">
        <Select value={form.currency ?? "INR"} onChange={(e) => set("currency", e.target.value)}>
          {CURRENCIES.map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </Select>
      </Labeled>
      <Labeled label="Tax / GST number">
        <TextInput value={form.tax_gst_number ?? ""} onChange={(e) => set("tax_gst_number", e.target.value)} placeholder="27AAPCS1234A1Z5" />
      </Labeled>
      <Labeled label="Default tax rate (%)">
        <TextInput type="number" value={form.default_tax_rate ?? "0"} onChange={(e) => set("default_tax_rate", e.target.value)} />
      </Labeled>
      <Labeled label="Payment due days">
        <TextInput type="number" value={form.payment_due_days ?? 30} onChange={(e) => set("payment_due_days", Number(e.target.value))} />
      </Labeled>
      <Labeled label="Invoice footer note" full>
        <TextArea value={form.invoice_footer_note ?? ""} onChange={(e) => set("invoice_footer_note", e.target.value)} placeholder="Thank you for your payment." />
      </Labeled>
      <Labeled label="Bank account details (for invoices)" full>
        <TextArea value={form.bank_account_details ?? ""} onChange={(e) => set("bank_account_details", e.target.value)} placeholder="Bank: … | A/C No: … | IFSC: … | Branch: …" />
      </Labeled>
    </Section>
  );
}

function Contact({ form, set }: SectionProps) {
  return (
    <Section title="Contact Details" subtitle="Address, phone, email and social links">
      <Labeled label="Street address" required full>
        <TextInput value={form.street_address ?? ""} onChange={(e) => set("street_address", e.target.value)} placeholder="42, Knowledge Park, Near City Mall" />
      </Labeled>
      <Labeled label="City">
        <TextInput value={form.city ?? ""} onChange={(e) => set("city", e.target.value)} placeholder="Springfield" />
      </Labeled>
      <Labeled label="State / province">
        <TextInput value={form.state_province ?? ""} onChange={(e) => set("state_province", e.target.value)} placeholder="Maharashtra" />
      </Labeled>
      <Labeled label="PIN / ZIP code">
        <TextInput value={form.zip_code ?? ""} onChange={(e) => set("zip_code", e.target.value)} placeholder="411001" />
      </Labeled>
      <Labeled label="Country">
        <Select value={form.country ?? "India"} onChange={(e) => set("country", e.target.value)}>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </Select>
      </Labeled>
      <Labeled label="Primary phone" required>
        <TextInput value={form.primary_phone ?? ""} onChange={(e) => set("primary_phone", e.target.value)} placeholder="+91 98765 43210" />
      </Labeled>
      <Labeled label="Alternate phone">
        <TextInput value={form.alternate_phone ?? ""} onChange={(e) => set("alternate_phone", e.target.value)} placeholder="+91 20 1234 5678" />
      </Labeled>
      <Labeled label="Official email ID" required>
        <TextInput type="email" value={form.official_email ?? ""} onChange={(e) => set("official_email", e.target.value)} placeholder="info@school.edu" />
      </Labeled>
      <Labeled label="Accounts / billing email">
        <TextInput type="email" value={form.accounts_email ?? ""} onChange={(e) => set("accounts_email", e.target.value)} placeholder="accounts@school.edu" />
      </Labeled>
      <Labeled label="Website URL" full>
        <TextInput value={form.website_url ?? ""} onChange={(e) => set("website_url", e.target.value)} placeholder="https://www.school.edu" />
      </Labeled>
      <Labeled label="Facebook">
        <TextInput value={form.facebook ?? ""} onChange={(e) => set("facebook", e.target.value)} placeholder="facebook.com/school" />
      </Labeled>
      <Labeled label="Instagram">
        <TextInput value={form.instagram ?? ""} onChange={(e) => set("instagram", e.target.value)} placeholder="instagram.com/school" />
      </Labeled>
      <Labeled label="LinkedIn">
        <TextInput value={form.linkedin ?? ""} onChange={(e) => set("linkedin", e.target.value)} placeholder="linkedin.com/school" />
      </Labeled>
    </Section>
  );
}

function Notifications({ form, set }: SectionProps) {
  return (
    <Section title="Notifications" subtitle="Choose which automated reminders to send">
      <div className="sm:col-span-2 space-y-3">
        <label className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
          <span className="text-sm font-medium text-slate-800">Due-date reminders</span>
          <input type="checkbox" className="h-5 w-5 rounded border-slate-300" checked={!!form.notify_due_reminders} onChange={(e) => set("notify_due_reminders", e.target.checked)} />
        </label>
        <label className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
          <span className="text-sm font-medium text-slate-800">Overdue alerts</span>
          <input type="checkbox" className="h-5 w-5 rounded border-slate-300" checked={!!form.notify_overdue} onChange={(e) => set("notify_overdue", e.target.checked)} />
        </label>
        <PushToggle />
      </div>
    </Section>
  );
}

function Payroll({ form, set }: SectionProps) {
  return (
    <Section title="Payroll" subtitle="Statutory deduction rates used when running payroll (PF / ESI / TDS)">
      <Labeled label="PF rate (fraction, e.g. 0.12 = 12%)">
        <TextInput type="number" step="0.0001" value={form.payroll_pf_rate ?? "0.12"} onChange={(e) => set("payroll_pf_rate", e.target.value)} />
      </Labeled>
      <Labeled label="PF wage ceiling">
        <TextInput type="number" value={form.payroll_pf_ceiling ?? "15000"} onChange={(e) => set("payroll_pf_ceiling", e.target.value)} />
      </Labeled>
      <Labeled label="ESI employee rate (fraction, e.g. 0.0075)">
        <TextInput type="number" step="0.0001" value={form.payroll_esi_rate ?? "0.0075"} onChange={(e) => set("payroll_esi_rate", e.target.value)} />
      </Labeled>
      <Labeled label="ESI wage threshold">
        <TextInput type="number" value={form.payroll_esi_threshold ?? "21000"} onChange={(e) => set("payroll_esi_threshold", e.target.value)} />
      </Labeled>
      <Labeled label="Professional tax (flat)">
        <TextInput type="number" value={form.payroll_professional_tax ?? "200"} onChange={(e) => set("payroll_professional_tax", e.target.value)} />
      </Labeled>
    </Section>
  );
}

function Security() {
  const { data } = useQuery({ queryKey: ["signing-key"], queryFn: () => collections.signingKey() });
  return (
    <Section title="Security" subtitle="The public key used to verify your digitally-signed receipts">
      <div className="sm:col-span-2 space-y-2">
        <p className="text-sm text-slate-600">
          Receipts are signed with your school's private key ({data?.algorithm ?? "ed25519"}). Share this
          public key with anyone who needs to independently verify a receipt's authenticity.
        </p>
        <pre className="overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs text-slate-700">
{data?.public_pem ?? "Loading…"}
        </pre>
      </div>
    </Section>
  );
}
