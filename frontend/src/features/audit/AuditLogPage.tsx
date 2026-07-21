import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditLogs } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader, TextInput } from "@/components/form";
import { formatDate } from "@/lib/dates";

const actionTone = (action: string) => {
  if (action.includes("reject") || action.includes("delete") || action.includes("bounce")) return "bg-rose-50 text-rose-600";
  if (action.includes("transition") || action.includes("update")) return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-600";
};

export function AuditLogPage() {
  const [action, setAction] = useState("");
  const [entity, setEntity] = useState("");
  const params = new URLSearchParams();
  if (action.trim()) params.set("action", action.trim());
  if (entity.trim()) params.set("entity_type", entity.trim());
  const qs = params.toString() ? `?${params.toString()}` : "";

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", qs],
    queryFn: () => auditLogs.list(qs),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Audit Log" subtitle="Immutable record of who changed what across the school" />

      <div className="flex flex-wrap gap-3">
        <div className="min-w-[220px] flex-1">
          <label className="mb-1 block text-sm font-medium text-slate-700">Filter by action</label>
          <TextInput value={action} onChange={(e) => setAction(e.target.value)} placeholder="e.g. payment.recorded, payout.transition" />
        </div>
        <div className="min-w-[180px] flex-1">
          <label className="mb-1 block text-sm font-medium text-slate-700">Filter by entity type</label>
          <TextInput value={entity} onChange={(e) => setEntity(e.target.value)} placeholder="e.g. Invoice, Payout" />
        </div>
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[820px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">When</th>
              <th className="px-6 py-3 font-semibold">Actor</th>
              <th className="px-6 py-3 font-semibold">Action</th>
              <th className="px-6 py-3 font-semibold">Entity</th>
              <th className="px-6 py-3 font-semibold">Summary</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((log) => (
              <tr key={log.id} className="hover:bg-slate-50 align-top">
                <td className="px-6 py-3 whitespace-nowrap text-slate-500">{formatDate(log.created_at)}</td>
                <td className="px-6 py-3 text-slate-700">{log.actor_label || "System"}</td>
                <td className="px-6 py-3">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${actionTone(log.action)}`}>{log.action}</span>
                </td>
                <td className="px-6 py-3 font-mono text-xs text-slate-500">{log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</td>
                <td className="px-6 py-3 text-slate-700">{log.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {!isLoading && data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No audit entries match these filters.</p>}
      </Card>
    </div>
  );
}
