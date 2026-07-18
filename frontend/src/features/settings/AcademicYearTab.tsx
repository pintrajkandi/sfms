import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ApiError } from "@/api/client";
import { academicYears } from "@/api/resources";
import { Button, Labeled, TextInput, Toast } from "@/components/form";
import { formatDate } from "@/lib/dates";

export function AcademicYearTab() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["academic-years"], queryFn: () => academicYears.list() });
  const [form, setForm] = useState({ label: "", start_date: "", end_date: "", is_current: false });
  const [err, setErr] = useState("");
  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const add = useMutation({
    mutationFn: () => academicYears.create(form),
    onSuccess: () => {
      setErr("");
      setForm({ label: "", start_date: "", end_date: "", is_current: false });
      qc.invalidateQueries({ queryKey: ["academic-years"] });
    },
    onError: (e) => setErr(e instanceof ApiError ? e.detail : "Could not add academic year."),
  });

  return (
    <>
      <div className="mb-5">
        <h2 className="text-base font-semibold text-slate-900">Academic Year</h2>
        <p className="text-sm text-slate-500">Define academic years used across fees and invoices.</p>
      </div>

      <div className="mb-6 overflow-hidden rounded-xl border border-slate-100">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-2 font-medium">Label</th>
              <th className="px-4 py-2 font-medium">Start</th>
              <th className="px-4 py-2 font-medium">End</th>
              <th className="px-4 py-2 font-medium">Current</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((y) => (
              <tr key={y.id}>
                <td className="px-4 py-2 font-medium text-slate-800">{y.label}</td>
                <td className="px-4 py-2 text-slate-600">{formatDate(y.start_date)}</td>
                <td className="px-4 py-2 text-slate-600">{formatDate(y.end_date)}</td>
                <td className="px-4 py-2">{y.is_current ? "✅" : "—"}</td>
              </tr>
            ))}
            {data?.results.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-3 text-slate-400">
                  No academic years yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {err && (
        <div className="mb-4">
          <Toast tone="error" message={err} />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Labeled label="Label">
          <TextInput placeholder="2024-2025" value={form.label} onChange={(e) => set("label", e.target.value)} />
        </Labeled>
        <label className="flex items-center gap-2 self-end pb-2.5 text-sm text-slate-700">
          <input type="checkbox" className="h-4 w-4 rounded border-slate-300" checked={form.is_current} onChange={(e) => set("is_current", e.target.checked)} />
          Set as current
        </label>
        <Labeled label="Start date">
          <TextInput type="date" value={form.start_date} onChange={(e) => set("start_date", e.target.value)} />
        </Labeled>
        <Labeled label="End date">
          <TextInput type="date" value={form.end_date} onChange={(e) => set("end_date", e.target.value)} />
        </Labeled>
        <div className="sm:col-span-2">
          <Button type="button" onClick={() => add.mutate()} disabled={!form.label || !form.start_date || !form.end_date || add.isPending}>
            {add.isPending ? "Adding…" : "Add academic year"}
          </Button>
        </div>
      </div>
    </>
  );
}
