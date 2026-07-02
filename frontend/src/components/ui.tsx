import { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export function PageHeader({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

export function KpiCard({
  label,
  value,
  sub,
  delta,
  accent = "#38bdf8",
  icon,
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  delta?: number;
  accent?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="card card-pad animate-fadeUp relative overflow-hidden">
      <div
        className="absolute -right-6 -top-6 h-20 w-20 rounded-full opacity-20 blur-xl"
        style={{ background: accent }}
      />
      <div className="flex items-center justify-between">
        <div className="stat-label">{label}</div>
        {icon && <div style={{ color: accent }}>{icon}</div>}
      </div>
      <div className="mt-2 text-3xl font-bold text-white tabular-nums">{value}</div>
      <div className="mt-1.5 flex items-center gap-2 text-xs">
        {delta !== undefined && (
          <span
            className={`badge ${
              delta >= 0 ? "bg-accent-red/15 text-accent-red" : "bg-accent-green/15 text-accent-green"
            }`}
          >
            {delta >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {Math.abs(delta)}%
          </span>
        )}
        {sub && <span className="text-slate-400">{sub}</span>}
      </div>
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-slate-400 text-sm">
      <div className="h-5 w-5 rounded-full border-2 border-ink-600 border-t-accent animate-spin" />
      {label ?? "Loading intelligence…"}
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: "bg-accent-red/20 text-accent-red border border-accent-red/40",
    high: "bg-accent-amber/20 text-accent-amber border border-accent-amber/40",
    elevated: "bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/30",
    High: "bg-accent-red/20 text-accent-red border border-accent-red/40",
    Medium: "bg-accent-amber/20 text-accent-amber border border-accent-amber/40",
    Low: "bg-accent-green/15 text-accent-green border border-accent-green/30",
  };
  return <span className={`badge ${map[severity] ?? "bg-ink-700 text-slate-300"}`}>{severity}</span>;
}

export function Section({ title, children, right }: { title: string; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between px-5 pt-4 pb-2">
        <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
        {right}
      </div>
      <div className="px-5 pb-5">{children}</div>
    </div>
  );
}
