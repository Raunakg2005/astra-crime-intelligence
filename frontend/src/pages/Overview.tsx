import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { FileText, ShieldAlert, CheckCircle2, Radar, AlertTriangle, TrendingUp } from "lucide-react";
import { api, Alert, District, Kpis, TimeSeries, headColor } from "../api";
import { PageHeader, KpiCard, Spinner, SeverityBadge, Section } from "../components/ui";

export default function Overview() {
  const [kpis, setKpis] = useState<Kpis>();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ts, setTs] = useState<TimeSeries>();
  const [districts, setDistricts] = useState<District[]>([]);

  useEffect(() => {
    api.kpis().then(setKpis);
    api.trends(2).then(setAlerts);
    api.timeseries().then(setTs);
    api.districts().then(setDistricts);
  }, []);

  if (!kpis || !ts) return <div className="p-8"><Spinner /></div>;

  const monthly = ts.monthly.map((m) => ({ ...m, label: m.month.slice(2) }));
  const heads = Object.entries(ts.by_head)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));
  const topDistricts = districts.slice(0, 8);

  return (
    <div className="p-6 md:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        title="State Intelligence Overview"
        subtitle="Karnataka State Police · State Crime Records Bureau"
        right={
          <div className="chip">
            <Radar className="h-3.5 w-3.5 text-accent" /> Live · {kpis.districts} districts
          </div>
        }
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total FIRs" value={kpis.total_cases.toLocaleString()} sub="all records"
          accent="#38bdf8" icon={<FileText className="h-4 w-4" />} />
        <KpiCard label="Last 30 days" value={kpis.cases_last_30d.toLocaleString()} delta={kpis.mom_change_pct}
          sub="vs prev 30d" accent="#22d3ee" icon={<TrendingUp className="h-4 w-4" />} />
        <KpiCard label="Clearance rate" value={`${kpis.clearance_rate_pct}%`} sub="charge-sheeted / convicted"
          accent="#34d399" icon={<CheckCircle2 className="h-4 w-4" />} />
        <KpiCard label="Active red-zones" value={kpis.active_alerts} sub="emerging spikes"
          accent="#f43f5e" icon={<ShieldAlert className="h-4 w-4" />} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mt-5">
        {/* trend area chart */}
        <div className="xl:col-span-2">
          <Section title="Monthly FIR volume — statewide">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={monthly} margin={{ left: -18, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2740" />
                <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} interval={2} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#131c30", border: "1px solid #293654", borderRadius: 12 }}
                  labelStyle={{ color: "#e2e8f0" }}
                  itemStyle={{ color: "#38bdf8" }}
                />
                <Area type="monotone" dataKey="count" stroke="#38bdf8" strokeWidth={2} fill="url(#g1)" />
              </AreaChart>
            </ResponsiveContainer>
          </Section>
        </div>

        {/* emerging alerts */}
        <Section title="Emerging-trend alerts" right={<AlertTriangle className="h-4 w-4 text-accent-red" />}>
          <div className="space-y-2.5 max-h-[260px] overflow-y-auto pr-1">
            {alerts.length === 0 && <div className="text-xs text-slate-500 py-8 text-center">No active spikes.</div>}
            {alerts.map((a, i) => (
              <div key={i} className="rounded-xl border border-ink-700 bg-ink-800/50 p-3 animate-fadeUp">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm text-white">{a.district}</span>
                  <SeverityBadge severity={a.severity} />
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {a.top_subcrime} · <span style={{ color: headColor(a.crime_head) }}>{a.crime_head}</span>
                </div>
                <div className="mt-2 flex items-center gap-3 text-[11px] font-mono">
                  <span className="text-accent-red font-semibold">z {a.z_score}</span>
                  <span className="text-slate-400">
                    {a.recent_count} vs {a.baseline_avg} avg
                  </span>
                  {a.ratio && <span className="text-accent-amber">×{a.ratio}</span>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 mt-5">
        {/* crime head breakdown */}
        <Section title="Crime composition by major head">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={heads} layout="vertical" margin={{ left: 30, right: 20 }}>
              <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={140} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: "#131c30", border: "1px solid #293654", borderRadius: 12 }}
                labelStyle={{ color: "#e2e8f0" }}
                itemStyle={{ color: "#e2e8f0" }}
                cursor={{ fill: "#1c2740" }}
              />
              <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                {heads.map((h) => (
                  <Cell key={h.name} fill={headColor(h.name)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        {/* top districts */}
        <Section title="Top districts by FIR volume">
          <div className="space-y-2">
            {topDistricts.map((d, i) => {
              const max = topDistricts[0].total_cases;
              return (
                <div key={d.district_id} className="flex items-center gap-3">
                  <span className="w-5 text-xs text-slate-500 font-mono">{i + 1}</span>
                  <span className="w-36 text-sm text-slate-200 truncate">{d.district}</span>
                  <div className="flex-1 h-2.5 rounded-full bg-ink-700 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(d.total_cases / max) * 100}%`,
                        background: headColor(d.top_crime_head),
                      }}
                    />
                  </div>
                  <span className="w-12 text-right text-xs font-mono text-slate-300">{d.total_cases}</span>
                  <span className="w-14 text-right text-[11px] text-accent-green">{d.clearance_pct}%</span>
                </div>
              );
            })}
          </div>
        </Section>
      </div>
    </div>
  );
}
