import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { students } from "@/api/resources";
import type { ImportResult, Paginated, Student } from "@/api/types";
import { api } from "@/api/client";
import { Card } from "@/components/Card";

export function StudentsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["students", search],
    queryFn: () => api.get<Paginated<Student>>(`/students/${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  });

  async function doImport(file: File) {
    setBusy(true);
    setErr("");
    setResult(null);
    try {
      const r = await students.importCsv(file);
      setResult(r);
      qc.invalidateQueries({ queryKey: ["students"] });
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Import failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Students</h1>
          <p className="text-sm text-slate-500">Enrolled students</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name, ID, guardian…"
            className="w-56 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <button onClick={() => setImporting(true)} className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">⬆ Import</button>
          <a href={students.exportUrl("csv")} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">CSV</a>
          <a href={students.exportUrl("xlsx")} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">Excel</a>
          <Link to="/students/new" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">Add student</Link>
        </div>
      </header>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="border-b border-slate-100 text-left text-slate-500">
            <tr>
              <th className="px-6 py-3 font-medium">Student ID</th>
              <th className="px-6 py-3 font-medium">Name</th>
              <th className="px-6 py-3 font-medium">Class</th>
              <th className="px-6 py-3 font-medium">Guardian</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((s) => (
              <tr key={s.id} onClick={() => navigate(`/students/${s.id}`)} className="cursor-pointer hover:bg-slate-50">
                <td className="px-6 py-3 font-mono text-xs">{s.student_id}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{s.full_name}</td>
                <td className="px-6 py-3">{s.grade || "—"}</td>
                <td className="px-6 py-3 text-slate-600">{s.guardian_name || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No students found.</p>}
      </Card>

      {/* Import modal */}
      {importing && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4" onClick={() => setImporting(false)}>
          <div className="absolute inset-0 bg-slate-900/40" />
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold text-slate-900">Import Students</h2>
            <p className="mt-1 text-sm text-slate-500">Upload a CSV. Not sure of the format? <a href={students.templateUrl()} className="font-semibold text-brand hover:underline">Download the template</a>.</p>

            <button
              onClick={() => fileRef.current?.click()}
              className="mt-4 flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-8 text-slate-400 hover:border-brand"
            >
              <span className="text-3xl">📄</span>
              <span className="mt-1 text-sm font-semibold text-slate-700">{busy ? "Importing…" : "Choose a CSV file"}</span>
            </button>
            <input ref={fileRef} type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => e.target.files?.[0] && doImport(e.target.files[0])} />

            {err && <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</p>}
            {result && (
              <div className="mt-4 space-y-2">
                <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">✓ Imported {result.created} student(s){result.error_count ? `, ${result.error_count} row(s) skipped` : ""}.</p>
                {result.errors.length > 0 && (
                  <div className="max-h-40 overflow-y-auto rounded-lg border border-slate-100 p-2 text-xs text-slate-600">
                    {result.errors.map((e, i) => <p key={i}>Row {e.row}: {e.error}</p>)}
                  </div>
                )}
              </div>
            )}

            <div className="mt-5 flex justify-end">
              <button onClick={() => setImporting(false)} className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Done</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
