import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { content } from "@/api/resources";
import type { FAQItem } from "@/api/types";
import { MarketingLayout } from "./MarketingLayout";

function Item({ faq }: { faq: FAQItem }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-slate-100 bg-white">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
        aria-expanded={open}
      >
        <span className="font-semibold text-slate-800">{faq.question}</span>
        <svg className={`h-5 w-5 shrink-0 text-slate-400 transition ${open ? "rotate-180" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && <p className="whitespace-pre-line px-5 pb-5 text-sm leading-relaxed text-slate-600">{faq.answer}</p>}
    </div>
  );
}

export function FAQPage() {
  const { data, isLoading } = useQuery({ queryKey: ["faqs"], queryFn: () => content.faqs() });
  const faqs = data ?? [];

  // Group by category (uncategorised falls under "General").
  const groups = useMemo(() => {
    const map = new Map<string, FAQItem[]>();
    for (const f of faqs) {
      const key = f.category || "General";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(f);
    }
    return Array.from(map.entries());
  }, [faqs]);

  return (
    <MarketingLayout>
      <section className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Help Center</p>
        <h1 className="mt-3 text-4xl font-extrabold text-slate-900">Frequently asked questions</h1>
        <p className="mt-3 text-lg text-slate-500">Answers to the most common questions. Still stuck? Email us at <a className="font-semibold text-indigo-600" href="mailto:support@yukicares.cloud">support@yukicares.cloud</a>.</p>

        {isLoading && <p className="mt-10 text-slate-400">Loading…</p>}
        {!isLoading && faqs.length === 0 && <p className="mt-10 text-slate-400">No questions published yet.</p>}

        <div className="mt-10 space-y-8">
          {groups.map(([category, items]) => (
            <div key={category}>
              {groups.length > 1 && <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">{category}</h2>}
              <div className="space-y-3">
                {items.map((f) => <Item key={f.id} faq={f} />)}
              </div>
            </div>
          ))}
        </div>
      </section>
    </MarketingLayout>
  );
}
