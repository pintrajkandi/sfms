import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { support } from "@/api/resources";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, Select, TextArea, TextInput, Toast } from "@/components/form";
import { formatDate } from "@/lib/dates";

const CATEGORIES = [
  { value: "billing", label: "Billing" },
  { value: "technical", label: "Technical" },
  { value: "feature", label: "Feature Request" },
  { value: "account", label: "Account" },
  { value: "other", label: "Other" },
];

const statusBadge: Record<string, string> = {
  open: "bg-amber-50 text-amber-700",
  in_progress: "bg-brand-light text-brand-dark",
  resolved: "bg-emerald-50 text-emerald-700",
};

const EMPTY = { subject: "", category: "technical", message: "", contact_email: "" };

export function SupportPage() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["support-tickets"], queryFn: () => support.list() });
  const [form, setForm] = useState({ ...EMPTY });
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);
  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = useMutation({
    mutationFn: () => support.create(form),
    onSuccess: () => {
      setForm({ ...EMPTY });
      setToast({ msg: "Thanks! Your request has been sent to our support team.", tone: "success" });
      qc.invalidateQueries({ queryKey: ["support-tickets"] });
    },
    onError: (e) => setToast({ msg: e instanceof ApiError ? e.detail : "Could not send your request.", tone: "error" }),
  });

  const canSubmit = form.subject.trim() && form.message.trim();

  return (
    <div className="space-y-6">
      <PageHeader title="Support" subtitle="Reach out to the Fee Ledger team for any issue or request" />
      {toast && <Toast message={toast.msg} tone={toast.tone} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Raise a request */}
        <Card className="lg:col-span-2">
          <h2 className="text-base font-semibold text-slate-800">Raise a support request</h2>
          <p className="text-sm text-slate-500">Describe the issue and we'll get back to you by email.</p>
          <form className="mt-4 space-y-4" onSubmit={(e) => { e.preventDefault(); if (canSubmit) submit.mutate(); }}>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Labeled label="Subject" required>
                <TextInput value={form.subject} onChange={(e) => set("subject", e.target.value)} placeholder="Brief summary of the issue" />
              </Labeled>
              <Labeled label="Category">
                <Select value={form.category} onChange={(e) => set("category", e.target.value)}>
                  {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </Select>
              </Labeled>
            </div>
            <Labeled label="Contact email">
              <TextInput type="email" value={form.contact_email} onChange={(e) => set("contact_email", e.target.value)} placeholder="Where should we reply?" />
            </Labeled>
            <Labeled label="Message" required>
              <TextArea rows={5} value={form.message} onChange={(e) => set("message", e.target.value)} placeholder="Tell us what's happening, and any steps to reproduce…" />
            </Labeled>
            <Button type="submit" disabled={!canSubmit || submit.isPending}>
              {submit.isPending ? "Sending…" : "Send request"}
            </Button>
          </form>
        </Card>

        {/* Contact + tips */}
        <Card>
          <h2 className="text-base font-semibold text-slate-800">Other ways to reach us</h2>
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-light">✉️</span>
              <div>
                <p className="font-medium text-slate-800">Email</p>
                <a href="mailto:support@feeledger.app" className="text-brand hover:underline">support@feeledger.app</a>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50">💬</span>
              <div>
                <p className="font-medium text-slate-800">Response time</p>
                <p className="text-slate-500">Usually within 1 business day</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* My requests */}
      <Card className="overflow-x-auto p-0">
        <div className="px-6 py-4">
          <h2 className="text-base font-semibold text-slate-800">Your requests</h2>
        </div>
        <table className="w-full min-w-[640px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Date</th>
              <th className="px-6 py-3 font-semibold">Subject</th>
              <th className="px-6 py-3 font-semibold">Category</th>
              <th className="px-6 py-3 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((t) => (
              <tr key={t.id} className="hover:bg-slate-50">
                <td className="px-6 py-3 whitespace-nowrap text-slate-500">{formatDate(t.created_at)}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{t.subject}</td>
                <td className="px-6 py-3 capitalize text-slate-600">{t.category.replace("_", " ")}</td>
                <td className="px-6 py-3">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusBadge[t.status] ?? "bg-slate-100 text-slate-600"}`}>{t.status.replace("_", " ")}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No requests yet.</p>}
      </Card>
    </div>
  );
}
