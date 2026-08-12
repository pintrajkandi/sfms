import { MarketingLayout, CONTACT } from "./MarketingLayout";

export type LegalSection = { heading: string; body: string[] };

/** Shared, readable layout for long-form legal text (Privacy Policy, Terms). */
export function LegalPage({
  kicker,
  title,
  updated,
  intro,
  sections,
}: {
  kicker: string;
  title: string;
  updated: string;
  intro: string;
  sections: LegalSection[];
}) {
  return (
    <MarketingLayout>
      <section className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">{kicker}</p>
        <h1 className="mt-3 text-4xl font-extrabold text-slate-900">{title}</h1>
        <p className="mt-2 text-sm text-slate-400">Last updated: {updated}</p>
        <p className="mt-6 text-lg leading-relaxed text-slate-600">{intro}</p>

        <div className="mt-10 space-y-8">
          {sections.map((s, i) => (
            <div key={s.heading}>
              <h2 className="text-lg font-bold text-slate-900">
                {i + 1}. {s.heading}
              </h2>
              {s.body.map((p, j) => (
                <p key={j} className="mt-2 text-sm leading-relaxed text-slate-600">
                  {p}
                </p>
              ))}
            </div>
          ))}
        </div>

        <p className="mt-12 rounded-xl border border-slate-100 bg-slate-50 p-5 text-sm text-slate-500">
          Questions? Contact us at{" "}
          <a href={`mailto:${CONTACT.email}`} className="font-semibold text-indigo-600 hover:underline">
            {CONTACT.email}
          </a>
          {" · "}
          {CONTACT.address}
        </p>
      </section>
    </MarketingLayout>
  );
}
