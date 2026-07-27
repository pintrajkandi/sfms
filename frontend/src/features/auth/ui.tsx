import type { ReactNode } from "react";

/* ---------------------------------------------------------------- icons -- */

type IconProps = { className?: string };
const base = "h-5 w-5";

export const SchoolIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 21h18M5 21V10l7-4 7 4v11" />
    <path d="M9 21v-5h6v5M12 3v3" />
  </svg>
);
export const MailIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="m3 7 9 6 9-6" />
  </svg>
);
export const LockIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="11" width="16" height="9" rx="2" />
    <path d="M8 11V7a4 4 0 0 1 8 0v4" />
  </svg>
);
export const GlobeIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18" />
  </svg>
);
export const UserIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4" />
    <path d="M4 20a8 8 0 0 1 16 0" />
  </svg>
);
export const EyeIcon = ({ off = false, className = base }: IconProps & { off?: boolean }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
    {off && <line x1="3" y1="3" x2="21" y2="21" />}
  </svg>
);
export const HeadsetIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 13v-1a8 8 0 0 1 16 0v1" />
    <rect x="3" y="13" width="4" height="6" rx="1" />
    <rect x="17" y="13" width="4" height="6" rx="1" />
    <path d="M20 19a4 4 0 0 1-4 3h-3" />
  </svg>
);
export const ShieldCheckIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3 5 6v6c0 4 3 7 7 9 4-2 7-5 7-9V6l-7-3Z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);
export const UsersIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="9" cy="8" r="3" />
    <path d="M3 20a6 6 0 0 1 12 0M16 6a3 3 0 0 1 0 6M18 20a6 6 0 0 0-3-5" />
  </svg>
);
export const ChartIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 20V4M4 20h16M8 20v-6M12 20v-9M16 20v-4" />
  </svg>
);
export const BellIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6M10 20a2 2 0 0 0 4 0" />
  </svg>
);
export const CalendarIcon = ({ className = base }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M3 9h18M8 3v4M16 3v4" />
  </svg>
);
export const CheckIcon = ({ className = "h-3.5 w-3.5" }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="m5 12 5 5L20 7" />
  </svg>
);
export const ArrowRightIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

/* ----------------------------------------------------------------- logo -- */

export function BrandLogo() {
  return (
    <div className="flex items-center gap-3">
      <svg className="h-11 w-11" viewBox="0 0 48 48" fill="none">
        <defs>
          <linearGradient id="ledgerShield" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#2563EB" />
            <stop offset="1" stopColor="#6366F1" />
          </linearGradient>
        </defs>
        <path
          d="M24 4 8 10v12c0 10 7 16 16 22 9-6 16-12 16-22V10L24 4Z"
          fill="#EEF4FF"
          stroke="url(#ledgerShield)"
          strokeWidth="2.5"
        />
        <path d="M19 16h11M22 16v13M22 22h6" stroke="#1D4ED8" strokeWidth="2.6" strokeLinecap="round" />
      </svg>
      <div className="leading-tight">
        <p className="text-lg font-bold tracking-tight text-slate-900">YukiCares</p>
        <p className="text-xs text-slate-500">Smart School Finance</p>
      </div>
    </div>
  );
}

/* -------------------------------------------------------- illustration -- */

export function SchoolIllustration({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 320 220" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="160" cy="150" r="120" fill="#DBEAFE" />
      <ellipse cx="70" cy="60" rx="26" ry="12" fill="#EAF1FE" />
      <ellipse cx="250" cy="48" rx="30" ry="13" fill="#EAF1FE" />
      {/* trees */}
      <g fill="#60A5FA">
        <circle cx="70" cy="150" r="22" />
        <circle cx="250" cy="150" r="22" />
      </g>
      <rect x="66" y="150" width="8" height="24" fill="#1D4ED8" />
      <rect x="246" y="150" width="8" height="24" fill="#1D4ED8" />
      {/* building */}
      <rect x="108" y="96" width="104" height="80" rx="4" fill="#93C5FD" />
      <rect x="140" y="70" width="40" height="30" fill="#60A5FA" />
      <path d="M132 70h56l-28-22-28 22Z" fill="#2563EB" />
      <circle cx="160" cy="84" r="7" fill="#EEF4FF" stroke="#1D4ED8" strokeWidth="2" />
      <path d="M160 80v4l3 2" stroke="#1D4ED8" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M160 48v-10" stroke="#1D4ED8" strokeWidth="2" strokeLinecap="round" />
      <path d="M160 38h12v8h-12Z" fill="#2563EB" />
      {/* windows + door */}
      <g fill="#EEF4FF">
        <rect x="120" y="110" width="16" height="18" rx="2" />
        <rect x="184" y="110" width="16" height="18" rx="2" />
        <rect x="120" y="140" width="16" height="18" rx="2" />
        <rect x="184" y="140" width="16" height="18" rx="2" />
      </g>
      <rect x="148" y="140" width="24" height="36" rx="12" fill="#1D4ED8" />
    </svg>
  );
}

/* -------------------------------------------------------- feature panel -- */

export interface Feature {
  icon: ReactNode;
  title: string;
  body: string;
}

export function FeaturePanel({ features }: { features: Feature[] }) {
  return (
    <div className="flex h-full flex-col justify-center px-10 py-12">
      <SchoolIllustration className="mx-auto mb-10 w-full max-w-sm" />
      <h2 className="text-2xl font-bold text-slate-900">
        Everything you need to <span className="text-brand">manage school fees</span>
      </h2>
      <ul className="mt-8 space-y-6">
        {features.map((f) => (
          <li key={f.title} className="flex gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-brand shadow-sm">
              {f.icon}
            </span>
            <div>
              <p className="font-semibold text-slate-900">{f.title}</p>
              <p className="text-sm text-slate-600">{f.body}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export const LOGIN_FEATURES: Feature[] = [
  {
    icon: <UsersIcon />,
    title: "Secure access",
    body: "Role-based access for staff with enterprise-grade security.",
  },
  {
    icon: <ChartIcon />,
    title: "Real-time insights",
    body: "Track collections and generate reports in real time.",
  },
  {
    icon: <BellIcon />,
    title: "Smart notifications",
    body: "Get reminders for dues, fees and important updates.",
  },
  {
    icon: <ShieldCheckIcon />,
    title: "Reliable & trusted",
    body: "Trusted by schools to simplify fee management.",
  },
];

export const SIGNUP_FEATURES: Feature[] = [
  {
    icon: <UsersIcon />,
    title: "Invite staff & manage roles",
    body: "Add teachers, accountants and more.",
  },
  {
    icon: <ChartIcon />,
    title: "Track fee collections",
    body: "Real-time reports and analytics.",
  },
  {
    icon: <CalendarIcon />,
    title: "Automate reminders",
    body: "Reduce defaults with smart notifications.",
  },
  {
    icon: <ShieldCheckIcon />,
    title: "Secure & reliable",
    body: "Your data is protected with enterprise-grade security.",
  },
];

/* ---------------------------------------------------------- icon input -- */

export function IconField({
  icon,
  trailing,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { icon: ReactNode; trailing?: ReactNode }) {
  return (
    <div className="flex items-stretch overflow-hidden rounded-xl border border-slate-200 bg-white focus-within:border-brand focus-within:ring-2 focus-within:ring-brand-ring/40">
      <span className="flex w-12 items-center justify-center border-r border-slate-100 bg-brand-light text-brand">
        {icon}
      </span>
      <input
        {...props}
        className="min-w-0 flex-1 bg-transparent px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none"
      />
      {trailing && <span className="flex items-center pr-3">{trailing}</span>}
    </div>
  );
}
