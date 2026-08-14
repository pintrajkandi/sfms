import { useState } from "react";
import { Link } from "react-router-dom";
import { authApi, type SchoolRef } from "@/api/auth";
import { ApiError } from "@/api/client";
import { log } from "@/lib/logger";
import { AuthLayout, Field, inputClass, SubmitButton } from "./AuthLayout";
import { ArrowRightIcon, MailIcon, SchoolIcon } from "./ui";

export function FindSchoolScreen() {
  const [email, setEmail] = useState("");
  const [schools, setSchools] = useState<SchoolRef[] | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSchools(null);
    setSubmitting(true);
    try {
      const { schools } = await authApi.findSchool(email.trim());
      setSchools(schools);
      log.info("find-school lookup", { action: "find_school" });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Find your school</h1>
        <p className="mt-1 text-sm text-slate-500">
          Forgot your school name or code? Enter your email and we'll show the school(s) linked to it.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-5">
        <Field label="Email address" htmlFor="email">
          <div className="relative">
            <MailIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              id="email"
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@school.edu"
              className={`${inputClass} pl-11`}
            />
          </div>
        </Field>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        <SubmitButton disabled={submitting || !email.trim()} icon={<ArrowRightIcon />}>
          {submitting ? "Searching…" : "Find my school"}
        </SubmitButton>
      </form>

      {/* Results */}
      {schools !== null && (
        <div className="mt-8">
          {schools.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-center">
              <p className="text-sm text-slate-600">
                No school is linked to <span className="font-semibold">{email.trim()}</span>.
              </p>
              <p className="mt-1 text-sm text-slate-500">
                Check the email address, or ask your school administrator for your school code.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm font-semibold text-slate-800">
                {schools.length === 1 ? "We found your school:" : "We found these schools:"}
              </p>
              {schools.map((s) => (
                <div
                  key={s.slug}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-light">
                      <SchoolIcon className="h-5 w-5 text-brand" />
                    </span>
                    <div>
                      <p className="font-semibold text-slate-900">{s.school_name}</p>
                      <p className="text-xs text-slate-500">
                        Code {s.school_code} · {s.domain}
                      </p>
                    </div>
                  </div>
                  <a
                    href={s.login_url}
                    className="shrink-0 rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95"
                  >
                    Go to login
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <p className="mt-8 text-center text-sm text-slate-500">
        Remembered it?{" "}
        <Link to="/login" className="font-semibold text-brand hover:underline">
          Back to sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
