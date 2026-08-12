import { LegalPage, type LegalSection } from "./LegalPage";
import { CONTACT } from "./MarketingLayout";

const B = CONTACT.brand;

const SECTIONS: LegalSection[] = [
  {
    heading: "Acceptance of these Terms",
    body: [
      `By creating an account or using ${B} (the "Service"), you agree to these Terms of Service on behalf of your school or institution. If you do not agree, do not use the Service.`,
    ],
  },
  {
    heading: "The Service",
    body: [
      `${B} provides a school finance and accounting platform, including fee collection, invoicing, payments, payroll, expenses, inventory, accounting, reporting, notifications and backups. Features may evolve over time as we improve the platform.`,
    ],
  },
  {
    heading: "Accounts and eligibility",
    body: [
      "You are responsible for the accuracy of the information you provide, for the activity that occurs under your accounts, and for keeping login credentials confidential. You must promptly notify us of any unauthorised use.",
    ],
  },
  {
    heading: "Your data and responsibilities",
    body: [
      "You retain ownership of the data you put into the Service. You are responsible for having a lawful basis (including any required consent, and verifiable parental consent for children) for the personal data you process, and for using the Service in compliance with applicable law.",
      "You agree not to misuse the Service, attempt to breach its security, or use it to store unlawful content.",
    ],
  },
  {
    heading: "Fees and plans",
    body: [
      `${B} offers a free plan for schools and an Enterprise plan for larger or multi-branch institutions. Where paid features apply, charges and terms will be communicated to you in advance.`,
    ],
  },
  {
    heading: "Availability and support",
    body: [
      "We work to keep the Service available and reliable, but it is provided on an 'as available' basis. Planned maintenance and occasional interruptions may occur. Support is provided by email and, where available, live chat.",
    ],
  },
  {
    heading: "Privacy and security",
    body: [
      "Our handling of personal data is described in our Privacy Policy and Data & Security page, and, for schools, in our Data Processing Agreement. These form part of your agreement with us.",
    ],
  },
  {
    heading: "Intellectual property",
    body: [
      `The Service, including its software, design and branding, is owned by ${B} and its licensors. These Terms do not grant you any rights to our intellectual property other than the right to use the Service.`,
    ],
  },
  {
    heading: "Limitation of liability",
    body: [
      "To the maximum extent permitted by law, the Service is provided without warranties of any kind, and our liability arising from your use of the Service is limited as set out in your agreement with us.",
    ],
  },
  {
    heading: "Suspension and termination",
    body: [
      "We may suspend or terminate access for breach of these Terms or misuse of the Service. You may stop using the Service at any time; on closure, we will return and/or delete your data as described in our Privacy Policy and DPA.",
    ],
  },
  {
    heading: "Changes to these Terms",
    body: [
      `We may update or change these Terms of Service at any time at our sole discretion. When we do, we will revise the "Last updated" date at the top of this page. Changes take effect as soon as they are posted here, and your continued use of ${B} after that means you accept the updated Terms. We encourage you to review this page periodically.`,
    ],
  },
  {
    heading: "Governing law",
    body: [
      "These Terms are governed by the laws of India, and the courts of India have jurisdiction over any dispute, without prejudice to any mandatory regulatory forum.",
    ],
  },
  {
    heading: "Contact",
    body: [
      `Questions about these Terms? Contact us at ${CONTACT.email}.`,
    ],
  },
];

export function TermsPage() {
  return (
    <LegalPage
      kicker="Legal"
      title="Terms of Service"
      updated="3 August 2026"
      intro={`These Terms of Service govern your use of ${B}. Please read them carefully.`}
      sections={SECTIONS}
    />
  );
}
