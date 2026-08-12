import { useState } from "react";
import { Link } from "react-router-dom";

/** Contact details shown across public pages. */
export const CONTACT = {
  brand: "YukiCares",
  website: "yukicares.cloud",
  email: "support@yukicares.cloud",
  address: "Shanthi Nagar, Sangareddy, Telangana 502001",
};

function Logo() {
  return (
    <Link to="/welcome" className="flex items-center gap-2.5">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 5a2 2 0 0 1 2-2h6v18H6a2 2 0 0 1-2-2z" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /><path d="M8 7h1M8 11h1" />
        </svg>
      </span>
      <span className="text-lg font-bold text-slate-900">{CONTACT.brand}</span>
    </Link>
  );
}

/**
 * Public marketing nav links, shared across pages. Route links (no "#") use the
 * SPA router; section links point at a landing-page anchor as a full URL so they
 * work from any page (Blog / FAQ / About), not just the landing page.
 */
export const NAV_LINKS: { label: string; to: string }[] = [
  { label: "Home", to: "/welcome" },
  { label: "About Us", to: "/about" },
  { label: "Pricing", to: "/welcome#pricing" },
  { label: "Blog", to: "/blog" },
  { label: "FAQ", to: "/faq" },
  { label: "Security", to: "/security" },
  { label: "Contact", to: "/welcome#footer" },
];

function NavItem({ to, label, onClick }: { to: string; label: string; onClick?: () => void }) {
  const cls = "text-sm font-medium text-slate-600 transition hover:text-indigo-600";
  // Anchor (section) links do a real navigation so the browser resolves the hash;
  // plain routes stay in the SPA.
  return to.includes("#") ? (
    <a href={to} onClick={onClick} className={cls}>{label}</a>
  ) : (
    <Link to={to} onClick={onClick} className={cls}>{label}</Link>
  );
}

/** Shared chrome (nav + footer) for public marketing pages like Blog & FAQ. */
export function MarketingLayout({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-800">
      <header className="sticky top-0 z-40 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <nav className="hidden items-center gap-7 lg:flex">
            {NAV_LINKS.map((l) => <NavItem key={l.label} to={l.to} label={l.label} />)}
          </nav>
          <div className="hidden items-center gap-3 lg:flex">
            <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-indigo-600">Login</Link>
            <Link to="/signup" className="rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-95">Book a Demo</Link>
          </div>
          <button onClick={() => setOpen((o) => !o)} className="lg:hidden" aria-label="Menu">
            <svg className="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d={open ? "M6 6l12 12M6 18L18 6" : "M4 7h16M4 12h16M4 17h16"} /></svg>
          </button>
        </div>
        {open && (
          <div className="border-t border-slate-100 bg-white px-6 py-4 lg:hidden">
            <div className="flex flex-col gap-3">
              {NAV_LINKS.map((l) => <NavItem key={l.label} to={l.to} label={l.label} onClick={() => setOpen(false)} />)}
              <div className="mt-2 flex gap-3">
                <Link to="/login" className="flex-1 rounded-lg border border-slate-200 py-2 text-center text-sm font-semibold text-slate-700">Login</Link>
                <Link to="/signup" className="flex-1 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 py-2 text-center text-sm font-semibold text-white">Book a Demo</Link>
              </div>
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-slate-100 bg-slate-50">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Logo />
          </div>
          <div className="space-y-1 sm:text-right">
            <p>🌐 {CONTACT.website} · ✉️ {CONTACT.email}</p>
            <p>📍 {CONTACT.address}</p>
            <p className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500 sm:justify-end">
              <Link to="/security" className="hover:text-indigo-600">Data &amp; Security</Link>
              <Link to="/privacy" className="hover:text-indigo-600">Privacy Policy</Link>
              <Link to="/terms" className="hover:text-indigo-600">Terms of Service</Link>
            </p>
            <p className="text-xs text-slate-400">© {new Date().getFullYear()} {CONTACT.brand}. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
