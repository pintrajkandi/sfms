import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { classes } from "@/api/resources";
import { ApiError } from "@/api/client";
import { Card } from "@/components/Card";
import { Button, PageHeader, TextInput, Toast } from "@/components/form";

export function ClassesPage({ embedded = false }: { embedded?: boolean }) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["classes"], queryFn: () => classes.list() });
  const [name, setName] = useState("");
  const [sectionInput, setSectionInput] = useState<Record<number, string>>({});
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["classes"] });
  const fail = (e: unknown) =>
    setToast({ msg: e instanceof ApiError ? e.detail : "Something went wrong.", tone: "error" });

  const addClass = useMutation({
    mutationFn: () => classes.create({ name: name.trim(), order: data?.count ?? 0 }),
    onSuccess: () => { setName(""); invalidate(); },
    onError: fail,
  });
  const delClass = useMutation({ mutationFn: (id: number) => classes.remove(id), onSuccess: invalidate, onError: fail });
  const addSection = useMutation({
    mutationFn: (v: { classId: number; name: string }) =>
      classes.addSection({ school_class: v.classId, name: v.name.trim() }),
    onSuccess: (_d, v) => { setSectionInput((s) => ({ ...s, [v.classId]: "" })); invalidate(); },
    onError: fail,
  });
  const delSection = useMutation({ mutationFn: (id: number) => classes.removeSection(id), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-6">
      {!embedded && (
        <PageHeader title="Classes & Sections" subtitle="Manage the classes and sections used across the school" />
      )}
      {toast && <Toast message={toast.msg} tone={toast.tone} />}

      <Card>
        <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); if (name.trim()) addClass.mutate(); }}>
          <div className="flex-1 min-w-[220px]">
            <label className="mb-1 block text-sm font-medium text-slate-700">Add a class</label>
            <TextInput value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Grade 1 or Class 10" />
          </div>
          <Button type="submit" disabled={addClass.isPending || !name.trim()}>Add class</Button>
        </form>
      </Card>

      {isLoading && <p className="text-slate-500">Loading…</p>}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {data?.results.map((c) => (
          <Card key={c.id}>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-800">{c.name}</h3>
              <button
                type="button"
                onClick={() => delClass.mutate(c.id)}
                className="text-xs font-medium text-rose-600 hover:underline"
              >
                Delete class
              </button>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {c.sections.length === 0 && <span className="text-xs text-slate-400">No sections yet.</span>}
              {c.sections.map((s) => (
                <span key={s.id} className="flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                  {s.name}
                  <button type="button" onClick={() => delSection.mutate(s.id)} className="text-slate-400 hover:text-rose-600">×</button>
                </span>
              ))}
            </div>

            <form
              className="mt-3 flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                const val = (sectionInput[c.id] ?? "").trim();
                if (val) addSection.mutate({ classId: c.id, name: val });
              }}
            >
              <TextInput
                value={sectionInput[c.id] ?? ""}
                onChange={(e) => setSectionInput((s) => ({ ...s, [c.id]: e.target.value }))}
                placeholder="Add section (e.g. A)"
                className="max-w-[180px]"
              />
              <Button type="submit" variant="ghost">Add</Button>
            </form>
          </Card>
        ))}
      </div>
    </div>
  );
}
