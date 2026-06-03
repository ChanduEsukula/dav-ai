import { useMemo, useState } from "react";
import "../styles/floating-safety-report-intake.css";

type ReportType =
  | "drug_product_recall"
  | "drug_safety_signal"
  | "food_product_recall"
  | "medical_device"
  | "general_safety_briefing";

type UserRole =
  | "consumer"
  | "pharmacy"
  | "clinic"
  | "public_health"
  | "student_researcher";

type ReportStyle = "simple" | "technical" | "pharmacy_clinic";

type IntakeStep = "intake" | "review" | "preview";

interface IntakeState {
  reportType: ReportType;
  query: string;
  role: UserRole;
  reportStyle: ReportStyle;
  optionalStateRegion: string;
  email: string;
  consentPublicDataOnly: boolean;
  acknowledgeNotMedicalAdvice: boolean;
}

const initialState: IntakeState = {
  reportType: "drug_product_recall",
  query: "",
  role: "consumer",
  reportStyle: "simple",
  optionalStateRegion: "",
  email: "",
  consentPublicDataOnly: false,
  acknowledgeNotMedicalAdvice: false,
};

const reportTypeLabels: Record<ReportType, string> = {
  drug_product_recall: "Drug / product recall",
  drug_safety_signal: "Drug safety signal",
  food_product_recall: "Food / product recall",
  medical_device: "Medical device",
  general_safety_briefing: "General safety briefing",
};

const roleLabels: Record<UserRole, string> = {
  consumer: "Consumer",
  pharmacy: "Pharmacy",
  clinic: "Clinic",
  public_health: "Public-health analyst",
  student_researcher: "Student / researcher",
};

const reportStyleLabels: Record<ReportStyle, string> = {
  simple: "Simple",
  technical: "Technical",
  pharmacy_clinic: "Pharmacy / clinic",
};

function getModuleLabel(reportType: ReportType): string {
  if (reportType === "drug_safety_signal") {
    return "DrugSignal";
  }

  if (reportType === "general_safety_briefing") {
    return "Briefing Engine";
  }

  return "RecallRadar";
}

function getLocalStorageReports(): IntakeState[] {
  try {
    const raw = window.localStorage.getItem("dav_ai_recent_safety_reports");
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveLocalReport(payload: IntakeState): void {
  try {
    const existing = getLocalStorageReports();
    const next = [
      {
        ...payload,
        email: "",
      },
      ...existing,
    ].slice(0, 8);

    window.localStorage.setItem("dav_ai_recent_safety_reports", JSON.stringify(next));
  } catch {
    // Local storage is best-effort only.
  }
}

export default function FloatingSafetyReportIntake() {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState<IntakeStep>("intake");
  const [form, setForm] = useState<IntakeState>(initialState);
  const [validationMessage, setValidationMessage] = useState("");
  const [emailMessage, setEmailMessage] = useState("");

  const moduleLabel = useMemo(() => getModuleLabel(form.reportType), [form.reportType]);
  const trimmedQuery = form.query.trim();
  const trimmedEmail = form.email.trim();

  const canReview =
    trimmedQuery.length >= 2 &&
    form.consentPublicDataOnly &&
    form.acknowledgeNotMedicalAdvice;

  function updateField<K extends keyof IntakeState>(key: K, value: IntakeState[K]) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
    setValidationMessage("");
    setEmailMessage("");
  }

  function closeDrawer() {
    setIsOpen(false);
    setStep("intake");
    setValidationMessage("");
    setEmailMessage("");
  }

  function handleReview() {
    if (!trimmedQuery) {
      setValidationMessage("Enter a drug, product, food, device, or safety topic to check.");
      return;
    }

    if (trimmedQuery.length < 2) {
      setValidationMessage("Please enter at least two characters for the search topic.");
      return;
    }

    if (!form.consentPublicDataOnly || !form.acknowledgeNotMedicalAdvice) {
      setValidationMessage("Please acknowledge the public-data and medical-safety boundaries.");
      return;
    }

    setStep("review");
  }

  function handleGeneratePreview() {
    saveLocalReport(form);
    setStep("preview");
  }

  function handleEmailAction() {
    if (!trimmedEmail) {
      setEmailMessage("Enter an email address to send this report when email delivery is connected.");
      return;
    }

    if (!trimmedEmail.includes("@")) {
      setEmailMessage("Enter a valid email address.");
      return;
    }

    setEmailMessage("Email delivery is the next backend step. Your report intent is ready to connect.");
  }

  return (
    <>
      {!isOpen && (
        <button
          className="floating-safety-report-button"
          type="button"
          onClick={() => setIsOpen(true)}
          aria-label="Open safety report intake"
        >
          <span className="floating-safety-report-button__spark">✨</span>
          <span>Get Your Safety Report</span>
        </button>
      )}

      {isOpen && (
        <div className="floating-safety-report-overlay" role="presentation">
          <section
            className="floating-safety-report-drawer"
            aria-label="Generate a public safety report"
          >
            <header className="floating-safety-report-header">
              <div>
                <p className="floating-safety-report-kicker">Public-data safety intelligence</p>
                <h2>Generate a Safety Report</h2>
                <p>
                  Search FDA/openFDA public data for recalls and safety-signal patterns.
                  This is not medical advice.
                </p>
              </div>
              <button
                className="floating-safety-report-close"
                type="button"
                onClick={closeDrawer}
                aria-label="Close safety report intake"
              >
                ×
              </button>
            </header>

            <div className="floating-safety-report-steps" aria-label="Report intake progress">
              <span className={step === "intake" ? "is-active" : ""}>1. Details</span>
              <span className={step === "review" ? "is-active" : ""}>2. Review</span>
              <span className={step === "preview" ? "is-active" : ""}>3. Preview</span>
            </div>

            {step === "intake" && (
              <div className="floating-safety-report-body">
                <div className="floating-safety-report-warning">
                  Do not enter symptoms, diagnoses, prescriptions, date of birth, full address,
                  insurance details, patient records, or private medical information.
                </div>

                <label>
                  What do you want to check?
                  <select
                    value={form.reportType}
                    onChange={(event) =>
                      updateField("reportType", event.target.value as ReportType)
                    }
                  >
                    {Object.entries(reportTypeLabels).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Search topic
                  <input
                    value={form.query}
                    onChange={(event) => updateField("query", event.target.value)}
                    placeholder="Example: eye drops, metformin, protein powder"
                  />
                </label>

                <div className="floating-safety-report-grid">
                  <label>
                    Who is this for?
                    <select
                      value={form.role}
                      onChange={(event) => updateField("role", event.target.value as UserRole)}
                    >
                      {Object.entries(roleLabels).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Report style
                    <select
                      value={form.reportStyle}
                      onChange={(event) =>
                        updateField("reportStyle", event.target.value as ReportStyle)
                      }
                    >
                      {Object.entries(reportStyleLabels).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <label>
                  Optional state / region
                  <input
                    value={form.optionalStateRegion}
                    onChange={(event) => updateField("optionalStateRegion", event.target.value)}
                    placeholder="Optional, example: MN"
                  />
                </label>

                <label className="floating-safety-report-checkbox">
                  <input
                    type="checkbox"
                    checked={form.consentPublicDataOnly}
                    onChange={(event) =>
                      updateField("consentPublicDataOnly", event.target.checked)
                    }
                  />
                  <span>I understand this uses public FDA/openFDA-style data only.</span>
                </label>

                <label className="floating-safety-report-checkbox">
                  <input
                    type="checkbox"
                    checked={form.acknowledgeNotMedicalAdvice}
                    onChange={(event) =>
                      updateField("acknowledgeNotMedicalAdvice", event.target.checked)
                    }
                  />
                  <span>
                    I understand this is not medical advice, diagnosis, treatment guidance,
                    clinical decision support, or a medical device.
                  </span>
                </label>

                {validationMessage && (
                  <p className="floating-safety-report-error" role="alert">
                    {validationMessage}
                  </p>
                )}

                <button
                  className="floating-safety-report-primary"
                  type="button"
                  onClick={handleReview}
                  disabled={!canReview}
                >
                  Review report request
                </button>
              </div>
            )}

            {step === "review" && (
              <div className="floating-safety-report-body">
                <div className="floating-safety-report-review-card">
                  <h3>Review before generation</h3>
                  <dl>
                    <div>
                      <dt>Module</dt>
                      <dd>{moduleLabel}</dd>
                    </div>
                    <div>
                      <dt>Search</dt>
                      <dd>{trimmedQuery}</dd>
                    </div>
                    <div>
                      <dt>Report type</dt>
                      <dd>{reportTypeLabels[form.reportType]}</dd>
                    </div>
                    <div>
                      <dt>Role</dt>
                      <dd>{roleLabels[form.role]}</dd>
                    </div>
                    <div>
                      <dt>Report style</dt>
                      <dd>{reportStyleLabels[form.reportStyle]}</dd>
                    </div>
                    <div>
                      <dt>Region</dt>
                      <dd>{form.optionalStateRegion.trim() || "Not provided"}</dd>
                    </div>
                  </dl>
                </div>

                <div className="floating-safety-report-boundary">
                  This report will use public safety data and source timestamps. It will not
                  diagnose, recommend medication changes, or make personal medical decisions.
                </div>

                <div className="floating-safety-report-actions">
                  <button
                    className="floating-safety-report-secondary"
                    type="button"
                    onClick={() => setStep("intake")}
                  >
                    Edit
                  </button>
                  <button
                    className="floating-safety-report-primary"
                    type="button"
                    onClick={handleGeneratePreview}
                  >
                    Generate preview
                  </button>
                </div>
              </div>
            )}

            {step === "preview" && (
              <div className="floating-safety-report-body">
                <div className="floating-safety-report-preview">
                  <p className="floating-safety-report-kicker">Preview prepared</p>
                  <h3>{trimmedQuery} safety report</h3>
                  <p>
                    DAV AI is ready to generate a {reportStyleLabels[form.reportStyle].toLowerCase()}{" "}
                    {roleLabels[form.role].toLowerCase()} report using the {moduleLabel} workflow.
                  </p>

                  <div className="floating-safety-report-preview-grid">
                    <span>Source scope</span>
                    <strong>Public FDA/openFDA data</strong>
                    <span>Medical boundary</span>
                    <strong>Not medical advice</strong>
                    <span>Storage</span>
                    <strong>Saved on this device only</strong>
                  </div>
                </div>

                <label>
                  Email this report later
                  <input
                    value={form.email}
                    onChange={(event) => updateField("email", event.target.value)}
                    placeholder="you@example.com"
                  />
                </label>

                {emailMessage && (
                  <p className="floating-safety-report-note" role="status">
                    {emailMessage}
                  </p>
                )}

                <div className="floating-safety-report-actions floating-safety-report-actions--stacked">
                  <button
                    className="floating-safety-report-primary"
                    type="button"
                    onClick={handleEmailAction}
                  >
                    Email me this report
                  </button>
                  <button className="floating-safety-report-secondary" type="button" disabled>
                    Save to My Safety Profile — coming next
                  </button>
                  <button className="floating-safety-report-secondary" type="button" disabled>
                    Monitor this weekly — coming next
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </>
  );
}
