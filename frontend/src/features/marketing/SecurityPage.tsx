import { Link } from "react-router-dom";
import { MarketingLayout, CONTACT } from "./MarketingLayout";

const COMMITMENTS: { icon: string; tint: string; title: string; body: string }[] = [
  {
    icon: "🔒",
    tint: "bg-indigo-100 text-indigo-600",
    title: "Isolated by design",
    body: "Every school runs in its own private database space. Your students, fees and financial records are never mixed with — or visible to — any other school.",
  },
  {
    icon: "🔐",
    tint: "bg-emerald-100 text-emerald-600",
    title: "Encrypted",
    body: "All data is encrypted in transit (HTTPS) and encrypted at rest — on both the database and the backups. Nobody can read it off the wire or off the disk.",
  },
  {
    icon: "💾",
    tint: "bg-amber-100 text-amber-600",
    title: "Backed up nightly & verified",
    body: "We take an automatic backup every night, verify it can actually be restored, and store it securely off-site — so your records are never lost.",
  },
  {
    icon: "🇮🇳",
    tint: "bg-rose-100 text-rose-600",
    title: "Hosted in India",
    body: "Your data is stored in India, in line with the Digital Personal Data Protection (DPDP) Act — it stays in the country where your school operates.",
  },
  {
    icon: "🧭",
    tint: "bg-sky-100 text-sky-600",
    title: "You stay in control",
    body: "The data is yours. You can export everything or ask us to delete it at any time. We are only the processor that safeguards it on your behalf.",
  },
  {
    icon: "🕵️",
    tint: "bg-violet-100 text-violet-600",
    title: "Fully audited",
    body: "Every important action — who recorded a payment, who changed a record, who accessed what — is logged with a timestamp for a complete, trustworthy trail.",
  },
  {
    icon: "🚨",
    tint: "bg-orange-100 text-orange-600",
    title: "Breach-ready",
    body: "Our systems are monitored around the clock. If anything ever goes wrong, we have a defined process to contain it and notify affected schools promptly.",
  },
  {
    icon: "👤",
    tint: "bg-cyan-100 text-cyan-600",
    title: "Least-privilege access",
    body: "Access is role-based, and any support access to your school by our team is restricted, time-limited and recorded — never silent or unlimited.",
  },
];

const RIGHTS = [
  ["Access & portability", "Get a complete, machine-readable copy of everything held on a student, at any time."],
  ["Erasure", "Remove a student's personal details on request — while keeping the financial records legally required for audit."],
  ["Consent", "Record and withdraw consent for how a student's data is used."],
  ["Retention", "Personal data of students who have left is automatically minimised after your chosen period."],
];

function Check() {
  return (
    <svg className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" className="opacity-20" />
      <path d="M8 12.5l2.5 2.5 5-6" />
    </svg>
  );
}

export function SecurityPage() {
  return (
    <MarketingLayout>
      {/* Hero */}
      <section className="bg-gradient-to-b from-indigo-50/50 to-white">
        <div className="mx-auto max-w-4xl px-6 py-16 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Data &amp; Security</p>
          <h1 className="mx-auto mt-4 max-w-3xl text-4xl font-extrabold leading-[1.15] text-slate-900 sm:text-5xl">
            Your school's data is{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">safe with us</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-500">
            Student information and school finances are sensitive. {CONTACT.brand} is built so that protecting them
            isn't a promise on paper — it's how the system works. Here's exactly what we do, in plain language.
          </p>
        </div>
      </section>

      {/* Commitments */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {COMMITMENTS.map((c) => (
              <div key={c.title} className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
                <span className={`flex h-11 w-11 items-center justify-center rounded-xl text-xl ${c.tint}`}>{c.icon}</span>
                <h2 className="mt-4 text-base font-bold text-slate-900">{c.title}</h2>
                <p className="mt-1.5 text-[13px] leading-relaxed text-slate-500">{c.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data rights */}
      <section className="bg-gradient-to-b from-white to-slate-50 py-16">
        <div className="mx-auto max-w-4xl px-6">
          <p className="text-center text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Your rights over the data</p>
          <h2 className="mx-auto mt-3 max-w-2xl text-center text-3xl font-bold text-slate-900 sm:text-4xl">
            Built-in data protection controls
          </h2>
          <ul className="mx-auto mt-10 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
            {RIGHTS.map(([title, body]) => (
              <li key={title} className="flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
                <Check />
                <span>
                  <span className="block text-sm font-semibold text-slate-800">{title}</span>
                  <span className="mt-0.5 block text-[13px] leading-relaxed text-slate-500">{body}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Roles + DPA */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-4xl px-6">
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-8">
            <h2 className="text-xl font-bold text-slate-900">Who is responsible for what</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              Under India's DPDP Act, your <strong>school is the Data Fiduciary</strong> — you decide what data is
              collected and why. <strong>{CONTACT.brand} is the Data Processor</strong> — we safeguard that data and
              act only on your instructions. Our Data Processing Agreement puts these responsibilities in writing:
              what we process, the security measures we maintain, our sub-processors, breach handling, and deletion of
              your data if you ever leave.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a href={`mailto:${CONTACT.email}?subject=${encodeURIComponent("Request: Data Processing Agreement (DPA)")}`} className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:opacity-95">
                Request our DPA
              </a>
              <Link to="/faq" className="rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                Read the FAQ
              </Link>
            </div>
          </div>

          <p className="mt-8 text-center text-sm text-slate-500">
            Questions about security or compliance? Email{" "}
            <a href={`mailto:${CONTACT.email}`} className="font-semibold text-indigo-600 hover:underline">{CONTACT.email}</a>.
          </p>
        </div>
      </section>
    </MarketingLayout>
  );
}
