import { createBrowserRouter } from "react-router-dom";
import { ActivityLogger } from "@/components/ActivityLogger";
import { AppShell } from "@/components/AppShell";
import { Auth0Callback } from "@/features/auth/Auth0Callback";
import { ForgotPasswordScreen } from "@/features/auth/ForgotPasswordScreen";
import { ImpersonateScreen } from "@/features/auth/ImpersonateScreen";
import { LoginScreen } from "@/features/auth/LoginScreen";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { ResetPasswordScreen } from "@/features/auth/ResetPasswordScreen";
import { SignupScreen } from "@/features/auth/SignupScreen";
import { VerifyEmailScreen } from "@/features/auth/VerifyEmailScreen";
import { CollectionRiskPage } from "@/features/collections/CollectionRiskPage";
import { FeeCollectionDashboard } from "@/features/collections/FeeCollectionDashboard";
import { FeeCollectionsListPage } from "@/features/collections/FeeCollectionsListPage";
import { FeeCollectionWizard } from "@/features/collections/FeeCollectionWizard";
import { InvoiceDetailPage } from "@/features/collections/InvoiceDetailPage";
import { ReceiptPage } from "@/features/collections/ReceiptPage";
import { InvoicesListPage } from "@/features/collections/InvoicesListPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { SubmitExpensePage } from "@/features/expenses/SubmitExpensePage";
import { AccountingPage } from "@/features/finance/AccountingPage";
import { FinanceDashboard } from "@/features/finance/FinanceDashboard";
import { AuditLogPage } from "@/features/audit/AuditLogPage";
import { LandingPage } from "@/features/marketing/LandingPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { SupportPage } from "@/features/support/SupportPage";
import { TransportPage } from "@/features/transport/TransportPage";
import { HostelPage } from "@/features/hostel/HostelPage";
import { DocumentsPage } from "@/features/documents/DocumentsPage";
import { AddInventoryPage } from "@/features/inventory/AddInventoryPage";
import { InventoryListPage } from "@/features/inventory/InventoryListPage";
import { OnboardingGate } from "@/features/onboarding/OnboardingGate";
import { ParentPortal } from "@/features/parent/ParentPortal";
import { ClassesPage } from "@/features/settings/ClassesPage";
import { FeeSetupPage } from "@/features/settings/FeeSetupPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { AddTeacherPage } from "@/features/staff/AddTeacherPage";
import { TeacherPayoutPage } from "@/features/staff/TeacherPayoutPage";
import { AddStudentPage } from "@/features/students/AddStudentPage";
import { ParentsPage } from "@/features/students/ParentsPage";
import { PlatformDashboard } from "@/features/platform/PlatformDashboard";
import { StudentDetailPage } from "@/features/students/StudentDetailPage";
import { StudentsPage } from "@/features/students/StudentsPage";

export const router = createBrowserRouter([
  {
    // Wraps everything so every route + click is logged (see ActivityLogger).
    element: <ActivityLogger />,
    children: [
      { path: "/welcome", element: <LandingPage /> },
      { path: "/signup", element: <SignupScreen /> },
      { path: "/login", element: <LoginScreen /> },
      { path: "/forgot-password", element: <ForgotPasswordScreen /> },
      { path: "/reset-password", element: <ResetPasswordScreen /> },
      { path: "/auth/callback", element: <Auth0Callback /> },
      { path: "/verify-email", element: <VerifyEmailScreen /> },
      { path: "/impersonate", element: <ImpersonateScreen /> },
      // Public parent portal — OUTSIDE RequireAuth/OnboardingGate (parents are not staff).
      { path: "/parent", element: <ParentPortal /> },
      {
        element: <RequireAuth />,
        children: [
          {
            element: <OnboardingGate />,
            children: [
              {
                path: "/",
                element: <AppShell />,
                children: [
                  { index: true, element: <DashboardPage /> },
                  { path: "students", element: <StudentsPage /> },
                  { path: "students/new", element: <AddStudentPage /> },
                  { path: "students/:id/edit", element: <AddStudentPage /> },
                  { path: "students/:id", element: <StudentDetailPage /> },
                  { path: "parents", element: <ParentsPage /> },
                  { path: "platform", element: <PlatformDashboard /> },
                  { path: "fee-collection", element: <FeeCollectionDashboard /> },
                  { path: "fee-collection/new", element: <FeeCollectionWizard /> },
                  { path: "fee-collections", element: <FeeCollectionsListPage /> },
                  { path: "invoices", element: <InvoicesListPage /> },
                  { path: "invoices/:id", element: <InvoiceDetailPage /> },
                  { path: "receipts/:id", element: <ReceiptPage /> },
                  { path: "payouts", element: <TeacherPayoutPage /> },
                  { path: "teachers/new", element: <AddTeacherPage /> },
                  { path: "teachers/:id/edit", element: <AddTeacherPage /> },
                  { path: "expenses/new", element: <SubmitExpensePage /> },
                  { path: "inventory", element: <InventoryListPage /> },
                  { path: "inventory/new", element: <AddInventoryPage /> },
                  { path: "inventory/:id/edit", element: <AddInventoryPage /> },
                  { path: "transport", element: <TransportPage /> },
                  { path: "hostel", element: <HostelPage /> },
                  { path: "documents", element: <DocumentsPage /> },
                  { path: "finance", element: <FinanceDashboard /> },
                  { path: "accounting", element: <AccountingPage /> },
                  { path: "reports", element: <ReportsPage /> },
                  { path: "audit-log", element: <AuditLogPage /> },
                  { path: "support", element: <SupportPage /> },
                  { path: "risk", element: <CollectionRiskPage /> },
                  { path: "classes", element: <ClassesPage /> },
                  { path: "fee-setup", element: <FeeSetupPage /> },
                  { path: "settings", element: <SettingsPage /> },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
]);
