import { useState } from "react";
import { Link } from "react-router-dom";

/**
 * Public marketing home page (route: /welcome).
 *
 * Rebuilt to match the EduLedger design mockups: sticky nav, split hero with a
 * product preview, module grid, "why choose" split, testimonials, CTA band and
 * a full footer. Light-theme only, fully responsive. Brand name is a single
 * constant so it is trivial to rename.
 */
const BRAND = "EduLedger";

// ---- data ---------------------------------------------------------------- //

const HERO_CHECKS = ["Easy to Use", "100% Secure", "Cloud Based", "24/7 Support"];

const MODULES: { icon: string; tint: string; title: string; body: string }[] = [
  { icon: "🧾", tint: "bg-indigo-100 text-indigo-600", title: "Fee Management", body: "Create fee structures, collect fees, manage discounts, late fees, refunds and receipts." },
  { icon: "📊", tint: "bg-emerald-100 text-emerald-600", title: "Accounting", body: "Automated accounting with journals, ledgers, trial balance, P&L and balance sheet." },
  { icon: "💸", tint: "bg-amber-100 text-amber-600", title: "Expense Management", body: "Track and manage all school expenses with approvals and categories." },
  { icon: "👥", tint: "bg-rose-100 text-rose-600", title: "Payroll", body: "Manage staff salaries, deductions, payslips, PF, ESI, TDS and more." },
  { icon: "📦", tint: "bg-sky-100 text-sky-600", title: "Inventory", body: "Manage school inventory, stock levels, purchases and consumables." },
  { icon: "🚌", tint: "bg-cyan-100 text-cyan-600", title: "Transport", body: "Manage transport routes, vehicles, expenses and collections." },
  { icon: "🏨", tint: "bg-fuchsia-100 text-fuchsia-600", title: "Hostel", body: "Hostel room allocation, mess charges and hostel accounting." },
  { icon: "💳", tint: "bg-violet-100 text-violet-600", title: "Online Payments", body: "Accept secure online payments and auto-reconcile transactions." },
  { icon: "📈", tint: "bg-blue-100 text-blue-600", title: "Reports", body: "40+ financial and operational reports at your fingertips." },
  { icon: "🔔", tint: "bg-orange-100 text-orange-600", title: "Reminders & Receipts", body: "Staged WhatsApp & SMS fee reminders with digitally-signed receipts." },
];

const WHY = [
  "Designed specifically for educational institutions",
  "Automate daily tasks and save 10+ hours every week",
  "Reduce fee defaults with smart reminders",
  "Make data-driven decisions with real-time insights",
  "Scalable from single school to multi-branch groups",
  "Dedicated support whenever you need us",
];

const OUTSTANDING: { name: string; cls: string; due: string; date: string; status: string; badge: string }[] = [
  { name: "Rehan Sharma", cls: "Class 8 - A", due: "₹12,500", date: "15 May 2025", status: "Overdue", badge: "bg-rose-100 text-rose-600" },
  { name: "Ananya Singh", cls: "Class 7 - B", due: "₹8,750", date: "20 May 2025", status: "Due Soon", badge: "bg-amber-100 text-amber-600" },
  { name: "Kartik Verma", cls: "Class 6 - A", due: "₹11,000", date: "25 May 2025", status: "Paid", badge: "bg-emerald-100 text-emerald-600" },
  { name: "Diya Patel", cls: "Class 9 - C", due: "₹15,200", date: "30 May 2025", status: "Paid", badge: "bg-emerald-100 text-emerald-600" },
  { name: "Aman Khan", cls: "Class 5 - B", due: "₹9,600", date: "30 May 2025", status: "Paid", badge: "bg-emerald-100 text-emerald-600" },
];

const TESTIMONIALS = [
  { quote: "EduLedger has completely transformed our fee collection process. It's easy to use, saves time and the reports are excellent.", who: "Principal", school: "Delhi Public School, Jaipur" },
  { quote: "The accounting module is powerful yet simple. Our monthly closing is now 70% faster!", who: "Accountant", school: "Cambridge International School" },
  { quote: "Parents love the reminders and online updates. Fee defaults reduced by 60% in just 3 months.", who: "Administrator", school: "St. Mary's School, Lucknow" },
];

const FOOTER_COLS: { title: string; links: string[] }[] = [
  { title: "Product", links: ["Features", "Modules", "Pricing", "Integrations", "Updates"] },
  { title: "Company", links: ["About Us", "Careers", "Partners", "Blog", "Contact Us"] },
  { title: "Resources", links: ["Help Center", "User Guides", "Webinars", "Privacy Policy", "Terms of Service"] },
];

// ---- small pieces -------------------------------------------------------- //

function Check({ className = "h-5 w-5 text-emerald-500" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" className="opacity-20" />
      <path d="M8 12.5l2.5 2.5 5-6" />
    </svg>
  );
}

function Logo({ light = false }: { light?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${light ? "bg-white/15" : "bg-gradient-to-br from-indigo-600 to-violet-600"} text-white`}>
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 5a2 2 0 0 1 2-2h6v18H6a2 2 0 0 1-2-2z" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /><path d="M8 7h1M8 11h1" />
        </svg>
      </span>
      <div className="leading-tight">
        <p className={`text-lg font-bold ${light ? "text-white" : "text-slate-900"}`}>{BRAND}</p>
        <p className={`text-[10px] ${light ? "text-white/60" : "text-slate-400"}`}>School Finance Simplified</p>
      </div>
    </div>
  );
}

// ---- nav ----------------------------------------------------------------- //

function NavBar() {
  const [open, setOpen] = useState(false);
  const links: { label: string; to: string; caret?: boolean }[] = [
    { label: "Features", to: "#modules", caret: true },
    { label: "Modules", to: "#modules" },
    { label: "Pricing", to: "#cta" },
    { label: "About Us", to: "#why" },
    { label: "Resources", to: "#footer", caret: true },
    { label: "Contact", to: "#footer" },
  ];
  return (
    <header className="sticky top-0 z-40 border-b border-slate-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="#top"><Logo /></a>

        <nav className="hidden items-center gap-7 lg:flex">
          {links.map((l) => (
            <a key={l.label} href={l.to} className="flex items-center gap-1 text-sm font-medium text-slate-600 transition hover:text-indigo-600">
              {l.label}
              {l.caret && <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"><path d="M6 9l6 6 6-6" /></svg>}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-indigo-600">Login</Link>
          <Link to="/signup" className="rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-95">
            Book a Demo
          </Link>
        </div>

        <button onClick={() => setOpen((o) => !o)} className="lg:hidden" aria-label="Menu">
          <svg className="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d={open ? "M6 6l12 12M6 18L18 6" : "M4 7h16M4 12h16M4 17h16"} /></svg>
        </button>
      </div>

      {open && (
        <div className="border-t border-slate-100 bg-white px-6 py-4 lg:hidden">
          <div className="flex flex-col gap-3">
            {links.map((l) => (
              <a key={l.label} href={l.to} onClick={() => setOpen(false)} className="text-sm font-medium text-slate-600">{l.label}</a>
            ))}
            <div className="mt-2 flex gap-3">
              <Link to="/login" className="flex-1 rounded-lg border border-slate-200 py-2 text-center text-sm font-semibold text-slate-700">Login</Link>
              <Link to="/signup" className="flex-1 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 py-2 text-center text-sm font-semibold text-white">Book a Demo</Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

// ---- hero product preview (pure CSS/SVG mock) ---------------------------- //

function DashboardPreview() {
  const kpis = [
    { label: "Total Collection", value: "₹24,35,000", delta: "+10.5%", up: true },
    { label: "Outstanding", value: "₹3,25,000", delta: "+8.2%", up: true },
    { label: "Expenses", value: "₹1,15,000", delta: "-2.4%", up: false },
    { label: "Net Income", value: "₹9,65,000", delta: "+15.6%", up: true },
  ];
  const nav = ["Dashboard", "Students", "Fee Collection", "Accounting", "Expenses", "Reports", "Payroll", "Inventory", "Settings"];
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
      <div className="flex">
        {/* sidebar */}
        <div className="hidden w-40 shrink-0 flex-col gap-1 bg-slate-900 p-3 sm:flex">
          <div className="mb-2 flex items-center gap-2 px-1">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 text-xs font-bold text-white">E</span>
          </div>
          {nav.map((n, i) => (
            <div key={n} className={`rounded-md px-2.5 py-1.5 text-[11px] font-medium ${i === 0 ? "bg-indigo-600 text-white" : "text-slate-400"}`}>{n}</div>
          ))}
        </div>
        {/* main */}
        <div className="min-w-0 flex-1 bg-slate-50 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-bold text-slate-800">Dashboard</p>
            <div className="flex items-center gap-1.5">
              <span className="h-6 w-6 rounded-full bg-gradient-to-br from-indigo-500 to-violet-500" />
              <span className="text-[11px] font-medium text-slate-600">Admin</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {kpis.map((k) => (
              <div key={k.label} className="rounded-lg border border-slate-100 bg-white p-2.5">
                <p className="truncate text-[9px] font-medium uppercase tracking-wide text-slate-400">{k.label}</p>
                <p className="mt-0.5 text-[13px] font-bold text-slate-800">{k.value}</p>
                <p className={`text-[9px] font-semibold ${k.up ? "text-emerald-500" : "text-rose-500"}`}>{k.delta}</p>
              </div>
            ))}
          </div>

          <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-5">
            {/* line chart */}
            <div className="rounded-lg border border-slate-100 bg-white p-3 lg:col-span-3">
              <p className="mb-1 text-[11px] font-semibold text-slate-700">Collection Overview</p>
              <svg viewBox="0 0 260 90" className="w-full">
                <defs>
                  <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366F1" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d="M0 78 L40 66 L80 70 L120 48 L160 52 L200 28 L260 16 L260 90 L0 90 Z" fill="url(#lg)" />
                <path d="M0 78 L40 66 L80 70 L120 48 L160 52 L200 28 L260 16" fill="none" stroke="#4F46E5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="200" cy="28" r="3.5" fill="#4F46E5" stroke="#fff" strokeWidth="1.5" />
              </svg>
            </div>
            {/* donut */}
            <div className="rounded-lg border border-slate-100 bg-white p-3 lg:col-span-2">
              <p className="mb-1 text-[11px] font-semibold text-slate-700">Fee Collection by Mode</p>
              <div className="flex items-center gap-3">
                <svg viewBox="0 0 42 42" className="h-16 w-16 -rotate-90">
                  <circle cx="21" cy="21" r="15.9" fill="none" stroke="#E2E8F0" strokeWidth="6" />
                  <circle cx="21" cy="21" r="15.9" fill="none" stroke="#4F46E5" strokeWidth="6" strokeDasharray="60 40" />
                  <circle cx="21" cy="21" r="15.9" fill="none" stroke="#22C55E" strokeWidth="6" strokeDasharray="20 80" strokeDashoffset="-60" />
                  <circle cx="21" cy="21" r="15.9" fill="none" stroke="#F59E0B" strokeWidth="6" strokeDasharray="15 85" strokeDashoffset="-80" />
                </svg>
                <div className="space-y-1 text-[9px] text-slate-500">
                  <p><span className="mr-1 inline-block h-2 w-2 rounded-full bg-indigo-600" />UPI · 60%</p>
                  <p><span className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-500" />Cash · 20%</p>
                  <p><span className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-500" />Bank · 15%</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-2 flex flex-wrap gap-1.5">
            {["Collect Fee", "Add Expense", "Add Student", "Generate Report"].map((q) => (
              <span key={q} className="rounded-md border border-slate-100 bg-white px-2 py-1 text-[9px] font-medium text-slate-500">{q}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---- sections ------------------------------------------------------------ //

function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-gradient-to-b from-white to-indigo-50/40">
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-24">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">All-in-One School Finance &amp; Accounting</p>
          <h1 className="mt-4 text-4xl font-extrabold leading-[1.1] text-slate-900 sm:text-5xl">
            The Financial{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">Operating System</span>{" "}
            for Schools
          </h1>
          <p className="mt-5 max-w-lg text-lg text-slate-500">
            {BRAND} helps schools automate fee collection, accounting, expense management and financial reporting — all in one powerful platform.
          </p>

          <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2">
            {HERO_CHECKS.map((c) => (
              <span key={c} className="flex items-center gap-2 text-sm font-medium text-slate-700"><Check /> {c}</span>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/signup" className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:opacity-95">
              Book a Free Demo
            </Link>
            <a href="#modules" className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              <svg className="h-4 w-4 text-indigo-600" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
              Watch Video
            </a>
          </div>

          <div className="mt-10">
            <p className="text-xs font-medium text-slate-400">Trusted by 1000+ Schools Across India</p>
            <div className="mt-3 flex items-center gap-4 opacity-70">
              {["🏫", "🎓", "📚", "🏛️", "🏫"].map((e, i) => (
                <span key={i} className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-lg grayscale">{e}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:pl-6">
          <DashboardPreview />
        </div>
      </div>
    </section>
  );
}

function Modules() {
  return (
    <section id="modules" className="bg-white py-20">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-center text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Everything You Need</p>
        <h2 className="mx-auto mt-3 max-w-3xl text-center text-3xl font-bold text-slate-900 sm:text-4xl">
          Powerful Modules for{" "}
          <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">Complete</span>{" "}
          School Financial Management
        </h2>

        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {MODULES.map((m) => (
            <div key={m.title} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <span className={`flex h-11 w-11 items-center justify-center rounded-xl text-xl ${m.tint}`}>{m.icon}</span>
              <h3 className="mt-4 text-base font-bold text-slate-900">{m.title}</h3>
              <p className="mt-1.5 text-[13px] leading-relaxed text-slate-500">{m.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PhoneReceipt() {
  return (
    <div className="relative mx-auto w-[210px] rounded-[2rem] border-[6px] border-slate-900 bg-white shadow-2xl">
      <div className="mx-auto mt-2 h-1.5 w-16 rounded-full bg-slate-800" />
      <div className="p-4">
        <p className="mb-3 text-[11px] font-semibold text-slate-500">Payment Receipt</p>
        <div className="flex flex-col items-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
            <Check className="h-7 w-7 text-emerald-500" />
          </span>
          <p className="mt-2 text-sm font-semibold text-slate-700">Payment Successful</p>
          <p className="mt-1 text-2xl font-extrabold text-slate-900">₹5,250</p>
        </div>
        <div className="mt-4 space-y-2 text-[11px]">
          {[["Student Name", "Rehan Sharma"], ["Class", "Class 8 - A"], ["Payment Mode", "UPI"], ["Transaction ID", "UPITXA6669876"], ["Date", "15 May 2025, 10:30 AM"]].map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-slate-400">{k}</span>
              <span className="font-medium text-slate-700">{v}</span>
            </div>
          ))}
        </div>
        <button className="mt-4 w-full rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 py-2 text-[11px] font-semibold text-white">Download Receipt</button>
      </div>
    </div>
  );
}

function WhyChoose() {
  return (
    <section id="why" className="bg-gradient-to-b from-white to-slate-50 py-20">
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 lg:grid-cols-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Why Choose {BRAND}?</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900 sm:text-4xl">
            Built for Schools.<br />
            <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">Loved</span> by Accountants.
          </h2>
          <ul className="mt-8 space-y-4">
            {WHY.map((w) => (
              <li key={w} className="flex items-start gap-3 text-slate-600"><Check className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" /> <span>{w}</span></li>
            ))}
          </ul>
        </div>

        <div className="relative">
          <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-xl">
            <p className="mb-3 text-sm font-bold text-slate-800">Student Outstanding</p>
            <div className="overflow-hidden">
              <table className="w-full text-left text-[12px]">
                <thead className="text-[10px] uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="pb-2 font-semibold">Student</th>
                    <th className="pb-2 font-semibold">Class</th>
                    <th className="pb-2 font-semibold">Total Due</th>
                    <th className="hidden pb-2 font-semibold sm:table-cell">Due Date</th>
                    <th className="pb-2 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {OUTSTANDING.map((r) => (
                    <tr key={r.name}>
                      <td className="py-2.5 font-medium text-slate-700">{r.name}</td>
                      <td className="py-2.5 text-slate-500">{r.cls}</td>
                      <td className="py-2.5 font-semibold text-slate-700">{r.due}</td>
                      <td className="hidden py-2.5 text-slate-500 sm:table-cell">{r.date}</td>
                      <td className="py-2.5"><span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${r.badge}`}>{r.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="mt-6 sm:absolute sm:-bottom-8 sm:-right-2 sm:mt-0">
            <PhoneReceipt />
          </div>
        </div>
      </div>
    </section>
  );
}

function Testimonials() {
  return (
    <section className="bg-white py-20">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-center text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">What Schools Say</p>
        <h2 className="mt-3 text-center text-3xl font-bold text-slate-900 sm:text-4xl">Trusted by Schools. Proven by Results.</h2>

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t) => (
            <figure key={t.school} className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="text-4xl leading-none text-indigo-200">“</div>
              <blockquote className="-mt-3 text-sm leading-relaxed text-slate-600">{t.quote}</blockquote>
              <figcaption className="mt-5 flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm">🏫</span>
                <div>
                  <p className="text-sm font-semibold text-slate-800">{t.who}</p>
                  <p className="text-xs text-slate-400">{t.school}</p>
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
        <div className="mt-8 flex justify-center gap-2">
          <span className="h-2 w-6 rounded-full bg-indigo-600" />
          <span className="h-2 w-2 rounded-full bg-slate-200" />
          <span className="h-2 w-2 rounded-full bg-slate-200" />
        </div>
      </div>
    </section>
  );
}

function CtaBand() {
  return (
    <section id="cta" className="bg-white px-6 pb-20">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-6 overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-600 to-violet-600 px-8 py-12 text-center text-white sm:flex-row sm:justify-between sm:text-left">
        <div className="flex items-center gap-4">
          <span className="hidden text-5xl sm:block">🏫</span>
          <div>
            <h2 className="text-2xl font-bold sm:text-3xl">Ready to Simplify Your School Finances?</h2>
            <p className="mt-2 max-w-xl text-sm text-white/80">Join 1000+ schools using {BRAND} to automate finance, save time and focus on education.</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap justify-center gap-3">
          <Link to="/signup" className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-indigo-600 hover:bg-slate-100">Book a Free Demo</Link>
          <a href="#footer" className="rounded-xl border border-white/50 px-6 py-3 text-sm font-semibold text-white hover:bg-white/10">Contact Sales</a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const social = [
    { label: "Facebook", d: "M13 22v-8h2.7l.4-3H13V9.2c0-.9.3-1.5 1.6-1.5H16V5.1C15.5 5 14.6 5 13.6 5 11.4 5 10 6.3 10 8.8V11H7.5v3H10v8z" },
    { label: "LinkedIn", d: "M6.9 8.8H4V20h2.9zM5.4 4a1.7 1.7 0 1 0 0 3.4 1.7 1.7 0 0 0 0-3.4M20 20v-6.2c0-3-1.6-4.4-3.8-4.4-1.7 0-2.5.9-2.9 1.6V9.6h-2.9V20h2.9v-5.6c0-1.5.3-2.9 2.1-2.9s1.8 1.7 1.8 3V20z" },
    { label: "YouTube", d: "M22 8.2a2.6 2.6 0 0 0-1.8-1.8C18.6 6 12 6 12 6s-6.6 0-8.2.4A2.6 2.6 0 0 0 2 8.2 27 27 0 0 0 1.7 12 27 27 0 0 0 2 15.8a2.6 2.6 0 0 0 1.8 1.8C5.4 18 12 18 12 18s6.6 0 8.2-.4a2.6 2.6 0 0 0 1.8-1.8A27 27 0 0 0 22.3 12 27 27 0 0 0 22 8.2M10 15V9l5.2 3z" },
  ];
  return (
    <footer id="footer" className="border-t border-slate-100 bg-white">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-6 py-14 sm:grid-cols-3 lg:grid-cols-5">
        <div className="col-span-2">
          <Logo />
          <p className="mt-4 max-w-xs text-sm text-slate-500">{BRAND} is the all-in-one financial management platform for schools. Automate, simplify and grow.</p>
          <div className="mt-4 flex gap-2">
            {social.map((s) => (
              <a key={s.label} href="#top" aria-label={s.label} className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 hover:bg-indigo-600 hover:text-white">
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d={s.d} /></svg>
              </a>
            ))}
          </div>
        </div>

        {FOOTER_COLS.map((col) => (
          <div key={col.title}>
            <p className="text-sm font-semibold text-slate-800">{col.title}</p>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l}><a href="#top" className="text-sm text-slate-500 hover:text-indigo-600">{l}</a></li>
              ))}
            </ul>
          </div>
        ))}

        <div className="col-span-2 sm:col-span-3 lg:col-span-1">
          <p className="text-sm font-semibold text-slate-800">Get in Touch</p>
          <ul className="mt-4 space-y-2.5 text-sm text-slate-500">
            <li className="flex items-center gap-2">📞 +91 98765 43210</li>
            <li className="flex items-center gap-2">✉️ hello@eduledger.app</li>
            <li className="flex items-center gap-2">📍 Bangalore, India</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-100 py-6 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} {BRAND}. All rights reserved.
      </div>
    </footer>
  );
}

// ---- page ---------------------------------------------------------------- //

export function LandingPage() {
  return (
    <div className="min-h-screen scroll-smooth bg-white text-slate-800">
      <NavBar />
      <Hero />
      <Modules />
      <WhyChoose />
      <Testimonials />
      <CtaBand />
      <Footer />
    </div>
  );
}
