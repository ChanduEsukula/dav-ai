import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  createSavedMonitor,
  deleteSavedMonitor,
  listSavedMonitors,
  runSavedMonitor,
} from "../api/savedMonitors";
import type {
  CreateSavedMonitorPayload,
  SavedMonitor,
  SavedMonitorModule,
} from "../api/savedMonitors";
import "./SavedMonitorsPage.css";

const moduleLabels: Record<SavedMonitorModule, string> = {
  recallradar: "RecallRadar",
  drugsignal: "DrugSignal",
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
  window.history.replaceState(null, "", url.toString());
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

  async function loadMonitors() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const data = await listSavedMonitors();
      setMonitors(data);
    } catch {
      setErrorMessage("Unable to load saved monitors.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadMonitors();
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
    } catch {
      setErrorMessage("Unable to run saved monitor check.");
    } finally {
      setRunningMonitorId(null);
    }
  }

  return (
    <section className="saved-monitors-page" aria-labelledby="saved-monitors-title">
      <div className="saved-monitors-hero">
        <p className="eyebrow">Saved Monitors v2.1</p>
        <h1 id="saved-monitors-title">Saved Monitors</h1>
        <p>
          Save repeatable RecallRadar or DrugSignal searches, run checks
          manually, compare latest and previous results, and open the related
          audit event for traceability.
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
            placeholder="eye drops"
          />
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
            No saved monitors yet. Create one above to start the monitoring
            workflow.
          </p>
        ) : (
          <div className="saved-monitor-table-wrap">
            <table className="saved-monitor-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Query</th>
                  <th>Module</th>
                  <th>Status</th>
                  <th>Latest score</th>
                  <th>Previous score</th>
                  <th>Records</th>
                  <th>Previous records</th>
                  <th>Change</th>
                  <th>Last checked</th>
                  <th>Latest audit</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {monitors.map((monitor) => {
                  const scoreTone = getChangeTone(
                    monitor.latest_score,
                    monitor.previous_score,
                  );
                  const recordTone = getChangeTone(
                    monitor.latest_record_count,
                    monitor.previous_record_count,
                  );

                  return (
                    <tr key={monitor.id}>
                      <td>{monitor.name}</td>
                      <td>{monitor.query}</td>
                      <td>{moduleLabels[monitor.module]}</td>
                      <td>{monitor.status.replace("_", " ")}</td>
                      <td>{formatNullableNumber(monitor.latest_score)}</td>
                      <td>{formatNullableNumber(monitor.previous_score)}</td>
                      <td>{formatNullableNumber(monitor.latest_record_count)}</td>
                      <td>{formatNullableNumber(monitor.previous_record_count)}</td>
                      <td>
                        <div className="saved-monitor-change-stack">
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
                      </td>
                      <td>{formatDate(monitor.last_checked_at)}</td>
                      <td>
                        {monitor.latest_audit_id ? (
                          <button
                            type="button"
                            className="audit-link-button"
                            onClick={() =>
                              openAuditDetail(monitor.latest_audit_id as string)
                            }
                          >
                            View Audit
                          </button>
                        ) : (
                          "N/A"
                        )}
                      </td>
                      <td>
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
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="saved-monitor-note">
        <strong>Current scope:</strong> Saved Monitors currently support manual
        run checks, Supabase persistence, latest/previous result comparison,
        change indicators, duplicate prevention, and audit linking. Scheduled
        refresh and alert notifications are future Saved Monitors v2 steps.
      </div>
    </section>
  );
}