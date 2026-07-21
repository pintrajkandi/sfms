import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { transport } from "@/api/resources";
import { Card } from "@/components/Card";
import { Button, Labeled, PageHeader, Select, TextInput, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";

type Tab = "routes" | "vehicles" | "expenses" | "profit";
const TABS: { key: Tab; label: string }[] = [
  { key: "routes", label: "Routes" },
  { key: "vehicles", label: "Vehicles" },
  { key: "expenses", label: "Expenses" },
  { key: "profit", label: "Route Profitability" },
];

const CATEGORIES = ["fuel", "driver_salary", "maintenance", "insurance", "other"];

function useToast() {
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null);
  const fail = (e: unknown) => setToast({ msg: e instanceof ApiError ? e.detail : "Something went wrong.", tone: "error" });
  return { toast, fail };
}

function Routes() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["transport-routes"], queryFn: () => transport.routes() });
  const { toast, fail } = useToast();
  const [form, setForm] = useState({ name: "", code: "", monthly_fare: "0.00", description: "" });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["transport-routes"] });
  const add = useMutation({ mutationFn: () => transport.createRoute(form), onSuccess: () => { setForm({ name: "", code: "", monthly_fare: "0.00", description: "" }); invalidate(); }, onError: fail });
  const remove = useMutation({ mutationFn: (id: number) => transport.removeRoute(id), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); if (form.name && form.code) add.mutate(); }}>
        <Labeled label="Route name"><TextInput value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. North Loop" /></Labeled>
        <Labeled label="Code"><TextInput value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="e.g. R-N" /></Labeled>
        <Labeled label="Monthly fare (₹)"><TextInput inputMode="decimal" value={form.monthly_fare} onChange={(e) => setForm({ ...form, monthly_fare: e.target.value })} /></Labeled>
        <Button type="submit" disabled={add.isPending || !form.name || !form.code}>Add route</Button>
      </form>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Code</th><th className="px-4 py-2">Route</th><th className="px-4 py-2 text-right">Fare</th><th className="px-4 py-2 text-right">Riders</th><th className="px-4 py-2 text-right">Vehicles</th><th className="px-4 py-2"></th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-slate-700">{r.code}</td>
                <td className="px-4 py-2 font-medium text-slate-800">{r.name}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.monthly_fare)}</td>
                <td className="px-4 py-2 text-right">{r.rider_count}</td>
                <td className="px-4 py-2 text-right">{r.vehicle_count}</td>
                <td className="px-4 py-2 text-right"><button onClick={() => remove.mutate(r.id)} className="text-xs text-rose-600 hover:underline">Delete</button></td>
              </tr>
            ))}
            {data?.results.length === 0 && <tr><td colSpan={6} className="px-4 py-3 text-slate-400">No routes yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Vehicles() {
  const qc = useQueryClient();
  const routes = useQuery({ queryKey: ["transport-routes"], queryFn: () => transport.routes() });
  const { data } = useQuery({ queryKey: ["vehicles"], queryFn: () => transport.vehicles() });
  const { toast, fail } = useToast();
  const [form, setForm] = useState({ registration_number: "", model: "", capacity: "", driver_name: "", driver_phone: "", route: "" });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["vehicles"] });
  const add = useMutation({
    mutationFn: () => transport.createVehicle({ registration_number: form.registration_number, model: form.model, capacity: Number(form.capacity || 0), driver_name: form.driver_name, driver_phone: form.driver_phone, route: form.route ? Number(form.route) : null }),
    onSuccess: () => { setForm({ registration_number: "", model: "", capacity: "", driver_name: "", driver_phone: "", route: "" }); invalidate(); },
    onError: fail,
  });
  const remove = useMutation({ mutationFn: (id: number) => transport.removeVehicle(id), onSuccess: invalidate, onError: fail });

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} tone={toast.tone} />}
      <form className="grid grid-cols-1 gap-3 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); if (form.registration_number) add.mutate(); }}>
        <Labeled label="Registration no."><TextInput value={form.registration_number} onChange={(e) => setForm({ ...form, registration_number: e.target.value.toUpperCase() })} placeholder="KA01AB1234" /></Labeled>
        <Labeled label="Model"><TextInput value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="Tata Bus" /></Labeled>
        <Labeled label="Capacity"><TextInput type="number" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} placeholder="40" /></Labeled>
        <Labeled label="Driver name"><TextInput value={form.driver_name} onChange={(e) => setForm({ ...form, driver_name: e.target.value })} /></Labeled>
        <Labeled label="Driver phone"><TextInput value={form.driver_phone} onChange={(e) => setForm({ ...form, driver_phone: e.target.value })} /></Labeled>
        <Labeled label="Route">
          <Select value={form.route} onChange={(e) => setForm({ ...form, route: e.target.value })}>
            <option value="">Unassigned</option>
            {routes.data?.results.map((r) => <option key={r.id} value={r.id}>{r.code} · {r.name}</option>)}
          </Select>
        </Labeled>
        <div className="flex items-end"><Button type="submit" disabled={add.isPending || !form.registration_number}>Add vehicle</Button></div>
      </form>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Reg. No.</th><th className="px-4 py-2">Model</th><th className="px-4 py-2 text-right">Capacity</th><th className="px-4 py-2">Driver</th><th className="px-4 py-2">Route</th><th className="px-4 py-2"></th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((v) => (
              <tr key={v.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-slate-700">{v.registration_number}</td>
                <td className="px-4 py-2 text-slate-600">{v.model || "—"}</td>
                <td className="px-4 py-2 text-right">{v.capacity || "—"}</td>
                <td className="px-4 py-2 text-slate-600">{v.driver_name || "—"}</td>
                <td className="px-4 py-2 text-slate-600">{v.route_name || "—"}</td>
                <td className="px-4 py-2 text-right"><button onClick={() => remove.mutate(v.id)} className="text-xs text-rose-600 hover:underline">Delete</button></td>
              </tr>
            ))}
            {data?.results.length === 0 && <tr><td colSpan={6} className="px-4 py-3 text-slate-400">No vehicles yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Expenses() {
  const qc = useQueryClient();
  const routes = useQuery({ queryKey: ["transport-routes"], queryFn: () => transport.routes() });
  const vehicles = useQuery({ queryKey: ["vehicles"], queryFn: () => transport.vehicles() });
  const { data } = useQuery({ queryKey: ["transport-expenses"], queryFn: () => transport.expenses() });
  const { toast, fail } = useToast();
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({ category: "fuel", amount: "0.00", spent_on: today, vehicle: "", route: "", vendor: "", payment_method: "cash" });
  const invalidate = () => { qc.invalidateQueries({ queryKey: ["transport-expenses"] }); qc.invalidateQueries({ queryKey: ["route-profit"] }); };
  const add = useMutation({
    mutationFn: () => transport.createExpense({ category: form.category, amount: form.amount, spent_on: form.spent_on, vehicle: form.vehicle ? Number(form.vehicle) : null, route: form.route ? Number(form.route) : null, vendor: form.vendor, payment_method: form.payment_method }),
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
        <Labeled label="Vehicle">
          <Select value={form.vehicle} onChange={(e) => setForm({ ...form, vehicle: e.target.value })}>
            <option value="">—</option>
            {vehicles.data?.results.map((v) => <option key={v.id} value={v.id}>{v.registration_number}</option>)}
          </Select>
        </Labeled>
        <Labeled label="Route">
          <Select value={form.route} onChange={(e) => setForm({ ...form, route: e.target.value })}>
            <option value="">—</option>
            {routes.data?.results.map((r) => <option key={r.id} value={r.id}>{r.code}</option>)}
          </Select>
        </Labeled>
        <Labeled label="Vendor"><TextInput value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })} placeholder="e.g. HP Petrol" /></Labeled>
        <div className="flex items-end"><Button type="submit" disabled={add.isPending || Number(form.amount) <= 0}>Add expense</Button></div>
      </form>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Date</th><th className="px-4 py-2">Category</th><th className="px-4 py-2">Vehicle</th><th className="px-4 py-2">Route</th><th className="px-4 py-2">Vendor</th><th className="px-4 py-2 text-right">Amount</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((x) => (
              <tr key={x.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 text-slate-500">{x.spent_on}</td>
                <td className="px-4 py-2 capitalize text-slate-700">{x.category.replace("_", " ")}</td>
                <td className="px-4 py-2 text-slate-600">{x.vehicle_reg || "—"}</td>
                <td className="px-4 py-2 text-slate-600">{x.route_name || "—"}</td>
                <td className="px-4 py-2 text-slate-600">{x.vendor || "—"}</td>
                <td className="px-4 py-2 text-right font-semibold text-rose-600">{formatMoney(x.amount, x.currency)}</td>
              </tr>
            ))}
            {data?.results.length === 0 && <tr><td colSpan={6} className="px-4 py-3 text-slate-400">No transport expenses yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Profitability() {
  const { data, isLoading } = useQuery({ queryKey: ["route-profit"], queryFn: () => transport.profitability() });
  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!data) return null;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Expected income</p><p className="mt-1 text-lg font-bold text-emerald-600">{formatMoney(data.total_income)}</p></div>
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Transport expense</p><p className="mt-1 text-lg font-bold text-rose-600">{formatMoney(data.total_expense)}</p></div>
        <div className="rounded-xl border border-slate-100 px-4 py-3"><p className="text-xs uppercase text-slate-400">Net</p><p className={`mt-1 text-lg font-bold ${Number(data.net) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>{formatMoney(data.net)}</p></div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-4 py-2">Route</th><th className="px-4 py-2 text-right">Riders</th><th className="px-4 py-2 text-right">Fare</th><th className="px-4 py-2 text-right">Income</th><th className="px-4 py-2 text-right">Expense</th><th className="px-4 py-2 text-right">Profit</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data.routes.map((r) => (
              <tr key={r.code} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-medium text-slate-800">{r.code} · {r.route}</td>
                <td className="px-4 py-2 text-right">{r.riders}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.monthly_fare)}</td>
                <td className="px-4 py-2 text-right text-emerald-600">{formatMoney(r.expected_income)}</td>
                <td className="px-4 py-2 text-right text-rose-600">{formatMoney(r.expense)}</td>
                <td className={`px-4 py-2 text-right font-semibold ${Number(r.profit) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>{formatMoney(r.profit)}</td>
              </tr>
            ))}
            {data.routes.length === 0 && <tr><td colSpan={6} className="px-4 py-3 text-slate-400">No routes yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function TransportPage() {
  const [tab, setTab] = useState<Tab>("routes");
  return (
    <div className="space-y-6">
      <PageHeader title="Transport" subtitle="Routes, vehicles, expenses and route profitability (₹ INR)" />
      <div className="flex flex-wrap gap-2 border-b border-slate-100">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t.key ? "border-brand text-brand" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            {t.label}
          </button>
        ))}
      </div>
      <Card>
        {tab === "routes" && <Routes />}
        {tab === "vehicles" && <Vehicles />}
        {tab === "expenses" && <Expenses />}
        {tab === "profit" && <Profitability />}
      </Card>
    </div>
  );
}
