# SFMS — Core Modules Feature Tracker

Status legend: `[x]` done · `[~]` partial · `[ ]` not built. Mapped against
`Core Modules.pdf`. Updated as we build.

> **Done (latest batch):** Push notifications (§15, web-push + VAPID),
> cross-school Admin Dashboard (§13, /platform), accountant dashboard breakouts
> (§11), receipt polish (§2, QR + barcode + email receipt + printable page),
> Parents as first-class records (§1, /parents), inventory accounting (§6).
> **Remaining (per your call):** deferred SaaS billing (§18); 2FA / IP
> restrictions dropped; Google/MS365 optional; multi-branch not needed.

---

## 1. School Management
- [x] Classes & Sections
- [x] Students
- [x] Parents (first-class Parent records + siblings) — /parents
- [x] Staff (teachers + payroll)
- [~] User roles & permissions (backend RBAC done; management UI removed earlier)

## 2. Fee Management
### Fee Structure
- [x] Class-wise fees
- [~] Student-wise custom fees (custom invoices + discounts; no per-student plan)
- [x] Route-wise transport fees (route fare + student route assignment)
- [x] Hostel fees (hostel fee + resident assignment)
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
- [x] QR code on receipt (+ barcode)
- [x] Barcode on receipt
- [x] Digital signature
- [x] Custom template (school-branded printable receipt)
- [x] Email receipt (on payment)
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
- [x] Inventory accounting (purchases journaled to ledger)

## 7. Transport Accounting
- [x] Routes + vehicles (drivers, capacity, route assignment)
- [x] Vehicle expenses (fuel / driver salary / maintenance / insurance) — auto-journaled
- [x] Route profitability (riders × fare − expenses)

## 9. Online Payments
- [x] Razorpay + automatic reconciliation

## 11. Accountant Dashboard
- [x] Daily/Monthly collection, pending, outstanding, trend, today's expenses
- [x] Cash in Hand / Bank Deposits / Yesterday Collection breakouts

## 13. Admin Dashboard (cross-school)
- [~] Platform admin + tenant/plan registry (Django admin)
- [x] MRR / Revenue / Growth / Renewals / Active Schools metrics (/platform)

## 14. Reports
- [x] Outstanding, Ageing, Expense, GST, Monthly Collection
- [x] Trial Balance, Balance Sheet, P&L, General Ledger (under /accounting)
- [x] Student Ledger, Parent Ledger (under /reports)
- [x] Cash Book, Bank Book, Day Book (under /accounting)
- [x] Transport Report (route profitability under /transport)
- [x] Collection by Class / Employee / Method (Reports → Collection Analysis)
- [~] Fee Register, Daily Collection, TDS
- [ ] Collection by Branch (no multi-branch model yet)
- [x] Hostel Report (occupancy + P/L under /hostel)

## 15. Notification Engine
- [x] WhatsApp / SMS reminders
- [~] Email reminders
- [x] Push notifications (web-push + VAPID)
- [x] Triggers: Due-soon, Overdue, Receipt Generated
- [~] Trigger: New Fee Added

## 16. Document Management
- [x] Unified document store (upload/list/download/delete) with categories
      (student docs, receipts, invoices, vendor bills, salary slips) — /documents

## 17. Audit Logs
- [x] Who / action / entity / before-after / timestamp + UI
- [~] IP capture

## 18. SaaS Features
### Organization
- [x] Multiple schools, schema-per-tenant isolation, custom domains, white-label branding, logo/theme
### Subscription & Billing
- [x] Trial period
- [x] Plans (monthly/yearly, limits, features, default) + Free plan auto-assigned
- [x] Subscription view (current plan + usage) — Settings → Subscription
- [ ] Online subscription payments (deferred until paid plans launch)
- [ ] Usage-based billing (deferred)
- [ ] SaaS invoice generation (deferred)
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

