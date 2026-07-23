import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { parents, students, type Parent } from "@/api/resources";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, TextInput, Toast } from "@/components/form";

function AddChild({ parent, onDone }: { parent: Parent; onDone: () => void }) {
  const [term, setTerm] = useState("");
  const search = useQuery({ queryKey: ["parent-child-search", term], queryFn: () => students.search(term), enabled: term.length > 0 });
  const attach = useMutation({
    mutationFn: (studentId: number) => students.update(studentId, { parent: parent.id }),
    onSuccess: onDone,
  });
  return (
    <div className="mt-2">
      <TextInput value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Search a student to add…" className="max-w-xs" />
      {term && (
        <div className="mt-1 max-w-xs divide-y divide-slate-50 rounded-lg border border-slate-100">
          {(search.data?.results ?? []).slice(0, 6).map((s) => (
            <button key={s.id} onClick={() => attach.mutate(s.id)} className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-slate-50">
              <span>{s.full_name} <span className="font-mono text-xs text-slate-400">{s.student_id}</span></span>
              <span className="text-xs text-brand">Add</span>
            </button>
          ))}
          {search.data?.results.length === 0 && <p className="px-3 py-1.5 text-xs text-slate-400">No match.</p>}
        </div>
      )}
    </div>
  );
}

export function ParentsPage() {
  const qc = useQueryClient();
  const [term, setTerm] = useState("");
  const { data } = useQuery({ queryKey: ["parents", term], queryFn: () => parents.list(term) });
  const [form, setForm] = useState({ name: "", relation: "Father", phone: "", email: "", occupation: "" });
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);
  const [adding, setAdding] = useState<number | null>(null);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["parents"] });
  const fail = (e: unknown) => setToast({ msg: e instanceof ApiError ? e.detail : "Something went wrong.", tone: "error" });

  const create = useMutation({
    mutationFn: () => parents.create(form),
    onSuccess: () => { setForm({ name: "", relation: "Father", phone: "", email: "", occupation: "" }); invalidate(); },
    onError: fail,
  });
  const remove = useMutation({ mutationFn: (id: number) => parents.remove(id), onSuccess: invalidate, onError: fail });
  const detach = useMutation({ mutationFn: (studentId: number) => students.update(studentId, { parent: null }), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-6">
      <PageHeader title="Parents" subtitle="Parent records with their children (siblings grouped)" />
      {toast && <Toast message={toast.msg} tone={toast.tone} />}

      <Card>
        <h2 className="text-base font-semibold text-slate-800">Add a parent</h2>
        <form className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-5" onSubmit={(e) => { e.preventDefault(); if (form.name.trim()) create.mutate(); }}>
          <Labeled label="Name"><TextInput value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ravi Kumar" /></Labeled>
          <Labeled label="Relation"><TextInput value={form.relation} onChange={(e) => setForm({ ...form, relation: e.target.value })} placeholder="Father" /></Labeled>
          <Labeled label="Phone"><TextInput value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></Labeled>
          <Labeled label="Email"><TextInput type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Labeled>
          <div className="flex items-end"><Button type="submit" disabled={create.isPending || !form.name.trim()}>Add parent</Button></div>
        </form>
      </Card>

      <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Search parents by name or phone…" className="w-full max-w-md rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {data?.results.map((p) => (
          <Card key={p.id}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-800">{p.name} <span className="text-sm font-normal text-slate-400">{p.relation}</span></h3>
                <p className="text-sm text-slate-500">{p.phone || "—"}{p.email ? ` · ${p.email}` : ""}</p>
              </div>
              <button onClick={() => remove.mutate(p.id)} className="text-xs font-medium text-rose-600 hover:underline">Delete</button>
            </div>
            <div className="mt-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Children ({p.children.length})</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {p.children.map((c) => (
                  <span key={c.id} className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                    {c.name} · {c.grade || "—"}
                    <button onClick={() => detach.mutate(c.id)} className="text-slate-400 hover:text-rose-600">×</button>
                  </span>
                ))}
                {p.children.length === 0 && <span className="text-xs text-slate-400">No children linked.</span>}
              </div>
              {adding === p.id ? (
                <AddChild parent={p} onDone={() => { invalidate(); setAdding(null); }} />
              ) : (
                <button onClick={() => setAdding(p.id)} className="mt-2 text-sm font-semibold text-brand hover:underline">+ Add child</button>
              )}
            </div>
          </Card>
        ))}
        {data?.results.length === 0 && <p className="text-slate-400">No parents yet.</p>}
      </div>
    </div>
  );
}
