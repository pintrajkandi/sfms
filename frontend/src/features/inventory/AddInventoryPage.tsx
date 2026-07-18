import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { inventory } from "@/api/resources";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { log } from "@/lib/logger";

const CATEGORIES = [
  { value: "furniture", label: "Furniture", icon: "🪑" },
  { value: "electronics", label: "Electronics", icon: "💻" },
  { value: "stationery", label: "Stationery", icon: "✏️" },
  { value: "sports", label: "Sports", icon: "⚽" },
  { value: "library", label: "Library", icon: "📚" },
  { value: "lab_equipment", label: "Lab Equipment", icon: "🧪" },
  { value: "cleaning", label: "Cleaning", icon: "🧹" },
  { value: "medical", label: "Medical", icon: "🏥" },
  { value: "other", label: "Other", icon: "⋯" },
];
const UNITS = ["Piece", "Box", "Set", "Pack", "Dozen", "Kg", "Litre", "Metre"];
const DEPARTMENTS = ["Administration", "Science", "Library", "Sports", "Computer Lab", "Medical", "General"];

const EMPTY = {
  category: "",
  name: "", sku: "", brand: "", unit_of_measurement: "", condition: "", description: "",
  unit_cost: "0.00", supplier_name: "", invoice_po_number: "", warranty_expiry: "",
  quantity: "0", min_stock_alert: "0", storage_location: "", department: "", assigned_to: "", date_acquired: "",
  is_active: true,
};

function Section({ icon, tint, title, subtitle, children }: { icon: React.ReactNode; tint: string; title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${tint}`}>{icon}</span>
        <div>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

export function AddInventoryPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ ...EMPTY });
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const photoRef = useRef<HTMLInputElement>(null);
  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }));

  function pickPhoto(file: File) {
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  function reset() {
    setForm({ ...EMPTY });
    setPhotoFile(null);
    setPhotoPreview(null);
    setErrors({});
    setError("");
  }

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!form.category) next.category = "Select a category";
    (["name", "sku", "unit_of_measurement", "quantity"] as const).forEach((k) => !form[k] && (next[k] = "Required"));
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function save() {
    setError("");
    if (!validate()) return;
    setSaving(true);
    try {
      const scalars = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== "")) as Record<string, unknown>;
      scalars.quantity = Number(form.quantity);
      scalars.min_stock_alert = Number(form.min_stock_alert || 0);
      const created = await inventory.create(scalars);
      if (photoFile) await inventory.uploadPhoto(created.id, photoFile);
      log.info("inventory item added", { entity: created.id, action: "add_inventory" });
      navigate("/inventory");
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") setErrors(err.body as Record<string, string>);
      setError(err instanceof ApiError ? err.detail : "Could not save the item.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">
            <Link to="/inventory" className="hover:text-brand">Dashboard</Link> ›{" "}
            <span className="text-brand">Add Inventory Item</span>
          </p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Add New Inventory Item</h1>
          <p className="mt-1 text-slate-500">Fill in all required fields to register a new school inventory item.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate("/inventory")} className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">✕ Cancel</button>
          <button onClick={save} disabled={saving} className="rounded-lg bg-brand-gradient px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">💾 Save Item</button>
        </div>
      </div>

      {error && <Toast tone="error" message={error} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-6 lg:col-span-2">
          <Section icon={<span className="text-brand">▦</span>} tint="bg-brand-light" title="Item Category" subtitle="Select the category that best describes this inventory item.">
            {errors.category && <p className="mb-2 text-xs text-rose-600">{errors.category}</p>}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {CATEGORIES.map((c) => (
                <button
                  key={c.value}
                  type="button"
                  onClick={() => set("category", c.value)}
                  className={`flex flex-col items-center gap-2 rounded-xl border py-5 text-sm font-medium transition ${
                    form.category === c.value ? "border-brand bg-brand-light text-brand-dark" : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <span className="text-2xl">{c.icon}</span>
                  {c.label}
                </button>
              ))}
            </div>
          </Section>

          <Section icon={<span className="text-emerald-600">ⓘ</span>} tint="bg-emerald-50" title="Item Details">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Item name" required error={errors.name} full>
                <TextInput placeholder="e.g. Student Desk Chair" value={form.name} onChange={(e) => set("name", e.target.value)} />
              </Labeled>
              <Labeled label="Item code / SKU" required error={errors.sku}>
                <TextInput placeholder="e.g. FUR-001" value={form.sku} onChange={(e) => set("sku", e.target.value)} />
              </Labeled>
              <Labeled label="Brand / manufacturer">
                <TextInput placeholder="e.g. Nilkamal" value={form.brand} onChange={(e) => set("brand", e.target.value)} />
              </Labeled>
              <Labeled label="Unit of measurement" required error={errors.unit_of_measurement}>
                <Select value={form.unit_of_measurement} onChange={(e) => set("unit_of_measurement", e.target.value)}>
                  <option value="">Select unit</option>
                  {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
                </Select>
              </Labeled>
              <Labeled label="Condition">
                <Select value={form.condition} onChange={(e) => set("condition", e.target.value)}>
                  <option value="">Select condition</option>
                  <option value="new">New</option>
                  <option value="good">Good</option>
                  <option value="fair">Fair</option>
                  <option value="poor">Poor</option>
                </Select>
              </Labeled>
              <Labeled label="Description" full>
                <TextArea placeholder="Brief description of this item…" value={form.description} onChange={(e) => set("description", e.target.value)} />
              </Labeled>
            </div>
          </Section>

          <Section icon={<span className="text-brand">▤</span>} tint="bg-brand-light" title="Stock & Location">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <Labeled label="Quantity" required error={errors.quantity}>
                <TextInput type="number" placeholder="0" value={form.quantity} onChange={(e) => set("quantity", e.target.value)} />
              </Labeled>
              <Labeled label="Min. stock alert">
                <TextInput type="number" placeholder="0" value={form.min_stock_alert} onChange={(e) => set("min_stock_alert", e.target.value)} />
              </Labeled>
              <Labeled label="Storage location">
                <TextInput placeholder="e.g. Room 102, Shelf B" value={form.storage_location} onChange={(e) => set("storage_location", e.target.value)} />
              </Labeled>
              <Labeled label="Department / block">
                <Select value={form.department} onChange={(e) => set("department", e.target.value)}>
                  <option value="">Select department</option>
                  {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
                </Select>
              </Labeled>
              <Labeled label="Assigned to">
                <TextInput placeholder="e.g. Class 10A, Lab 3" value={form.assigned_to} onChange={(e) => set("assigned_to", e.target.value)} />
              </Labeled>
              <Labeled label="Date acquired">
                <TextInput type="date" value={form.date_acquired} onChange={(e) => set("date_acquired", e.target.value)} />
              </Labeled>
            </div>
          </Section>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Section icon={<span className="text-brand">🖼</span>} tint="bg-brand-light" title="Item Photo">
            <button type="button" onClick={() => photoRef.current?.click()} className="flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-8 text-slate-400 hover:border-brand">
              {photoPreview ? (
                <img src={photoPreview} alt="preview" className="h-24 w-24 rounded-lg object-cover" />
              ) : (
                <>
                  <span className="text-3xl">☁️</span>
                  <span className="mt-1 text-sm font-medium text-slate-600">Click to upload photo</span>
                  <span className="text-xs">PNG, JPG up to 5MB</span>
                </>
              )}
            </button>
            <input ref={photoRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && pickPhoto(e.target.files[0])} />
          </Section>

          <Section icon={<span className="text-amber-500">₹</span>} tint="bg-amber-50" title="Purchase Info">
            <div className="space-y-4">
              <Labeled label="Unit cost">
                <TextInput placeholder="0.00" value={form.unit_cost} onChange={(e) => set("unit_cost", e.target.value)} />
              </Labeled>
              <Labeled label="Supplier name">
                <TextInput placeholder="e.g. ABC Traders" value={form.supplier_name} onChange={(e) => set("supplier_name", e.target.value)} />
              </Labeled>
              <Labeled label="Invoice / PO number">
                <TextInput placeholder="e.g. INV-2024-0081" value={form.invoice_po_number} onChange={(e) => set("invoice_po_number", e.target.value)} />
              </Labeled>
              <Labeled label="Warranty expiry">
                <TextInput type="date" value={form.warranty_expiry} onChange={(e) => set("warranty_expiry", e.target.value)} />
              </Labeled>
            </div>
          </Section>

          <Section icon={<span className="text-emerald-600">◉</span>} tint="bg-emerald-50" title="Status">
            <label className="flex items-center justify-between">
              <span>
                <span className="block text-sm font-medium text-slate-800">Active in Inventory</span>
                <span className="block text-xs text-slate-500">Item will be visible in records</span>
              </span>
              <input type="checkbox" className="h-6 w-6 rounded border-slate-300" checked={form.is_active} onChange={(e) => set("is_active", e.target.checked)} />
            </label>
          </Section>

          <button onClick={save} disabled={saving} className="w-full rounded-xl bg-brand-gradient py-3 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50">
            💾 {saving ? "Saving…" : "Save Inventory Item"}
          </button>
          <button onClick={reset} className="w-full rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            ↺ Reset Form
          </button>
        </div>
      </div>
    </div>
  );
}
