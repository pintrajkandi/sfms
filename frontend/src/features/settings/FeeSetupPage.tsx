import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fees } from "@/api/resources";
import { ApiError } from "@/api/client";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, Select, TextInput, Toast } from "@/components/form";

const PALETTE = ["#6366F1", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"];

export function FeeSetupPage({ embedded = false }: { embedded?: boolean }) {
  const qc = useQueryClient();
  const cats = useQuery({ queryKey: ["fee-categories"], queryFn: () => fees.categories() });
  const types = useQuery({ queryKey: ["fee-types"], queryFn: () => fees.types() });
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);

  const [catName, setCatName] = useState("");
  const [catColor, setCatColor] = useState(PALETTE[0]);
  const [ft, setFt] = useState({ name: "", category: "" });

  const fail = (e: unknown) =>
    setToast({ msg: e instanceof ApiError ? e.detail : "Something went wrong.", tone: "error" });
  const refetchCats = () => qc.invalidateQueries({ queryKey: ["fee-categories"] });
  const refetchTypes = () => qc.invalidateQueries({ queryKey: ["fee-types"] });

  const addCat = useMutation({
    mutationFn: () => fees.createCategory({ name: catName.trim(), color: catColor }),
    onSuccess: () => { setCatName(""); refetchCats(); },
    onError: fail,
  });
  const delCat = useMutation({ mutationFn: (id: number) => fees.removeCategory(id), onSuccess: refetchCats, onError: fail });
  const addType = useMutation({
    mutationFn: () =>
      fees.createType({ name: ft.name.trim(), category: Number(ft.category) }),
    onSuccess: () => { setFt({ name: "", category: "" }); refetchTypes(); },
    onError: fail,
  });
  const delType = useMutation({ mutationFn: (id: number) => fees.removeType(id), onSuccess: refetchTypes, onError: fail });

  return (
    <div className="space-y-6">
      {!embedded && (
        <PageHeader title="Fee Setup" subtitle="Manage fee categories and fee types used in fee collection" />
      )}
      {toast && <Toast message={toast.msg} tone={toast.tone} />}

      {/* Categories */}
      <Card>
        <h2 className="text-base font-semibold text-slate-800">Fee categories</h2>
        <p className="text-sm text-slate-500">Groupings shown on invoices (e.g. Academic, Facility, Transport).</p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); if (catName.trim()) addCat.mutate(); }}>
          <Labeled label="Category name"><TextInput value={catName} onChange={(e) => setCatName(e.target.value)} placeholder="e.g. Academic" /></Labeled>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Color</label>
            <div className="flex gap-1.5">
              {PALETTE.map((c) => (
                <button key={c} type="button" onClick={() => setCatColor(c)} style={{ background: c }}
                  className={`h-7 w-7 rounded-full ${catColor === c ? "ring-2 ring-offset-2 ring-slate-400" : ""}`} />
              ))}
            </div>
          </div>
          <Button type="submit" disabled={addCat.isPending || !catName.trim()}>Add category</Button>
        </form>

        <div className="mt-4 flex flex-wrap gap-2">
          {cats.data?.results.map((c) => (
            <span key={c.id} className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-sm">
              <span className="h-3 w-3 rounded-full" style={{ background: c.color }} />
              {c.name}
              <button type="button" onClick={() => delCat.mutate(c.id)} className="text-slate-400 hover:text-rose-600">×</button>
            </span>
          ))}
          {cats.data?.results.length === 0 && <span className="text-sm text-slate-400">No categories yet.</span>}
        </div>
      </Card>

      {/* Fee types */}
      <Card>
        <h2 className="text-base font-semibold text-slate-800">Fee types</h2>
        <p className="text-sm text-slate-500">The billable items (Tuition, Lab, Transport…) picked during fee collection.</p>
        <form className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); if (ft.name.trim() && ft.category) addType.mutate(); }}>
          <Labeled label="Fee type name"><TextInput value={ft.name} onChange={(e) => setFt({ ...ft, name: e.target.value })} placeholder="e.g. Tuition" /></Labeled>
          <Labeled label="Category">
            <Select value={ft.category} onChange={(e) => setFt({ ...ft, category: e.target.value })}>
              <option value="">Select category</option>
              {cats.data?.results.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </Labeled>
          <div className="flex items-end">
            <Button type="submit" disabled={addType.isPending || !ft.name.trim() || !ft.category}>Add fee type</Button>
          </div>
        </form>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr><th className="px-4 py-2">Name</th><th className="px-4 py-2">Category</th><th className="px-4 py-2"></th></tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {types.data?.results.map((t) => (
                <tr key={t.id}>
                  <td className="px-4 py-2 font-medium text-slate-800">{t.name}</td>
                  <td className="px-4 py-2 text-slate-500">{t.category_name}</td>
                  <td className="px-4 py-2 text-right"><button type="button" onClick={() => delType.mutate(t.id)} className="text-xs text-rose-600 hover:underline">Delete</button></td>
                </tr>
              ))}
              {types.data?.results.length === 0 && <tr><td colSpan={3} className="px-4 py-3 text-slate-400">No fee types yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
