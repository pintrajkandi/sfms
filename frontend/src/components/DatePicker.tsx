import { useEffect, useMemo, useRef, useState } from "react";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const DOW = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

function toISO(y: number, m: number, d: number): string {
  return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function parse(value: string | null | undefined): Date | null {
  if (!value) return null;
  const [y, m, d] = value.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

interface Props {
  value: string; // ISO YYYY-MM-DD
  onChange: (iso: string) => void;
  minYear?: number;
  maxYear?: number;
  placeholder?: string;
}

/** Accessible calendar date picker (month + year dropdowns, day grid). */
export function DatePicker({ value, onChange, minYear, maxYear, placeholder = "Select date" }: Props) {
  const now = new Date();
  const lo = minYear ?? 1940;
  const hi = maxYear ?? now.getFullYear() + 1;
  const selected = parse(value);

  const [open, setOpen] = useState(false);
  const [viewY, setViewY] = useState(selected?.getFullYear() ?? Math.min(now.getFullYear(), hi));
  const [viewM, setViewM] = useState(selected?.getMonth() ?? now.getMonth());
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selected) {
      setViewY(selected.getFullYear());
      setViewM(selected.getMonth());
    }
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const years = useMemo(() => {
    const out: number[] = [];
    for (let y = hi; y >= lo; y--) out.push(y);
    return out;
  }, [lo, hi]);

  const cells = useMemo(() => {
    const firstDow = new Date(viewY, viewM, 1).getDay();
    const daysInMonth = new Date(viewY, viewM + 1, 0).getDate();
    const grid: { day: number; iso: string; muted: boolean }[] = [];
    for (let i = 0; i < firstDow; i++) grid.push({ day: 0, iso: "", muted: true });
    for (let d = 1; d <= daysInMonth; d++) grid.push({ day: d, iso: toISO(viewY, viewM, d), muted: false });
    return grid;
  }, [viewY, viewM]);

  const label = selected
    ? `${MONTHS[selected.getMonth()]} ${selected.getDate()}, ${selected.getFullYear()}`
    : placeholder;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`flex w-full items-center justify-between rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-left text-sm ${selected ? "text-slate-800" : "text-slate-400"}`}
      >
        <span>{label}</span>
        <svg className="h-4 w-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 9h18M8 3v4M16 3v4" /></svg>
      </button>

      {open && (
        <div className="absolute z-30 mt-2 w-[320px] rounded-2xl border border-slate-200 bg-white p-4 shadow-xl">
          <div className="mb-3 flex items-center gap-2">
            <select value={viewM} onChange={(e) => setViewM(Number(e.target.value))} className="flex-1 rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-800">
              {MONTHS.map((m, i) => <option key={m} value={i}>{m}</option>)}
            </select>
            <select value={viewY} onChange={(e) => setViewY(Number(e.target.value))} className="w-24 rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-800">
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-semibold text-slate-400">
            {DOW.map((d) => <div key={d} className="py-1">{d}</div>)}
          </div>
          <div className="mt-1 grid grid-cols-7 gap-1">
            {cells.map((c, i) =>
              c.muted ? (
                <div key={i} />
              ) : (
                <button
                  key={c.iso}
                  type="button"
                  onClick={() => { onChange(c.iso); setOpen(false); }}
                  className={`h-9 rounded-lg text-sm transition ${
                    c.iso === value
                      ? "bg-brand-gradient font-semibold text-white"
                      : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  {c.day}
                </button>
              ),
            )}
          </div>
        </div>
      )}
    </div>
  );
}
