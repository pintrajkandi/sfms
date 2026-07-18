import type { ReactNode } from "react";
import { BrandLogo, type Feature, FeaturePanel, LOGIN_FEATURES, ShieldCheckIcon } from "./ui";

/** Two-column auth shell: form on the left, green feature panel on the right. */
export function AuthLayout({
  children,
  features = LOGIN_FEATURES,
}: {
  children: ReactNode;
  features?: Feature[];
}) {
  return (
    <div className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-2">
      <div className="flex flex-col justify-center px-6 py-10 sm:px-12 lg:px-16">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-10">
            <BrandLogo />
          </div>
          {children}
          <p className="mt-10 flex items-center justify-center gap-2 text-sm text-slate-400">
            <ShieldCheckIcon className="h-4 w-4" />
            Your data is secure and encrypted
          </p>
        </div>
      </div>
      <aside className="hidden bg-brand-light/60 lg:block">
        <FeaturePanel features={features} />
      </aside>
    </div>
  );
}

export function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-semibold text-slate-800">
        {label}
      </label>
      {children}
      {error ? (
        <p className="text-sm text-rose-600">{error}</p>
      ) : (
        hint && <p className="text-sm text-slate-500">{hint}</p>
      )}
    </div>
  );
}

export const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 placeholder:text-slate-400 " +
  "focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand-ring/40";

export function SubmitButton({
  children,
  disabled,
  icon,
}: {
  children: ReactNode;
  disabled?: boolean;
  icon?: ReactNode;
}) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient py-3.5 text-center text-base font-semibold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {icon}
      {children}
    </button>
  );
}
