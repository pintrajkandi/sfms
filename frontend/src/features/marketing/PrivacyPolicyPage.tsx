import { LegalPage, type LegalSection } from "./LegalPage";
import { CONTACT } from "./MarketingLayout";

const B = CONTACT.brand;

const SECTIONS: LegalSection[] = [
  {
    heading: "Who we are",
    body: [
      `${B} provides a school finance and accounting platform. When a school uses ${B}, the school is the "Data Fiduciary" (it decides what data is collected and why) and ${B} acts as the "Data Processor", safeguarding that data and processing it only on the school's instructions. This policy explains how we handle personal data.`,
    ],
  },
  {
    heading: "Information we process",
    body: [
      "On behalf of schools we process: student details (name, ID, date of birth, contact, guardian details, class), financial records (invoices, fees, payments), staff and payroll details, and account information (login email, role, activity logs).",
      "We do not sell personal data, and we do not use school or student data to train external advertising or profiling systems.",
    ],
  },
  {
    heading: "How we use the information",
    body: [
      "We use the information solely to provide and maintain the service — collecting fees, generating invoices and receipts, running payroll, sending notifications, producing reports, and keeping secure backups — and to provide support when a school requests it.",
    ],
  },
  {
    heading: "How we protect it",
    body: [
      "Each school's data is isolated in its own database space, encrypted in transit and at rest, backed up nightly with verified restores, and access is role-based and audited. See our Data & Security page for details.",
    ],
  },
  {
    heading: "Data residency",
    body: [
      "We store personal data and backups within India, in line with the Digital Personal Data Protection (DPDP) Act, 2023.",
    ],
  },
  {
    heading: "Sub-processors",
    body: [
      "We use trusted service providers to deliver the platform — for hosting and storage, email/SMS/WhatsApp notifications, online payments, optional single sign-on, and error monitoring. Each is bound by confidentiality and data-protection obligations. A current list is available on request.",
    ],
  },
  {
    heading: "Your rights",
    body: [
      "Schools (and, through them, students and guardians) can request access to, correction of, or erasure of personal data, and can manage consent and retention. Erasure anonymises personal details while retaining financial records required by law.",
    ],
  },
  {
    heading: "Data retention",
    body: [
      "We keep personal data for as long as the school uses the service and for any retention period the school configures. On request or on account closure, we return and/or delete the data, including from backups within the normal backup rotation.",
    ],
  },
  {
    heading: "Changes to this Policy",
    body: [
      `We may update or change this Privacy Policy at any time at our sole discretion. When we do, we will revise the "Last updated" date at the top of this page. Any changes take effect as soon as they are posted here, and your continued use of ${B} after that means you accept the updated policy. We encourage you to review this page periodically.`,
    ],
  },
  {
    heading: "Contact",
    body: [
      `For any privacy question or data request, contact us at ${CONTACT.email}.`,
    ],
  },
];

export function PrivacyPolicyPage() {
  return (
    <LegalPage
      kicker="Legal"
      title="Privacy Policy"
      updated="3 August 2026"
      intro={`This Privacy Policy explains how ${B} handles personal data when schools use our platform. We keep it deliberately plain so it is easy to understand.`}
      sections={SECTIONS}
    />
  );
}
