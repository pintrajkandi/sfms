import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { ApiError, isTenantHost } from "@/api/client";
import { log } from "@/lib/logger";
import { auth0Enabled } from "@/lib/auth0";
import { Auth0Button } from "./Auth0Button";
import { AuthLayout, Field } from "./AuthLayout";
import { useAuth } from "./AuthProvider";
import {
  ArrowRightIcon,
  EyeIcon,
  HeadsetIcon,
  IconField,
  LockIcon,
  LOGIN_FEATURES,
  MailIcon,
  SchoolIcon,
} from "./ui";

export function LoginScreen() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const onTenant = isTenantHost();

  const [schoolCode, setSchoolCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [keepSignedIn, setKeepSignedIn] = useState(true);
  const [error, setError] = useState("");
  const [unverified, setUnverified] = useState(false);
  const [resent, setResent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (onTenant) {
      authApi
        .tenant()
        .then((t) => t.code && setSchoolCode(t.code))
        .catch(() => undefined);
    }
    const prefill = new URLSearchParams(window.location.search).get("email");
    if (prefill) setEmail(prefill);
  }, [onTenant]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setUnverified(false);
    setSubmitting(true);
    try {
      if (!onTenant) {
        const school = await authApi.resolveSchool(schoolCode);
        window.location.href = `${school.login_url}?email=${encodeURIComponent(email)}`;
        return;
      }
      await authApi.csrf();
      const user = await authApi.login({
        email,
        password,
        school_code: schoolCode,
        keep_signed_in: keepSignedIn,
      });
      setUser(user);
      log.info("signed in", { entity: user.id, action: "login" });
      navigate("/");
    } catch (err) {
      if (err instanceof ApiError) {
        const code = (err.body as { code?: string } | null)?.code;
        if (code === "email_unverified") setUnverified(true);
        setError(err.status === 404 ? "No school found for that code." : err.detail);
      } else {
        setError("Could not sign in. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function resend() {
    try {
      await authApi.resendVerification(email);
    } finally {
      setResent(true);
    }
  }

  return (
    <AuthLayout features={LOGIN_FEATURES}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">
          Welcome <span className="text-brand">back</span>
        </h1>
        <p className="mt-2 text-slate-500">Enter your school code and staff credentials to sign in.</p>
      </div>

      {error && (
        <div className="mb-6 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
          {unverified && !resent && (
            <button
              type="button"
              onClick={resend}
              className="ml-1 font-semibold underline"
            >
              Resend verification email
            </button>
          )}
          {resent && <span className="ml-1 font-medium">Verification email sent.</span>}
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-5" noValidate>
        <Field
          label="School code"
          htmlFor="school_code"
          hint="Enter the unique code provided by your school."
        >
          <IconField
            id="school_code"
            icon={<SchoolIcon />}
            placeholder="e.g. GHPS-2847"
            value={schoolCode}
            onChange={(e) => setSchoolCode(e.target.value.toUpperCase())}
            autoComplete="off"
          />
        </Field>

        {!onTenant && (
          <p className="-mt-2 text-sm text-slate-500">
            Don't know your school code?{" "}
            <Link to="/find-school" className="font-semibold text-brand hover:underline">
              Find your school
            </Link>
          </p>
        )}

        <Field label="Work email" htmlFor="email">
          <IconField
            id="email"
            type="email"
            icon={<MailIcon />}
            placeholder="you@school.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        <Field label="Password" htmlFor="password">
          <IconField
            id="password"
            type={showPassword ? "text" : "password"}
            icon={<LockIcon />}
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            trailing={
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                className="text-slate-400 hover:text-slate-700"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                <EyeIcon off={showPassword} />
              </button>
            }
          />
        </Field>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
              checked={keepSignedIn}
              onChange={(e) => setKeepSignedIn(e.target.checked)}
            />
            Keep me signed in
          </label>
          <a href="/forgot-password" className="text-sm font-semibold text-brand hover:underline">
            Forgot password?
          </a>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient py-3.5 text-base font-semibold text-white shadow-sm transition hover:opacity-95 disabled:opacity-50"
        >
          <LockIcon className="h-4 w-4" />
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <div className="my-6 flex items-center gap-4 text-sm text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />
        or
        <span className="h-px flex-1 bg-slate-200" />
      </div>

      {onTenant && auth0Enabled() && (
        <div className="mb-3">
          <Auth0Button />
        </div>
      )}

      <a
        href="/signup"
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
      >
        <HeadsetIcon className="h-4 w-4 text-brand" />
        New school onboarding? <span className="font-semibold text-brand">Talk to us</span>
        <ArrowRightIcon className="h-4 w-4 text-brand" />
      </a>
    </AuthLayout>
  );
}
