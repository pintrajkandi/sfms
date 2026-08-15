// Sidebar mirrors the original Mintlify docs.json navigation groups.
/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: "category",
      label: "Get Started",
      collapsed: false,
      items: ["introduction", "quickstart", "getting-started/sign-up", "getting-started/logging-in"],
    },
    {
      type: "category",
      label: "School Settings",
      items: [
        "settings/overview",
        "settings/school-profile",
        "settings/classes-sections",
        "settings/departments",
        "settings/fee-setup",
        "settings/academic-year",
        "settings/payroll",
        "settings/notifications",
      ],
    },
    {
      type: "category",
      label: "Users & Access",
      items: ["users/users", "users/roles-permissions"],
    },
    {
      type: "category",
      label: "Students",
      items: ["students/add-student", "students/manage-students"],
    },
    {
      type: "category",
      label: "Fees & Collection",
      items: ["fees/fee-types", "fees/collect-fee", "fees/invoices-receipts"],
    },
    {
      type: "category",
      label: "Staff & Payroll",
      items: ["staff/add-teacher", "staff/teachers-list", "staff/payouts"],
    },
    {
      type: "category",
      label: "Other Modules",
      items: [
        "modules/expenses",
        "modules/inventory",
        "modules/transport-hostel",
        "modules/finance-reports",
      ],
    },
    {
      type: "category",
      label: "Help",
      items: ["mobile-app", "faq"],
    },
  ],
};

module.exports = sidebars;
