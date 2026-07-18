import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "@/api/auth";
import { ApiError } from "@/api/client";
import { AuthLayout, Field, inputClass, SubmitButton } from "./AuthLayout";

export function ResetPasswordScreen() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const invalidLink = !uid || !token;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await authApi.confirmPasswordReset(uid, token, password);
      setDone(true);
      setTimeout(() => navigate("/login"), 1800);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not reset your password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="mb-8">
        <h1 className="font-serif text-3xl text-slate-900">Choose a new password</h1>
        <p className="mt-2 text-slate-600">Enter a new password for your staff account.</p>
      </div>

      {invalidLink ? (
        <div className="rounded-md bg-rose-50 px-4 py-4 text-sm text-rose-700">
          This reset link is missing information. Please request a new one from{" "}
          <a href="/forgot-password" className="font-semibold underline">
            Reset your password
          </a>
          .
        </div>
      ) : done ? (
        <div className="rounded-md bg-emerald-50 px-4 py-4 text-sm text-emerald-800">
          Your password has been reset. Redirecting you to sign in…
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-6" noValidate>
          {error && (
            <div className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
          )}
          <Field label="New password" htmlFor="password">
            <input
              id="password"
              type="password"
              className={inputClass}
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          <Field label="Confirm new password" htmlFor="confirm">
            <input
              id="confirm"
              type="password"
              className={inputClass}
              placeholder="Re-enter password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </Field>
          <SubmitButton disabled={submitting}>
            {submitting ? "Saving…" : "Reset password"}
          </SubmitButton>
        </form>
      )}
    </AuthLayout>
  );
}
