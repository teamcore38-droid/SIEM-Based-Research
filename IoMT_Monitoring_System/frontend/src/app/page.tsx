"use client";

import { useEffect, useMemo, useState } from "react";
import jsPDF from "jspdf";
import Image from "next/image";
import {
  Activity,
  AlertTriangle,
  Archive,
  BadgeCheck,
  BarChart3,
  Bell,
  ClipboardList,
  Database,
  GitBranch,
  FileDown,
  Gauge,
  Lock,
  Network,
  Play,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Stethoscope,
  StopCircle,
  Table2
} from "lucide-react";
import { AlertIncidentRecord, AnalyzeResult, PredictionRecord, ReportPayload, SensorProfile, SimulationConfig, SimulatorStatus, Summary, TelemetryItem, TickResult, api } from "@/lib/api";

const SYSTEM_NAME = "MedGuard X";
const SYSTEM_TAGLINE = "Security Operations";
const SYSTEM_DESCRIPTION = "Real-time security monitoring for connected medical devices.";
const LOGIN_LOGO_SRC = "/medguard-x-logo.jpeg";
const SIDEBAR_LOGO_SRC = "/medguard-x-logo-icon.png";

const views = [
  { id: "dashboard", label: "Dashboard", icon: BarChart3 },
  { id: "architecture", label: "Architecture", icon: GitBranch },
  { id: "telemetry", label: "Telemetry", icon: Stethoscope },
  { id: "logs", label: "MongoDB Logs", icon: Database },
  { id: "priority", label: "AI Priority", icon: Gauge },
  { id: "alert-grouping", label: "Alert Grouping", icon: Table2 },
  { id: "attack", label: "Attack Prediction", icon: ShieldAlert },
  { id: "correlation", label: "Correlation", icon: Network },
  { id: "response", label: "Response", icon: Bell },
  { id: "quarantine", label: "Quarantine", icon: Lock },
  { id: "reports", label: "Reports", icon: FileDown }
] as const;

type ViewId = (typeof views)[number]["id"];

const severityOrder = ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const;
const incidentCategoryOrder = ["critical", "high", "attack", "normal"] as const;

function value(item: TelemetryItem, key: string, fallback = "-") {
  const result = item[key];
  if (result === null || result === undefined || result === "") return fallback;
  return String(result);
}

function isTimestampKey(key: string) {
  return key === "timestamp" || key.endsWith("_at") || key.endsWith("_timestamp");
}

function formatLocalDateTime(raw: unknown, fallback = "-") {
  if (raw === null || raw === undefined || raw === "") return fallback;

  let date: Date;
  if (typeof raw === "number") {
    date = new Date(raw);
  } else {
    const text = String(raw);
    const numeric = Number(text);
    date = /^\d{12,}$/.test(text) && Number.isFinite(numeric) ? new Date(numeric) : new Date(text);
  }

  if (Number.isNaN(date.getTime())) return String(raw);

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZoneName: "short"
  }).format(date);
}

function displayValue(item: TelemetryItem, key: string, fallback = "-") {
  if (key === "network_status") return networkStatus(item).label;
  const result = item[key];
  if (isTimestampKey(key)) return formatLocalDateTime(result, fallback);
  if (result === null || result === undefined || result === "") return fallback;
  return String(result);
}

function booleanValue(value: unknown) {
  return String(value).toLowerCase() === "true" || value === true || value === 1 || value === "1";
}

function networkStatus(item: TelemetryItem) {
  const state = value(item, "device_state", "").toLowerCase();
  if (booleanValue(item.network_blocked) || state === "quarantined") {
    return { label: "Blocked", className: "critical" };
  }
  if (booleanValue(item.network_isolated) || state === "temporarily isolated") {
    return { label: "Restricted", className: "medium" };
  }
  return { label: "Normal", className: "low" };
}

function operatorNoticeForState(item?: TelemetryItem) {
  const state = value(item ?? {}, "state", "").toLowerCase();
  const lastAction = value(item ?? {}, "last_action", "").toLowerCase();
  if (state === "quarantined" || ["quarantine", "shutdown"].includes(lastAction)) {
    return "This sensor is quarantined. Please turn it off.";
  }
  if (state === "temporarily isolated") {
    return "This sensor is temporarily isolated in the backend. Please limit physical use until reviewed.";
  }
  return "";
}

function severityClass(priority = "LOW") {
  return `badge ${priority.toLowerCase()}`;
}

function actionLabel(action?: string) {
  return String(action ?? "monitor").replaceAll("_", " ");
}

function detailValue(valueText: unknown, fallback = "-") {
  if (valueText === null || valueText === undefined || valueText === "") return fallback;
  return String(valueText);
}

function normalizeIncidentCategory(value: unknown) {
  const category = String(value ?? "").toLowerCase();
  return incidentCategoryOrder.includes(category as (typeof incidentCategoryOrder)[number]) ? category : "normal";
}

function incidentCategoryLabel(category: string) {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

function incidentCategoryTone(category: string) {
  if (category === "critical") return "critical";
  if (category === "high") return "high";
  if (category === "attack") return "medium";
  return "low";
}

function responseOrigin(item: TelemetryItem) {
  const requestedBy = String(item.requested_by ?? "").toLowerCase();
  const metadata = item.metadata as Record<string, unknown> | undefined;
  const manualFlag = metadata?.manual_dashboard_action;
  const stage = String(metadata?.stage ?? "").toLowerCase();
  const hasAutomationSignals =
    requestedBy === "system" ||
    requestedBy === "backend" ||
    requestedBy === "pipeline" ||
    requestedBy === "aice" ||
    stage.length > 0 ||
    metadata?.simulated === true ||
    metadata?.analysis !== undefined ||
    metadata?.ars_response !== undefined;
  if (manualFlag === true) {
    return "Manual";
  }
  if (hasAutomationSignals) {
    return "Automatic";
  }
  if (requestedBy === "admin-demo" || requestedBy === "dashboard") {
    return "Manual";
  }
  return "Automatic";
}

function temporaryStatusLabel(action: unknown, predictedAttack = false) {
  const normalized = String(action ?? "").toLowerCase();
  if (["quarantine", "shutdown"].includes(normalized)) return "Temporarily isolated";
  if (["temporary_isolate", "isolate"].includes(normalized)) return "Temporarily isolated";
  if (["restore", "rollback", "false_positive"].includes(normalized)) return "Monitor";
  if (normalized === "monitor" || normalized === "log_and_monitor") return "Monitor";
  return predictedAttack ? "Temporarily isolated" : "Monitor";
}

function validationStatusLabel(item: Pick<PredictionRecord, "confirmed_real_attack" | "correlation_verdict" | "decision_action" | "predicted_attack">) {
  if (item.confirmed_real_attack) return "Confirmed attack";
  const verdict = String(item.correlation_verdict ?? "").toLowerCase();
  const action = String(item.decision_action ?? "").toLowerCase();
  if (["restore", "rollback", "false_positive"].includes(action)) return "Validated false positive";
  if (verdict === "confirmed_attack") return "Confirmed attack";
  if (verdict === "suspicious") return "Pending review";
  if (Boolean(item.predicted_attack)) return "Pending validation";
  return "Normal traffic";
}

function correlationActionLabel(action: unknown, deviceState?: unknown) {
  const normalizedAction = String(action ?? "").toLowerCase();
  const normalizedState = String(deviceState ?? "").toLowerCase();
  if (["quarantine", "shutdown"].includes(normalizedAction) || normalizedState === "quarantined") return "Quarantine";
  if (["temporary_isolate", "isolate"].includes(normalizedAction) || normalizedState === "temporarily isolated") return "Temporary isolate";
  return "Monitor";
}

function tickKey(result: TickResult) {
  return [
    value(result.event, "timestamp", ""),
    value(result.event, "device_id", ""),
    result.analysis?.decision.action ?? result.message ?? ""
  ].join("|");
}

export default function Home() {
  const [authenticated, setAuthenticated] = useState(false);
  const [active, setActive] = useState<ViewId>("dashboard");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [health, setHealth] = useState<{ mongo: boolean; mode: string } | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryItem[]>([]);
  const [logs, setLogs] = useState<TelemetryItem[]>([]);
  const [incidents, setIncidents] = useState<AlertIncidentRecord[]>([]);
  const [responses, setResponses] = useState<TelemetryItem[]>([]);
  const [quarantined, setQuarantined] = useState<TelemetryItem[]>([]);
  const [deviceStates, setDeviceStates] = useState<TelemetryItem[]>([]);
  const [predictions, setPredictions] = useState<PredictionRecord[]>([]);
  const [sensors, setSensors] = useState<SensorProfile[]>([]);
  const [feed, setFeed] = useState<TickResult[]>([]);
  const [selectedDevice, setSelectedDevice] = useState("890cc34f");
  const [simulatorStatus, setSimulatorStatus] = useState<SimulatorStatus | null>(null);
  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig>({
    data_mode: "simulation",
    simulation_mode: "normal",
    anomaly_device_id: "",
    anomaly_type: "sensor_spoofing"
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [groupingRefreshing, setGroupingRefreshing] = useState(false);
  const [groupingMessage, setGroupingMessage] = useState("");

  const latest = feed[0];
  const latestAnalysis: AnalyzeResult | undefined = latest?.analysis ?? undefined;
  const simulatorRunning = simulatorStatus?.running ?? false;
  const quarantinedWithOrigin = quarantined.map((item) => ({
    ...item,
    change_origin: responseOrigin(item),
  }));

  const loadAll = async () => {
    setError("");
    try {
      const [healthData, summaryData, telemetryData, logData, incidentData, responseData, quarantineData, stateData, predictionData, sensorData, simulatorData, simulatorLatest, simulationConfigData] =
        await Promise.all([
          api.health(),
          api.summary(),
          api.telemetry(40),
          api.logs(70),
          api.incidents(50),
          api.responses(50),
          api.quarantine(50),
          api.deviceStates(100),
          api.predictions(10),
          api.sensors(),
          api.simulatorStatus(),
          api.simulatorLatest(),
          api.simulationConfig()
        ]);
      setHealth(healthData);
      setSummary(summaryData);
      setTelemetry(telemetryData.items);
      setLogs(logData.items);
      setIncidents(incidentData.items);
      setResponses(responseData.items);
      setQuarantined(quarantineData.items);
      setDeviceStates(stateData.items);
      setPredictions(predictionData.items);
      setSensors(sensorData.items);
      setSimulatorStatus(simulatorData);
      setSimulationConfig(simulationConfigData);
      if (simulatorLatest.item?.analysis) {
        setFeed((items) => {
          if (items[0] && tickKey(items[0]) === tickKey(simulatorLatest.item as TickResult)) return items;
          return [simulatorLatest.item as TickResult, ...items].slice(0, 10);
        });
      }
      const availableDevices = sensorData.items.map((item) => String(item.device_id)).filter(Boolean);
      if (availableDevices.length) {
        setSelectedDevice((current) => (availableDevices.includes(current) ? current : availableDevices[0]));
      } else if (telemetryData.items[0]?.device_id) {
        setSelectedDevice(String(telemetryData.items[0].device_id));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach backend API");
    }
  };

  const refreshAlertGrouping = async () => {
    setGroupingRefreshing(true);
    setError("");
    setGroupingMessage("");
    try {
      const result = await api.refreshAlertGrouping();
      setGroupingMessage(result.message);
      await loadAll();
      setActive("alert-grouping");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to refresh alert grouping");
    } finally {
      setGroupingRefreshing(false);
    }
  };

  const runTick = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.tick();
      if (result.analysis) {
        setFeed((items) => [result, ...items].slice(0, 10));
      }
      if (result.event.device_id) setSelectedDevice(String(result.event.device_id));
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation tick failed");
    } finally {
      setLoading(false);
    }
  };

  const updateSimulationConfig = async (changes: Partial<SimulationConfig>) => {
    setLoading(true);
    setError("");
    try {
      const result = await api.updateSimulationConfig({ ...simulationConfig, ...changes });
      setSimulationConfig(result.config);
      setSimulatorStatus(result.simulator);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update simulation controls");
    } finally {
      setLoading(false);
    }
  };

  const toggleSimulator = async () => {
    setLoading(true);
    setError("");
    try {
      const status = simulatorRunning ? await api.stopSimulator() : await api.startSimulator(4.5);
      setSimulatorStatus(status);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to control simulator");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAll();
  }, []);

  useEffect(() => {
    if (!simulatorRunning) return;
    const id = window.setInterval(() => {
      void loadAll();
    }, 4500);
    return () => window.clearInterval(id);
  }, [simulatorRunning]);

  const flow = useMemo(
    () => [
      { label: "Telemetry", value: summary?.totalLogs ?? telemetry.length, tone: "green" },
      { label: "MongoDB Logs", value: summary?.mode ?? health?.mode ?? "mock", tone: "ink" },
      { label: "Attack AI", value: latestAnalysis?.attack_prediction.predicted_label ?? "waiting", tone: "red" },
      { label: "AI Priority", value: latestAnalysis?.alert.priority ?? "waiting", tone: "amber" },
      { label: "Correlation", value: latestAnalysis?.correlation.final_action ?? "monitor", tone: "blue" },
      { label: "AR Response", value: latestAnalysis?.ars_response.action_label ?? "waiting", tone: "red" }
    ],
    [summary, telemetry.length, health, latestAnalysis]
  );

  const issueAction = async (action: string) => {
    setLoading(true);
    setError("");
    try {
      await api.action(selectedDevice, action, `Manual ${actionLabel(action)} from demo dashboard`);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setLoading(false);
    }
  };

  const exportJson = async () => {
    const report = await api.report();
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "medguard-x-report.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = () => {
    const rows = telemetry.slice(0, 40);
    const headers = [
      "timestamp",
      "device_id",
      "device_type",
      "ward",
      "protocol",
      "src_ip",
      "dst_port",
      "attack_type",
      "is_attack",
      "device_state",
      "network_status"
    ];
    const encodeCell = (raw: string) => `"${raw.replaceAll("\"", "\"\"")}"`;
    const csv = [
      headers.join(","),
      ...rows.map((row) => headers.map((key) => encodeCell(displayValue(row, key, ""))).join(","))
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "medguard-x-telemetry-evidence.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportPdf = async () => {
    const report = await api.report();
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 16;
    const contentWidth = pageWidth - margin * 2;
    let y = 20;

    const ensureSpace = (height: number) => {
      if (y + height <= pageHeight - 18) return;
      doc.addPage();
      y = 20;
    };

    const addWrapped = (text: string, x: number, maxWidth: number, lineHeight = 6) => {
      const lines = doc.splitTextToSize(text, maxWidth);
      ensureSpace(lines.length * lineHeight + 4);
      doc.text(lines, x, y);
      y += lines.length * lineHeight + 2;
    };

    const addSectionTitle = (title: string) => {
      ensureSpace(16);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(14);
      doc.setTextColor(21, 25, 23);
      doc.text(title, margin, y);
      y += 4;
      doc.setDrawColor(24, 115, 93);
      doc.line(margin, y, pageWidth - margin, y);
      y += 8;
    };

    const addLabelValue = (label: string, valueText: string) => {
      ensureSpace(8);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.text(`${label}:`, margin, y);
      doc.setFont("helvetica", "normal");
      doc.text(valueText, margin + 35, y);
      y += 7;
    };

    const addBulletList = (items: string[]) => {
      items.forEach((item) => {
        ensureSpace(8);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        addWrapped(`- ${item}`, margin + 3, contentWidth - 3, 5);
      });
    };

    const addMetricGrid = (items: Array<{ label: string; value: string }>) => {
      const gap = 6;
      const boxWidth = (contentWidth - gap) / 2;
      const boxHeight = 22;
      for (let index = 0; index < items.length; index += 2) {
        ensureSpace(boxHeight + 6);
        const row = items.slice(index, index + 2);
        row.forEach((item, columnIndex) => {
          const x = margin + columnIndex * (boxWidth + gap);
          doc.setFillColor(244, 247, 242);
          doc.setDrawColor(215, 223, 216);
          doc.roundedRect(x, y, boxWidth, boxHeight, 3, 3, "FD");
          doc.setFont("helvetica", "bold");
          doc.setFontSize(9);
          doc.setTextColor(102, 113, 107);
          doc.text(item.label.toUpperCase(), x + 4, y + 7);
          doc.setFontSize(13);
          doc.setTextColor(21, 25, 23);
          doc.text(item.value, x + 4, y + 16);
        });
        y += boxHeight + 6;
      }
    };

    const latestAnalysis = report.latest_analysis;
    const restrictions = report.active_restrictions?.items ?? [];
    const recentPredictions = report.recent_predictions ?? [];

    doc.setFillColor(21, 25, 23);
    doc.rect(0, 0, pageWidth, 42, "F");
    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text("MedGuard X Evidence Report", margin, 18);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text("Research monitoring, AI validation, and operational response summary", margin, 27);
    doc.text(`Generated ${formatLocalDateTime(report.generated_at)}`, margin, 34);
    y = 54;

    addSectionTitle("Executive Summary");
    addMetricGrid([
      { label: "Mode", value: String(report.mode ?? "unknown").toUpperCase() },
      { label: "Active devices", value: String(report.active_devices ?? 0) },
      { label: "Total telemetry logs", value: String(report.total_logs ?? 0) },
      { label: "Attack-like logs", value: String(report.attack_logs ?? 0) },
      { label: "Response actions", value: String(report.total_responses ?? 0) },
      { label: "Alert reduction", value: String(report.alert_reduction ?? "-") },
    ]);

    addSectionTitle("Severity Distribution");
    addMetricGrid([
      { label: "Critical", value: String(report.severity_counts?.CRITICAL ?? 0) },
      { label: "High", value: String(report.severity_counts?.HIGH ?? 0) },
      { label: "Medium", value: String(report.severity_counts?.MEDIUM ?? 0) },
      { label: "Low", value: String(report.severity_counts?.LOW ?? 0) },
    ]);

    addSectionTitle("Operational State");
    addLabelValue("Simulator", report.simulator?.running ? `Running (${report.simulator.ticks} ticks)` : "Stopped");
    addLabelValue("Data mode", String(report.simulation_config?.data_mode ?? "simulation"));
    addLabelValue("Simulation mode", String(report.simulation_config?.simulation_mode ?? "normal"));
    addLabelValue("Active restrictions", String(report.active_restrictions?.count ?? 0));

    if (restrictions.length) {
      ensureSpace(10);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.text("Restricted / quarantined devices", margin, y);
      y += 7;
      restrictions.slice(0, 5).forEach((item) => {
        const line = `${value(item, "device_id")} | ${value(item, "state")} | ${value(item, "reason")}`;
        addWrapped(line, margin + 2, contentWidth - 2, 5);
      });
    }

    if (latestAnalysis) {
      addSectionTitle("Latest Incident Assessment");
      addLabelValue("Priority", String(latestAnalysis.alert.priority));
      addLabelValue("Attack prediction", String(latestAnalysis.attack_prediction.predicted_label));
      addLabelValue("Correlation verdict", String(latestAnalysis.live_correlation.recommended_verdict));
      addLabelValue("Final action", actionLabel(latestAnalysis.decision.action));
      addWrapped(latestAnalysis.decision.reason, margin, contentWidth, 5);
    }

    if (recentPredictions.length) {
      addSectionTitle("Recent Prediction Snapshot");
      recentPredictions.slice(0, 5).forEach((item) => {
        const line = [
          value(item, "device_id"),
          value(item, "priority"),
          value(item, "attack_label"),
          value(item, "correlation_verdict"),
          actionLabel(value(item, "decision_action", "monitor")),
        ].join(" | ");
        addWrapped(line, margin, contentWidth, 5);
      });
    }

    addSectionTitle("PHI-Redacted Evidence");
    addWrapped(String(report.redacted_evidence ?? "No redacted evidence available."), margin, contentWidth, 5);

    addSectionTitle("Method Notes");
    addBulletList(report.notes ?? []);

    doc.save("medguard-x-evidence-report.pdf");
  };

  if (!authenticated) {
    return (
      <main className="login-shell">
        <section className="login-stage">
          <article className="login-hero">
            <div className="brand-row login-brand">
              <Image
                  src={LOGIN_LOGO_SRC}
                alt={`${SYSTEM_NAME} logo`}
                width={108}
                height={108}
                className="brand-logo brand-logo-lg"
                priority
              />
              <div>
                <span>{SYSTEM_NAME}</span>
                <strong>{SYSTEM_TAGLINE}</strong>
              </div>
            </div>
            <div className="login-copy">
              <p className="login-kicker">{SYSTEM_NAME} demo environment</p>
              <h1>{SYSTEM_NAME}</h1>
              <p>
                {SYSTEM_DESCRIPTION} Simulated telemetry, AI threat detection, alert prioritization,
                live correlation, automated response, and evidence reporting in one supervised
                control surface.
              </p>
            </div>
            <div className="login-highlights">
              <div className="login-highlight-card">
                <Stethoscope size={18} />
                <div>
                  <strong>4 medical sensors</strong>
                  <span>Heart rate, ECG, temperature, and fall detection telemetry</span>
                </div>
              </div>
              <div className="login-highlight-card">
                <ShieldAlert size={18} />
                <div>
                  <strong>AI threat pipeline</strong>
                  <span>Random Forest, Isolation Forest, prioritization, and live validation</span>
                </div>
              </div>
              <div className="login-highlight-card">
                <Database size={18} />
                <div>
                  <strong>Operational traceability</strong>
                  <span>MongoDB logging, device states, prediction history, and responses</span>
                </div>
              </div>
            </div>
          </article>

          <aside className="login-panel">
            <div className="login-panel-top">
              <span className="login-chip">Research Control Console</span>
              <strong>Admin demo access</strong>
              <p>
                Enter the supervised dashboard to inspect telemetry, validate incidents, review
                model decisions, and manage isolation or quarantine actions.
              </p>
            </div>

            <div className="login-metrics">
              <div className="login-metric">
                <Activity size={18} />
                <div>
                  <strong>Live pipeline</strong>
                  <span>Telemetry to response in a single workflow</span>
                </div>
              </div>
              <div className="login-metric">
                <Network size={18} />
                <div>
                  <strong>Correlation aware</strong>
                  <span>Context validation before high-impact actions</span>
                </div>
              </div>
              <div className="login-metric">
                <ClipboardList size={18} />
                <div>
                  <strong>Evidence ready</strong>
                  <span>Prediction history, reports, and operator notices</span>
                </div>
              </div>
            </div>

            <button className="primary-action login-cta" onClick={() => setAuthenticated(true)}>
              <BadgeCheck size={18} />
              Launch Admin Console
            </button>

            <div className="login-footer-note">
              <span>Demo mode</span>
              <p>Backend-controlled simulation with support for future real-sensor integration.</p>
            </div>
          </aside>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <button
          type="button"
          className="product-mark product-mark-button"
          onClick={() => setActive("dashboard")}
          aria-label="Go to dashboard"
        >
          <Image
            src={SIDEBAR_LOGO_SRC}
            alt={`${SYSTEM_NAME} logo`}
            width={56}
            height={56}
            className="brand-logo brand-logo-sm"
          />
          <div>
            <strong>{SYSTEM_NAME}</strong>
            <span>Admin demo</span>
          </div>
        </button>
        <nav>
          {views.map((view) => {
            const Icon = view.icon;
            return (
              <button key={view.id} className={active === view.id ? "nav-item active" : "nav-item"} onClick={() => setActive(view.id)}>
                <Icon size={17} />
                <span>{view.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Architecture demo</span>
            <h1>{views.find((view) => view.id === active)?.label}</h1>
          </div>
          <div className="top-actions">
            <span className={health?.mongo ? "status-dot online" : "status-dot mock"}>{health?.mongo ? "MongoDB Atlas" : "Mock mode"}</span>
            <span className={simulatorRunning ? "status-dot online" : "status-dot mock"}>
              Simulator {simulatorRunning ? `running (${simulatorStatus?.ticks ?? 0})` : "stopped"}
            </span>
            <select
              className="top-select"
              value={simulationConfig.data_mode}
              onChange={(event) => void updateSimulationConfig({ data_mode: event.target.value as SimulationConfig["data_mode"] })}
              disabled={loading}
              title="Choose real data or controlled simulation mode"
            >
              <option value="real">Real Data</option>
              <option value="simulation">Simulation</option>
            </select>
            <select
              className="top-select"
              value={simulationConfig.simulation_mode}
              onChange={(event) => void updateSimulationConfig({ simulation_mode: event.target.value as SimulationConfig["simulation_mode"] })}
              disabled={loading || simulationConfig.data_mode === "real"}
              title="Choose normal-only or targeted anomaly simulation"
            >
              <option value="normal">Normal Mode</option>
              <option value="anomaly">Anomaly Mode</option>
            </select>
            <select
              className="top-select sensor-select"
              value={simulationConfig.anomaly_device_id}
              onChange={(event) => void updateSimulationConfig({ anomaly_device_id: event.target.value })}
              disabled={loading || simulationConfig.data_mode === "real" || simulationConfig.simulation_mode !== "anomaly"}
              title="Select the sensor that should emit anomaly data"
            >
              <option value="">Select anomaly sensor</option>
              {sensors.map((sensor) => (
                <option value={sensor.device_id} key={sensor.device_id}>
                  {sensor.device_id}
                </option>
              ))}
            </select>
            <button
              className={simulatorRunning ? "icon-button active" : "icon-button"}
              onClick={toggleSimulator}
              disabled={loading || (simulationConfig.data_mode === "real" && !simulatorRunning)}
              title="Start or stop backend simulator"
            >
              {simulatorRunning ? <StopCircle size={17} /> : <Activity size={17} />}
            </button>
            <button className="icon-button" onClick={runTick} disabled={loading || simulationConfig.data_mode === "real"} title="Generate one simulated event">
              <Play size={17} />
            </button>
            <button className="icon-button" onClick={loadAll} title="Refresh dashboard">
              <RefreshCw size={17} />
            </button>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {active === "dashboard" && (
          <section className="view-stack">
            <div className="metric-grid">
              <Metric label="Sensor logs" value={summary?.totalLogs ?? telemetry.length} detail={summary?.mode ?? "loading"} />
              <Metric label="Attack logs" value={summary?.attackLogs ?? 0} detail="AI input candidates" tone="red" />
              <Metric label="Incident groups" value={summary?.incidentGroups ?? incidents.length} detail="prediction-derived grouping" tone="green" />
              <Metric label="Model accuracy" value={summary?.modelAccuracy ?? "-"} detail="saved Random Forest" tone="amber" />
            </div>
            <div className="flow-row">
              {flow.map((step) => (
                <div className={`flow-step ${step.tone}`} key={step.label}>
                  <span>{step.label}</span>
                  <strong>{String(step.value)}</strong>
                </div>
              ))}
            </div>
            <LiveFlowTimeline
              latest={latest}
              simulatorStatus={simulatorStatus}
              mongoMode={health?.mongo ? "MongoDB Atlas" : "Mock mode"}
            />
            <section className="split-layout">
              <SeverityPanel summary={summary} />
              <LatestPanel latest={latest} />
            </section>
          </section>
        )}

        {active === "architecture" && (
          <ArchitectureDemoView
            latest={latest}
            simulatorStatus={simulatorStatus}
            telemetry={telemetry}
            logs={logs}
            responses={responses}
            deviceStates={deviceStates}
            summary={summary}
            mongoMode={health?.mongo ? "MongoDB Atlas" : "Mock mode"}
          />
        )}
        {active === "telemetry" && <DataTable title="Live telemetry" items={telemetry} columns={["timestamp", "device_id", "device_type", "ward", "heart_rate_bpm_pulse", "temperature_celsius", "attack_type", "device_state", "network_status"]} />}
        {active === "logs" && <DataTable title="MongoDB sensor_logs collection" items={logs} columns={["timestamp", "device_id", "device_type", "ward", "protocol", "src_ip", "dst_port", "attack_type"]} />}
        {active === "priority" && <PriorityView latest={latest} summary={summary} predictions={predictions} />}
        {active === "alert-grouping" && (
          <AlertGroupingView
            summary={summary}
            incidents={incidents}
            onRefresh={refreshAlertGrouping}
            refreshing={groupingRefreshing}
            message={groupingMessage}
          />
        )}
        {active === "attack" && <AttackView latest={latest} predictions={predictions} />}
        {active === "correlation" && (
          <section className="view-stack">
            <LiveCorrelationView latest={latest} />
            <CorrelationSensorLogs sensors={sensors} predictions={predictions} deviceStates={deviceStates} />
            <DataTable title="Prediction incident correlation output" items={incidents} columns={["incident_id", "group_category", "alert_count", "attack_types", "wards_affected", "incident_priority", "life_support_involved"]} />
          </section>
        )}
        {active === "response" && (
        <ResponseView
          sensors={sensors}
          selectedDevice={selectedDevice}
          setSelectedDevice={setSelectedDevice}
          telemetry={telemetry}
            responses={responses}
            deviceStates={deviceStates}
            latest={latest}
            onAction={issueAction}
            loading={loading}
          />
        )}
        {active === "quarantine" && (
          <section className="view-stack">
            <DataTable title="Device state registry" items={deviceStates} columns={["updated_at", "device_id", "device_type", "state", "last_action", "reason"]} />
            <OperatorNoticeList states={deviceStates} />
            <DataTable title="Isolated and quarantined response commands" items={quarantinedWithOrigin} columns={["created_at", "device_id", "action", "status", "change_origin", "requested_by"]} />
          </section>
        )}
        {active === "reports" && (
          <ReportsView
            summary={summary}
            latest={latest}
            onPdf={exportPdf}
            onCsv={exportCsv}
            onJson={exportJson}
          />
        )}
      </section>
    </main>
  );
}

function Metric({ label, value: metricValue, detail, tone = "blue" }: { label: string; value: string | number; detail: string; tone?: string }) {
  return (
    <article className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{metricValue}</strong>
      <small>{detail}</small>
    </article>
  );
}

function SeverityPanel({ summary }: { summary: Summary | null }) {
  const counts = summary?.severityCounts ?? { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  const max = Math.max(...Object.values(counts), 1);
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Severity distribution</h2>
        <span>Computed pipeline output</span>
      </div>
      {severityOrder.map((level) => (
        <div className="severity-row" key={level}>
          <span className={severityClass(level)}>{level}</span>
          <div className="bar-track">
            <div className={`bar-fill ${level.toLowerCase()}`} style={{ width: `${(counts[level] / max) * 100}%` }} />
          </div>
          <strong>{counts[level]}</strong>
        </div>
      ))}
    </section>
  );
}

function resultValue(result: Record<string, unknown> | null | undefined, key: string, fallback = "waiting") {
  const item = result?.[key];
  if (item === null || item === undefined || item === "") return fallback;
  return String(item);
}

function LiveFlowTimeline({
  latest,
  simulatorStatus,
  mongoMode
}: {
  latest?: TickResult;
  simulatorStatus: SimulatorStatus | null;
  mongoMode: string;
}) {
  const lastResult = simulatorStatus?.last_result;
  const priority = latest?.analysis?.alert.priority ?? resultValue(lastResult, "priority");
  const attack = latest?.analysis?.attack_prediction.predicted_label ?? resultValue(lastResult, "attack_label");
  const action = latest?.analysis?.decision.action ?? resultValue(lastResult, "action", "monitor");
  const deviceId = value(latest?.event ?? {}, "device_id", resultValue(lastResult, "device_id", "waiting"));
  const deviceType = value(latest?.event ?? {}, "device_type", resultValue(lastResult, "device_type", "sensor"));
  const deviceState = resultValue(lastResult, "state", action === "quarantine" ? "Quarantined" : "Normal");
  const isCritical = ["CRITICAL", "HIGH"].includes(priority.toUpperCase()) || ["quarantine", "shutdown"].includes(action);

  const steps = [
    {
      label: "1. Hardware",
      title: deviceType,
      detail: `Sensor ${deviceId}`,
      tone: "green",
      state: simulatorStatus?.running ? "streaming" : "ready"
    },
    {
      label: "2. Log Store",
      title: mongoMode,
      detail: "sensor_logs collection",
      tone: "ink",
      state: "collected"
    },
    {
      label: "3. Attack AI",
      title: attack,
      detail: "AI Threat Intel models",
      tone: attack === "ATTACK" ? "red" : "green",
      state: "predicted"
    },
    {
      label: "4. Priority AI",
      title: priority,
      detail: "Alert prioritization model",
      tone: priority.toLowerCase(),
      state: "scored"
    },
    {
      label: "5. Correlation",
      title: isCritical ? "validate attack" : "monitor path",
      detail: latest?.analysis?.live_correlation.recommended_verdict ?? "AICE window check",
      tone: isCritical ? "amber" : "blue",
      state: "validated"
    },
    {
      label: "6. Response",
      title: actionLabel(action),
      detail: "AR model + safety policy",
      tone: ["quarantine", "shutdown"].includes(action) ? "red" : "green",
      state: "issued"
    },
    {
      label: "7. Device State",
      title: deviceState,
      detail: "Other sensors continue logging",
      tone: deviceState === "Quarantined" ? "red" : "green",
      state: "tracked"
    }
  ];

  return (
    <section className="panel wide live-flow-panel">
      <div className="panel-heading">
        <div>
          <h2>Live architecture flow</h2>
          <span>Sensor telemetry to AI decision to response action</span>
        </div>
        <div className="simulator-mini">
          <span className={simulatorStatus?.running ? "badge low" : "badge medium"}>
            {simulatorStatus?.running ? "simulator running" : "simulator stopped"}
          </span>
          <strong>{simulatorStatus?.ticks ?? 0} ticks</strong>
          <small>{simulatorStatus?.last_tick_at ? `last: ${formatLocalDateTime(simulatorStatus.last_tick_at)}` : "no backend tick yet"}</small>
        </div>
      </div>
      <div className="timeline-rail">
        {steps.map((step) => (
          <article className={`timeline-card ${step.tone}`} key={step.label}>
            <span>{step.label}</span>
            <strong>{step.title}</strong>
            <small>{step.detail}</small>
            <em>{step.state}</em>
          </article>
        ))}
      </div>
      {simulatorStatus?.last_error && <div className="timeline-warning">Simulator warning: {simulatorStatus.last_error}</div>}
    </section>
  );
}

function ArchitectureDemoView({
  latest,
  simulatorStatus,
  telemetry,
  logs,
  responses,
  deviceStates,
  summary,
  mongoMode
}: {
  latest?: TickResult;
  simulatorStatus: SimulatorStatus | null;
  telemetry: TelemetryItem[];
  logs: TelemetryItem[];
  responses: TelemetryItem[];
  deviceStates: TelemetryItem[];
  summary: Summary | null;
  mongoMode: string;
}) {
  const lastResult = simulatorStatus?.last_result;
  const deviceId = value(latest?.event ?? {}, "device_id", resultValue(lastResult, "device_id", "waiting"));
  const deviceType = value(latest?.event ?? {}, "device_type", resultValue(lastResult, "device_type", "simulated sensor"));
  const ward = value(latest?.event ?? {}, "ward", "observed ward");
  const priority = latest?.analysis?.alert.priority ?? resultValue(lastResult, "priority");
  const attackLabel = latest?.analysis?.attack_prediction.predicted_label ?? resultValue(lastResult, "attack_label");
  const action = latest?.analysis?.decision.action ?? resultValue(lastResult, "action", "monitor");
  const state = value(latest?.state_update ?? {}, "state", resultValue(lastResult, "state", action === "quarantine" ? "Quarantined" : "Normal"));
  const related = latest?.analysis?.live_correlation.related_alert_count ?? 0;
  const verdict = latest?.analysis?.live_correlation.recommended_verdict ?? "waiting";
  const realAttack = latest?.analysis?.correlation.confirmed_real_attack ? "Yes" : "Pending";
  const critical = latest?.analysis?.correlation.confirmed_critical ? "Confirmed" : priority;
  const appliedAction = value(latest?.command ?? {}, "action", actionLabel(action));
  const quarantinedDevices = deviceStates.filter((item) => value(item, "state") === "Quarantined").length;

  return (
    <section className="architecture-board">
      <section className="architecture-hero">
        <div>
          <span className="eyebrow">Viva diagram mode</span>
          <h2>MedGuard X cybersecurity monitoring architecture</h2>
          <p>
            This view maps your planned diagram into the running system: simulated medical sensors publish logs, AI models analyze
            severity and attacks, correlation validates the decision, and the response layer records isolation or quarantine actions.
          </p>
        </div>
        <div className="architecture-status-card">
          <span className={simulatorStatus?.running ? "badge low" : "badge medium"}>
            {simulatorStatus?.running ? "live simulation active" : "simulation paused"}
          </span>
          <strong>{simulatorStatus?.ticks ?? 0}</strong>
          <small>backend ticks generated</small>
        </div>
      </section>

      <div className="architecture-layers">
        <section className="architecture-layer hardware-layer">
          <div className="layer-title">
            <span>Hardware Layer</span>
            <strong>Telemetry / Sensors</strong>
          </div>
          <div className="sensor-grid">
            <DeviceTile label="Heart Rate Machine" metric={value(latest?.event ?? {}, "heart_rate_bpm_pulse", "simulated")} active={deviceType.includes("Pulse") || deviceType.includes("Heart")} />
            <DeviceTile label="ECG Machine" metric={value(latest?.event ?? {}, "ecg_raw_value", "simulated")} active={deviceType.includes("ECG")} />
            <DeviceTile label="Temperature Machine" metric={value(latest?.event ?? {}, "temperature_celsius", "simulated")} active={deviceType.includes("Temperature")} />
            <DeviceTile label="Fall Detection Machine" metric={value(latest?.event ?? {}, "fall_detected", "simulated")} active={deviceType.includes("Motion") || deviceType.includes("Fall")} />
          </div>
          <div className="layer-evidence">
            <span>Latest device</span>
            <strong>{deviceId}</strong>
            <small>{deviceType} in {ward}</small>
          </div>
        </section>

        <section className="architecture-layer ai-layer">
          <div className="layer-title">
            <span>AI/ML Layer</span>
            <strong>Logs, Prediction, Priority, Correlation</strong>
          </div>
          <div className="pipeline-stack">
            <PipelineNode title="Collect Logs" value={mongoMode} detail={`${logs.length} visible MongoDB log records`} tone="ink" />
            <div className="pipeline-split">
              <PipelineNode title="AI Alert Prioritization" value={priority} detail="Random Forest priority model" tone={priority.toLowerCase()} />
              <PipelineNode title="AI Attack Prediction" value={attackLabel} detail="AI Threat Intel RF + Isolation Forest" tone={attackLabel === "ATTACK" ? "red" : "green"} />
            </div>
            <PipelineNode title="Attack Severity Decision" value={critical} detail="Critical/high path triggers temporary isolation" tone={["CRITICAL", "HIGH", "Confirmed"].includes(critical) ? "red" : "amber"} />
            <PipelineNode title="Correlation of Logs" value={verdict} detail={`${related} related events in live AICE window`} tone={verdict === "confirmed_attack" ? "red" : "blue"} />
            <PipelineNode title="Correlation Decision" value={`Real attack: ${realAttack}`} detail="Validates true attack vs false positive" tone={realAttack === "Yes" ? "red" : "green"} />
          </div>
        </section>

        <section className="architecture-layer response-layer">
          <div className="layer-title">
            <span>Response Layer</span>
            <strong>Dashboard, Rollback, Quarantine</strong>
          </div>
          <div className="response-decision-map">
            <PipelineNode title="Response Decision" value={actionLabel(action)} detail="AR response model plus safety policy" tone={["quarantine", "shutdown"].includes(action) ? "red" : "green"} />
            <PipelineNode title="Device State" value={state} detail="Stored in device_states collection" tone={state === "Quarantined" ? "red" : "green"} />
            <PipelineNode title="Response Applied" value={actionLabel(appliedAction)} detail={`${responses.length} response commands visible`} tone="amber" />
            <PipelineNode title="Quarantine Count" value={quarantinedDevices} detail="Other sensors continue logging normally" tone={quarantinedDevices > 0 ? "red" : "green"} />
          </div>
          <div className="architecture-footer-card">
            <span>Current evidence summary</span>
            <strong>{summary?.totalLogs ?? telemetry.length} logs</strong>
            <small>{summary?.attackLogs ?? 0} attack candidates, {summary?.responses ?? responses.length} response records</small>
          </div>
        </section>
      </div>
    </section>
  );
}

function DeviceTile({ label, metric, active }: { label: string; metric: string; active: boolean }) {
  return (
    <article className={active ? "device-tile active" : "device-tile"}>
      <span>{label}</span>
      <strong>{metric}</strong>
      <small>{active ? "latest event source" : "available sensor"}</small>
    </article>
  );
}

function PipelineNode({ title, value: nodeValue, detail, tone }: { title: string; value: string | number; detail: string; tone: string }) {
  return (
    <article className={`pipeline-node ${tone}`}>
      <span>{title}</span>
      <strong>{nodeValue}</strong>
      <small>{detail}</small>
    </article>
  );
}

function LatestPanel({ latest }: { latest?: TickResult }) {
  const analysis = latest?.analysis;
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Latest AI decision</h2>
        <span>Random live simulation</span>
      </div>
      {latest && analysis ? (
        <div className="decision-card">
          <span className={severityClass(analysis.alert.priority)}>{analysis.alert.priority}</span>
          <h3>{value(latest.event, "device_type")}</h3>
          <p>{analysis.correlation.reason}</p>
          <div className="decision-grid">
            <span>Device</span>
            <strong>{value(latest.event, "device_id")}</strong>
            <span>Attack</span>
            <strong>{analysis.attack_prediction.predicted_label}</strong>
            <span>Action</span>
            <strong>{actionLabel(analysis.decision.action)}</strong>
            <span>AR model</span>
            <strong>{analysis.ars_response.action_label}</strong>
            <span>Live related</span>
            <strong>{analysis.live_correlation.related_alert_count}</strong>
            <span>PHI guard</span>
            <strong>{analysis.privacy.phi_detected ? "PHI redacted" : "Safe"}</strong>
          </div>
        </div>
      ) : (
        <div className="empty-state">Run one simulation tick to generate a live model decision.</div>
      )}
    </section>
  );
}

function LiveCorrelationView({ latest }: { latest?: TickResult }) {
  const analysis = latest?.analysis;
  return (
    <section className="panel wide">
      <div className="panel-heading">
        <h2>Live AICE correlation</h2>
        <span>Recent MongoDB window</span>
      </div>
      {latest && analysis ? (
        <div className="attack-layout">
          <div>
            <span className={analysis.live_correlation.recommended_verdict === "confirmed_attack" ? "badge critical" : "badge medium"}>
              {analysis.live_correlation.recommended_verdict}
            </span>
            <h3>{analysis.live_correlation.related_alert_count} related events</h3>
            <p>{analysis.live_correlation.reason}</p>
          </div>
          <div className="decision-grid compact">
            <span>Window</span>
            <strong>{analysis.live_correlation.window_seconds}s</strong>
            <span>Attack alerts</span>
            <strong>{analysis.live_correlation.attack_alert_count}</strong>
            <span>High-risk</span>
            <strong>{analysis.live_correlation.high_risk_attack_count}</strong>
            <span>Score</span>
            <strong>{analysis.live_correlation.correlation_score}</strong>
            <span>Attack types</span>
            <strong>{analysis.live_correlation.attack_types.join(", ") || "none"}</strong>
          </div>
        </div>
      ) : (
        <div className="empty-state">Run one simulation tick to build a live AICE correlation window.</div>
      )}
    </section>
  );
}

function CorrelationSensorLogs({
  sensors,
  predictions,
  deviceStates
}: {
  sensors: SensorProfile[];
  predictions: PredictionRecord[];
  deviceStates: TelemetryItem[];
}) {
  const devices = sensors.length
    ? sensors
    : Array.from(
        new Map(
          predictions
            .filter((item) => item.device_id)
            .map((item) => [
              String(item.device_id),
              {
                device_id: String(item.device_id),
                device_type: String(item.device_type ?? item.device_id),
                ward: String(item.ward ?? "-"),
                life_support: false,
                criticality_tier: 0,
                protocol: "-",
                src_ip: "-",
                sensor_source: "history"
              } satisfies SensorProfile
            ])
        ).values()
      );

  const latestPredictionByDevice = new Map<string, PredictionRecord>();
  predictions.forEach((item) => {
    const deviceId = String(item.device_id ?? "");
    if (!deviceId || latestPredictionByDevice.has(deviceId)) return;
    latestPredictionByDevice.set(deviceId, item);
  });

  const latestStateByDevice = new Map<string, TelemetryItem>();
  deviceStates.forEach((item) => {
    const deviceId = String(item.device_id ?? "");
    if (!deviceId || latestStateByDevice.has(deviceId)) return;
    latestStateByDevice.set(deviceId, item);
  });

  return (
    <section className="panel wide">
      <div className="panel-heading">
        <div>
          <h2>Per-sensor correlation logs</h2>
          <span>How correlation validates each sensor case before the response layer decides monitor, temporary isolation, or quarantine</span>
        </div>
        <span>{devices.length} sensors</span>
      </div>
      {devices.length ? (
        <div className="correlation-log-grid">
          {devices.map((sensor) => {
            const prediction = latestPredictionByDevice.get(String(sensor.device_id));
            const deviceState = latestStateByDevice.get(String(sensor.device_id));
            const recommendedAction = correlationActionLabel(prediction?.decision_action, deviceState?.state ?? prediction?.device_state);
            const validationStatus = prediction
              ? validationStatusLabel(prediction)
              : "No recent correlated event";
            const cardTone =
              recommendedAction === "Quarantine"
                ? "critical"
                : recommendedAction === "Temporary isolate"
                  ? "medium"
                  : "green";

            return (
              <article className={`history-card correlation-log-card ${cardTone}`} key={sensor.device_id}>
                <div>
                  <span className={recommendedAction === "Quarantine" ? "badge critical" : recommendedAction === "Temporary isolate" ? "badge medium" : "badge low"}>
                    {recommendedAction}
                  </span>
                  <span className={prediction?.correlation_verdict === "confirmed_attack" ? "badge critical" : "badge low"}>
                    {detailValue(prediction?.correlation_verdict, "no recent verdict")}
                  </span>
                </div>
                <strong>{sensor.device_type} / {sensor.device_id}</strong>
                <p>
                  {prediction
                    ? `Correlation checked the recent evidence for ${sensor.device_id} and currently supports ${recommendedAction.toLowerCase()} based on attack likelihood, severity, and device context.`
                    : `No recent analyzed event is available for ${sensor.device_id}. The sensor remains in normal monitoring until a new correlated case is produced.`}
                </p>
                <div className="history-detail-grid">
                  <div className="history-detail-item">
                    <span>Time</span>
                    <b>{prediction ? displayValue(prediction, "created_at") : "-"}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Ward</span>
                    <b>{detailValue(prediction?.ward ?? sensor.ward)}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Attack type</span>
                    <b>{detailValue(prediction?.attack_type, "normal")}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Validation status</span>
                    <b>{validationStatus}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Correlation score</span>
                    <b>{prediction?.correlation_score !== undefined ? `${Math.round(Number(prediction.correlation_score) * 100) / 100}` : "-"}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Recommended handling</span>
                    <b>{recommendedAction}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Current device state</span>
                    <b>{detailValue(deviceState?.state ?? prediction?.device_state, "Normal")}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Reason</span>
                    <b>
                      {recommendedAction === "Quarantine"
                        ? "Escalated because correlation supports a confirmed or critical attack case."
                        : recommendedAction === "Temporary isolate"
                          ? "Restricted while the suspicious case remains under validation."
                          : "Recent evidence does not justify escalation, so monitoring continues."}
                    </b>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">No sensors are available yet. Start the simulator or connect live telemetry to populate per-sensor correlation logs.</div>
      )}
    </section>
  );
}

function PriorityView({ latest, summary, predictions }: { latest?: TickResult; summary: Summary | null; predictions: PredictionRecord[] }) {
  const priorityMetricDetail = summary?.mode === "mongodb" ? "live MongoDB priority count" : "incident priority count";
  return (
    <section className="view-stack">
      <div className="metric-grid">
        {severityOrder.map((level) => (
          <Metric key={level} label={level} value={summary?.severityCounts[level] ?? 0} detail={priorityMetricDetail} tone={level.toLowerCase()} />
        ))}
      </div>
      <PriorityHistory predictions={predictions} latest={latest} />
    </section>
  );
}

function AlertGroupingView({
  summary,
  incidents,
  onRefresh,
  refreshing,
  message
}: {
  summary: Summary | null;
  incidents: AlertIncidentRecord[];
  onRefresh: () => void;
  refreshing: boolean;
  message: string;
}) {
  const groupedAlerts = incidents.reduce((total, incident) => total + Number(incident.alert_count ?? 0), 0);
  const multiAlertGroups = incidents.filter((incident) => Number(incident.alert_count ?? 0) > 1).length;
  const categoryGroups = useMemo(() => {
    const buckets = new Map<string, AlertIncidentRecord[]>();
    incidents.forEach((incident) => {
      const category = normalizeIncidentCategory(incident.group_category ?? incident.incident_priority);
      const existing = buckets.get(category) ?? [];
      existing.push(incident);
      buckets.set(category, existing);
    });
    return incidentCategoryOrder
      .map((category) => ({
        category,
        label: incidentCategoryLabel(category),
        tone: incidentCategoryTone(category),
        incidents: buckets.get(category) ?? []
      }))
      ;
  }, [incidents]);
  const affectedWards = new Set(
    incidents.flatMap((incident) =>
      String(incident.wards_affected ?? "")
        .split(",")
        .map((ward) => ward.trim())
        .filter(Boolean)
    )
  );

  return (
    <section className="view-stack">
      <div className="metric-grid">
        <Metric label="Incident groups" value={summary?.incidentGroups ?? incidents.length} detail="prediction-derived grouped output" tone="green" />
        <Metric label="Grouped alerts" value={groupedAlerts} detail="prediction records assigned to clusters" />
        <Metric label="Alert reduction" value={summary?.alertReduction ?? "-"} detail="from prediction grouping script" tone="amber" />
        <Metric label="Affected wards" value={affectedWards.size} detail="distinct wards in grouped incidents" tone="red" />
      </div>

      <section className="panel wide">
        <div className="panel-heading">
          <div>
            <h2>Alert grouping incidents</h2>
            <span>{message || "Read-only output from /incidents using grouped prediction records"}</span>
          </div>
          <div className="download-row">
            <button className="grouping-refresh-button" onClick={onRefresh} disabled={refreshing} type="button">
              <RefreshCw size={16} />
              {refreshing ? "Refreshing..." : "Refresh grouping"}
            </button>
          </div>
        </div>
        <div className="metric-grid" style={{ marginBottom: 20 }}>
          <Metric label="Multi-alert clusters" value={multiAlertGroups} detail="clusters containing more than one alert" tone="blue" />
        </div>
        {incidents.length ? (
          <div className="history-stack">
            {categoryGroups.map((section) => {
              const sectionAlerts = section.incidents.reduce((total, incident) => total + Number(incident.alert_count ?? 0), 0);
              const sectionWards = new Set(
                section.incidents.flatMap((incident) =>
                  String(incident.wards_affected ?? "")
                    .split(",")
                    .map((ward) => ward.trim())
                    .filter(Boolean)
                )
              );
              const sectionDevices = new Set(
                section.incidents.flatMap((incident) =>
                  String(incident.devices_affected ?? "")
                    .split(",")
                    .map((device) => device.trim())
                    .filter(Boolean)
                )
              );
              const sectionMultiAlertGroups = section.incidents.filter((incident) => Number(incident.alert_count ?? 0) > 1).length;
              return (
                <article className={`history-card category-shell category-${section.category}`} key={section.category}>
                  <div>
                    <span className={severityClass(section.tone.toUpperCase())}>{section.label}</span>
                    <span className="badge low">{section.incidents.length} incidents</span>
                  </div>
                  <strong>{section.label} grouping</strong>
                  <p>{sectionAlerts} prediction records grouped under {section.label.toLowerCase()} severity/category.</p>
                  <div className="history-detail-grid">
                    <div className="history-detail-item">
                      <span>Category</span>
                      <b>{section.label}</b>
                    </div>
                    <div className="history-detail-item">
                      <span>Incident count</span>
                      <b>{section.incidents.length}</b>
                    </div>
                    <div className="history-detail-item">
                      <span>Total alerts</span>
                      <b>{sectionAlerts}</b>
                    </div>
                    <div className="history-detail-item">
                      <span>Multi-alert groups</span>
                      <b>{sectionMultiAlertGroups}</b>
                    </div>
                    <div className="history-detail-item">
                      <span>Wards</span>
                      <b>{sectionWards.size}</b>
                    </div>
                    <div className="history-detail-item">
                      <span>Devices</span>
                      <b>{sectionDevices.size}</b>
                    </div>
                  </div>
                  {section.incidents.length ? (
                    <>
                      <div className="history-stack" style={{ marginTop: 16 }}>
                        {section.incidents.slice(0, 3).map((incident) => (
                          <article className={`history-card latest category-incident category-${section.category}`} key={incident.incident_id ?? `${incident.group_id}-${incident.start_timestamp}`}>
                            <div>
                              <span className={severityClass(String(incident.incident_priority ?? "LOW"))}>{String(incident.incident_priority ?? "LOW")}</span>
                              <span className="badge low">{String(incident.alert_count ?? 0)} alerts</span>
                            </div>
                            <strong>{incident.incident_id ?? `Incident ${incident.group_id ?? "-"}`}</strong>
                            <p>{incident.attack_types ?? "Grouped prediction records clustered by category, device, ward, and time window."}</p>
                            <div className="history-detail-grid">
                              <div className="history-detail-item">
                                <span>Wards</span>
                                <b>{detailValue(incident.wards_affected)}</b>
                              </div>
                              <div className="history-detail-item">
                                <span>Devices</span>
                                <b>{detailValue(incident.devices_affected)}</b>
                              </div>
                              <div className="history-detail-item">
                                <span>Source IPs</span>
                                <b>{detailValue(incident.src_ips)}</b>
                              </div>
                              <div className="history-detail-item">
                                <span>Start</span>
                                <b>{displayValue(incident, "start_timestamp")}</b>
                              </div>
                              <div className="history-detail-item">
                                <span>End</span>
                                <b>{displayValue(incident, "end_timestamp")}</b>
                              </div>
                              <div className="history-detail-item">
                                <span>Life support</span>
                                <b>{booleanValue(incident.life_support_involved) ? "Yes" : "No"}</b>
                              </div>
                            </div>
                          </article>
                        ))}
                      </div>
                      {section.incidents.length > 3 && (
                        <div className="empty-state" style={{ marginTop: 12 }}>
                          + {section.incidents.length - 3} more incidents in {section.label.toLowerCase()}.
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="empty-state" style={{ marginTop: 16 }}>
                      No grouped incidents are currently assigned to {section.label.toLowerCase()}.
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-state">
            No grouped incidents are available yet. Run the alert grouping refresh to rebuild <code>grouped_incidents.csv</code> from stored predictions and then reload this page.
          </div>
        )}
      </section>

      <DataTable
        title="Grouped incident table"
        items={incidents}
        columns={["incident_id", "group_category", "alert_count", "incident_priority", "attack_types", "wards_affected", "devices_affected", "src_ips", "start_timestamp", "end_timestamp"]}
      />
    </section>
  );
}

function PriorityHistory({ predictions, latest }: { predictions: PredictionRecord[]; latest?: TickResult }) {
  const rows = predictions.slice(0, 10);
  return (
    <section className="panel wide">
      <div className="panel-heading">
        <div>
          <h2>Recent AI priority decisions</h2>
          <span>Persisted from MongoDB predictions collection</span>
        </div>
        <span>{rows.length} recent decisions</span>
      </div>
      {rows.length ? (
        <div className="history-stack">
          {rows.map((item, index) => (
            <article className={index === 0 ? "history-card latest" : "history-card"} key={value(item, "_id", `${item.device_id}-${index}`)}>
              <div>
                <span className={severityClass(String(item.priority ?? "LOW"))}>{String(item.priority ?? "-")}</span>
                {index === 0 && <span className="badge low">Most recent</span>}
              </div>
              <strong>{item.device_type ?? "Unknown device"} / {item.device_id ?? "-"}</strong>
              <p>{item.priority_reason ?? "Priority decision generated by the alert prioritization model."}</p>
              <div className="history-detail-grid">
                <div className="history-detail-item">
                  <span>Time</span>
                  <b>{displayValue(item, "created_at")}</b>
                </div>
                <div className="history-detail-item">
                  <span>Attack type</span>
                  <b>{detailValue(item.attack_type)}</b>
                </div>
                <div className="history-detail-item">
                  <span>Priority confidence</span>
                  <b>{Math.round(Number(item.priority_confidence ?? 0) * 100)}%</b>
                </div>
                <div className="history-detail-item">
                  <span>Real attack</span>
                  <b>{item.confirmed_real_attack ? "Yes" : "No"}</b>
                </div>
                <div className="history-detail-item">
                  <span>Ward</span>
                  <b>{detailValue(item.ward)}</b>
                </div>
                <div className="history-detail-item">
                  <span>Final action</span>
                  <b>{actionLabel(String(item.decision_action ?? "monitor"))}</b>
                </div>
                <div className="history-detail-item">
                  <span>Correlation</span>
                  <b>{detailValue(item.correlation_verdict)}</b>
                </div>
                <div className="history-detail-item">
                  <span>Device state</span>
                  <b>{detailValue(item.device_state)}</b>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          No persisted priority decisions yet. Run the simulator or click one simulation tick to save prediction history.
          {latest?.analysis ? " The current in-memory latest decision is available on the Dashboard." : ""}
        </div>
      )}
    </section>
  );
}

function AttackView({ latest, predictions }: { latest?: TickResult; predictions: PredictionRecord[] }) {
  const analysis = latest?.analysis;
  const temporaryStatus = analysis
    ? temporaryStatusLabel(analysis.decision.action, analysis.attack_prediction.predicted_attack)
    : "Monitor";
  const validationStatus = analysis
    ? (analysis.correlation.confirmed_real_attack
        ? "Confirmed attack"
        : analysis.attack_prediction.predicted_attack
          ? "Pending validation"
          : "Normal traffic")
    : "Normal traffic";
  return (
    <section className="view-stack">
      {latest && analysis && (
        <section className="panel wide">
          <div className="panel-heading">
            <h2>Most recent attack prediction</h2>
            <span>Live event context</span>
          </div>
          <div className="attack-layout">
            <div>
              <span className={analysis.attack_prediction.predicted_attack ? "badge high" : "badge low"}>{analysis.attack_prediction.predicted_label}</span>
              <h3>{value(latest.event, "device_type")}</h3>
              <p>{analysis.attack_prediction.reason}</p>
            </div>
            <div className="decision-grid compact">
              <span>Predicted threat</span>
              <strong>{analysis.attack_prediction.predicted_attack ? "Yes" : "No"}</strong>
              <span>RF confidence</span>
              <strong>{Math.round(analysis.attack_prediction.confidence * 100)}%</strong>
              <span>Risk score</span>
              <strong>{Math.round(analysis.attack_prediction.risk_score * 100)}%</strong>
              <span>Anomaly flag</span>
              <strong>{analysis.attack_prediction.anomaly_flag}</strong>
              <span>Temporary status</span>
              <strong>{temporaryStatus}</strong>
              <span>Validation status</span>
              <strong>{validationStatus}</strong>
              <span>Correlation status</span>
              <strong>{detailValue(analysis.live_correlation.recommended_verdict)}</strong>
            </div>
          </div>
        </section>
      )}
      <AttackHistory predictions={predictions} />
    </section>
  );
}

function AttackHistory({ predictions }: { predictions: PredictionRecord[] }) {
  const rows = predictions.slice(0, 10);
  return (
    <section className="panel wide">
      <div className="panel-heading">
        <div>
          <h2>Recent attack predictions</h2>
          <span>Last 10 saved Random Forest + Isolation Forest outputs</span>
        </div>
        <span>{rows.length} records</span>
      </div>
      {rows.length ? (
        <div className="history-stack">
          {rows.map((item, index) => {
            const predictedAttack = Boolean(item.predicted_attack);
            const risk = Math.round(Number(item.risk_score ?? 0) * 100);
            return (
              <article className={index === 0 ? "history-card latest" : "history-card"} key={value(item, "_id", `${item.device_id}-${index}`)}>
                <div>
                  <span className={predictedAttack ? "badge high" : "badge low"}>{String(item.attack_label ?? "-")}</span>
                  <span className={String(item.anomaly_flag).toUpperCase() === "ANOMALY" ? "badge medium" : "badge low"}>
                    {String(item.anomaly_flag ?? "NORMAL")}
                  </span>
                  {index === 0 && <span className="badge low">Most recent</span>}
                </div>
                <strong>{item.device_type ?? "Unknown device"} / {item.device_id ?? "-"}</strong>
                <p>Attack prediction from saved AI Threat Intel Random Forest with Isolation Forest anomaly context.</p>
                <div className="history-detail-grid">
                  <div className="history-detail-item">
                    <span>Time</span>
                    <b>{displayValue(item, "created_at")}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Attack type</span>
                    <b>{detailValue(item.attack_type)}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>RF confidence</span>
                    <b>{Math.round(Number(item.attack_confidence ?? 0) * 100)}%</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Risk score</span>
                    <b>{risk}%</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Predicted threat</span>
                    <b>{predictedAttack ? "Yes" : "No"}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Temporary status</span>
                    <b>{temporaryStatusLabel(item.decision_action, predictedAttack)}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Validation status</span>
                    <b>{validationStatusLabel(item)}</b>
                  </div>
                  <div className="history-detail-item">
                    <span>Correlation status</span>
                    <b>{detailValue(item.correlation_verdict)}</b>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">No persisted attack predictions yet. Run the simulator or click one simulation tick to save prediction history.</div>
      )}
    </section>
  );
}

function ARResponseSummary({ latest }: { latest?: TickResult }) {
  const analysis = latest?.analysis;
  return (
    <section className="panel wide">
      <div className="panel-heading">
        <h2>AR System model decision</h2>
        <span>ars_decision_model_final.pkl</span>
      </div>
      {latest && analysis ? (
        <div className="attack-layout">
          <div>
            <span className={analysis.ars_response.mapped_action === "quarantine" ? "badge critical" : "badge medium"}>
              {analysis.ars_response.action_label}
            </span>
            <h3>{actionLabel(analysis.decision.action)}</h3>
            <p>{analysis.decision.reason}</p>
          </div>
          <div className="decision-grid compact">
            <span>Model confidence</span>
            <strong>{Math.round(analysis.ars_response.confidence * 100)}%</strong>
            <span>Mapped action</span>
            <strong>{actionLabel(analysis.ars_response.mapped_action)}</strong>
            <span>Anomaly score</span>
            <strong>{String(analysis.ars_response.features.anomaly_score ?? "-")}</strong>
            <span>Packet size</span>
            <strong>{String(analysis.ars_response.features.packet_size ?? "-")}</strong>
          </div>
        </div>
      ) : (
        <div className="empty-state">Run one simulation tick to get an AR System response prediction.</div>
      )}
    </section>
  );
}

function ResponseView({
  selectedDevice,
  setSelectedDevice,
  sensors,
  telemetry,
  responses,
  deviceStates,
  latest,
  onAction,
  loading
}: {
  selectedDevice: string;
  setSelectedDevice: (device: string) => void;
  sensors: SensorProfile[];
  telemetry: TelemetryItem[];
  responses: TelemetryItem[];
  deviceStates: TelemetryItem[];
  latest?: TickResult;
  onAction: (action: string) => Promise<void>;
  loading: boolean;
}) {
  const devices = sensors.length
    ? sensors
    : Array.from(new Set(telemetry.map((item) => String(item.device_id ?? "")).filter(Boolean))).map((device_id) => ({
        device_id,
        device_type: device_id,
        ward: "",
        life_support: false,
        criticality_tier: 0,
        protocol: "",
        src_ip: "",
        sensor_source: ""
      }));
  const selectedState = deviceStates.find((item) => value(item, "device_id", "") === selectedDevice);
  const selectedNotice = operatorNoticeForState(selectedState);
  const responseHistory = responses.map((item) => ({
    ...item,
    change_origin: responseOrigin(item),
  }));
  return (
    <section className="view-stack">
      <section className="panel wide">
        <div className="panel-heading">
          <h2>Response decision controls</h2>
          <span>AR model + backend state control</span>
        </div>
        {selectedNotice && (
          <div className="operator-notice critical">
            <AlertTriangle size={18} />
            <span>{selectedNotice}</span>
          </div>
        )}
        <div className="control-row">
          <select value={selectedDevice} onChange={(event) => setSelectedDevice(event.target.value)}>
            {devices.length ? (
              devices.map((device) => (
                <option key={device.device_id} value={device.device_id}>
                  {device.device_id} - {device.device_type}
                </option>
              ))
            ) : (
              <option value={selectedDevice}>{selectedDevice}</option>
            )}
          </select>
          <button onClick={() => onAction("temporary_isolate")} disabled={loading}><StopCircle size={16} /> Isolate</button>
          <button onClick={() => onAction("quarantine")} disabled={loading}><Lock size={16} /> Quarantine</button>
          <button onClick={() => onAction("shutdown")} disabled={loading}><StopCircle size={16} /> Shutdown</button>
          <button onClick={() => onAction("rollback")} disabled={loading}><RotateCcw size={16} /> Rollback</button>
          <button onClick={() => onAction("false_positive")} disabled={loading}><ShieldCheck size={16} /> False positive</button>
          <button onClick={() => onAction("log_and_monitor")} disabled={loading}><ClipboardList size={16} /> Log</button>
          <button onClick={() => onAction("restore")} disabled={loading}><RefreshCw size={16} /> Restore</button>
        </div>
      </section>
      <ARResponseSummary latest={latest} />
      <DataTable title="Response action history" items={responseHistory} columns={["created_at", "device_id", "action", "status", "change_origin", "requested_by"]} />
    </section>
  );
}

function OperatorNoticeList({ states }: { states: TelemetryItem[] }) {
  const notices = states
    .map((item) => ({ item, notice: operatorNoticeForState(item) }))
    .filter(({ notice }) => notice);

  if (!notices.length) return null;

  return (
    <section className="panel wide">
      <div className="panel-heading">
        <h2>Operator notifications</h2>
        <span>{notices.length} active</span>
      </div>
      <div className="notice-list">
        {notices.map(({ item, notice }) => (
          <div className="operator-notice critical" key={value(item, "device_id")}>
            <AlertTriangle size={18} />
            <span>
              <strong>{value(item, "device_id")}</strong>: {notice}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ReportsView({ summary, latest, onPdf, onCsv, onJson }: { summary: Summary | null; latest?: TickResult; onPdf: () => void; onCsv: () => void; onJson: () => void }) {
  return (
    <section className="view-stack">
      <div className="metric-grid">
        <Metric label="Evidence logs" value={summary?.totalLogs ?? 0} detail="MongoDB or mock source" />
        <Metric label="Alert reduction" value={summary?.alertReduction ?? "-"} detail="grouping output" tone="green" />
        <Metric label="Responses" value={summary?.responses ?? 0} detail="response collection" tone="amber" />
        <Metric label="Devices" value={summary?.activeDevices ?? 0} detail="observed endpoints" tone="blue" />
      </div>
      <section className="panel wide">
        <div className="panel-heading">
          <h2>Downloadable evidence pack</h2>
          <span>Structured exports for demo, viva, and review</span>
        </div>
        <div className="history-stack">
          <article className="history-card">
            <div>
              <span className="badge critical">PDF brief</span>
            </div>
            <strong>Executive incident report</strong>
            <p>Formatted evidence brief with system posture, severity distribution, latest validation outcome, restriction status, and PHI-redacted evidence.</p>
            <div className="download-row">
              <button onClick={onPdf}><FileDown size={16} /> Download PDF report</button>
            </div>
          </article>
          <article className="history-card">
            <div>
              <span className="badge medium">CSV evidence</span>
            </div>
            <strong>Telemetry evidence extract</strong>
            <p>Recent telemetry rows with protocol, attack flags, device state, and current network status for audit or spreadsheet analysis.</p>
            <div className="download-row">
              <button onClick={onCsv}><Table2 size={16} /> Download CSV evidence</button>
            </div>
          </article>
          <article className="history-card">
            <div>
              <span className="badge low">JSON summary</span>
            </div>
            <strong>Machine-readable report bundle</strong>
            <p>Structured export containing simulator state, severity counts, active restrictions, recent predictions, and the latest AI analysis block.</p>
            <div className="download-row">
              <button onClick={onJson}><Archive size={16} /> Download JSON summary</button>
            </div>
          </article>
        </div>
      </section>
      <PrivacyView latest={latest} />
    </section>
  );
}

function PrivacyView({ latest }: { latest?: TickResult }) {
  const analysis = latest?.analysis;
  return (
    <section className="panel wide">
      <div className="panel-heading">
        <h2>PHI privacy guard</h2>
        <span>AR System PHI model</span>
      </div>
      {latest && analysis ? (
        <div className="attack-layout">
          <div>
            <span className={analysis.privacy.phi_detected ? "badge high" : "badge low"}>
              {analysis.privacy.phi_detected ? "PHI detected" : "No PHI"}
            </span>
            <h3>{analysis.privacy.redaction_count} redactions</h3>
            <p>{analysis.privacy.reason}</p>
          </div>
          <div className="decision-grid compact">
            <span>Redacted evidence</span>
            <strong>{analysis.privacy.redacted_text}</strong>
          </div>
        </div>
      ) : (
        <div className="empty-state">Run one simulation tick to evaluate privacy evidence.</div>
      )}
    </section>
  );
}

function DataTable({ title, items, columns }: { title: string; items: TelemetryItem[]; columns: string[] }) {
  return (
    <section className="panel wide">
      <div className="panel-heading">
        <h2>{title}</h2>
        <span>{items.length} records</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${value(item, "_id", String(index))}-${index}`}>
                {columns.map((column) => (
                  <td key={column}>
                    {column === "network_status" ? (
                      <span className={`badge ${networkStatus(item).className}`}>{networkStatus(item).label}</span>
                    ) : column.includes("priority") ? (
                      <span className={severityClass(value(item, column))}>{displayValue(item, column)}</span>
                    ) : (
                      displayValue(item, column)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
