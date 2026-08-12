import { Link } from "react-router-dom";
import { MarketingLayout, CONTACT } from "./MarketingLayout";

const PILLARS: { icon: string; tint: string; title: string; body: string }[] = [
  {
    icon: "🔭",
    tint: "bg-indigo-100 text-indigo-600",
    title: "Our Vision",
    body: "To become the financial backbone of every school in India — making world-class accounting, fee management and financial insight accessible to institutions of every size.",
  },
  {
    icon: "🎯",
    tint: "bg-emerald-100 text-emerald-600",
    title: "Our Mission",
    body: "To free schools from manual, error-prone finance work — so administrators can spend less time on spreadsheets and more time on education, backed by accurate, real-time numbers.",
  },
  {
    icon: "💎",
    tint: "bg-amber-100 text-amber-600",
    title: "Our Core Values",
    body: "Trust with money, simplicity by design, security by default, and genuine care for the schools we serve. We treat every school's data as if it were our own.",
  },
];

const VALUES = [
  ["Integrity", "Every rupee is tracked, auditable and accurate. Money is not a place for guesswork."],
  ["Simplicity", "Powerful features that anyone on your staff can use — no accounting degree required."],
  ["Security", "Isolated data per school, encrypted storage and automatic daily backups."],
  ["Support", "Real humans who understand schools, ready to help when you need us."],
];

const WHY = [
  "Purpose-built for Indian schools — fees, payroll, GST, transport, hostel and more.",
  "All-in-one platform: replace 5+ disconnected tools with a single system.",
  "Your own secure school subdomain with fully isolated data.",
  "Automatic daily backups so your records are never lost.",
  "Reduce fee defaults with smart WhatsApp & SMS reminders.",
  "Transparent pricing — free to get started, with support that actually helps.",
];

function Check() {
  return (
    <svg className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" className="opacity-20" />
      <path d="M8 12.5l2.5 2.5 5-6" />
    </svg>
  );
}

export function AboutPage() {
  return (
    <MarketingLayout>
      {/* Intro */}
      <section className="bg-gradient-to-b from-indigo-50/50 to-white">
        <div className="mx-auto max-w-4xl px-6 py-16 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">About {CONTACT.brand}</p>
          <h1 className="mx-auto mt-4 max-w-3xl text-4xl font-extrabold leading-[1.15] text-slate-900 sm:text-5xl">
            India's Top{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">School Accounting</span>{" "}
            Software
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-500">
            {CONTACT.brand} is an all-in-one financial management platform built specifically for schools.
            From fee collection and receipts to payroll, expenses, inventory and complete accounting, we bring
            every part of your school's finances into one secure, easy-to-use system — trusted by institutions
            across the country to run their money with confidence.
          </p>
        </div>
      </section>

      {/* Vision / Mission / Core Values */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {PILLARS.map((p) => (
              <div key={p.title} className="rounded-2xl border border-slate-100 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
                <span className={`flex h-12 w-12 items-center justify-center rounded-xl text-2xl ${p.tint}`}>{p.icon}</span>
                <h2 className="mt-5 text-lg font-bold text-slate-900">{p.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">{p.body}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {VALUES.map(([title, body]) => (
              <div key={title} className="rounded-xl border border-slate-100 bg-slate-50 p-5">
                <h3 className="text-sm font-bold text-indigo-600">{title}</h3>
                <p className="mt-1.5 text-[13px] leading-relaxed text-slate-500">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="bg-gradient-to-b from-white to-slate-50 py-16">
        <div className="mx-auto max-w-4xl px-6">
          <p className="text-center text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Why Choose Us?</p>
          <h2 className="mx-auto mt-3 max-w-2xl text-center text-3xl font-bold text-slate-900 sm:text-4xl">
            Schools trust {CONTACT.brand} to run their finances
          </h2>
          <ul className="mx-auto mt-10 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
            {WHY.map((w) => (
              <li key={w} className="flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-4 text-sm text-slate-600 shadow-sm">
                <Check /> <span>{w}</span>
              </li>
            ))}
          </ul>

          <div className="mt-12 flex flex-wrap justify-center gap-3">
            <Link to="/signup" className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:opacity-95">
              Get Started Free
            </Link>
            <a href={`mailto:${CONTACT.email}`} className="rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              Talk to Us
            </a>
          </div>
        </div>
      </section>
    </MarketingLayout>
  );
}
