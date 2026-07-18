import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ApiError } from "@/api/client";
import { academicYears, fees, invoices, payments, students } from "@/api/resources";
import type { FeeType, Student } from "@/api/types";
import { Labeled, Select, TextArea, TextInput, Toast } from "@/components/form";
import { formatMoney } from "@/lib/money";

const STEPS = ["Student Info", "Fee Details", "Payment"];

const METHODS = [
  { value: "card", label: "Credit Card", icon: "💳" },
  { value: "bank_transfer", label: "Bank Transfer", icon: "🏦" },
  { value: "paypal", label: "PayPal", icon: "🅿️" },
  { value: "cash", label: "Cash", icon: "💵" },
];

interface Line {
  fee_type: number;
  name: string;
  amount: string;
}

const readonly = "bg-slate-50 text-slate-700";

export function FeeCollectionWizard() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [step, setStep] = useState(0);

  const [query, setQuery] = useState("");
  const [student, setStudent] = useState<Student | null>(null);
  const [academicYearId, setAcademicYearId] = useState("");
  const [term, setTerm] = useState("Semester 1");

  const [lines, setLines] = useState<Line[]>([]);
  const [addFeeId, setAddFeeId] = useState("");

  const [method, setMethod] = useState("card");
  const [amount, setAmount] = useState("");
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10));
  const [txn, setTxn] = useState("");
  const [collectedBy, setCollectedBy] = useState("");
  const [remarks, setRemarks] = useState("");

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const preStudent = params.get("student");
  const preloaded = useQuery({
    queryKey: ["wiz-student", preStudent],
    queryFn: () => students.get(preStudent!),
    enabled: !!preStudent,
  });
  useEffect(() => {
    if (preloaded.data && !student) setStudent(preloaded.data);
  }, [preloaded.data, student]);

  const search = useQuery({
    queryKey: ["wiz-search", query],
    queryFn: () => students.search(query),
    enabled: step === 0 && query.length > 1 && !student,
  });
  const feeTypes = useQuery({ queryKey: ["fee-types"], queryFn: () => fees.types() });
  const years = useQuery({ queryKey: ["academic-years"], queryFn: () => academicYears.list() });

  const total = useMemo(
    () => lines.reduce((s, l) => s + (Number.parseFloat(l.amount) || 0), 0),
    [lines],
  );
  useEffect(() => setAmount(total.toFixed(2)), [total]);

  function addFee(ft: FeeType) {
    if (lines.some((l) => l.fee_type === ft.id)) return;
    setLines((ls) => [...ls, { fee_type: ft.id, name: ft.name, amount: ft.default_amount }]);
  }

  async function confirm() {
    if (!student || lines.length === 0) return;
    setSubmitting(true);
    setError("");
    try {
      const invoice = await invoices.create({
        student: student.id,
        academic_year: academicYearId ? Number(academicYearId) : null,
        lines: lines.map((l) => ({ fee_type: l.fee_type, quantity: 1, unit_price: l.amount })),
      });
      await payments.create({
        invoice: invoice.id,
        amount: amount || invoice.total,
        method,
        reference: txn,
        paid_at: paymentDate ? `${paymentDate}T00:00:00Z` : undefined,
        idempotency_key: crypto.randomUUID(),
      });
      navigate(`/students/${student.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not process the payment.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-10">
      {/* Banner */}
      <div className="rounded-2xl bg-brand-gradient px-8 py-8 text-center text-white">
        <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-3 py-1 text-xs font-semibold">
          ◉ Fee Collection Portal
        </span>
        <h1 className="mt-3 text-3xl font-bold">Student Fee Collection</h1>
        <p className="mx-auto mt-1 max-w-md text-sm text-white/80">
          Submit and process student fee payments quickly and securely.
        </p>
      </div>

      {/* Step tracker */}
      <div className="flex items-center justify-center">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold ${
                  i <= step ? "bg-brand text-white" : "bg-slate-200 text-slate-400"
                }`}
              >
                {i + 1}
              </div>
              <span className={`mt-1 text-xs ${i === step ? "font-semibold text-brand" : "text-slate-400"}`}>
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`mx-3 mb-4 h-0.5 w-20 ${i < step ? "bg-brand" : "bg-slate-200"}`} />
            )}
          </div>
        ))}
      </div>

      {error && <Toast tone="error" message={error} />}

      {/* Step 1 — Student Info */}
      {step === 0 && (
        <div className="space-y-6">
          <Card icon="🎓" title="Student Information" subtitle="Enter the student's personal details">
            {!student && (
              <div className="mb-5">
                <TextInput placeholder="Search student by name or ID…" value={query} onChange={(e) => setQuery(e.target.value)} />
                {search.data && query.length > 1 && (
                  <div className="mt-2 divide-y divide-slate-50 rounded-lg border border-slate-100">
                    {search.data.results.map((s) => (
                      <button key={s.id} onClick={() => setStudent(s)} className="flex w-full justify-between px-4 py-2.5 text-left text-sm hover:bg-slate-50">
                        <span className="font-medium text-slate-800">{s.full_name}</span>
                        <span className="font-mono text-xs text-slate-400">{s.student_id}</span>
                      </button>
                    ))}
                    {search.data.results.length === 0 && <p className="px-4 py-2.5 text-sm text-slate-400">No students found.</p>}
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <Labeled label="Student ID" required>
                <TextInput className={readonly} readOnly value={student?.student_id ?? ""} placeholder="e.g. STU-2024-001" />
              </Labeled>
              <Labeled label="First name" required>
                <TextInput className={readonly} readOnly value={student?.first_name ?? ""} placeholder="First name" />
              </Labeled>
              <Labeled label="Last name" required>
                <TextInput className={readonly} readOnly value={student?.last_name ?? ""} placeholder="Last name" />
              </Labeled>
              <Labeled label="Date of birth">
                <TextInput className={readonly} readOnly value={student?.date_of_birth ?? ""} placeholder="—" />
              </Labeled>
              <Labeled label="Gender">
                <TextInput className={`${readonly} capitalize`} readOnly value={student?.gender ?? ""} placeholder="—" />
              </Labeled>
              <Labeled label="Email address">
                <TextInput className={readonly} readOnly value={student?.email ?? ""} placeholder="student@school.edu" />
              </Labeled>
            </div>
            {student && (
              <button onClick={() => setStudent(null)} className="mt-3 text-sm text-brand hover:underline">
                Change student
              </button>
            )}
          </Card>

          <Card icon="🏫" title="Academic Details" subtitle="Course, class, and academic year">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <Labeled label="Department" required>
                <TextInput className={readonly} readOnly value={student?.department || student?.program || ""} placeholder="—" />
              </Labeled>
              <Labeled label="Class / grade" required>
                <TextInput className={readonly} readOnly value={student?.grade ?? ""} placeholder="—" />
              </Labeled>
              <Labeled label="Academic year" required>
                <Select value={academicYearId} onChange={(e) => setAcademicYearId(e.target.value)}>
                  <option value="">Select year</option>
                  {years.data?.results.map((y) => (
                    <option key={y.id} value={y.id}>{y.label}</option>
                  ))}
                </Select>
              </Labeled>
            </div>
          </Card>

          <div className="flex justify-end">
            <NextButton disabled={!student} onClick={() => setStep(1)}>Continue to Fee Details</NextButton>
          </div>
        </div>
      )}

      {/* Step 2 — Fee Details */}
      {step === 1 && (
        <div className="space-y-6">
          <Card icon="🧾" title="Fee Details" subtitle="Select fee types and enter amounts">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Fee type" required>
                <Select
                  value={addFeeId}
                  onChange={(e) => {
                    const ft = feeTypes.data?.results.find((f) => String(f.id) === e.target.value);
                    if (ft) addFee(ft);
                    setAddFeeId("");
                  }}
                >
                  <option value="">Select fee type</option>
                  {feeTypes.data?.results.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </Select>
              </Labeled>
              <Labeled label="Term / semester">
                <Select value={term} onChange={(e) => setTerm(e.target.value)}>
                  <option>Semester 1</option>
                  <option>Semester 2</option>
                  <option>Full Year</option>
                </Select>
              </Labeled>
            </div>

            <div className="mt-5 overflow-hidden rounded-xl border border-slate-100">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Fee Component</th>
                    <th className="px-4 py-3 font-semibold">Amount ($)</th>
                    <th className="px-4 py-3 text-right font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {lines.map((l, i) => (
                    <tr key={l.fee_type}>
                      <td className="px-4 py-3 font-medium text-slate-800">📘 {l.name}</td>
                      <td className="px-4 py-3">
                        <input
                          className="w-32 rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-brand focus:outline-none"
                          value={l.amount}
                          onChange={(e) => setLines((ls) => ls.map((x, j) => (j === i ? { ...x, amount: e.target.value } : x)))}
                        />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
                          ⏳ Pending
                        </span>
                        <button onClick={() => setLines((ls) => ls.filter((_, j) => j !== i))} className="ml-2 text-slate-300 hover:text-rose-500">✕</button>
                      </td>
                    </tr>
                  ))}
                  {lines.length === 0 && (
                    <tr><td colSpan={3} className="px-4 py-4 text-slate-400">Add a fee type above to begin.</td></tr>
                  )}
                </tbody>
                <tfoot>
                  <tr className="bg-brand-light/60">
                    <td className="px-4 py-3 font-semibold text-slate-800">Total Due</td>
                    <td className="px-4 py-3 text-lg font-bold text-brand" colSpan={2}>{formatMoney(total.toFixed(2))}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </Card>

          <div className="flex justify-between">
            <BackButton onClick={() => setStep(0)} />
            <NextButton disabled={lines.length === 0} onClick={() => setStep(2)}>Continue to Payment</NextButton>
          </div>
        </div>
      )}

      {/* Step 3 — Payment */}
      {step === 2 && (
        <div className="space-y-6">
          <Card icon="💳" title="Payment Information" subtitle="Select payment method and confirm amount">
            <label className="mb-2 block text-sm font-semibold text-slate-700">Payment method *</label>
            <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {METHODS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setMethod(m.value)}
                  className={`flex flex-col items-center gap-2 rounded-xl border px-3 py-4 text-sm font-medium ${
                    method === m.value ? "border-brand bg-brand-light text-brand-dark" : "border-slate-200 text-slate-600"
                  }`}
                >
                  <span className="text-xl">{m.icon}</span>
                  {m.label}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <Labeled label="Amount to pay" required>
                <TextInput value={amount} onChange={(e) => setAmount(e.target.value)} />
              </Labeled>
              <Labeled label="Payment date" required>
                <TextInput type="date" value={paymentDate} onChange={(e) => setPaymentDate(e.target.value)} />
              </Labeled>
              <Labeled label="Transaction / receipt no.">
                <TextInput placeholder="e.g. TXN-20240512-001" value={txn} onChange={(e) => setTxn(e.target.value)} />
              </Labeled>
              <Labeled label="Collected by">
                <TextInput placeholder="Staff name" value={collectedBy} onChange={(e) => setCollectedBy(e.target.value)} />
              </Labeled>
              <Labeled label="Remarks / notes" full>
                <TextArea placeholder="Optional notes or remarks about this payment…" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
              </Labeled>
            </div>

            <div className="mt-5 flex items-center justify-between rounded-xl bg-brand-light/60 px-5 py-4">
              <div>
                <p className="text-sm font-semibold text-slate-900">Payment Summary</p>
                <p className="text-sm text-slate-600">Total Amount: <span className="font-bold text-brand">{formatMoney(amount || total.toFixed(2))}</span></p>
              </div>
              <div className="text-right">
                <p className="text-xs uppercase tracking-wide text-slate-500">Payment Method</p>
                <p className="text-sm font-medium text-slate-800">{METHODS.find((m) => m.value === method)?.label}</p>
              </div>
            </div>
          </Card>

          <button
            onClick={confirm}
            disabled={submitting}
            className="w-full rounded-xl bg-brand-gradient py-3.5 text-base font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-50"
          >
            {submitting ? "Processing…" : "✓ Confirm Payment"}
          </button>
          <button onClick={() => setStep(1)} className="w-full rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            ↩ Back
          </button>
        </div>
      )}
    </div>
  );
}

function Card({ icon, title, subtitle, children }: { icon: string; title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-light text-lg">{icon}</span>
        <div>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function NextButton({ children, disabled, onClick }: { children: React.ReactNode; disabled?: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} disabled={disabled} className="rounded-xl bg-brand-gradient px-6 py-3 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50">
      {children} →
    </button>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button onClick={onClick} className="rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
      ← Back
    </button>
  );
}
