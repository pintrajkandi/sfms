import { Link } from "react-router-dom";

const FEATURES: { icon: string; title: string; body: string }[] = [
  { icon: "🧾", title: "Fees & Invoicing", body: "Fee structures, GST e-invoices with IRN/QR, installments, discounts & scholarships." },
  { icon: "💳", title: "Collections", body: "Cash, cards, UPI & Razorpay online payments, UPI Autopay mandates, auto-reconciliation." },
  { icon: "🔔", title: "Reminders", body: "Staged WhatsApp & SMS reminders, a parent portal, and digitally-signed receipts." },
  { icon: "📊", title: "Finance & Payroll", body: "Income vs expense, staff payroll with PF/ESI/TDS & payslips, Tally/Zoho/QuickBooks export." },
  { icon: "🤖", title: "Predictive AI", body: "Risk-scores students likely to fall behind and an AI assistant to guide collections." },
  { icon: "🔒", title: "Secure & Compliant", body: "Per-school isolation, granular roles, audit trail, DPDP/FERPA/GDPR tools, verified backups." },
];

const STEPS = ["Sign up your school", "Set up fees & students", "Collect & reconcile", "Report & relax"];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-slate-800">
      {/* Nav */}
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient font-bold text-white">₹</span>
          <span className="font-semibold tracking-wide">FEE LEDGER</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">Sign in</Link>
          <Link to="/signup" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm">Get started</Link>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-brand-gradient text-white">
        <div className="mx-auto max-w-6xl px-6 py-20 text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-white/70">School Fee Management System</p>
          <h1 className="mx-auto mt-3 max-w-3xl text-4xl font-bold leading-tight sm:text-5xl">
            Run your school's finances end-to-end — fees, payments, payroll & compliance.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-white/85">
            A multi-tenant platform built for schools: collect fees online, remind parents automatically,
            e-invoice for GST, run payroll, and see who's at risk — all in one place.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link to="/signup" className="rounded-xl bg-white px-6 py-3 font-semibold text-slate-900 shadow hover:bg-slate-100">Start free trial</Link>
            <Link to="/login" className="rounded-xl border border-white/40 px-6 py-3 font-semibold text-white hover:bg-white/10">Sign in to your school</Link>
          </div>
          <p className="mt-4 text-xs text-white/60">No credit card required · Each school gets its own isolated workspace</p>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="text-center text-2xl font-bold text-slate-900">Everything the front office & accountant need</h2>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-2xl border border-slate-100 p-6 shadow-sm">
              <div className="text-3xl">{f.icon}</div>
              <h3 className="mt-3 text-lg font-semibold text-slate-900">{f.title}</h3>
              <p className="mt-1 text-sm text-slate-500">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Steps */}
      <section className="bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-center text-2xl font-bold text-slate-900">Live in four steps</h2>
          <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-4">
            {STEPS.map((s, i) => (
              <div key={s} className="rounded-2xl bg-white p-6 text-center shadow-sm">
                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-brand-gradient font-bold text-white">{i + 1}</div>
                <p className="mt-3 text-sm font-medium text-slate-700">{s}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 py-20 text-center">
        <h2 className="text-3xl font-bold text-slate-900">Ready to simplify fee management?</h2>
        <p className="mt-3 text-slate-500">Onboard your school in minutes.</p>
        <Link to="/signup" className="mt-6 inline-block rounded-xl bg-brand-gradient px-8 py-3 font-semibold text-white shadow">Get started free</Link>
      </section>

      <footer className="border-t border-slate-100 py-8 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} Fee Ledger · School Fee Management System
      </footer>
    </div>
  );
}
