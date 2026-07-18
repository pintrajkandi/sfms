import type { ReactNode, SelectHTMLAttributes } from "react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}

export function SectionCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {description && <p className="text-sm text-slate-500">{description}</p>}
      </div>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">{children}</div>
    </section>
  );
}

export const fieldClass =
  "w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 " +
  "placeholder:text-slate-400 focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";

export function Labeled({
  label,
  required,
  error,
  full,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  full?: boolean;
  children: ReactNode;
}) {
  return (
    <div className={full ? "sm:col-span-2" : undefined}>
      <label className="mb-1.5 block text-sm font-medium text-slate-700">
        {label} {required && <span className="text-rose-500">*</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
    </div>
  );
}

export function TextInput({ className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${fieldClass} ${className}`} />;
}

export function TextArea({
  className = "",
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`${fieldClass} min-h-[96px] ${className}`} />;
}

export function Select({
  children,
  className = "",
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }) {
  return (
    <select {...props} className={`${fieldClass} ${className}`}>
      {children}
    </select>
  );
}

export function Button({
  children,
  variant = "primary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const base =
    "rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";
  const styles =
    variant === "primary"
      ? "bg-brand-gradient text-white shadow-sm hover:opacity-95"
      : "border border-slate-300 text-slate-700 hover:bg-slate-50";
  return (
    <button {...props} className={`${base} ${styles}`}>
      {children}
    </button>
  );
}

const STATUS_STYLES: Record<string, string> = {
  paid: "bg-emerald-50 text-emerald-700",
  processed: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  partial: "bg-sky-50 text-sky-700",
  overdue: "bg-rose-50 text-rose-700",
  rejected: "bg-rose-50 text-rose-700",
  submitted: "bg-slate-100 text-slate-600",
  draft: "bg-slate-100 text-slate-600",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${style}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export function Toast({ message, tone = "success" }: { message: string; tone?: "success" | "error" }) {
  const style = tone === "success" ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-700";
  return <div className={`rounded-lg px-4 py-3 text-sm ${style}`}>{message}</div>;
}
