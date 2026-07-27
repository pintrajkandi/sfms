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

/** Shared chrome (nav + footer) for public marketing pages like Blog & FAQ. */
export function MarketingLayout({ children }: { children: React.ReactNode }) {
  const links = [
    { label: "Home", to: "/welcome" },
    { label: "Blog", to: "/blog" },
    { label: "FAQ", to: "/faq" },
  ];
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-800">
      <header className="sticky top-0 z-40 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <nav className="hidden items-center gap-7 sm:flex">
            {links.map((l) => (
              <Link key={l.label} to={l.to} className="text-sm font-medium text-slate-600 hover:text-indigo-600">{l.label}</Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-indigo-600">Login</Link>
            <Link to="/signup" className="rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-95">Book a Demo</Link>
          </div>
        </div>
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
            <p className="text-xs text-slate-400">© {new Date().getFullYear()} {CONTACT.brand}. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
