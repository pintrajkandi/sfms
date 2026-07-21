import { api } from "./client";
import type {
  AcademicYear,
  CollectionDashboard,
  CollectionStats,
  DefaulterReport,
  Expense,
  FinanceDashboard,
  ImportResult,
  FeePlan,
  FeeCategory,
  FeeType,
  InventoryItem,
  Invoice,
  AssistantAnswer,
  Paginated,
  Payment,
  Payout,
  RazorpayConfig,
  RiskReport,
  SchoolClass,
  Section,
  StaffCreateInput,
  TeamUser,
  RazorpayOrder,
  RazorpayVerifyPayload,
  RazorpayVerifyResult,
  Student,
  StudentFeeSummary,
  Teacher,
} from "./types";

const list = <T>(path: string) => api.get<Paginated<T>>(path);

export const classes = {
  list: () => list<SchoolClass>("/classes/"),
  create: (body: { name: string; order?: number }) => api.post<SchoolClass>("/classes/", body),
  remove: (id: number) => api.delete<void>(`/classes/${id}/`),
  addSection: (body: { school_class: number; name: string }) =>
    api.post<Section>("/sections/", body),
  removeSection: (id: number) => api.delete<void>(`/sections/${id}/`),
};

export const students = {
  search: (q: string) =>
    list<Student>(`/students/${q ? `?search=${encodeURIComponent(q)}` : ""}`),
  get: (id: number | string) => api.get<Student>(`/students/${id}/`),
  create: (body: Partial<Student>) => api.post<Student>("/students/", body),
  update: (id: number | string, body: Partial<Student>) =>
    api.patch<Student>(`/students/${id}/`, body),
  fees: (id: number | string) => api.get<StudentFeeSummary>(`/students/${id}/fees/`),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData();
    form.append("photo", file);
    return api.patchForm<Student>(`/students/${id}/`, form);
  },
  importCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.postForm<ImportResult>("/students/import/", form);
  },
  templateUrl: () => api.fileUrl("/students/import-template/"),
  exportUrl: (fmt: string) => api.fileUrl(`/students/export/?fmt=${fmt}`),
};

export const fees = {
  types: () => list<FeeType>("/fee-types/"),
  plans: (params = "") => list<FeePlan>(`/fee-plans/${params}`),
  categories: () => list<FeeCategory>("/fee-categories/"),
  createCategory: (body: { name: string; color?: string }) =>
    api.post<FeeCategory>("/fee-categories/", body),
  removeCategory: (id: number) => api.delete<void>(`/fee-categories/${id}/`),
  createType: (body: { name: string; category: number }) =>
    api.post<FeeType>("/fee-types/", body),
  removeType: (id: number) => api.delete<void>(`/fee-types/${id}/`),
};

export const academicYears = {
  list: () => list<AcademicYear>("/academic-years/"),
  create: (body: Partial<AcademicYear>) => api.post<AcademicYear>("/academic-years/", body),
  update: (id: number, body: Partial<AcademicYear>) =>
    api.patch<AcademicYear>(`/academic-years/${id}/`, body),
  setCurrent: (id: number) =>
    api.post<AcademicYear>(`/academic-years/${id}/set-current/`, {}),
};

export const team = {
  list: () => list<TeamUser>("/team/"),
  create: (body: StaffCreateInput) => api.post<TeamUser>("/team/", body),
  update: (id: number, body: Partial<TeamUser>) => api.patch<TeamUser>(`/team/${id}/`, body),
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
  defaulters: () => api.get<DefaulterReport>("/collections/defaulters/"),
  defaultersExportUrl: (fmt: string) => api.fileUrl(`/collections/defaulters/?fmt=${fmt}`),
  paymentsExportUrl: (fmt: string) => api.fileUrl(`/payments/export/?fmt=${fmt}`),
  risk: () => api.get<RiskReport>("/collections/risk/"),
  ask: (question: string) => api.post<AssistantAnswer>("/collections/assistant/", { question }),
  signingKey: () =>
    api.get<{ algorithm: string; public_pem: string; key_id: number }>("/collections/signing-key/"),
};

export const finance = {
  dashboard: () => api.get<FinanceDashboard>("/finance/dashboard/"),
};

export interface Account {
  id: number;
  code: string;
  name: string;
  type: "asset" | "liability" | "equity" | "income" | "expense";
  description: string;
  is_active: boolean;
  is_system: boolean;
}

interface StatementRow {
  code: string;
  name: string;
  amount?: string;
  debit?: string;
  credit?: string;
  type?: string;
}
export interface TrialBalance {
  rows: StatementRow[];
  total_debit: string;
  total_credit: string;
  balanced: boolean;
  as_of: string;
}
export interface ProfitLoss {
  income: StatementRow[];
  expense: StatementRow[];
  total_income: string;
  total_expense: string;
  net_profit: string;
}
export interface BalanceSheet {
  assets: StatementRow[];
  liabilities: StatementRow[];
  equity: StatementRow[];
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  balanced: boolean;
  as_of: string;
}
export interface GeneralLedger {
  account: { code: string; name: string; type: string } | null;
  lines: { date: string; narration: string; debit: string; credit: string; balance: string }[];
  closing_balance?: string;
}

export const accounting = {
  accounts: (params = "") => list<Account>(`/accounts/${params}`),
  createAccount: (body: { code: string; name: string; type: string; description?: string }) =>
    api.post<Account>("/accounts/", body),
  updateAccount: (id: number, body: Partial<Account>) =>
    api.patch<Account>(`/accounts/${id}/`, body),
  removeAccount: (id: number) => api.delete<void>(`/accounts/${id}/`),
  trialBalance: () => api.get<TrialBalance>("/finance/trial-balance/"),
  profitLoss: () => api.get<ProfitLoss>("/finance/profit-loss/"),
  balanceSheet: () => api.get<BalanceSheet>("/finance/balance-sheet/"),
  generalLedger: (code: string) =>
    api.get<GeneralLedger>(`/finance/general-ledger/?account=${encodeURIComponent(code)}`),
  dayBook: () => api.get<DayBook>("/finance/day-book/"),
};

export interface DayBook {
  entries: {
    id: number;
    date: string;
    narration: string;
    lines: { account: string; debit: string; credit: string }[];
  }[];
  total_debit: string;
  total_credit: string;
}

export interface LedgerStatement {
  student?: { id: number; name: string; student_id: string; grade: string; section: string; guardian_name: string; guardian_phone: string };
  guardian?: { name: string; phone: string };
  students?: { id: number; name: string; student_id: string; grade: string }[];
  lines: { student?: string; date: string; particulars: string; type: string; debit: string; credit: string; balance: string }[];
  total_billed: string;
  total_paid: string;
  outstanding: string;
}

export const ledgers = {
  student: (studentId: number | string) =>
    api.get<LedgerStatement>(`/collections/student-ledger/?student=${studentId}`),
  parent: (studentId: number | string) =>
    api.get<LedgerStatement>(`/collections/parent-ledger/?student=${studentId}`),
};

export interface AuditLog {
  id: number;
  created_at: string;
  actor: number | null;
  actor_label: string;
  action: string;
  entity_type: string;
  entity_id: string;
  summary: string;
  changes: Record<string, unknown> | null;
}

export const auditLogs = {
  list: (params = "") => list<AuditLog>(`/audit-logs/${params}`),
};

export interface SupportTicket {
  id: number;
  subject: string;
  category: string;
  message: string;
  contact_email: string;
  status: string;
  created_at: string;
}

export const support = {
  list: () => list<SupportTicket>("/support-tickets/"),
  create: (body: { subject: string; category: string; message: string; contact_email?: string }) =>
    api.post<SupportTicket>("/support-tickets/", body),
};

export const payments = {
  list: (invoice: number) => list<Payment>(`/payments/?invoice=${invoice}`),
  recent: () => list<Payment>("/payments/"),
  search: (term: string) =>
    list<Payment>(`/payments/${term ? `?search=${encodeURIComponent(term)}` : ""}`),
  create: (body: {
    invoice: number;
    amount: string;
    method: string;
    reference?: string;
    paid_at?: string;
    idempotency_key?: string;
  }) => api.post("/payments/", body),
};

export const razorpay = {
  config: () => api.get<RazorpayConfig>("/payments/razorpay/config/"),
  createOrder: (invoice: number) =>
    api.post<RazorpayOrder>("/payments/razorpay/order/", { invoice }),
  verify: (payload: RazorpayVerifyPayload) =>
    api.post<RazorpayVerifyResult>("/payments/razorpay/verify/", payload),
};

export const teachers = {
  list: () => list<Teacher>("/teachers/"),
  get: (id: number | string) => api.get<Teacher>(`/teachers/${id}/`),
  create: (body: Partial<Teacher>) => api.post<Teacher>("/teachers/", body),
  update: (id: number | string, body: Partial<Teacher>) =>
    api.patch<Teacher>(`/teachers/${id}/`, body),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData();
    form.append("photo", file);
    return api.patchForm<Teacher>(`/teachers/${id}/`, form);
  },
};

export interface Department {
  id: number;
  name: string;
  is_active: boolean;
}

export const departments = {
  list: () => list<Department>("/departments/"),
  create: (body: { name: string }) => api.post<Department>("/departments/", body),
  remove: (id: number) => api.delete<void>(`/departments/${id}/`),
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
    payment_reference?: string;
    notes?: string;
    days_present?: number | null;
    days_absent?: number | null;
    deduction_reason?: string;
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
  get: (id: number | string) => api.get<InventoryItem>(`/inventory/${id}/`),
  create: (body: Partial<InventoryItem>) => api.post<InventoryItem>("/inventory/", body),
  update: (id: number | string, body: Partial<InventoryItem>) =>
    api.patch<InventoryItem>(`/inventory/${id}/`, body),
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
  // Payroll (statutory rates)
  payroll_pf_rate: string;
  payroll_pf_ceiling: string;
  payroll_esi_rate: string;
  payroll_esi_threshold: string;
  payroll_professional_tax: string;
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
