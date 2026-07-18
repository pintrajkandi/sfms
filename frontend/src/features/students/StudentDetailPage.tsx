import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { students } from "@/api/resources";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/form";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

function feeIcon(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("tuition")) return "🏛";
  if (n.includes("lab")) return "🧪";
  if (n.includes("transport")) return "🚌";
  if (n.includes("librar")) return "📗";
  if (n.includes("sport")) return "⚽";
  if (n.includes("exam")) return "📝";
  return "💰";
}

function InfoRow({ icon, label, value }: { icon: string; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-brand-light text-sm">{icon}</span>
      <div>
        <p className="text-xs text-slate-400">{label}</p>
        <p className="text-sm font-medium text-slate-800">{value}</p>
      </div>
    </div>
  );
}

export function StudentDetailPage() {
  const { id = "" } = useParams();
  const s = useQuery({ queryKey: ["student", id], queryFn: () => students.get(id) }).data;
  const f = useQuery({ queryKey: ["student-fees", id], queryFn: () => students.fees(id) }).data;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between print:hidden">
        <div>
          <p className="text-sm text-slate-400">
            <Link to="/students" className="hover:text-brand">Students</Link> › Student Detail &amp; Fee
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">Student Detail &amp; Fee</h1>
        </div>
        <div className="flex gap-2">
          <button onClick={() => window.print()} className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">🖨 Print</button>
          <Link to={`/fee-collection?student=${id}`} className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">+ Add Fee</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Profile column */}
        <div className="space-y-6">
          <Card className="overflow-hidden p-0">
            <div className="relative h-24 bg-brand-gradient">
              <span className="absolute right-4 top-4 rounded-full bg-white/20 px-3 py-0.5 text-xs font-semibold text-white capitalize">
                {s?.status || "active"}
              </span>
              <div className="absolute -bottom-8 left-6 h-16 w-16 overflow-hidden rounded-2xl border-4 border-white bg-slate-100">
                {s?.photo && <img src={s.photo} alt="" className="h-full w-full object-cover" />}
              </div>
            </div>
            <div className="px-6 pb-6 pt-10">
              <h2 className="text-lg font-bold text-slate-900">{s?.full_name}</h2>
              <p className="text-sm text-slate-500">Student ID: <span className="font-mono text-brand">{s?.student_id}</span></p>
              <div className="mt-5 space-y-4">
                <InfoRow icon="📘" label="Course" value={s?.program || "—"} />
                <InfoRow icon="📚" label="Class / Section" value={`${s?.grade || "—"}${s?.section ? ` / ${s.section}` : ""}`} />
                <InfoRow icon="📅" label="Enrollment Date" value={formatDate(s?.enrollment_date)} />
                <InfoRow icon="✉️" label="Email" value={s?.email || "—"} />
                <InfoRow icon="📞" label="Phone" value={s?.phone || "—"} />
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="mb-3 flex items-center gap-2 text-base font-semibold">👤 Guardian Info</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Name</span><span className="font-medium">{s?.guardian_name || "—"}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Relation</span><span className="font-medium capitalize">{s?.guardian_relation || "—"}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Phone</span><span className="font-medium">{s?.guardian_phone || "—"}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Email</span><span className="font-medium text-brand">{s?.guardian_email || "—"}</span></div>
            </div>
          </Card>
        </div>

        {/* Fee column */}
        <div className="space-y-6 lg:col-span-2">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-brand-gradient p-5 text-white">
              <p className="text-sm text-white/80">Total Fee</p>
              <p className="mt-1 text-2xl font-bold">{formatMoney(f?.total_fee ?? "0")}</p>
            </div>
            <Card>
              <p className="text-sm text-slate-500">Amount Paid</p>
              <p className="mt-1 text-2xl font-bold text-emerald-600">{formatMoney(f?.paid ?? "0")}</p>
              <p className="mt-1 text-xs text-emerald-600">✓ {f?.progress_percent ?? 0}% paid</p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Outstanding</p>
              <p className="mt-1 text-2xl font-bold text-rose-600">{formatMoney(f?.outstanding ?? "0")}</p>
            </Card>
          </div>

          <Card>
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700">Fee Payment Progress</span>
              <span className="font-semibold text-brand">{f?.progress_percent ?? 0}%</span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-brand-gradient" style={{ width: `${f?.progress_percent ?? 0}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-xs text-slate-400">
              <span>Paid: {formatMoney(f?.paid ?? "0")}</span>
              <span>Remaining: {formatMoney(f?.outstanding ?? "0")}</span>
            </div>
          </Card>

          <Card className="p-0">
            <h3 className="px-6 py-4 text-base font-semibold">Fee Breakdown</h3>
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-semibold">Fee Type</th>
                  <th className="px-6 py-3 text-right font-semibold">Amount</th>
                  <th className="px-6 py-3 text-right font-semibold">Paid</th>
                  <th className="px-6 py-3 text-right font-semibold">Balance</th>
                  <th className="px-6 py-3 text-right font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {f?.fee_breakdown.map((row) => (
                  <tr key={row.fee_type}>
                    <td className="px-6 py-3 font-medium text-slate-800">{feeIcon(row.fee_type)} {row.fee_type}</td>
                    <td className="px-6 py-3 text-right">{formatMoney(row.amount)}</td>
                    <td className="px-6 py-3 text-right text-emerald-600">{formatMoney(row.paid)}</td>
                    <td className={`px-6 py-3 text-right ${Number(row.balance) > 0 ? "text-rose-600" : "text-slate-400"}`}>{formatMoney(row.balance)}</td>
                    <td className="px-6 py-3 text-right"><StatusBadge status={row.status} /></td>
                  </tr>
                ))}
                {f && f.fee_breakdown.length === 0 && (
                  <tr><td colSpan={5} className="px-6 py-4 text-slate-400">No fees billed yet.</td></tr>
                )}
              </tbody>
              {f && f.fee_breakdown.length > 0 && (
                <tfoot>
                  <tr className="border-t border-slate-100 bg-slate-50 font-bold">
                    <td className="px-6 py-3">Total</td>
                    <td className="px-6 py-3 text-right">{formatMoney(f.total_fee)}</td>
                    <td className="px-6 py-3 text-right text-emerald-600">{formatMoney(f.paid)}</td>
                    <td className="px-6 py-3 text-right text-rose-600">{formatMoney(f.outstanding)}</td>
                    <td />
                  </tr>
                </tfoot>
              )}
            </table>
          </Card>

          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">Payment History</h3>
            </div>
            <div className="space-y-3">
              {f?.payment_history.map((p, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">✓</span>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{p.fee_type || "Payment"}</p>
                      <p className="text-xs text-slate-400">Receipt #{p.receipt} · {formatDate(p.paid_at)}</p>
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-emerald-600">+{formatMoney(p.amount)}</span>
                </div>
              ))}
              {f && f.payment_history.length === 0 && <p className="text-sm text-slate-400">No payments recorded.</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
