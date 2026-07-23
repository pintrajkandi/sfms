import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { documents } from "@/api/resources";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, Select, TextInput, Toast } from "@/components/form";
import { formatDate } from "@/lib/dates";

const CATEGORIES = [
  { value: "student", label: "Student Document" },
  { value: "receipt", label: "Receipt" },
  { value: "invoice", label: "Invoice" },
  { value: "vendor_bill", label: "Vendor Bill" },
  { value: "salary_slip", label: "Salary Slip" },
  { value: "other", label: "Other" },
];
const LABEL: Record<string, string> = Object.fromEntries(CATEGORIES.map((c) => [c.value, c.label]));

const badge: Record<string, string> = {
  student: "bg-brand-light text-brand-dark",
  receipt: "bg-emerald-50 text-emerald-700",
  invoice: "bg-indigo-50 text-indigo-700",
  vendor_bill: "bg-amber-50 text-amber-700",
  salary_slip: "bg-violet-50 text-violet-700",
  other: "bg-slate-100 text-slate-600",
};

export function DocumentsPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["documents", filter],
    queryFn: () => documents.list(filter ? `?category=${filter}` : ""),
  });

  const [form, setForm] = useState({ title: "", category: "student", notes: "" });
  const [file, setFile] = useState<File | null>(null);
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const upload = useMutation({
    mutationFn: () => {
      const fd = new FormData();
      fd.append("title", form.title.trim());
      fd.append("category", form.category);
      if (form.notes.trim()) fd.append("notes", form.notes.trim());
      if (file) fd.append("file", file);
      return documents.upload(fd);
    },
    onSuccess: () => {
      setForm({ title: "", category: form.category, notes: "" });
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      setToast({ msg: "Document uploaded.", tone: "success" });
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (e) => setToast({ msg: e instanceof ApiError ? e.detail : "Upload failed.", tone: "error" }),
  });
  const remove = useMutation({
    mutationFn: (id: number) => documents.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
    onError: (e) => setToast({ msg: e instanceof ApiError ? e.detail : "Delete failed.", tone: "error" }),
  });

  const canUpload = form.title.trim() && file;

  return (
    <div className="space-y-6">
      <PageHeader title="Documents" subtitle="Store and retrieve student docs, receipts, invoices, vendor bills & salary slips" />
      {toast && <Toast message={toast.msg} tone={toast.tone} />}

      <Card>
        <h2 className="text-base font-semibold text-slate-800">Upload a document</h2>
        <form className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-4" onSubmit={(e) => { e.preventDefault(); if (canUpload) upload.mutate(); }}>
          <Labeled label="Title"><TextInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Aadhaar card" /></Labeled>
          <Labeled label="Category">
            <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </Select>
          </Labeled>
          <Labeled label="Notes"><TextInput value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional" /></Labeled>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">File</label>
            <input ref={fileRef} type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-light file:px-3 file:py-2 file:text-sm file:font-medium file:text-brand-dark" />
          </div>
          <div className="sm:col-span-4">
            <Button type="submit" disabled={!canUpload || upload.isPending}>{upload.isPending ? "Uploading…" : "Upload"}</Button>
          </div>
        </form>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-slate-500">Filter:</span>
        <button onClick={() => setFilter("")} className={`rounded-full px-3 py-1 text-xs font-medium ${filter === "" ? "bg-brand text-white" : "bg-slate-100 text-slate-600"}`}>All</button>
        {CATEGORIES.map((c) => (
          <button key={c.value} onClick={() => setFilter(c.value)} className={`rounded-full px-3 py-1 text-xs font-medium ${filter === c.value ? "bg-brand text-white" : "bg-slate-100 text-slate-600"}`}>{c.label}</button>
        ))}
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3 font-semibold">Title</th>
              <th className="px-6 py-3 font-semibold">Category</th>
              <th className="px-6 py-3 font-semibold">Linked student</th>
              <th className="px-6 py-3 font-semibold">Uploaded</th>
              <th className="px-6 py-3 font-semibold">By</th>
              <th className="px-6 py-3 text-right font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((d) => (
              <tr key={d.id} className="hover:bg-slate-50">
                <td className="px-6 py-3 font-medium text-slate-800">{d.title}</td>
                <td className="px-6 py-3"><span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge[d.category] ?? "bg-slate-100"}`}>{LABEL[d.category] ?? d.category}</span></td>
                <td className="px-6 py-3 text-slate-600">{d.student_name || "—"}</td>
                <td className="px-6 py-3 whitespace-nowrap text-slate-500">{formatDate(d.created_at)}</td>
                <td className="px-6 py-3 text-slate-500">{d.uploaded_by_name || "—"}</td>
                <td className="px-6 py-3 text-right">
                  <a href={d.file} target="_blank" rel="noreferrer" className="text-xs font-semibold text-brand hover:underline">Download</a>
                  <button onClick={() => remove.mutate(d.id)} className="ml-3 text-xs text-rose-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {!isLoading && data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No documents yet.</p>}
      </Card>
    </div>
  );
}
