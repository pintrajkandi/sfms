# Data Processing Agreement (DPA)

**Template — review with legal counsel before use. Bracketed `[…]` fields are to be completed per school.**

This Data Processing Agreement ("**DPA**") forms part of the agreement between:

- **The School** — `[School legal name]`, `[address]` (the "**School**", acting as the **Data Fiduciary / Data Controller**); and
- **YukiCares** — `[YukiCares legal entity name]`, `[registered address]` (the "**Processor**"),

each a "Party" and together the "Parties", governing the Processor's processing of Personal Data on behalf of the School through the YukiCares school finance platform (the "**Service**").

Effective date: `[date]`.

---

## 1. Definitions

Terms such as **Personal Data**, **Data Principal**, **Data Fiduciary**, **Data Processor**, **Processing**, and **Personal Data Breach** have the meanings given in India's **Digital Personal Data Protection Act, 2023 ("DPDP Act")** and, where applicable to the School, equivalent laws (e.g. GDPR, FERPA). "Data Controller" and "Data Processor" are used interchangeably with "Data Fiduciary" and the Act's processor concept.

## 2. Roles of the Parties

2.1 The **School is the Data Fiduciary**: it determines the purposes and means of processing the Personal Data of its Data Principals.

2.2 **YukiCares is the Data Processor**: it processes Personal Data **only on the documented instructions of the School**, including as set out in this DPA and the Service.

2.3 The School is responsible for having a lawful basis (including any required consent, and verifiable parental consent for children) for the data it puts into the Service.

## 3. Subject matter, duration, nature and purpose

3.1 **Subject matter & duration:** processing for the term of the School's subscription to the Service, plus any deletion period in Section 11.

3.2 **Nature & purpose:** hosting and processing school-finance data to provide fee collection, invoicing, payments, payroll, expenses, inventory, accounting, reporting, notifications and backups.

3.3 **Categories of Data Principals:** students; parents/guardians; teaching and non-teaching staff; School administrators.

3.4 **Categories of Personal Data:**
- Student: name, student ID, date of birth, gender, photo, contact details, guardian details, class/section, enrolment status.
- Financial: invoices, fees, payments, payment references, mandates.
- Staff: name, contact, role, payroll and statutory details (e.g. PF/ESI/TDS).
- Account: login email, role, activity/audit logs.

3.5 **No special-category processing beyond the above is instructed** unless separately agreed in writing.

## 4. Processor obligations

YukiCares shall:

- (a) process Personal Data **only on the School's documented instructions**, and not for its own purposes;
- (b) ensure persons authorised to process are under an obligation of **confidentiality**;
- (c) implement and maintain the **technical and organisational security measures** in **Annex B**;
- (d) respect the conditions in Section 6 for engaging **sub-processors**;
- (e) **assist the School** in responding to Data Principal requests (Section 7);
- (f) assist the School with security, breach notification, and (where applicable) data-protection impact assessments;
- (g) at the School's choice, **delete or return** all Personal Data at the end of the engagement (Section 11);
- (h) make available information necessary to **demonstrate compliance** and allow for audits (Section 9);
- (i) **not transfer** Personal Data outside the agreed territory (Section 8) without the School's authorisation.

## 5. Data residency

Unless otherwise agreed in writing, YukiCares stores the School's Personal Data and backups **within India**. Any change of storage location will be notified to the School in advance.

## 6. Sub-processors

6.1 The School provides **general authorisation** for YukiCares to engage the sub-processors listed in **Annex C** to deliver the Service.

6.2 YukiCares imposes data-protection obligations on each sub-processor **no less protective** than this DPA and remains liable for their performance.

6.3 YukiCares will give the School **reasonable prior notice** of any intended addition or replacement of a sub-processor, and the School may object on reasonable data-protection grounds.

## 7. Assisting with Data Principal rights

The Service provides tools, and YukiCares will otherwise reasonably assist the School, to fulfil requests for:

- **access / portability** — a machine-readable export of a Data Principal's data;
- **correction**;
- **erasure** — anonymisation of personal details while retaining financial records required by law;
- **consent** management (record / withdraw);
- **retention** — automatic minimisation of data of Data Principals who have left, per the School's configured period.

## 8. International transfers

YukiCares will not transfer Personal Data to a location outside the territory agreed in Section 5 except on the School's instructions or as permitted by applicable law, and subject to appropriate safeguards.

## 9. Audit

YukiCares will make available to the School the information reasonably necessary to demonstrate compliance with this DPA, and will allow for and contribute to audits (including inspections) conducted by the School or its mandated auditor, on reasonable notice and subject to confidentiality, no more than once per year unless required by a regulator or following a breach.

## 10. Personal Data Breach

10.1 YukiCares will notify the School **without undue delay and in any case within 72 hours** of becoming aware of a Personal Data Breach affecting the School's data.

10.2 The notification will describe, to the extent known: the nature of the breach, categories and approximate number of Data Principals and records affected, likely consequences, and the measures taken or proposed.

10.3 YukiCares will assist the School with its own notification obligations to the Data Protection Board of India and affected Data Principals.

## 11. Return and deletion

On termination or expiry, or on the School's earlier written request, YukiCares will, at the School's choice, **return** the Personal Data (e.g. full export) and/or **delete** it, including from backups within the normal backup rotation cycle, save where retention is required by law. A certificate of deletion will be provided on request.

## 12. Liability and governing law

Liability is as set out in the main agreement between the Parties. This DPA is governed by the laws of **India**, and the courts of `[city, India]` have exclusive jurisdiction, without prejudice to any mandatory regulatory forum.

---

## Annex A — Processing details

As described in **Section 3** (subject matter, duration, nature, purpose, categories of Data Principals and Personal Data).

## Annex B — Technical and organisational security measures

YukiCares maintains at least the following measures:

1. **Tenant isolation** — each School's data is stored in its own database schema; queries cannot cross School boundaries; sessions are tenant-scoped.
2. **Encryption** — TLS/HTTPS for all data in transit; encryption at rest for the database and backups.
3. **Access control** — role-based permissions; verified accounts; least-privilege internal access; any support access to a School is restricted, time-limited and logged.
4. **Backups & recovery** — automated nightly backups with integrity checksums and restore verification, stored off-site; documented recovery objectives.
5. **Auditability** — an immutable-style audit log of key actions (who, what, when, on which record).
6. **Logging hygiene** — application logs exclude secrets and full personal data.
7. **Monitoring** — error and security monitoring with alerting; a defined incident-response process.
8. **Data-subject tooling** — built-in export, erasure/anonymisation, consent and retention controls.
9. **Secure development & maintenance** — dependency and vulnerability management; segregation of production access.

## Annex C — Approved sub-processors

| Sub-processor | Purpose | Location |
|---|---|---|
| `[Hosting/DB provider]` | Application hosting & managed database | `[India region]` |
| Bunny.net (or `[object storage provider]`) | File & backup storage | `[India region/zone]` |
| MSG91 | Email / SMS / WhatsApp notifications | `[region]` |
| Razorpay | Online payment processing | India |
| Auth0 (Okta) | Optional single sign-on | `[region]` |
| Sentry | Error monitoring (PII-scrubbed) | `[region]` |

*Update this list as sub-processors change; notify Schools of changes per Section 6.3.*

---

## Signatures

**For the School (Data Fiduciary)**  
Name: `___________________`  Title: `___________________`  
Signature: `___________________`  Date: `___________`

**For YukiCares (Data Processor)**  
Name: `___________________`  Title: `___________________`  
Signature: `___________________`  Date: `___________`

---

*This template is provided for convenience and does not constitute legal advice. Have it reviewed by qualified counsel before signing.*
