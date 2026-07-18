import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { inventory } from "@/api/resources";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/form";
import { formatMoney } from "@/lib/money";

export function InventoryListPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["inventory", search],
    queryFn: () => inventory.list(search ? `?search=${encodeURIComponent(search)}` : ""),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Inventory"
        subtitle="School assets and stock"
        actions={
          <Link to="/inventory/new" className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white hover:opacity-95">
            + Add Item
          </Link>
        }
      />

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search name, SKU, supplier…"
        className="w-full max-w-sm rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
      />

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="border-b border-slate-100 text-left text-slate-500">
            <tr>
              <th className="px-6 py-3 font-medium">Item</th>
              <th className="px-6 py-3 font-medium">SKU</th>
              <th className="px-6 py-3 font-medium">Category</th>
              <th className="px-6 py-3 font-medium">Qty</th>
              <th className="px-6 py-3 font-medium">Unit Cost</th>
              <th className="px-6 py-3 font-medium">Location</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((it) => (
              <tr key={it.id} className="hover:bg-slate-50">
                <td className="px-6 py-3 font-medium text-slate-800">{it.name}</td>
                <td className="px-6 py-3 font-mono text-xs">{it.sku}</td>
                <td className="px-6 py-3 capitalize">{it.category.replace("_", " ")}</td>
                <td className={`px-6 py-3 ${it.quantity <= it.min_stock_alert ? "font-semibold text-rose-600" : ""}`}>{it.quantity}</td>
                <td className="px-6 py-3">{formatMoney(it.unit_cost, it.currency)}</td>
                <td className="px-6 py-3 text-slate-500">{it.storage_location || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {data?.results.length === 0 && <p className="px-6 py-4 text-slate-400">No inventory items yet.</p>}
      </Card>
    </div>
  );
}
