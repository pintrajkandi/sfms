import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthProvider";

type IconProps = { className?: string };
const ic = "h-6 w-6";
const HomeIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 11l9-7 9 7M5 10v10h14V10" /></svg>
);
const UsersIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="8" r="3" /><path d="M3 20a6 6 0 0 1 12 0M16 6a3 3 0 0 1 0 6M18 20a6 6 0 0 0-3-5" /></svg>
);
const WalletIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="6" width="18" height="13" rx="2" /><path d="M3 10h18M16 14h2" /></svg>
);
const CoinsIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="9" cy="7" rx="6" ry="3" /><path d="M3 7v5c0 1.7 2.7 3 6 3s6-1.3 6-3V7M15 12c0 1.7 2.7 3 6 3M9 15v2c0 1.7 2.7 3 6 3s6-1.3 6-3v-5" /></svg>
);
const GridIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>
);
const DocIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2h8l4 4v16H6z" /><path d="M14 2v4h4M9 13h6M9 17h6" /></svg>
);
const BoxIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8" /></svg>
);
const ChartIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20V4M4 20h16M8 20v-6M12 20v-9M16 20v-4" /></svg>
);
const BedIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7v11M3 12h18v6M21 12v-1a3 3 0 0 0-3-3H8" /><circle cx="6.5" cy="10.5" r="1.5" /></svg>
);
const BusIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="12" rx="2" /><path d="M3 11h18M7 17v2M17 17v2" /><circle cx="7.5" cy="14.5" r="0.5" /><circle cx="16.5" cy="14.5" r="0.5" /></svg>
);
const ChatIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
);
const CogIcon = ({ className = ic }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.3 1a7 7 0 0 0-1.7-1L14.5 2h-5l-.4 2.6a7 7 0 0 0-1.7 1l-2.3-1-2 3.4 2 1.5a7 7 0 0 0 0 2l-2 1.5 2 3.4 2.3-1a7 7 0 0 0 1.7 1l.4 2.6h5l.4-2.6a7 7 0 0 0 1.7-1l2.3 1 2-3.4-2-1.5c.06-.33.1-.66.1-1Z" /></svg>
);

type NavItem = { to: string; label: string; icon: (p: IconProps) => JSX.Element; end?: boolean; adminOnly?: boolean; superuserOnly?: boolean; external?: string };

const NAV: NavItem[] = [
  { to: "/", label: "Dashboard", icon: HomeIcon, end: true },
  { to: "/students", label: "Students", icon: UsersIcon },
  { to: "/fee-collection", label: "Fee Collection", icon: WalletIcon },
  { to: "/invoices", label: "Invoices", icon: DocIcon },
  { to: "/teachers", label: "Teachers", icon: UsersIcon },
  { to: "/teachers/new", label: "Add Teacher", icon: UsersIcon },
  { to: "/payouts", label: "Teacher Payouts", icon: CoinsIcon },
  { to: "/teacher-payouts", label: "Payouts List", icon: CoinsIcon },
  { to: "/expenses/new", label: "Expenses", icon: DocIcon },
  { to: "/inventory", label: "Inventory", icon: BoxIcon },
  { to: "/transport", label: "Transport", icon: BusIcon },
  { to: "/hostel", label: "Hostel", icon: BedIcon },
  { to: "/finance", label: "Finance", icon: ChartIcon },
  { to: "/accounting", label: "Accounting", icon: ChartIcon },
  { to: "/documents", label: "Documents", icon: DocIcon },
  { to: "/reports", label: "Reports", icon: DocIcon },
  { to: "/risk", label: "Predictive", icon: ChartIcon },
  { to: "/audit-log", label: "Audit Log", icon: DocIcon, adminOnly: true },
  { to: "/support", label: "Support", icon: ChatIcon },
  { to: "/docs", label: "Docs", icon: DocIcon, external: "/docs/" },
  { to: "/settings", label: "Settings", icon: CogIcon },
];

const isVisible = (item: NavItem, role?: string, isSuperuser?: boolean) => {
  if (item.superuserOnly) return Boolean(isSuperuser);
  return !item.adminOnly || role === "admin";
};

// Primary tabs shown in the mobile bottom bar (5th is the "More" sheet).
const BOTTOM = ["/", "/students", "/fee-collection", "/payouts"].map(
  (to) => NAV.find((n) => n.to === to)!,
);

export function AppShell() {
  const { user, logout } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col bg-brand-gradient text-white lg:flex print:!hidden">
        <div className="flex items-center gap-2 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 font-bold">₹</div>
          <div className="leading-tight">
            <p className="font-semibold tracking-wide">YukiCares</p>
            <p className="text-[11px] text-white/70">Smart School Finance</p>
          </div>
        </div>
        <nav className="mt-2 flex flex-1 flex-col gap-1 px-3">
          {NAV.filter((item) => isVisible(item, user?.role, user?.is_superuser)).map((item) =>
            item.external ? (
              <a
                key={item.to}
                href={item.external}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-white/75 transition hover:bg-white/10"
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </a>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition ${
                    isActive ? "bg-white/20 text-white" : "text-white/75 hover:bg-white/10"
                  }`
                }
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            ),
          )}
        </nav>
        <div className="border-t border-white/10 px-4 py-4">
          <p className="truncate text-sm font-medium">{user?.full_name}</p>
          <p className="truncate text-xs capitalize text-white/60">{user?.role}</p>
          <button onClick={logout} className="mt-3 w-full rounded-lg bg-white/10 py-2 text-sm font-medium hover:bg-white/20">
            Sign out
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between bg-brand-gradient px-4 py-3 text-white lg:hidden print:!hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15 font-bold">₹</div>
            <span className="font-semibold tracking-wide">YukiCares</span>
          </div>
          <button
            onClick={logout}
            className="rounded-lg bg-white/15 px-3 py-1.5 text-xs font-medium"
          >
            Sign out
          </button>
        </header>

        <main className="flex-1 overflow-x-hidden p-4 pb-24 sm:p-6 lg:p-8 lg:pb-8">
          <Outlet />
        </main>
      </div>

      {/* Mobile bottom tab bar */}
      <nav className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden print:!hidden">
        {BOTTOM.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${
                isActive ? "text-brand" : "text-slate-400"
              }`
            }
          >
            <item.icon className="h-6 w-6" />
            {item.label.split(" ")[0]}
          </NavLink>
        ))}
        <button
          onClick={() => setMoreOpen(true)}
          className="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium text-slate-400"
        >
          <GridIcon className="h-6 w-6" />
          More
        </button>
      </nav>

      {/* Mobile "More" sheet */}
      {moreOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setMoreOpen(false)}>
          <div className="absolute inset-0 bg-slate-900/40" />
          <div
            className="absolute inset-x-0 bottom-0 rounded-t-2xl bg-white p-4 pb-[calc(env(safe-area-inset-bottom)+1rem)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-slate-200" />
            <div className="grid grid-cols-3 gap-3">
              {NAV.filter((n) => !BOTTOM.includes(n) && isVisible(n, user?.role, user?.is_superuser)).map((item) =>
                item.external ? (
                  <a
                    key={item.to}
                    href={item.external}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => setMoreOpen(false)}
                    className="flex flex-col items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 py-4 text-xs font-medium text-slate-700"
                  >
                    <item.icon className="h-6 w-6 text-brand" />
                    {item.label}
                  </a>
                ) : (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={() => setMoreOpen(false)}
                    className="flex flex-col items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 py-4 text-xs font-medium text-slate-700"
                  >
                    <item.icon className="h-6 w-6 text-brand" />
                    {item.label}
                  </NavLink>
                ),
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
