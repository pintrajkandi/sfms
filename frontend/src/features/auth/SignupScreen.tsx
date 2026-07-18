import { useMemo, useState } from "react";
import { authApi, type SchoolRef } from "@/api/auth";
import { ApiError } from "@/api/client";
import { log } from "@/lib/logger";
import { AuthLayout, Field } from "./AuthLayout";
import {
  CheckIcon,
  EyeIcon,
  GlobeIcon,
  IconField,
  LockIcon,
  MailIcon,
  SchoolIcon,
  SIGNUP_FEATURES,
  UserIcon,
} from "./ui";

type Errors = Partial<Record<string, string>>;

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 63);
}

const RULES = [
  { key: "len", label: "8+ characters", test: (p: string) => p.length >= 8 },
  { key: "num", label: "One number", test: (p: string) => /[0-9]/.test(p) },
  { key: "upper", label: "One uppercase", test: (p: string) => /[A-Z]/.test(p) },
  { key: "special", label: "One special character", test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

export function SignupScreen() {
  const [form, setForm] = useState({
    school_name: "",
    slug: "",
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
    agree_terms: false,
  });
  const [slugEdited, setSlugEdited] = useState(false);
  const [show, setShow] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState<SchoolRef | null>(null);

  const ruleState = useMemo(() => RULES.map((r) => ({ ...r, ok: r.test(form.password) })), [form.password]);
  const passwordStrong = ruleState.every((r) => r.ok);
  const canSubmit =
    form.school_name && form.slug && form.full_name && form.email && passwordStrong &&
    form.password === form.confirm_password && form.agree_terms;

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    if (form.password !== form.confirm_password) {
      setErrors({ confirm_password: "Passwords do not match" });
      return;
    }
    setSubmitting(true);
    try {
      const { confirm_password, ...rest } = form;
      const school = await authApi.signup({ ...rest, confirm_password, agree_terms: true });
      log.info("school account created", { entity: school.school_code, action: "signup" });
      setCreated(school);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setErrors({ form: err.detail, slug: err.detail });
      } else {
        setErrors({ form: "Could not create your account. Please try again." });
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (created) {
    return (
      <AuthLayout features={SIGNUP_FEATURES}>
        <h1 className="text-3xl font-bold text-slate-900">Check your email 📧</h1>
        <p className="mt-3 text-slate-600">
          <strong>{created.school_name}</strong> is created. We sent a verification link to your
          email — <strong>confirm it to activate your account</strong>, then sign in with your
          school code{" "}
          <span className="rounded bg-brand-light px-2 py-0.5 font-mono text-brand-dark">
            {created.school_code}
          </span>
          .
        </p>
        <a
          href={created.login_url}
          className="mt-8 block w-full rounded-xl bg-brand-gradient py-3.5 text-center text-base font-semibold text-white hover:opacity-95"
        >
          Go to sign in
        </a>
        <p className="mt-4 text-center text-sm text-slate-500">{created.domain}</p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout features={SIGNUP_FEATURES}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">
          Create your <span className="text-brand">school's account</span>
        </h1>
        <p className="mt-2 flex items-center gap-2 text-slate-500">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-light text-brand">
            <CheckIcon />
          </span>
          You'll be the first admin — invite staff once you're in.
        </p>
      </div>

      {errors.form && (
        <div className="mb-6 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{errors.form}</div>
      )}

      <form onSubmit={onSubmit} className="space-y-5" noValidate>
        <Field label="School name" htmlFor="school_name" error={errors.school_name}>
          <IconField
            id="school_name"
            icon={<SchoolIcon />}
            placeholder="Greenfield High School"
            value={form.school_name}
            onChange={(e) => {
              set("school_name", e.target.value);
              if (!slugEdited) set("slug", slugify(e.target.value));
            }}
          />
        </Field>

        <Field
          label="Your web address"
          htmlFor="slug"
          error={errors.slug}
          hint="This is where your staff will sign in from. You can change it later."
        >
          <IconField
            id="slug"
            icon={<GlobeIcon />}
            placeholder="greenfield-high"
            value={form.slug}
            onChange={(e) => {
              setSlugEdited(true);
              set("slug", slugify(e.target.value));
            }}
            trailing={<span className="text-sm text-slate-500">.feeledger.app</span>}
          />
        </Field>

        <Field label="Your full name" htmlFor="full_name" error={errors.full_name}>
          <IconField
            id="full_name"
            icon={<UserIcon />}
            placeholder="Aditi Sharma"
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
          />
        </Field>

        <Field label="Work email" htmlFor="email" error={errors.email}>
          <IconField
            id="email"
            type="email"
            icon={<MailIcon />}
            placeholder="you@school.edu"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Password" htmlFor="password">
            <IconField
              id="password"
              type={show ? "text" : "password"}
              icon={<LockIcon />}
              placeholder="At least 8 characters"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              trailing={
                <button type="button" onClick={() => setShow((s) => !s)} className="text-slate-400 hover:text-slate-700">
                  <EyeIcon off={show} />
                </button>
              }
            />
          </Field>
          <Field label="Confirm password" htmlFor="confirm_password" error={errors.confirm_password}>
            <IconField
              id="confirm_password"
              type={showConfirm ? "text" : "password"}
              icon={<LockIcon />}
              placeholder="Re-enter password"
              value={form.confirm_password}
              onChange={(e) => set("confirm_password", e.target.value)}
              trailing={
                <button type="button" onClick={() => setShowConfirm((s) => !s)} className="text-slate-400 hover:text-slate-700">
                  <EyeIcon off={showConfirm} />
                </button>
              }
            />
          </Field>
        </div>

        <div className="rounded-xl bg-slate-50 px-4 py-3">
          <p className="mb-2 text-sm font-medium text-slate-600">Password should include:</p>
          <ul className="grid grid-cols-2 gap-2 text-sm">
            {ruleState.map((r) => (
              <li key={r.key} className={`flex items-center gap-2 ${r.ok ? "text-brand" : "text-slate-400"}`}>
                <span className={`flex h-4 w-4 items-center justify-center rounded-full ${r.ok ? "bg-brand text-white" : "bg-slate-200 text-white"}`}>
                  <CheckIcon />
                </span>
                {r.label}
              </li>
            ))}
          </ul>
        </div>

        <label className="flex items-start gap-3 text-sm text-slate-700">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
            checked={form.agree_terms}
            onChange={(e) => set("agree_terms", e.target.checked)}
          />
          <span>
            I agree to the <a href="#" className="font-semibold text-brand hover:underline">Terms of Service</a> and{" "}
            <a href="#" className="font-semibold text-brand hover:underline">Privacy Policy</a>.
          </span>
        </label>

        <button
          type="submit"
          disabled={!canSubmit || submitting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient py-3.5 text-base font-semibold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <UserIcon className="h-4 w-4" />
          {submitting ? "Creating…" : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
