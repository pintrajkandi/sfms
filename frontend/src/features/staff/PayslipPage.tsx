import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { payouts, settings } from "@/api/resources";
import { alertError, alertSuccess, confirmDialog } from "@/lib/alerts";
import { formatMoney } from "@/lib/money";

const STATUS_BADGE: Record<string, string> = {
  submitted: "bg-amber-100 text-amber-700",
  hod_approved: "bg-amber-100 text-amber-700",
  finance_approved: "bg-amber-100 text-amber-700",
  processed: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-600",
};
const STATUS_LABEL: Record<string, string> = {
  submitted: "Pending",
  hod_approved: "Pending",
  finance_approved: "Pending",
  processed: "Paid",
  rejected: "Rejected",
};

export function PayslipPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const slipQ = useQuery({ queryKey: ["payslip", id], queryFn: () => payouts.payslip(id!), enabled: Boolean(id) });
  const settingsQ = useQuery({ queryKey: ["settings"], queryFn: () => settings.get() });

  const transition = useMutation({
    mutationFn: (to: string) => payouts.transition(Number(id), to),
    onSuccess: (_d, to) => {
      qc.invalidateQueries({ queryKey: ["payslip", id] });
      qc.invalidateQueries({ queryKey: ["payouts"] });
      void alertSuccess(to === "processed" ? "Payout marked as paid" : "Payout rejected");
    },
    onError: (e) => void alertError("Could not update status", e instanceof ApiError ? e.detail : "Transition not allowed."),
  });

  if (slipQ.isLoading) return <p className="p-8 text-slate-500">Loading…</p>;
  if (!slipQ.data) return <p className="p-8 text-slate-400">Payslip not found.</p>;

  const s = slipQ.data;
  const school = settingsQ.data?.results?.[0];
  const cur = s.currency;
  const canAct = !["processed", "rejected"].includes(s.status);

  async function act(to: string, label: string) {
    if (await confirmDialog(`${label}?`, `This will mark the payout as "${label}".`, label)) transition.mutate(to);
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      {/* Actions (hidden on print) */}
      <div className="flex flex-wrap items-center justify-between gap-2 print:hidden">
        <button onClick={() => navigate(-1)} className="text-sm font-medium text-slate-500 hover:text-brand">← Back</button>
        <div className="flex flex-wrap gap-2">
          {canAct && (
            <>
              <button onClick={() => act("processed", "Mark as Paid")} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">✓ Mark as Paid</button>
              <button onClick={() => act("rejected", "Reject")} className="rounded-lg border border-rose-200 bg-white px-4 py-2 text-sm font-semibold text-rose-600 hover:bg-rose-50">Reject</button>
            </>
          )}
          <button onClick={() => window.print()} className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">🖨 Print Payslip</button>
        </div>
      </div>

      {/* Payslip document — letterhead */}
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm print:border-0 print:shadow-none">
        <div className="flex items-start justify-between border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3">
            {school?.logo ? (
              <img src={school.logo} alt="School logo" className="h-12 w-12 rounded-lg object-contain" />
            ) : (
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-gradient text-xl font-bold text-white">🏫</div>
            )}
            <div>
              <h1 className="text-lg font-bold text-slate-900">{school?.name || "School"}</h1>
              <p className="text-xs text-slate-500">{[school?.street_address, school?.city, school?.state_province].filter(Boolean).join(", ")}</p>
              <p className="text-xs text-slate-500">{[school?.primary_phone, school?.official_email].filter(Boolean).join(" · ")}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-400">Salary Payslip</p>
            <p className="text-sm font-semibold text-slate-800">{s.pay_period}</p>
            <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_BADGE[s.status] ?? "bg-slate-100 text-slate-600"}`}>{STATUS_LABEL[s.status] ?? s.status}</span>
          </div>
        </div>

        {/* Employee */}
        <div className="grid grid-cols-2 gap-4 py-5 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Employee</p>
            <p className="font-medium text-slate-800">{s.employee_name}</p>
            <p className="text-slate-500">ID: {s.employee_id}</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-400">Pay Period</p>
            <p className="font-medium text-slate-800">{s.pay_period}</p>
          </div>
        </div>

        {/* Earnings & deductions */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="overflow-hidden rounded-xl border border-slate-100">
            <div className="bg-emerald-50 px-4 py-2 text-xs font-bold uppercase tracking-wide text-emerald-700">Earnings</div>
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-50">
                {s.earnings.map((e) => (
                  <tr key={e.label}><td className="px-4 py-2 text-slate-600">{e.label}</td><td className="px-4 py-2 text-right font-medium text-slate-800">{formatMoney(e.amount, cur)}</td></tr>
                ))}
                <tr className="bg-slate-50 font-semibold"><td className="px-4 py-2 text-slate-700">Gross</td><td className="px-4 py-2 text-right text-slate-900">{formatMoney(s.gross_amount, cur)}</td></tr>
              </tbody>
            </table>
          </div>
          <div className="overflow-hidden rounded-xl border border-slate-100">
            <div className="bg-rose-50 px-4 py-2 text-xs font-bold uppercase tracking-wide text-rose-600">Deductions</div>
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-50">
                {s.deductions.map((d) => (
                  <tr key={d.label}><td className="px-4 py-2 text-slate-600">{d.label}</td><td className="px-4 py-2 text-right font-medium text-slate-800">{formatMoney(d.amount, cur)}</td></tr>
                ))}
                <tr className="bg-slate-50 font-semibold"><td className="px-4 py-2 text-slate-700">Total</td><td className="px-4 py-2 text-right text-slate-900">{formatMoney(s.total_deductions, cur)}</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Net */}
        <div className="mt-5 flex items-center justify-between rounded-xl bg-brand-gradient px-5 py-4 text-white">
          <span className="text-sm font-semibold uppercase tracking-wide">Net Pay</span>
          <span className="text-2xl font-bold">{formatMoney(s.net_amount, cur)}</span>
        </div>

        <p className="mt-6 border-t border-slate-100 pt-4 text-center text-[10px] text-slate-300">This is a computer-generated payslip and does not require a signature.</p>
      </div>
    </div>
  );
}
