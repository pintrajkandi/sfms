import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { collections } from "@/api/resources";
import type { RiskBand } from "@/api/types";
import { Card } from "@/components/Card";
import { Button, PageHeader, TextArea } from "@/components/form";
import { formatMoney } from "@/lib/money";

const BAND_META: Record<RiskBand, { label: string; badge: string; bar: string; dot: string }> = {
  high: { label: "High risk", badge: "bg-rose-100 text-rose-700", bar: "bg-rose-500", dot: "text-rose-500" },
  medium: { label: "Medium risk", badge: "bg-amber-100 text-amber-700", bar: "bg-amber-500", dot: "text-amber-500" },
  low: { label: "Low risk", badge: "bg-emerald-100 text-emerald-700", bar: "bg-emerald-500", dot: "text-emerald-500" },
};

const SUGGESTIONS = [
  "Who should we call first about overdue fees?",
  "Which grades have the most at-risk students?",
  "Summarize this month's collection risk.",
];

export function CollectionRiskPage() {
  const { data, isLoading } = useQuery({ queryKey: ["collection-risk"], queryFn: () => collections.risk() });
  const [question, setQuestion] = useState("");
  const ask = useMutation({ mutationFn: (q: string) => collections.ask(q) });

  const counts = data?.counts ?? { high: 0, medium: 0, low: 0 };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Predictive Collections"
        subtitle="Which students are most likely to fall behind — and what to do about it"
      />

      {/* Risk band summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {(["high", "medium", "low"] as RiskBand[]).map((band) => (
          <Card key={band}>
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{BAND_META[band].label}</p>
              <span className={`text-lg ${BAND_META[band].dot}`}>●</span>
            </div>
            <p className="mt-1 text-2xl font-bold text-slate-800">{counts[band]}</p>
            <p className="text-xs text-slate-400">students</p>
          </Card>
        ))}
      </div>

      {/* AI assistant */}
      <Card>
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-white">✦</span>
          <h2 className="text-base font-semibold text-slate-800">Ask the collections assistant</h2>
        </div>
        <div className="mt-3 flex flex-col gap-3">
          <TextArea
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Who should we prioritise for follow-up this week?"
          />
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => question.trim() && ask.mutate(question.trim())} disabled={ask.isPending || !question.trim()}>
              {ask.isPending ? "Thinking…" : "Ask"}
            </Button>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => { setQuestion(s); ask.mutate(s); }}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
              >
                {s}
              </button>
            ))}
          </div>
          {ask.data && (
            <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
              <p className="whitespace-pre-wrap text-sm text-slate-700">{ask.data.answer}</p>
              <p className="mt-2 text-[11px] uppercase tracking-wide text-slate-400">
                source: {ask.data.source}
              </p>
            </div>
          )}
          {ask.isError && <p className="text-sm text-rose-600">Couldn't reach the assistant. Try again.</p>}
        </div>
      </Card>

      {/* At-risk table */}
      <Card className="overflow-x-auto p-0">
        <div className="px-6 py-4">
          <h2 className="text-base font-semibold">{data?.total_at_risk ?? 0} students at risk</h2>
        </div>
        <table className="w-full min-w-[820px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Student</th>
              <th className="px-6 py-3 font-semibold">Class</th>
              <th className="px-6 py-3 font-semibold">Risk</th>
              <th className="px-6 py-3 text-right font-semibold">Outstanding</th>
              <th className="px-6 py-3 font-semibold">Why</th>
              <th className="px-6 py-3 font-semibold">Recommended action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.at_risk.map((r) => (
              <tr key={r.student_id} className="hover:bg-slate-50">
                <td className="px-6 py-3">
                  <p className="font-medium text-slate-800">{r.student}</p>
                  <p className="font-mono text-xs text-slate-400">{r.student_id}</p>
                </td>
                <td className="px-6 py-3">{r.grade || "—"}</td>
                <td className="px-6 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-100">
                      <div className={`h-full ${BAND_META[r.risk_band].bar}`} style={{ width: `${r.risk_score}%` }} />
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${BAND_META[r.risk_band].badge}`}>
                      {r.risk_score}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-3 text-right font-semibold text-rose-600">{formatMoney(r.outstanding)}</td>
                <td className="px-6 py-3 text-slate-500">{r.reasons.join(", ")}</td>
                <td className="px-6 py-3 text-slate-600">{r.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {data?.at_risk.length === 0 && (
          <p className="px-6 py-4 text-emerald-600">🎉 No students flagged at risk right now.</p>
        )}
      </Card>
    </div>
  );
}
