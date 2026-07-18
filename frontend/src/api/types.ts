/**
 * API response types — keep in sync with the DRF serializers (CLAUDE.md §6).
 * Money fields are DECIMAL STRINGS, never numbers.
 */
export type InvoiceStatus = "draft" | "pending" | "partial" | "paid" | "overdue" | "cancelled";

export interface Student {
  id: number;
  student_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string | null;
  gender: string;
  nationality: string;
  photo: string | null;
  email: string;
  phone: string;
  home_address: string;
  guardian_name: string;
  guardian_relation: string;
  guardian_phone: string;
  guardian_email: string;
  department: string;
  grade: string;
  section: string;
  program: string;
  enrollment_date: string | null;
  status: string;
  previous_school: string;
  notes: string;
}

export interface InvoiceLine {
  id: number;
  fee_type: number;
  fee_type_name: string;
  fee_type_category: string;
  description: string;
  quantity: number;
  unit_price: string;
  amount: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  student: number;
  student_name: string;
  academic_year_label: string;
  status: InvoiceStatus;
  currency: string;
  issue_date: string;
  due_date: string | null;
  subtotal: string;
  discount_amount: string;
  late_fee_amount: string;
  total: string;
  amount_paid: string;
  balance: string;
  lines: InvoiceLine[];
}

export interface Payment {
  id: number;
  invoice: number;
  amount: string;
  currency: string;
  method: string;
  reference: string;
  status: string;
  paid_at: string;
  student_name: string;
  student_grade: string;
  invoice_status: string;
  fee_type: string;
  recorded_by: number | null;
}

export interface FinanceDashboard {
  total_balance: string;
  total_income: string;
  total_expense: string;
  net_savings: string;
  savings_rate_percent: number;
  monthly: { month: string; income: string; expense: string }[];
  net_savings_trend: { month: string; balance: string }[];
  expense_breakdown: { category: string; total: string }[];
  recent_transactions: {
    title: string;
    category: string;
    date: string;
    amount: string;
    direction: "in" | "out";
  }[];
}

export interface CollectionDashboard extends CollectionStats {
  collection_rate_percent: number;
  monthly: { month: string; collected: string; pending: string }[];
  category_breakdown: { fee_type: string; amount: string; percent: number }[];
  upcoming: { student: string; invoice: string; amount: string; due_date: string; days: number }[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FeeCategory {
  id: number;
  name: string;
  color: string;
}

export interface FeeType {
  id: number;
  name: string;
  category: number;
  category_name: string;
  default_amount: string;
  currency: string;
}

export interface FeePlan {
  id: number;
  fee_type: number;
  fee_type_name: string;
  academic_year: number;
  grade: string;
  amount: string;
  currency: string;
  due_date: string | null;
}

export interface StudentFeeSummary {
  total_fee: string;
  paid: string;
  outstanding: string;
  progress_percent: number;
  fee_breakdown: {
    fee_type: string;
    category: string;
    amount: string;
    paid: string;
    balance: string;
    status: string;
  }[];
  invoices: {
    invoice_number: string;
    status: InvoiceStatus;
    total: string;
    amount_paid: string;
    balance: string;
    due_date: string | null;
  }[];
  payment_history: {
    amount: string;
    method: string;
    paid_at: string;
    receipt: string;
    fee_type: string;
  }[];
}

export interface ImportResult {
  created: number;
  error_count: number;
  errors: { row: number; error: string }[];
}

export interface Defaulter {
  student: string;
  student_id: string;
  grade: string;
  outstanding: string;
  days_overdue: number;
  oldest_due: string | null;
  bucket: string;
  invoices: number;
}

export interface DefaulterReport {
  defaulters: Defaulter[];
  aging: Record<string, string>;
  total_outstanding: string;
  count: number;
}

export interface CollectionStats {
  total_collected: string;
  pending_dues: string;
  paid_students: number;
  total_students: number;
  todays_collection: string;
  todays_receipts: number;
}

export type PayoutStatus =
  | "submitted"
  | "hod_approved"
  | "finance_approved"
  | "processed"
  | "rejected";

export interface TeacherClass {
  id?: number;
  class_name: string;
  role_in_class: string;
  academic_year: string;
}

export interface Teacher {
  id: number;
  employee_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  gender: string;
  date_of_birth: string | null;
  address: string;
  photo: string | null;
  status: string;
  department: string;
  joining_date: string | null;
  employment_type: string;
  years_of_experience: number | null;
  qualification: string;
  bio: string;
  base_salary: string;
  currency: string;
  pay_frequency: string;
  last_increment_date: string | null;
  increment_percent: string;
  next_increment_due: string | null;
  increment_reason: string;
  bank_name: string;
  account_number?: string;
  routing_code: string;
  classes: TeacherClass[];
}

export interface PayoutApproval {
  from_status: string;
  to_status: string;
  actor: number | null;
  note: string;
  created_at: string;
}

export interface Payout {
  id: number;
  teacher: number;
  teacher_name: string;
  pay_type: string;
  pay_period: string;
  base_amount: string;
  bonus_amount: string;
  deductions: string;
  net_amount: string;
  currency: string;
  payment_method: string;
  notes: string;
  status: PayoutStatus;
  approvals: PayoutApproval[];
}

export interface Expense {
  id: number;
  title: string;
  category: string;
  expense_date: string;
  amount: string;
  currency: string;
  payment_method: string;
  reimbursable: boolean;
  vendor: string;
  project_cost_center: string;
  notes: string;
  receipt: string | null;
}

export interface InventoryItem {
  id: number;
  category: string;
  name: string;
  sku: string;
  brand: string;
  unit_of_measurement: string;
  condition: string;
  description: string;
  unit_cost: string;
  currency: string;
  supplier_name: string;
  invoice_po_number: string;
  warranty_expiry: string | null;
  quantity: number;
  min_stock_alert: number;
  storage_location: string;
  department: string;
  assigned_to: string;
  date_acquired: string | null;
  photo: string | null;
  is_active: boolean;
}

export interface AcademicYear {
  id: number;
  label: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

export interface RazorpayConfig {
  enabled: boolean;
  key_id: string;
}

export interface RazorpayOrder {
  order_id: string;
  amount: number; // paise (minor units)
  currency: string;
  key_id: string;
}

export interface RazorpayVerifyPayload {
  invoice: number;
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface RazorpayVerifyResult {
  status: string;
  payment_id: number;
  invoice_status: string;
}

/* ---- Parent portal (public, X-Parent-Token authed) ---- */

export interface ParentVerifyResult {
  token: string;
  student_name: string;
  student_id: string;
}

export interface ParentInvoice {
  id: number;
  invoice_number: string;
  total: string;
  amount_paid: string;
  balance: string;
  status: InvoiceStatus;
  due_date: string | null;
}

export interface ParentPayOrder {
  order_id: string;
  amount: number; // paise (minor units)
  currency: string;
  key_id: string;
}

export interface ParentPayVerifyResult {
  status: string;
  invoice_status: string;
}
