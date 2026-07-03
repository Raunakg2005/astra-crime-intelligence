import { useEffect, useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import { AlertOctagon, Gauge, Sparkles, Cpu, Trophy, GitBranch } from "lucide-react";
import { api, Anomaly, ModelInfo, ModelRegistry, RiskDistrict } from "../api";
import { PageHeader, Spinner, SeverityBadge, Section } from "../components/ui";

const bandColor = (b: string) => (b === "High" ? "#f43f5e" : b === "Medium" ? "#fbbf24" : "#34d399");

export default function Predictive() {
  const [risk, setRisk] = useState<RiskDistrict[]>([]);
  const [anoms, setAnoms] = useState<Anomaly[]>([]);
  const [flagged, setFlagged] = useState<{ n: number; total: number }>();
  const [model, setModel] = useState<ModelInfo>();
  const [reg, setReg] = useState<ModelRegistry>();

  useEffect(() => {
    api.risk().then(setRisk);
    api.modelInfo().then(setModel);
    api.modelRegistry().then(setReg);
    api.anomalies(30).then((a) => {
      setAnoms(a.anomalies);
      setFlagged({ n: a.n_flagged, total: a.total_cases });
    });
  }, []);

  if (!risk.length) return <div className="p-8"><Spinner /></div>;

  const clf = reg?.tasks?.risk_classifier;

  const scatter = risk.map((r) => ({
    x: r.recent_30d,
    y: r.trend_pct,
    z: r.risk_score,
    name: r.district,
    band: r.risk_band,
  }));

  return (
    <div className="p-6 md:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        title="Predictive Intelligence & Anomaly AI"
        subtitle="District risk scoring (Zia AutoML) · Isolation-Forest anomaly detection"
        right={
          flagged && (
            <div className="chip">
              <Sparkles className="h-3.5 w-3.5 text-accent-violet" />
              {flagged.n} anomalies / {flagged.total.toLocaleString()} cases
            </div>
          )
        }
      />

      {/* model card — MLOps transparency */}
      {model?.risk && (
        <div className="card card-pad mb-5 animate-fadeUp">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <Cpu className="h-4 w-4 text-accent-green" />
            <span className="text-sm font-semibold text-slate-200">Model card</span>
            {clf && (
              <span className="chip !py-0.5">
                <Trophy className="h-3 w-3 text-accent-amber" /> champion: {clf.family} · v{clf.champion_version}
              </span>
            )}
            {clf?.cv?.n_candidates && (
              <span className="chip !py-0.5">
                {clf.cv.n_candidates} families · {clf.cv.n_splits}-fold time-series CV
              </span>
            )}
            {reg?.pipeline?.gpu && (
              <span className="chip !py-0.5 !border-accent-green/40 !text-accent-green">GPU · {reg.pipeline.device}</span>
            )}
            {reg?.pipeline?.mlflow && <span className="chip !py-0.5">MLflow tracked</span>}
            {clf && (
              <span className="text-[11px] text-slate-500 ml-auto">
                {(clf.n_train ?? 0).toLocaleString()} train / {(clf.n_holdout ?? 0).toLocaleString()} hold-out rows
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Metric label="Risk ROC-AUC" value={model.risk.classifier.roc_auc} good />
            <Metric label="Precision" value={model.risk.classifier.precision} />
            <Metric label="Forecast MAE" value={model.risk.regressor.mae} sub={`vs ${model.risk.regressor.baseline_mae_lag1} baseline`} good />
            <Metric label="Forecast R²" value={model.risk.regressor.r2} good />
            <Metric label="Anomalies" value={model.anomaly?.flagged ?? "—"} sub={`/ ${model.anomaly?.n_cases?.toLocaleString() ?? ""}`} />
          </div>
          {clf?.cv?.leaderboard && (
            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <span className="stat-label flex items-center gap-1"><GitBranch className="h-3 w-3" /> families compared:</span>
              {clf.cv.leaderboard.map((l, i) => (
                <span
                  key={l.family}
                  className={`badge ${i === 0 ? "bg-accent-green/15 text-accent-green border border-accent-green/30" : "bg-ink-700 text-slate-400"}`}
                >
                  {l.family} · {l.cv_score}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* risk scatter */}
        <Section title="Risk landscape — volume × trend × score">
          <ResponsiveContainer width="100%" height={330}>
            <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: -10 }}>
              <CartesianGrid stroke="#1c2740" />
              <XAxis
                type="number"
                dataKey="x"
                name="Recent 30d"
                tick={{ fill: "#64748b", fontSize: 11 }}
                label={{ value: "Recent 30d volume", position: "insideBottom", offset: -2, fill: "#64748b", fontSize: 11 }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Trend %"
                tick={{ fill: "#64748b", fontSize: 11 }}
                label={{ value: "Trend %", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }}
              />
              <ZAxis type="number" dataKey="z" range={[40, 500]} />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                contentStyle={{ background: "#131c30", border: "1px solid #293654", borderRadius: 12 }}
                formatter={(v: any, n: any) => [v, n]}
                labelFormatter={() => ""}
                content={({ payload }) =>
                  payload && payload[0] ? (
                    <div className="card card-pad !p-2.5 text-xs">
                      <div className="font-semibold text-white">{payload[0].payload.name}</div>
                      <div className="text-slate-400">risk {payload[0].payload.z} · {payload[0].payload.band}</div>
                    </div>
                  ) : null
                }
              />
              <Scatter data={scatter}>
                {scatter.map((s, i) => (
                  <Cell key={i} fill={bandColor(s.band)} fillOpacity={0.75} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </Section>

        {/* risk ranking */}
        <Section title="District risk ranking" right={<Gauge className="h-4 w-4 text-accent-amber" />}>
          <div className="space-y-2 max-h-[330px] overflow-y-auto pr-1">
            {risk.slice(0, 12).map((r, i) => (
              <div key={r.district_id} className="flex items-center gap-3">
                <span className="w-5 text-xs font-mono text-slate-500">{i + 1}</span>
                <span className="w-32 text-sm text-slate-200 truncate">{r.district}</span>
                <div className="flex-1 h-2.5 rounded-full bg-ink-700 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${r.risk_score}%`, background: bandColor(r.risk_band) }} />
                </div>
                {r.predicted_next_week !== undefined && (
                  <span className="w-16 text-right text-[10px] font-mono text-accent-cyan" title="predicted FIRs next week">
                    ~{r.predicted_next_week}/wk
                  </span>
                )}
                <span className="w-9 text-right text-xs font-mono text-white">{r.risk_score}</span>
                <SeverityBadge severity={r.risk_band} />
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* anomaly radar */}
      <div className="card mt-5">
        <div className="flex items-center gap-2 px-5 pt-4 pb-1">
          <AlertOctagon className="h-4 w-4 text-accent-red" />
          <h2 className="text-sm font-semibold text-slate-200">Anomaly radar — cases deviating from behavioural norms</h2>
        </div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {anoms.map((a) => (
            <div key={a.case_id} className="rounded-xl border border-ink-700 bg-ink-800/40 p-3 animate-fadeUp">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-white">{a.crime}</span>
                <span className="badge bg-accent-red/15 text-accent-red">score {a.score}</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">{a.district} · {a.date}</div>
              <div className="text-[10px] font-mono text-slate-500 mt-0.5">{a.crime_no}</div>
              <div className="mt-2 flex flex-wrap gap-1">
                {a.reasons.map((r, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-accent-red/10 text-accent-red border border-accent-red/20">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, sub, good }: { label: string; value: number | string; sub?: string; good?: boolean }) {
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-800/40 p-3">
      <div className="stat-label">{label}</div>
      <div className={`text-xl font-bold tabular-nums mt-1 ${good ? "text-accent-green" : "text-white"}`}>{value}</div>
      {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
