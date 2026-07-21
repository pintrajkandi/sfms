# SFMS — Core Modules Feature Tracker

Status legend: `[x]` done · `[~]` partial · `[ ]` not built. Mapped against
`Core Modules.pdf`. Updated as we build.

> **Done (latest):** §3 Accounting — Chart of Accounts, double-entry Journals
> (auto-posted), General Ledger, Trial Balance, P&L, Balance Sheet, **Day Book**,
> **Cash/Bank Book** (GL presets). §14 — **Student Ledger** + **Parent Ledger**
> reports. UI under **/accounting** and **/reports**.
> **Next up:** Transport module (§7) or SaaS subscription billing (§18);
> Collection-by-Class/Employee reports; push notifications (§15).

---

## 1. School Management
- [x] Classes & Sections
- [x] Students
- [~] Parents (guardian fields + OTP parent portal; no parent entity/management)
- [x] Staff (teachers + payroll)
- [~] User roles & permissions (backend RBAC done; management UI removed earlier)

## 2. Fee Management
### Fee Structure
- [x] Class-wise fees
- [~] Student-wise custom fees (custom invoices + discounts; no per-student plan)
- [ ] Route-wise transport fees
- [ ] Hostel fees
- [~] Late fee rules (per-invoice late fee; no rules engine)
- [x] Discounts
- [x] Scholarships
- [~] One-time fees (recurring flag)
- [~] Monthly / Quarterly / Annual fees (no auto-frequency schedule generator)
### Fee Collection
- [x] Cash / UPI / Card / Bank transfer / Cheque
- [x] Partial payments
- [~] Advance payments
- [x] Refunds
- [x] Adjustments (credit notes)
### Fee Receipt
- [~] QR code (only on GST e-invoice)
- [ ] Barcode
- [x] Digital signature
- [~] Custom template
- [~] Email receipt
- [x] WhatsApp receipt

## 3. Accounting  ← core DONE
- [x] Chart of Accounts (Assets / Liabilities / Income / Expenses / Equity + custom)
- [x] Journals (auto entries: fee/invoice, payment, refund, salary/payroll, expense)
- [x] General Ledger (per-account, running balance)
- [x] Trial Balance
- [x] Profit & Loss (formal statement)
- [x] Balance Sheet
- [~] Cash Flow (monthly trend; no daily/weekly cashbook)
- [x] Bank Reconciliation (upload + auto-match)
- [x] Outstanding Receivables
- [x] Ageing Report 30/60/90

## 4. Expense Management
- [x] Expense categories + vendor bills
- [~] Approval workflow (reimbursable flag; no multi-stage)

## 5. Payroll
- [x] Salary / Deductions / PF / ESI / Professional Tax / TDS
- [x] Payslips

## 6. Inventory
- [x] Item tracking (categories, SKU, cost, supplier, edit)
- [~] Inventory accounting (not journaled)

## 7. Transport Accounting
- [ ] Vehicle expenses (fuel / driver salary / maintenance / insurance)
- [ ] Route profitability

## 9. Online Payments
- [x] Razorpay + automatic reconciliation

## 11. Accountant Dashboard
- [~] Daily/Monthly collection, pending, outstanding, trend, today's expenses
- [ ] Cash in Hand / Bank Deposits / Yesterday Collection breakouts

## 13. Admin Dashboard (cross-school)
- [~] Platform admin + tenant/plan registry
- [ ] MRR / Revenue / Growth / Renewals / Active Schools metrics

## 14. Reports
- [x] Outstanding, Ageing, Expense, GST, Monthly Collection
- [x] Trial Balance, Balance Sheet, P&L, General Ledger (under /accounting)
- [x] Student Ledger, Parent Ledger (under /reports)
- [x] Cash Book, Bank Book, Day Book (under /accounting)
- [~] Fee Register, Daily Collection, TDS
- [ ] Collection by Employee / Branch / Class
- [ ] Transport Report / Hostel Report

## 15. Notification Engine
- [x] WhatsApp / SMS reminders
- [~] Email reminders
- [ ] Push notifications
- [x] Triggers: Due-soon, Overdue, Receipt Generated
- [~] Trigger: New Fee Added

## 16. Document Management
- [~] Files stored in MinIO; no unified document-store UI + categories

## 17. Audit Logs
- [x] Who / action / entity / before-after / timestamp + UI
- [~] IP capture

## 18. SaaS Features
### Organization
- [x] Multiple schools, schema-per-tenant isolation, custom domains, white-label branding, logo/theme
### Subscription & Billing
- [x] Trial period
- [~] Monthly/yearly plans
- [ ] Online subscription payments
- [ ] Usage-based billing
- [ ] SaaS invoice generation
### Tenant Management
- [x] Enable/disable schools
- [~] User limits (max_students); feature flags (JSON, enforcement partial)
- [ ] Storage quotas
- [ ] Branch limits
### Integrations
- [x] Razorpay / WhatsApp / SMS / Email
- [x] Accounting exports (Tally / Zoho / QuickBooks / CSV / PDF)
- [ ] Google Workspace / Microsoft 365
### Security
- [x] RBAC, Audit trails, Automated backups
- [~] Disaster recovery (warm standby), SSO (Auth0, env-gated)
- [ ] 2FA
- [ ] IP restrictions
