import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { departments } from "@/api/resources";
import { Button, TextInput, Toast } from "@/components/form";

export function DepartmentsTab() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["departments"], queryFn: () => departments.list() });
  const [name, setName] = useState("");
  const [err, setErr] = useState("");

  const invalidate = () => qc.invalidateQueries({ queryKey: ["departments"] });
  const fail = (e: unknown) => setErr(e instanceof ApiError ? e.detail : "Something went wrong.");

  const add = useMutation({
    mutationFn: () => departments.create({ name: name.trim() }),
    onSuccess: () => { setErr(""); setName(""); invalidate(); },
    onError: fail,
  });
  const remove = useMutation({ mutationFn: (id: number) => departments.remove(id), onSuccess: invalidate, onError: fail });

  return (
    <>
      <div className="mb-5">
        <h2 className="text-base font-semibold text-slate-900">Departments</h2>
        <p className="text-sm text-slate-500">Departments used to tag teachers (e.g. Science, Administration).</p>
      </div>

      {err && <div className="mb-4"><Toast tone="error" message={err} /></div>}

      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); if (name.trim()) add.mutate(); }}>
        <div className="min-w-[220px] flex-1">
          <label className="mb-1 block text-sm font-medium text-slate-700">Add a department</label>
          <TextInput value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Mathematics" />
        </div>
        <Button type="submit" disabled={add.isPending || !name.trim()}>Add department</Button>
      </form>

      <div className="mt-5 flex flex-wrap gap-2">
        {data?.results.map((d) => (
          <span key={d.id} className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-sm">
            {d.name}
            <button type="button" onClick={() => remove.mutate(d.id)} className="text-slate-400 hover:text-rose-600">×</button>
          </span>
        ))}
        {data?.results.length === 0 && <span className="text-sm text-slate-400">No departments yet.</span>}
      </div>
    </>
  );
}
