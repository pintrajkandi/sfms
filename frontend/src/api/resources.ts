import { api } from "./client";
import type {
  AcademicYear,
  CollectionDashboard,
  CollectionStats,
  Expense,
  FinanceDashboard,
  FeePlan,
  FeeType,
  InventoryItem,
  Invoice,
  Paginated,
  Payment,
  Payout,
  Student,
  StudentFeeSummary,
  Teacher,
} from "./types";

const list = <T>(path: string) => api.get<Paginated<T>>(path);

export const students = {
  search: (q: string) =>
    list<Student>(`/students/${q ? `?search=${encodeURIComponent(q)}` : ""}`),
  get: (id: number | string) => api.get<Student>(`/students/${id}/`),
  create: (body: Partial<Student>) => api.post<Student>("/students/", body),
  fees: (id: number | string) => api.get<StudentFeeSummary>(`/students/${id}/fees/`),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData();
    form.append("photo", file);
    return api.patchForm<Student>(`/students/${id}/`, form);
  },
};

export const fees = {
  types: () => list<FeeType>("/fee-types/"),
  plans: (params = "") => list<FeePlan>(`/fee-plans/${params}`),
};

export const academicYears = {
  list: () => list<AcademicYear>("/academic-years/"),
  create: (body: Partial<AcademicYear>) => api.post<AcademicYear>("/academic-years/", body),
};

export interface InvoiceLineInput {
  fee_type: number;
  description?: string;
  quantity: number;
  unit_price: string;
}

export const invoices = {
  list: (params = "") => list<Invoice>(`/invoices/${params}`),
  get: (id: number | string) => api.get<Invoice>(`/invoices/${id}/`),
  create: (body: {
    student: number;
    academic_year?: number | null;
    due_date?: string | null;
    discount_amount?: string;
    lines: InvoiceLineInput[];
  }) => api.post<Invoice>("/invoices/", body),
};

export const collections = {
  stats: () => api.get<CollectionStats>("/collections/stats/"),
  dashboard: () => api.get<CollectionDashboard>("/collections/dashboard/"),
};

export const finance = {
  dashboard: () => api.get<FinanceDashboard>("/finance/dashboard/"),
};

export const payments = {
  list: (invoice: number) => list<Payment>(`/payments/?invoice=${invoice}`),
  recent: () => list<Payment>("/payments/"),
  create: (body: {
    invoice: number;
    amount: string;
    method: string;
    reference?: string;
    paid_at?: string;
    idempotency_key?: string;
  }) => api.post("/payments/", body),
};

export const teachers = {
  list: () => list<Teacher>("/teachers/"),
  create: (body: Partial<Teacher>) => api.post<Teacher>("/teachers/", body),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData();
    form.append("photo", file);
    return api.patchForm<Teacher>(`/teachers/${id}/`, form);
  },
};

export const payouts = {
  list: () => list<Payout>("/payouts/"),
  create: (body: {
    teacher: number;
    pay_type: string;
    pay_period: string;
    base_amount: string;
    bonus_amount: string;
    deductions: string;
    payment_method?: string;
    notes?: string;
  }) => api.post<Payout>("/payouts/", body),
  transition: (id: number, to_status: string, note = "") =>
    api.post<Payout>(`/payouts/${id}/transition/`, { to_status, note }),
};

export const expenses = {
  create: (body: Partial<Expense>) => api.post<Expense>("/expenses/", body),
  uploadReceipt: (id: number, file: File) => {
    const form = new FormData();
    form.append("receipt", file);
    return api.patchForm<Expense>(`/expenses/${id}/`, form);
  },
};

export const inventory = {
  list: (params = "") => list<InventoryItem>(`/inventory/${params}`),
  create: (body: Partial<InventoryItem>) => api.post<InventoryItem>("/inventory/", body),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData();
    form.append("photo", file);
    return api.patchForm<InventoryItem>(`/inventory/${id}/`, form);
  },
};

// School settings — one row per tenant. GET the list; create if empty, else patch.
export interface SchoolSettings {
  id: number;
  // School Info
  name: string;
  school_type: string;
  registration_number: string;
  established_year: number | null;
  affiliation_board: string;
  tagline: string;
  // Branding & Logos (read-only URLs; upload via settings.uploadFile)
  logo: string | null;
  letterhead_logo: string | null;
  favicon: string | null;
  brand_color: string;
  // Invoice Settings
  invoice_prefix: string;
  starting_invoice_number: number;
  currency: string;
  tax_gst_number: string;
  default_tax_rate: string;
  payment_due_days: number;
  invoice_footer_note: string;
  bank_account_details: string;
  // Contact Details
  street_address: string;
  city: string;
  state_province: string;
  zip_code: string;
  country: string;
  primary_phone: string;
  alternate_phone: string;
  official_email: string;
  accounts_email: string;
  website_url: string;
  facebook: string;
  instagram: string;
  linkedin: string;
  // Notifications
  notify_due_reminders: boolean;
  notify_overdue: boolean;
}

// Fields uploaded as files rather than JSON.
export type SettingsFileField = "logo" | "letterhead_logo" | "favicon";

export const settings = {
  get: () => list<SchoolSettings>("/settings/"),
  create: (body: Partial<SchoolSettings>) => api.post<SchoolSettings>("/settings/", body),
  update: (id: number, body: Partial<SchoolSettings>) =>
    api.patch<SchoolSettings>(`/settings/${id}/`, body),
  uploadFile: (id: number, field: SettingsFileField, file: File) => {
    const form = new FormData();
    form.append(field, file);
    return api.patchForm<SchoolSettings>(`/settings/${id}/`, form);
  },
};
