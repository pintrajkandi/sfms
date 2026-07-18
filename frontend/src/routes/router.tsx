import { createBrowserRouter } from "react-router-dom";
import { ActivityLogger } from "@/components/ActivityLogger";
import { AppShell } from "@/components/AppShell";
import { Auth0Callback } from "@/features/auth/Auth0Callback";
import { ForgotPasswordScreen } from "@/features/auth/ForgotPasswordScreen";
import { LoginScreen } from "@/features/auth/LoginScreen";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { ResetPasswordScreen } from "@/features/auth/ResetPasswordScreen";
import { SignupScreen } from "@/features/auth/SignupScreen";
import { VerifyEmailScreen } from "@/features/auth/VerifyEmailScreen";
import { FeeCollectionDashboard } from "@/features/collections/FeeCollectionDashboard";
import { FeeCollectionWizard } from "@/features/collections/FeeCollectionWizard";
import { InvoiceDetailPage } from "@/features/collections/InvoiceDetailPage";
import { InvoicesListPage } from "@/features/collections/InvoicesListPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { SubmitExpensePage } from "@/features/expenses/SubmitExpensePage";
import { FinanceDashboard } from "@/features/finance/FinanceDashboard";
import { DefaultersPage } from "@/features/reports/DefaultersPage";
import { AddInventoryPage } from "@/features/inventory/AddInventoryPage";
import { InventoryListPage } from "@/features/inventory/InventoryListPage";
import { OnboardingGate } from "@/features/onboarding/OnboardingGate";
import { ParentPortal } from "@/features/parent/ParentPortal";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { AddTeacherPage } from "@/features/staff/AddTeacherPage";
import { TeacherPayoutPage } from "@/features/staff/TeacherPayoutPage";
import { AddStudentPage } from "@/features/students/AddStudentPage";
import { StudentDetailPage } from "@/features/students/StudentDetailPage";
import { StudentsPage } from "@/features/students/StudentsPage";

export const router = createBrowserRouter([
  {
    // Wraps everything so every route + click is logged (see ActivityLogger).
    element: <ActivityLogger />,
    children: [
      { path: "/signup", element: <SignupScreen /> },
      { path: "/login", element: <LoginScreen /> },
      { path: "/forgot-password", element: <ForgotPasswordScreen /> },
      { path: "/reset-password", element: <ResetPasswordScreen /> },
      { path: "/auth/callback", element: <Auth0Callback /> },
      { path: "/verify-email", element: <VerifyEmailScreen /> },
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
                  { path: "students/:id", element: <StudentDetailPage /> },
                  { path: "fee-collection", element: <FeeCollectionDashboard /> },
                  { path: "fee-collection/new", element: <FeeCollectionWizard /> },
                  { path: "invoices", element: <InvoicesListPage /> },
                  { path: "invoices/:id", element: <InvoiceDetailPage /> },
                  { path: "payouts", element: <TeacherPayoutPage /> },
                  { path: "teachers/new", element: <AddTeacherPage /> },
                  { path: "expenses/new", element: <SubmitExpensePage /> },
                  { path: "inventory", element: <InventoryListPage /> },
                  { path: "inventory/new", element: <AddInventoryPage /> },
                  { path: "finance", element: <FinanceDashboard /> },
                  { path: "reports", element: <DefaultersPage /> },
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
