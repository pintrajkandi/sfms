import { useEffect, useMemo, useRef, useState } from "react";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const MONTHS_LONG = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

interface Props {
  value: string; // "YYYY-MM"
  onChange: (v: string) => void;
  placeholder?: string;
}

/** Compact month/year picker — outputs "YYYY-MM". */
export function MonthPicker({ value, onChange, placeholder = "Select month" }: Props) {
  const now = new Date();
  const [y, m] = value ? value.split("-").map(Number) : [NaN, NaN];
  const [open, setOpen] = useState(false);
  const [viewY, setViewY] = useState(Number.isNaN(y) ? now.getFullYear() : y);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!Number.isNaN(y)) setViewY(y);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const label = useMemo(() => {
    if (Number.isNaN(y) || Number.isNaN(m)) return "";
    return `${MONTHS_LONG[m - 1]} ${y}`;
  }, [y, m]);

  const pick = (monthIndex: number) => {
    onChange(`${viewY}-${String(monthIndex + 1).padStart(2, "0")}`);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm focus:border-brand focus:outline-none"
      >
        <span className={label ? "text-slate-800" : "text-slate-400"}>{label || placeholder}</span>
        <span className="text-slate-400">📅</span>
      </button>
      {open && (
        <div className="absolute z-30 mt-1 w-64 rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
          <div className="mb-3 flex items-center justify-between">
            <button type="button" onClick={() => setViewY((v) => v - 1)} className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100">‹</button>
            <span className="text-sm font-semibold text-slate-800">{viewY}</span>
            <button type="button" onClick={() => setViewY((v) => v + 1)} className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100">›</button>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {MONTHS.map((mm, i) => {
              const active = viewY === y && i + 1 === m;
              return (
                <button
                  key={mm}
                  type="button"
                  onClick={() => pick(i)}
                  className={`rounded-lg py-2 text-sm font-medium ${
                    active ? "bg-brand text-white" : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {mm}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
