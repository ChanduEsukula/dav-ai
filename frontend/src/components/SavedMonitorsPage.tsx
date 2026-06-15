import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  createSavedMonitor,
  deleteSavedMonitor,
  getSavedMonitorInsight,
  listSavedMonitorRuns,
  listSavedMonitors,
  runSavedMonitor,
} from "../api/savedMonitors";
import type {
  CreateSavedMonitorPayload,
  MonitorInsight,
  SavedMonitor,
  SavedMonitorModule,
  SavedMonitorRun,
} from "../api/savedMonitors";
import "./SavedMonitorsPage.css";

const moduleLabels: Record<SavedMonitorModule, string> = {
  recallradar: "RecallRadar",
  drugsignal: "DrugSignal",
  foodradar: "FoodRadar",
  cosmeticsignal: "CosmeticSignal",
  regional_health_pulse: "Regional Health Pulse",
};

const moduleQueryHelp: Record<SavedMonitorModule, string> = {
  recallradar: "Example: eye drops, insulin, metformin, or aspirin",
  drugsignal: "Example: metformin, aspirin, ibuprofen, or insulin",
  foodradar: "Example: chicken, protein powder, peanut butter, spinach, or salmonella",
  cosmeticsignal: "Example: sunscreen, hair dye, face cream, fragrance, rash, or irritation",
  regional_health_pulse: "Use format: MN respiratory. Example: MN respiratory or MN hospital pressure",
};

const modulePlaceholders: Record<SavedMonitorModule, string> = {
  recallradar: "eye drops",
  drugsignal: "metformin",
  foodradar: "chicken",
  cosmeticsignal: "sunscreen",
  regional_health_pulse: "MN respiratory",
};

function formatDate(value: string | null): string {
  if (!value) {
    return "Not checked yet";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatNullableNumber(value: number | null): string {
  return value === null ? "N/A" : String(value);
}

function formatNullablePercent(value: number | null): string {
  return value === null ? "N/A" : `${value}%`;
}

function formatInsightLabel(label: string): string {
  return label
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatPayloadChangeLabel(label: string): string {
  return label
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getInsightTone(label: string): "neutral" | "up" | "down" {
  if (label.includes("increase")) {
    return "up";
  }

  if (label.includes("decrease") || label === "source_warning") {
    return "down";
  }

  return "neutral";
}

function formatScore(run: SavedMonitorRun): string {
  if (run.score === null) {
    return "Score N/A";
  }

  return run.score_label ? `${run.score} ${run.score_label}` : String(run.score);
}

function formatSignedChange(value: number): string {
  if (value > 0) {
    return `+${value}`;
  }

  return String(value);
}

function formatChangeLabel(
  label: string,
  latestValue: number | null,
  previousValue: number | null,
): string {
  if (latestValue === null || previousValue === null) {
    return `${label} N/A`;
  }

  const change = latestValue - previousValue;

  if (change === 0) {
    return `${label} unchanged`;
  }

  return `${label} ${formatSignedChange(change)}`;
}

function getChangeTone(
  latestValue: number | null,
  previousValue: number | null,
): "neutral" | "up" | "down" {
  if (latestValue === null || previousValue === null) {
    return "neutral";
  }

  const change = latestValue - previousValue;

  if (change > 0) {
    return "up";
  }

  if (change < 0) {
    return "down";
  }

  return "neutral";
}

function getCreateErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (
      typeof detail === "object" &&
      detail !== null &&
      "message" in detail &&
      typeof detail.message === "string"
    ) {
      return detail.message;
    }
  }

  return "Unable to create saved monitor.";
}

function openAuditDetail(auditId: string) {
  const url = new URL(window.location.href);
  url.searchParams.set("page", "audit");
  url.searchParams.set("audit_id", auditId);
  window.history.pushState(null, "", url.toString());
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export default function SavedMonitorsPage() {
  const [monitors, setMonitors] = useState<SavedMonitor[]>([]);
  const [name, setName] = useState("");
  const [query, setQuery] = useState("");
  const [module, setModule] = useState<SavedMonitorModule>("recallradar");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [runningMonitorId, setRunningMonitorId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [runHistoryByMonitor, setRunHistoryByMonitor] = useState<
    Record<string, SavedMonitorRun[]>
  >({});
  const [insightsByMonitor, setInsightsByMonitor] = useState<
    Record<string, MonitorInsight | null>
  >({});

  async function loadRunHistoryForMonitor(monitorId: string) {
    try {
      const runs = await listSavedMonitorRuns(monitorId);
      setRunHistoryByMonitor((current) => ({
        ...current,
        [monitorId]: runs,
      }));
    } catch {
      setRunHistoryByMonitor((current) => ({
        ...current,
        [monitorId]: [],
      }));
    }
  }

  async function loadInsightForMonitor(monitorId: string) {
    try {
      const insight = await getSavedMonitorInsight(monitorId);
      setInsightsByMonitor((current) => ({
        ...current,
        [monitorId]: insight,
      }));
    } catch {
      setInsightsByMonitor((current) => ({
        ...current,
        [monitorId]: null,
      }));
    }
  }

  async function loadRunHistoryForMonitors(items: SavedMonitor[]) {
    await Promise.all(items.map((monitor) => loadRunHistoryForMonitor(monitor.id)));
  }

  async function loadInsightsForMonitors(items: SavedMonitor[]) {
    await Promise.all(items.map((monitor) => loadInsightForMonitor(monitor.id)));
  }

  async function loadMonitors() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const data = await listSavedMonitors();
      setMonitors(data);
      await Promise.all([
        loadRunHistoryForMonitors(data),
        loadInsightsForMonitors(data),
      ]);
    } catch {
      setErrorMessage("Unable to load saved monitors.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadMonitors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");

    const payload: CreateSavedMonitorPayload = {
      name: name.trim(),
      query: query.trim(),
      module,
    };

    if (payload.name.length < 2 || payload.query.length < 2) {
      setErrorMessage("Name and query must each be at least 2 characters.");
      return;
    }

    setIsSaving(true);

    try {
      const created = await createSavedMonitor(payload);
      setMonitors((current) => [created, ...current]);
      setRunHistoryByMonitor((current) => ({
        ...current,
        [created.id]: [],
      }));
      await loadInsightForMonitor(created.id);
      setName("");
      setQuery("");
      setModule("recallradar");
    } catch (error) {
      setErrorMessage(getCreateErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(monitorId: string) {
    setErrorMessage("");

    const confirmed = window.confirm(
      "Are you sure you want to delete this saved monitor?",
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteSavedMonitor(monitorId);
      setMonitors((current) =>
        current.filter((monitor) => monitor.id !== monitorId),
      );
      setRunHistoryByMonitor((current) => {
        const next = { ...current };
        delete next[monitorId];
        return next;
      });
      setInsightsByMonitor((current) => {
        const next = { ...current };
        delete next[monitorId];
        return next;
      });
    } catch {
      setErrorMessage("Unable to delete saved monitor.");
    }
  }

  async function handleRunCheck(monitorId: string) {
    setErrorMessage("");
    setRunningMonitorId(monitorId);

    try {
      const updated = await runSavedMonitor(monitorId);
      setMonitors((current) =>
        current.map((monitor) =>
          monitor.id === monitorId ? updated : monitor,
        ),
      );
      await Promise.all([
        loadRunHistoryForMonitor(monitorId),
        loadInsightForMonitor(monitorId),
      ]);
    } catch {
      setErrorMessage("Unable to run saved monitor check.");
      await Promise.all([
        loadRunHistoryForMonitor(monitorId),
        loadInsightForMonitor(monitorId),
      ]);
    } finally {
      setRunningMonitorId(null);
    }
  }

  return (
    <section className="saved-monitors-page" aria-labelledby="saved-monitors-title">
      <div className="saved-monitors-hero">
        <p className="eyebrow">Saved Monitors</p>
        <h1 id="saved-monitors-title">Saved Monitors</h1>
        <p>
          Save repeatable RecallRadar, DrugSignal, FoodRadar, CosmeticSignal, or Regional Health
          Pulse searches, run checks manually, compare changes over time, and review deterministic
          monitor insights based on stored public-data history.
        </p>
      </div>

      <form className="saved-monitor-form" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="monitor-name">Monitor name</label>
          <input
            id="monitor-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Eye drops monitor"
          />
        </div>

        <div>
          <label htmlFor="monitor-query">Search query</label>
          <input
            id="monitor-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={modulePlaceholders[module]}
          />
          <small className="saved-monitor-muted-inline">
            {moduleQueryHelp[module]}
          </small>
        </div>

        <div>
          <label htmlFor="monitor-module">Module</label>
          <select
            id="monitor-module"
            value={module}
            onChange={(event) =>
              setModule(event.target.value as SavedMonitorModule)
            }
          >
            <option value="recallradar">RecallRadar</option>
            <option value="drugsignal">DrugSignal</option>
            <option value="foodradar">FoodRadar</option>
            <option value="cosmeticsignal">CosmeticSignal</option>
            <option value="regional_health_pulse">Regional Health Pulse</option>
          </select>
        </div>

        <button type="submit" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Monitor"}
        </button>
      </form>

      {errorMessage ? (
        <div className="saved-monitor-error" role="alert">
          {errorMessage}
        </div>
      ) : null}

      <div className="saved-monitor-panel">
        <div className="saved-monitor-panel-header">
          <h2>Monitor list</h2>
          <button type="button" onClick={loadMonitors}>
            Refresh
          </button>
        </div>

        {isLoading ? (
          <p className="saved-monitor-muted">Loading saved monitors...</p>
        ) : monitors.length === 0 ? (
          <p className="saved-monitor-muted">
            No saved monitors yet. Create one above to start the monitoring workflow.
          </p>
        ) : (
          <div className="saved-monitor-card-list">
            {monitors.map((monitor) => {
              const scoreTone = getChangeTone(
                monitor.latest_score,
                monitor.previous_score,
              );
              const recordTone = getChangeTone(
                monitor.latest_record_count,
                monitor.previous_record_count,
              );
              const insight = insightsByMonitor[monitor.id];
              const insightTone = insight
                ? getInsightTone(insight.label)
                : "neutral";
              const runs = runHistoryByMonitor[monitor.id] ?? [];

              return (
                <article className="saved-monitor-card" key={monitor.id}>
                  <div className="saved-monitor-card-header">
                    <div>
                      <p className="saved-monitor-card-kicker">
                        {moduleLabels[monitor.module]} ·{" "}
                        {monitor.status.replace("_", " ")}
                      </p>
                      <h3>{monitor.name}</h3>
                      <p className="saved-monitor-query">
                        Query: {monitor.query}
                      </p>
                    </div>

                    <div className="saved-monitor-actions">
                      <button
                        type="button"
                        onClick={() => void handleRunCheck(monitor.id)}
                        disabled={runningMonitorId === monitor.id}
                      >
                        {runningMonitorId === monitor.id
                          ? "Running..."
                          : "Run Check"}
                      </button>

                      <button
                        type="button"
                        className="danger-button"
                        onClick={() => void handleDelete(monitor.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="saved-monitor-card-grid">
                    <div className="saved-monitor-metric-card">
                      <span>Latest score</span>
                      <strong>{formatNullableNumber(monitor.latest_score)}</strong>
                      <small>
                        Previous: {formatNullableNumber(monitor.previous_score)}
                      </small>
                    </div>

                    <div className="saved-monitor-metric-card">
                      <span>Records</span>
                      <strong>
                        {formatNullableNumber(monitor.latest_record_count)}
                      </strong>
                      <small>
                        Previous:{" "}
                        {formatNullableNumber(monitor.previous_record_count)}
                      </small>
                    </div>

                    <div className="saved-monitor-metric-card">
                      <span>Last checked</span>
                      <strong>{formatDate(monitor.last_checked_at)}</strong>
                    </div>

                    <div className="saved-monitor-change-stack saved-monitor-card-change">
                      <span className={`change-pill change-pill-${scoreTone}`}>
                        {formatChangeLabel(
                          "Score",
                          monitor.latest_score,
                          monitor.previous_score,
                        )}
                      </span>
                      <span className={`change-pill change-pill-${recordTone}`}>
                        {formatChangeLabel(
                          "Records",
                          monitor.latest_record_count,
                          monitor.previous_record_count,
                        )}
                      </span>
                    </div>
                  </div>

                  <div className="saved-monitor-card-body">
                    <section className="saved-monitor-card-section">
                      <div className="saved-monitor-section-heading">
                        <h4>Monitor Insight</h4>
                        {insight ? (
                          <span
                            className={`change-pill change-pill-${insightTone}`}
                          >
                            {formatInsightLabel(insight.label)}
                          </span>
                        ) : null}
                      </div>

                      {insight ? (
                        <div className="monitor-insight-card monitor-insight-card-wide">
                          <div className="monitor-insight-card-top">
                            <strong>{insight.headline}</strong>
                            <small>{insight.insight_version}</small>
                          </div>

                          <p>{insight.explanation}</p>

                          <div className="monitor-insight-grid">
                            <span>
                              Latest records:{" "}
                              {formatNullableNumber(
                                insight.latest_record_count,
                              )}
                            </span>
                            <span>
                              Previous records:{" "}
                              {formatNullableNumber(
                                insight.previous_record_count,
                              )}
                            </span>
                            <span>
                              Delta:{" "}
                              {insight.record_count_delta === null
                                ? "N/A"
                                : formatSignedChange(
                                    insight.record_count_delta,
                                  )}
                            </span>
                            <span>
                              Change:{" "}
                              {formatNullablePercent(insight.percent_change)}
                            </span>
                            <span>Confidence: {insight.confidence}</span>
                          </div>

                          <small className="monitor-insight-limitation">
                            Based only on stored Dav AI public-data monitor history. Not medical
                            advice or proof of causality.
                          </small>
                        </div>
                      ) : (
                        <span className="saved-monitor-muted-inline">
                          Insight unavailable.
                        </span>
                      )}
                    </section>

                    <section className="saved-monitor-card-section">
                      <div className="saved-monitor-section-heading">
                        <h4>Recent manual runs</h4>
                        {monitor.latest_audit_id ? (
                          <button
                            type="button"
                            className="audit-link-button"
                            onClick={() =>
                              openAuditDetail(
                                monitor.latest_audit_id as string,
                              )
                            }
                          >
                            View Audit
                          </button>
                        ) : null}
                      </div>

                      <div className="saved-monitor-run-history saved-monitor-run-history-cards">
                        {runs.length === 0 ? (
                          <span className="saved-monitor-muted-inline">
                            No manual run history yet.
                          </span>
                        ) : (
                          runs.slice(0, 3).map((run) => (
                            <div
                              className="saved-monitor-run-item"
                              key={run.run_id}
                            >
                              <div>
                                <strong>{formatDate(run.created_at)}</strong>
                                <span>
                                  {moduleLabels[run.module]} · {run.status}
                                </span>
                              </div>

                              <div>
                                <span>
                                  Records{" "}
                                  {formatNullableNumber(run.record_count)}
                                </span>
                                <span>{formatScore(run)}</span>
                              </div>

                              {run.payload_change ? (
                                <div className="saved-monitor-payload-change">
                                  <span>
                                    Payload:{" "}
                                    {formatPayloadChangeLabel(
                                      run.payload_change.label,
                                    )}
                                  </span>
                                  <small>{run.payload_change.reason}</small>
                                </div>
                              ) : null}

                              {run.audit_id ? (
                                <button
                                  type="button"
                                  className="audit-link-button"
                                  onClick={() =>
                                    openAuditDetail(run.audit_id as string)
                                  }
                                >
                                  View run audit
                                </button>
                              ) : null}
                            </div>
                          ))
                        )}
                      </div>
                    </section>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      <div className="saved-monitor-note">
        <strong>Current scope:</strong> Saved Monitors currently support manual run checks for
        RecallRadar, DrugSignal, FoodRadar, CosmeticSignal, and Regional Health Pulse, Supabase
        persistence, latest/previous result comparison, run history, change indicators, duplicate
        prevention, audit linking, deterministic monitor insights, and backend scheduler-lock
        protection. Production Cron, alert notifications, and public scheduling UI are not enabled
        yet.
      </div>
    </section>
  );
}
