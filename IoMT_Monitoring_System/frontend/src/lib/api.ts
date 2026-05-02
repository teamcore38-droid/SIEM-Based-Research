const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Summary = {
  mode: string;
  totalLogs: number;
  attackLogs: number;
  responses: number;
  activeDevices: number;
  incidentGroups: number;
  modelAccuracy: string;
  alertReduction: string;
  severityCounts: Record<"CRITICAL" | "HIGH" | "MEDIUM" | "LOW", number>;
  devices: string[];
};

export type TelemetryItem = Record<string, unknown>;
export type SensorProfile = TelemetryItem & {
  device_id: string;
  device_type: string;
  ward: string;
  life_support: boolean;
  criticality_tier: number;
  protocol: string;
  src_ip: string;
  sensor_source: string;
};

export type AnalyzeResult = {
  alert: {
    device_id: string;
    priority: string;
    confidence: number;
    reason: string;
  };
  attack_prediction: {
    device_id: string;
    predicted_label: string;
    predicted_attack: boolean;
    confidence: number;
    anomaly_flag: string;
    anomaly_score: number;
    risk_score: number;
    reason: string;
  };
  correlation: {
    device_id: string;
    confirmed_critical: boolean;
    confirmed_real_attack: boolean;
    final_action: string;
    reason: string;
    related_alert_count: number;
  };
  live_correlation: {
    device_id: string;
    window_seconds: number;
    events_considered: number;
    related_alert_count: number;
    attack_alert_count: number;
    high_risk_attack_count: number;
    attack_types: string[];
    correlation_score: number;
    recommended_verdict: string;
    reason: string;
  };
  ars_response: {
    action_label: string;
    mapped_action: string;
    confidence: number;
    reason: string;
    features: Record<string, unknown>;
  };
  privacy: {
    phi_detected: boolean;
    original_text: string;
    redacted_text: string;
    redaction_count: number;
    reason: string;
  };
  decision: {
    action: string;
    should_quarantine: boolean;
    should_shutdown: boolean;
    should_rollback: boolean;
    reason: string;
  };
};

export type TickResult = {
  event: TelemetryItem;
  analysis: AnalyzeResult | null;
  command: Record<string, unknown> | null;
  state_update?: Record<string, unknown> | null;
  skipped?: boolean;
  message?: string;
};

export type SimulatorStatus = {
  running: boolean;
  interval_seconds: number;
  ticks: number;
  started_at: string | null;
  stopped_at: string | null;
  last_tick_at: string | null;
  last_error: string | null;
  last_result: Record<string, unknown> | null;
  blocked?: boolean;
  message?: string;
};

export type SimulationConfig = {
  data_mode: "real" | "simulation";
  simulation_mode: "normal" | "anomaly";
  anomaly_device_id: string;
  anomaly_type: string;
};

export type PredictionRecord = TelemetryItem & {
  created_at?: string;
  timestamp?: string | number;
  device_id?: string;
  device_type?: string;
  ward?: string;
  attack_type?: string;
  priority?: string;
  priority_confidence?: number;
  priority_reason?: string;
  attack_label?: string;
  predicted_attack?: boolean;
  attack_confidence?: number;
  anomaly_flag?: string;
  risk_score?: number;
  correlation_verdict?: string;
  correlation_score?: number;
  confirmed_real_attack?: boolean;
  confirmed_critical?: boolean;
  decision_action?: string;
  device_state?: string;
};

export type ReportPayload = {
  generated_at: string;
  total_logs: number;
  attack_logs: number;
  total_responses: number;
  active_devices: number;
  model_accuracy: string;
  alert_reduction: string;
  notes: string[];
  mode: string;
  severity_counts: Record<"CRITICAL" | "HIGH" | "MEDIUM" | "LOW", number>;
  simulator?: SimulatorStatus;
  simulation_config?: SimulationConfig;
  active_restrictions?: {
    count: number;
    items: TelemetryItem[];
  };
  recent_predictions?: PredictionRecord[];
  latest_event?: TelemetryItem | null;
  latest_analysis?: AnalyzeResult | null;
  redacted_evidence?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; mongo: boolean; mode: string; simulator: SimulatorStatus; simulation_config: SimulationConfig }>("/health"),
  summary: () => request<Summary>("/dashboard/summary"),
  telemetry: (limit = 30) => request<{ mode: string; items: TelemetryItem[] }>(`/telemetry?limit=${limit}`),
  sensors: () => request<{ count: number; items: SensorProfile[] }>("/sensors"),
  logs: (limit = 60) => request<{ mode: string; items: TelemetryItem[] }>(`/logs?limit=${limit}`),
  incidents: (limit = 40) => request<{ mode: string; items: TelemetryItem[] }>(`/incidents?limit=${limit}`),
  responses: (limit = 40) => request<{ mode: string; items: TelemetryItem[] }>(`/responses?limit=${limit}`),
  quarantine: (limit = 40) => request<{ mode: string; items: TelemetryItem[] }>(`/quarantine?limit=${limit}`),
  deviceStates: (limit = 100) => request<{ mode: string; items: TelemetryItem[] }>(`/devices/states?limit=${limit}`),
  predictions: (limit = 10) => request<{ mode: string; items: PredictionRecord[] }>(`/predictions/recent?limit=${limit}`),
  tick: () => request<TickResult>("/simulate/tick", { method: "POST" }),
  simulationConfig: () => request<SimulationConfig>("/simulation/config"),
  updateSimulationConfig: (config: Partial<SimulationConfig>) =>
    request<{ config: SimulationConfig; simulator: SimulatorStatus }>("/simulation/config", {
      method: "POST",
      body: JSON.stringify(config)
    }),
  simulatorStatus: () => request<SimulatorStatus>("/simulate/status"),
  simulatorLatest: () => request<{ item: TickResult | null }>("/simulate/latest"),
  startSimulator: (intervalSeconds = 4.5) =>
    request<SimulatorStatus>(`/simulate/start?interval_seconds=${intervalSeconds}`, { method: "POST" }),
  stopSimulator: () => request<SimulatorStatus>("/simulate/stop", { method: "POST" }),
  action: (device_id: string, action: string, reason: string) =>
    request<{ issued: boolean; command: Record<string, unknown>; state_update?: Record<string, unknown> | null }>("/responses/action", {
      method: "POST",
      body: JSON.stringify({ device_id, action, reason, requested_by: "admin-demo" })
    }),
  report: () => request<ReportPayload>("/reports/summary")
};
