import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import { payments } from "@/api/resources";
import { formatMoney } from "@/lib/money";
import { formatDate } from "@/lib/dates";

export function ReceiptPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["receipt", id], queryFn: () => payments.receipt(id!), enabled: Boolean(id) });

  if (isLoading) return <p className="p-8 text-slate-500">Loading…</p>;
  if (!data) return <p className="p-8 text-slate-400">Receipt not found.</p>;

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      {/* Actions (hidden when printing) */}
      <div className="flex items-center justify-between print:hidden">
        <button onClick={() => navigate(-1)} className="text-sm font-medium text-slate-500 hover:text-brand">← Back</button>
        <button onClick={() => window.print()} className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">🖨 Print / Save PDF</button>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm print:border-0 print:shadow-none">
        {/* Header / branding */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3">
            {data.school.logo ? <img src={data.school.logo} alt="logo" className="h-12 w-12 rounded-lg object-cover" /> : <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-gradient text-xl font-bold text-white">₹</div>}
            <div>
              <h1 className="text-lg font-bold text-slate-900">{data.school.name || "School"}</h1>
              <p className="text-xs text-slate-500">{data.school.address}</p>
              <p className="text-xs text-slate-500">{[data.school.phone, data.school.email].filter(Boolean).join(" · ")}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-400">Fee Receipt</p>
            <p className="font-mono text-sm font-semibold text-slate-800">{data.receipt_number}</p>
            <p className="text-xs text-slate-500">{formatDate(data.date)}</p>
            {data.verified && <span className="mt-1 inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">✓ Digitally signed</span>}
          </div>
        </div>

        {/* Student + invoice */}
        <div className="grid grid-cols-2 gap-4 py-5 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Received from</p>
            <p className="font-medium text-slate-800">{data.student.name}</p>
            <p className="text-slate-500">{data.student.student_id} · {data.student.grade}{data.student.section ? ` · ${data.student.section}` : ""}</p>
            {data.student.guardian && <p className="text-slate-500">Guardian: {data.student.guardian}</p>}
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-400">Against invoice</p>
            <p className="font-medium text-slate-800">{data.invoice.number}</p>
            <p className="text-slate-500">Balance: {formatMoney(data.invoice.balance, data.currency)}</p>
          </div>
        </div>

        {/* Amount */}
        <div className="flex items-center justify-between rounded-xl bg-slate-50 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Amount paid</p>
            <p className="text-2xl font-bold text-emerald-600">{formatMoney(data.amount, data.currency)}</p>
          </div>
          <div className="text-right text-sm text-slate-500">
            <p className="capitalize">Method: {data.method.replace("_", " ")}</p>
            {data.reference && <p>Ref: {data.reference}</p>}
          </div>
        </div>

        {/* QR + barcode */}
        <div className="mt-6 flex items-end justify-between">
          <div className="text-center">
            <img src={data.qr} alt="verification QR" className="h-24 w-24" />
            <p className="mt-1 text-[10px] text-slate-400">Scan to verify</p>
          </div>
          <img src={data.barcode} alt="barcode" className="h-14" />
        </div>

        {data.school.footer && <p className="mt-6 border-t border-slate-100 pt-4 text-center text-xs text-slate-400">{data.school.footer}</p>}
        <p className="mt-2 text-center text-[10px] text-slate-300">This is a computer-generated receipt.</p>
      </div>
    </div>
  );
}
