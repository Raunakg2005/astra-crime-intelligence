import axios from "axios";

const http = axios.create({ baseURL: "" });

// ---- response types (mirror backend/appsail_ml/analytics.py) ----
export interface Kpis {
  total_cases: number;
  cases_last_30d: number;
  cases_prev_30d: number;
  mom_change_pct: number;
  clearance_rate_pct: number;
  heinous_cases: number;
  districts: number;
  active_alerts: number;
  data_from: string;
  data_to: string;
}

export interface District {
  district_id: number;
  district: string;
  lat: number;
  lng: number;
  total_cases: number;
  recent_90d: number;
  clearance_pct: number;
  heinous: number;
  heinous_pct: number;
  top_crime_head: string;
}

export interface Cluster {
  cluster_id: number;
  lat: number;
  lng: number;
  count: number;
  district: string;
  dominant_crime: string;
  dominant_head: string;
  peak_hour: number | null;
  night_share_pct: number;
  heinous_pct: number;
  intensity: number;
}
export interface Hotspots {
  clusters: Cluster[];
  n_points: number;
  n_clustered: number;
  n_clusters: number;
}

export interface Alert {
  district_id: number;
  district: string;
  crime_head: string;
  recent_count: number;
  baseline_avg: number;
  z_score: number;
  ratio: number | null;
  top_subcrime: string;
  severity: "critical" | "high" | "elevated";
}

export interface Offender {
  name: string;
  cases: number;
  districts: number;
  district_names: string[];
  primary_mo: string;
  mo_breakdown: Record<string, number>;
  age: number;
}

export interface Community {
  community_id: number;
  size: number;
  members: string[];
  total_cases: number;
  districts_spanned: number;
  districts: string[];
  dominant_mo: string;
  internal_edges: number;
}
export interface Communities {
  communities: Community[];
  n_nodes: number;
  n_edges: number;
  n_communities: number;
}

export interface EgoNode {
  id: string;
  type: "offender" | "district";
  kind: string;
  cases: number;
  shared_cases?: number;
}
export interface EgoEdge {
  source: string;
  target: string;
  weight: number;
  label: string;
}
export interface Ego {
  ego: string;
  profile: {
    total_cases: number;
    districts: number;
    co_offenders: number;
    primary_mo: string;
    mo_breakdown: Record<string, number>;
  };
  nodes: EgoNode[];
  edges: EgoEdge[];
}

export interface Anomaly {
  case_id: number;
  crime_no: string;
  district: string;
  crime: string;
  date: string;
  score: number;
  reasons: string[];
}
export interface AnomalyResp {
  anomalies: Anomaly[];
  n_flagged: number;
  total_cases: number;
}

export interface RiskDistrict {
  district_id: number;
  district: string;
  lat: number;
  lng: number;
  risk_score: number;
  recent_30d: number;
  trend_pct: number;
  heinous_share_pct: number;
  risk_band: "High" | "Medium" | "Low";
  predicted_next_week?: number;
  high_risk_probability?: number;
  model?: string;
}

export interface ModelInfo {
  trained?: boolean;
  risk?: {
    classifier: { roc_auc: number; f1: number; precision: number; recall: number; accuracy: number };
    regressor: { mae: number; baseline_mae_lag1: number; r2: number };
    n_train_rows: number;
    n_test_rows: number;
    feature_importance: Record<string, number>;
  };
  anomaly?: { n_cases: number; flagged: number };
}

export interface ModelRegistry {
  pipeline: { xgboost?: boolean; gpu?: boolean; device?: string; mlflow?: boolean };
  tasks: Record<
    string,
    {
      champion_version: number;
      versions: number[];
      family: string;
      metrics: Record<string, number>;
      cv: {
        n_splits?: number;
        n_candidates?: number;
        metric?: string;
        mean?: number;
        leaderboard?: { family: string; cv_score: number }[];
      };
      n_train?: number;
      n_holdout?: number;
    }
  >;
}

export interface NlpClassification {
  input: string;
  model?: string;
  predicted_head: string;
  predictions: { crime_head: string; confidence: number }[];
  entities: Record<string, string[]>;
  error?: string;
}

export interface NlpModelRow {
  family: string;
  cv_score: number;
  cv_std: number;
  accuracy?: number;
  macro_f1?: number;
  weighted_f1?: number;
  has_proba?: boolean;
}

export interface NlpModelInfo {
  champion: string;
  champion_version: number;
  metrics: { accuracy: number; macro_f1: number; weighted_f1: number; cv_macro_f1: number; n_classes: number };
  leaderboard: NlpModelRow[];
  classes: string[];
  per_class_f1: Record<string, number>;
  gpu: boolean;
  device: string;
  data_rows: number;
}

export interface MoCluster {
  cluster: number;
  size: number;
  top_terms: string[];
  dominant_head: string;
}

export interface TimeSeries {
  monthly: { month: string; count: number }[];
  dow_hour: { dow: number; hour: number; count: number }[];
  by_head: Record<string, number>;
}

// ---- api calls ----
export const api = {
  kpis: () => http.get<Kpis>("/api/kpis").then((r) => r.data),
  districts: () => http.get<District[]>("/api/districts").then((r) => r.data),
  hotspots: (p: { district_id?: number; crime_head?: string; days?: number } = {}) =>
    http.get<Hotspots>("/api/hotspots", { params: p }).then((r) => r.data),
  trends: (z = 2) =>
    http.get<{ alerts: Alert[] }>("/api/trends", { params: { z_threshold: z } }).then((r) => r.data.alerts),
  timeseries: (p: { crime_head?: string; district_id?: number } = {}) =>
    http.get<TimeSeries>("/api/timeseries", { params: p }).then((r) => r.data),
  communities: (top = 15) =>
    http.get<Communities>("/api/network/communities", { params: { top } }).then((r) => r.data),
  repeatOffenders: (min_cases = 5, top = 25) =>
    http
      .get<{ offenders: Offender[] }>("/api/network/repeat-offenders", { params: { min_cases, top } })
      .then((r) => r.data.offenders),
  ego: (name: string) => http.get<Ego>(`/api/network/ego/${encodeURIComponent(name)}`).then((r) => r.data),
  anomalies: (top = 30) => http.get<AnomalyResp>("/api/anomalies", { params: { top } }).then((r) => r.data),
  risk: () => http.get<{ districts: RiskDistrict[] }>("/api/risk").then((r) => r.data.districts),
  modelInfo: () => http.get<ModelInfo>("/api/model-info").then((r) => r.data),
  modelRegistry: () => http.get<ModelRegistry>("/api/model-registry").then((r) => r.data),
  nlpClassify: (text: string, model?: string) =>
    http.get<NlpClassification>("/api/nlp/classify", { params: { text, model } }).then((r) => r.data),
  nlpModelInfo: () => http.get<NlpModelInfo>("/api/nlp/model-info").then((r) => r.data),
  nlpClusters: () =>
    http.get<{ clusters: MoCluster[]; n_clusters: number }>("/api/nlp/clusters").then((r) => r.data),
};

// crime-head -> colour (consistent across views)
export const HEAD_COLORS: Record<string, string> = {
  "Crimes Against Body": "#f43f5e",
  "Crimes Against Property": "#38bdf8",
  "Crimes Against Women": "#a78bfa",
  "Crimes Against Children": "#f472b6",
  "Crimes Against Public Order & Safety": "#fbbf24",
  "Economic Offences": "#34d399",
  "Offences Against State / Special Laws": "#fb923c",
  "Cyber Crimes": "#22d3ee",
};
export const headColor = (h: string) => HEAD_COLORS[h] ?? "#94a3b8";
