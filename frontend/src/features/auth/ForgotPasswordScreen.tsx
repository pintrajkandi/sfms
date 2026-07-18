import { useState } from "react";
import { authApi } from "@/api/auth";
import { isTenantHost } from "@/api/client";
import { AuthLayout, Field, inputClass, SubmitButton } from "./AuthLayout";

export function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!isTenantHost()) {
      setError("Open this page from your school's address, e.g. yourschool.feeledger.app.");
      return;
    }
    setSubmitting(true);
    try {
      await authApi.requestPasswordReset(email);
      setSent(true);
    } catch {
      setSent(true); // never reveal whether the account exists
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="mb-8">
        <h1 className="font-serif text-3xl text-slate-900">Reset your password</h1>
        <p className="mt-2 text-slate-600">
          Enter your work email and we'll send you a link to set a new password.
        </p>
      </div>

      {sent ? (
        <div className="rounded-md bg-emerald-50 px-4 py-4 text-sm text-emerald-800">
          If <strong>{email}</strong> belongs to a staff account, a reset link is on its way.
          Check your inbox.
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-6" noValidate>
          {error && (
            <div className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
          )}
          <Field label="Work email" htmlFor="email">
            <input
              id="email"
              type="email"
              className={inputClass}
              placeholder="you@school.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <SubmitButton disabled={submitting}>
            {submitting ? "Sending…" : "Send reset link"}
          </SubmitButton>
        </form>
      )}

      <p className="mt-10 text-center text-sm text-slate-600">
        <a href="/login" className="font-semibold text-slate-900 hover:underline">
          Back to sign in
        </a>
      </p>
    </AuthLayout>
  );
}
