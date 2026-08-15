import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { hostel, students } from "@/api/resources";
import type { Student } from "@/api/types";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, Select, TextInput, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";

type Tab = "hostels" | "rooms" | "residents" | "expenses" | "report";
const TABS: { key: Tab; label: string }[] = [
  { key: "hostels", label: "Hostels" },
  { key: "rooms", label: "Rooms" },
  { key: "residents", label: "Residents" },
  { key: "expenses", label: "Expenses" },
  { key: "report", label: "Occupancy & P/L" },
];

const CATEGORIES = ["mess", "maintenance", "utilities", "staff_salary", "other"];

function useToast() {
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);
  const fail = (e: unknown) => setToast({ msg: e instanceof ApiError ? e.detail : "Something went wrong.", tone: "error" });
  return { toast, fail };
}

function Hostels() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["hostels"], queryFn: () => hostel.hostels() });
  const { toast, fail } = useToast();
  const [form, setForm] = useState({ name: "", code: "", monthly_fee: "0.00", capacity: "", warden_name: "", warden_phone: "" });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["hostels"] });
  const add = useMutation({
    mutationFn: () => hostel.createHostel({ name: form.name, code: form.code, monthly_fee: form.monthly_fee, capacity: Number(form.capacity || 0), warden_name: form.warden_name, warden_phone: form.warden_phone }),
    onSuccess: () => { setForm({ name: "", code: "", monthly_fee: "0.00", capacity: "", warden_name: "", warden_phone: "" }); invalidate(); },
    onError: fail,
  });
  const remove = useMutation({ mutationFn: (id: number) => hostel.removeHostel(id), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <form className="grid grid-cols-1 gap-3 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); if (form.name && form.code) add.mutate(); }}>
        <Labeled label="Hostel name"><TextInput value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Boys Block A" /></Labeled>
        <Labeled label="Code"><TextInput value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="e.g. H-A" /></Labeled>
        <Labeled label="Monthly fee (₹)"><TextInput inputMode="decimal" value={form.monthly_fee} onChange={(e) => setForm({ ...form, monthly_fee: e.target.value })} /></Labeled>
        <Labeled label="Capacity (beds)"><TextInput type="number" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} /></Labeled>
        <Labeled label="Warden"><TextInput value={form.warden_name} onChange={(e) => setForm({ ...form, warden_name: e.target.value })} /></Labeled>
        <div className="flex items-end"><Button type="submit" disabled={add.isPending || !form.name || !form.code}>Add hostel</Button></div>
      </form>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Code</th><th className="px-4 py-2">Hostel</th><th className="px-4 py-2 text-right">Fee</th><th className="px-4 py-2 text-right">Residents</th><th className="px-4 py-2 text-right">Capacity</th><th className="px-4 py-2">Warden</th><th className="px-4 py-2"></th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((h) => (
              <tr key={h.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-slate-700">{h.code}</td>
                <td className="px-4 py-2 font-medium text-slate-800">{h.name}</td>
                <td className="px-4 py-2 text-right">{formatMoney(h.monthly_fee)}</td>
                <td className="px-4 py-2 text-right">{h.resident_count}</td>
                <td className="px-4 py-2 text-right">{h.capacity || "—"}</td>
                <td className="px-4 py-2 text-slate-600">{h.warden_name || "—"}</td>
                <td className="px-4 py-2 text-right"><button onClick={() => remove.mutate(h.id)} className="text-xs text-rose-600 hover:underline">Delete</button></td>
              </tr>
            ))}
            {data?.results.length === 0 && <tr><td colSpan={7} className="px-4 py-3 text-slate-400">No hostels yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Rooms() {
  const qc = useQueryClient();
  const hostels = useQuery({ queryKey: ["hostels"], queryFn: () => hostel.hostels() });
  const { data } = useQuery({ queryKey: ["hostel-rooms"], queryFn: () => hostel.rooms() });
  const { toast, fail } = useToast();
  const [form, setForm] = useState({ hostel: "", room_number: "", floor: "", capacity: "" });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["hostel-rooms"] });
  const add = useMutation({
    mutationFn: () => hostel.createRoom({ hostel: Number(form.hostel), room_number: form.room_number, floor: form.floor, capacity: Number(form.capacity || 0) }),
    onSuccess: () => { setForm({ ...form, room_number: "", floor: "", capacity: "" }); invalidate(); },
    onError: fail,
  });
  const remove = useMutation({ mutationFn: (id: number) => hostel.removeRoom(id), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <form className="grid grid-cols-1 gap-3 sm:grid-cols-4" onSubmit={(e) => { e.preventDefault(); if (form.hostel && form.room_number) add.mutate(); }}>
        <Labeled label="Hostel">
          <Select value={form.hostel} onChange={(e) => setForm({ ...form, hostel: e.target.value })}>
            <option value="">Select</option>
            {hostels.data?.results.map((h) => <option key={h.id} value={h.id}>{h.code} · {h.name}</option>)}
          </Select>
        </Labeled>
        <Labeled label="Room number"><TextInput value={form.room_number} onChange={(e) => setForm({ ...form, room_number: e.target.value })} placeholder="101" /></Labeled>
        <Labeled label="Floor"><TextInput value={form.floor} onChange={(e) => setForm({ ...form, floor: e.target.value })} placeholder="1st" /></Labeled>
        <Labeled label="Beds"><TextInput type="number" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} placeholder="4" /></Labeled>
        <div className="flex items-end"><Button type="submit" disabled={add.isPending || !form.hostel || !form.room_number}>Add room</Button></div>
      </form>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Hostel</th><th className="px-4 py-2">Room</th><th className="px-4 py-2">Floor</th><th className="px-4 py-2 text-right">Beds</th><th className="px-4 py-2"></th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-slate-700">{r.hostel_code}</td>
                <td className="px-4 py-2 font-medium text-slate-800">{r.room_number}</td>
                <td className="px-4 py-2 text-slate-600">{r.floor || "—"}</td>
                <td className="px-4 py-2 text-right">{r.capacity || "—"}</td>
                <td className="px-4 py-2 text-right"><button onClick={() => remove.mutate(r.id)} className="text-xs text-rose-600 hover:underline">Delete</button></td>
              </tr>
            ))}
            {data?.results.length === 0 && <tr><td colSpan={5} className="px-4 py-3 text-slate-400">No rooms yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Residents() {
  const qc = useQueryClient();
  const hostels = useQuery({ queryKey: ["hostels"], queryFn: () => hostel.hostels() });
  const { toast, fail } = useToast();
  const [hostelId, setHostelId] = useState("");
  const [q, setQ] = useState("");
  const [room, setRoom] = useState("");
  const [picked, setPicked] = useState<Student | null>(null);

  const residents = useQuery({
    queryKey: ["hostel-residents", hostelId],
    queryFn: () => students.byHostel(hostelId),
    enabled: !!hostelId,
  });
  const search = useQuery({
    queryKey: ["student-search", q],
    queryFn: () => students.search(q),
    enabled: q.trim().length >= 2,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["hostel-residents", hostelId] });
    qc.invalidateQueries({ queryKey: ["hostels"] });
    qc.invalidateQueries({ queryKey: ["hostel-report"] });
  };
  const allocate = useMutation({
    mutationFn: () => students.update(picked!.id, { hostel: Number(hostelId), hostel_room: room }),
    onSuccess: () => { setPicked(null); setQ(""); setRoom(""); invalidate(); },
    onError: fail,
  });
  const removeRes = useMutation({
    mutationFn: (id: number) => students.update(id, { hostel: null, hostel_room: "" }),
    onSuccess: invalidate,
    onError: fail,
  });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <Labeled label="Hostel">
        <Select value={hostelId} onChange={(e) => { setHostelId(e.target.value); setPicked(null); setQ(""); }}>
          <option value="">Select a hostel to manage residents</option>
          {hostels.data?.results.map((h) => <option key={h.id} value={h.id}>{h.code} · {h.name}</option>)}
        </Select>
      </Labeled>

      {hostelId && (
        <>
          <div className="rounded-xl border border-slate-100 p-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-800">Add a resident</h3>
            {picked ? (
              <div className="flex flex-wrap items-end gap-3">
                <div className="text-sm">
                  <p className="font-medium text-slate-800">{picked.full_name}</p>
                  <p className="text-slate-500">{picked.student_id} · Class {picked.grade || "—"}</p>
                </div>
                <Labeled label="Room number"><TextInput value={room} onChange={(e) => setRoom(e.target.value)} placeholder="e.g. 101" /></Labeled>
                <Button onClick={() => allocate.mutate()} disabled={allocate.isPending}>Allocate</Button>
                <button type="button" onClick={() => setPicked(null)} className="pb-2 text-sm text-slate-500 hover:text-slate-700">Cancel</button>
              </div>
            ) : (
              <div className="space-y-2">
                <TextInput value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search a student by name, ID or phone…" />
                {q.trim().length >= 2 && (
                  <div className="max-h-56 divide-y divide-slate-50 overflow-y-auto rounded-lg border border-slate-100">
                    {search.data?.results.map((s) => (
                      <button key={s.id} type="button" onClick={() => { setPicked(s); setRoom(s.hostel_room || ""); }}
                        className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50">
                        <span><span className="font-medium text-slate-800">{s.full_name}</span> <span className="text-slate-400">· {s.student_id}</span></span>
                        {s.hostel && <span className="text-xs text-amber-600">already in a hostel</span>}
                      </button>
                    ))}
                    {search.data && search.data.results.length === 0 && <p className="px-3 py-2 text-sm text-slate-400">No students found.</p>}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr><th className="px-4 py-2">Student</th><th className="px-4 py-2">ID</th><th className="px-4 py-2">Class</th><th className="px-4 py-2">Room</th><th className="px-4 py-2"></th></tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {residents.data?.results.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 font-medium text-slate-800">{s.full_name}</td>
                    <td className="px-4 py-2 font-mono text-slate-600">{s.student_id}</td>
                    <td className="px-4 py-2 text-slate-600">{s.grade || "—"}</td>
                    <td className="px-4 py-2 text-slate-700">{s.hostel_room || "—"}</td>
                    <td className="px-4 py-2 text-right"><button onClick={() => removeRes.mutate(s.id)} className="text-xs text-rose-600 hover:underline">Remove</button></td>
                  </tr>
                ))}
                {residents.data?.results.length === 0 && <tr><td colSpan={5} className="px-4 py-3 text-slate-400">No residents allocated yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Expenses() {
  const qc = useQueryClient();
  const hostels = useQuery({ queryKey: ["hostels"], queryFn: () => hostel.hostels() });
  const { data } = useQuery({ queryKey: ["hostel-expenses"], queryFn: () => hostel.expenses() });
  const { toast, fail } = useToast();
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({ category: "mess", amount: "0.00", spent_on: today, hostel: "", vendor: "", payment_method: "cash" });
  const invalidate = () => { qc.invalidateQueries({ queryKey: ["hostel-expenses"] }); qc.invalidateQueries({ queryKey: ["hostel-report"] }); };
  const add = useMutation({
    mutationFn: () => hostel.createExpense({ category: form.category, amount: form.amount, spent_on: form.spent_on, hostel: form.hostel ? Number(form.hostel) : null, vendor: form.vendor, payment_method: form.payment_method }),
    onSuccess: () => { setForm({ ...form, amount: "0.00", vendor: "" }); invalidate(); },
    onError: fail,
  });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <form className="grid grid-cols-1 gap-3 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); if (Number(form.amount) > 0) add.mutate(); }}>
        <Labeled label="Category">
          <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
          </Select>
        </Labeled>
        <Labeled label="Amount (₹)"><TextInput inputMode="decimal" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Labeled>
        <Labeled label="Date"><TextInput type="date" value={form.spent_on} onChange={(e) => setForm({ ...form, spent_on: e.target.value })} /></Labeled>
        <Labeled label="Hostel">
          <Select value={form.hostel} onChange={(e) => setForm({ ...form, hostel: e.target.value })}>
            <option value="">—</option>
            {hostels.data?.results.map((h) => <option key={h.id} value={h.id}>{h.code}</option>)}
          </Select>
        </Labeled>
        <Labeled label="Vendor"><TextInput value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })} placeholder="e.g. Mess contractor" /></Labeled>
        <div className="flex items-end"><Button type="submit" disabled={add.isPending || Number(form.amount) <= 0}>Add expense</Button></div>
      </form>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Date</th><th className="px-4 py-2">Category</th><th className="px-4 py-2">Hostel</th><th className="px-4 py-2">Vendor</th><th className="px-4 py-2 text-right">Amount</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((x) => (
              <tr key={x.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 text-slate-500">{x.spent_on}</td>
                <td className="px-4 py-2 capitalize text-slate-700">{x.category.replace("_", " ")}</td>
                <td className="px-4 py-2 text-slate-600">{x.hostel_name || "—"}</td>
                <td className="px-4 py-2 text-slate-600">{x.vendor || "—"}</td>
                <td className="px-4 py-2 text-right font-semibold text-rose-600">{formatMoney(x.amount, x.currency)}</td>
              </tr>
            ))}
            {data?.results.length === 0 && <tr><td colSpan={5} className="px-4 py-3 text-slate-400">No hostel expenses yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Report() {
  const { data, isLoading } = useQuery({ queryKey: ["hostel-report"], queryFn: () => hostel.report() });
  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!data) return null;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Occupancy</p><p className="mt-1 text-lg font-bold text-slate-900">{data.total_residents} / {data.total_capacity || "—"}</p></div>
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Income</p><p className="mt-1 text-lg font-bold text-emerald-600">{formatMoney(data.total_income)}</p></div>
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Expense</p><p className="mt-1 text-lg font-bold text-rose-600">{formatMoney(data.total_expense)}</p></div>
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Net</p><p className={`mt-1 text-lg font-bold ${Number(data.net) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>{formatMoney(data.net)}</p></div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Hostel</th><th className="px-4 py-2 text-right">Residents</th><th className="px-4 py-2 text-right">Occupancy</th><th className="px-4 py-2 text-right">Fee</th><th className="px-4 py-2 text-right">Income</th><th className="px-4 py-2 text-right">Expense</th><th className="px-4 py-2 text-right">Profit</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data.hostels.map((h) => (
              <tr key={h.code} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-medium text-slate-800">{h.code} · {h.hostel}</td>
                <td className="px-4 py-2 text-right">{h.residents} / {h.capacity || "—"}</td>
                <td className="px-4 py-2 text-right">{h.occupancy_percent}%</td>
                <td className="px-4 py-2 text-right">{formatMoney(h.monthly_fee)}</td>
                <td className="px-4 py-2 text-right text-emerald-600">{formatMoney(h.expected_income)}</td>
                <td className="px-4 py-2 text-right text-rose-600">{formatMoney(h.expense)}</td>
                <td className={`px-4 py-2 text-right font-semibold ${Number(h.profit) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>{formatMoney(h.profit)}</td>
              </tr>
            ))}
            {data.hostels.length === 0 && <tr><td colSpan={7} className="px-4 py-3 text-slate-400">No hostels yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function HostelPage() {
  const [tab, setTab] = useState<Tab>("hostels");
  return (
    <div className="space-y-6">
      <PageHeader title="Hostel" subtitle="Buildings, rooms, expenses and occupancy P/L (₹ INR)" />
      <div className="flex flex-wrap gap-2 border-b border-slate-100">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t.key ? "border-brand text-brand" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            {t.label}
          </button>
        ))}
      </div>
      <Card>
        {tab === "hostels" && <Hostels />}
        {tab === "rooms" && <Rooms />}
        {tab === "residents" && <Residents />}
        {tab === "expenses" && <Expenses />}
        {tab === "report" && <Report />}
      </Card>
    </div>
  );
}
