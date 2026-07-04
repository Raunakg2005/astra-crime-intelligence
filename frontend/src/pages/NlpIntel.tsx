import { useEffect, useState } from "react";
import { ScanText, Sparkles, Cpu, Tags, Layers3, Send, Trophy } from "lucide-react";
import { api, headColor, MoCluster, NlpClassification, NlpModelInfo } from "../api";
import { PageHeader, Spinner, Section } from "../components/ui";

const EXAMPLES = [
  "The accused threatened the complainant with a knife near the bus stand and snatched a gold chain before fleeing on a motorcycle.",
  "Complainant received a fraudulent call, shared an OTP on a link and lost Rs 2,00,000 from the bank account.",
  "A married woman alleged persistent harassment and cruelty by her husband and in-laws over dowry demands.",
  "The accused was intercepted during patrolling and found in possession of ganja concealed in a scooter.",
  "House lock was found broken during the night and jewellery and a laptop were missing from the premises.",
];

export default function NlpIntel() {
  const [info, setInfo] = useState<NlpModelInfo>();
  const [clusters, setClusters] = useState<MoCluster[]>([]);
  const [text, setText] = useState(EXAMPLES[0]);
  const [result, setResult] = useState<NlpClassification>();
  const [busy, setBusy] = useState(false);
  const [model, setModel] = useState("");   // "" = champion

  useEffect(() => {
    api.nlpModelInfo().then(setInfo);
    api.nlpClusters().then((c) => setClusters(c.clusters));
    classify(EXAMPLES[0], "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const classify = (t: string, m: string) => {
    setBusy(true);
    api.nlpClassify(t, m || undefined).then(setResult).finally(() => setBusy(false));
  };

  if (!info) return <div className="p-8"><Spinner label="Loading NLP model…" /></div>;

  return (
    <div className="p-6 md:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        title="NLP Crime-Text Intelligence"
        subtitle="Classify FIR narratives · entity extraction · modus-operandi clustering"
        right={
          <div className="flex gap-2 flex-wrap justify-end">
            <span className="chip"><Trophy className="h-3.5 w-3.5 text-accent-amber" /> {info.champion}</span>
            <span className="chip">{info.leaderboard.length} models compared</span>
            {info.gpu && <span className="chip !border-accent-green/40 !text-accent-green">GPU · {info.device}</span>}
          </div>
        }
      />

      {/* metrics strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <Metric label="Accuracy" value={`${(info.metrics.accuracy * 100).toFixed(1)}%`} good />
        <Metric label="Macro-F1" value={info.metrics.macro_f1} good />
        <Metric label="Weighted-F1" value={info.metrics.weighted_f1} />
        <Metric label="Crime classes" value={info.metrics.n_classes} sub={`${info.data_rows.toLocaleString()} narratives`} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
        {/* live classifier */}
        <Section title="Live classifier — paste a FIR narrative">
          <div className="flex flex-wrap gap-1.5 mb-3">
            {EXAMPLES.map((e, i) => (
              <button key={i} onClick={() => { setText(e); classify(e, model); }}
                className="text-[11px] px-2 py-1 rounded-lg bg-ink-700/60 border border-ink-600 text-slate-400 hover:text-white">
                example {i + 1}
              </button>
            ))}
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            className="w-full bg-ink-800 border border-ink-600 rounded-xl p-3 text-sm text-slate-200 resize-none focus:outline-none focus:border-accent"
            placeholder="Describe the incident…"
          />
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <button
              onClick={() => classify(text, model)}
              disabled={busy || !text.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-accent/15 border border-accent/40 text-accent text-sm font-medium hover:bg-accent/25 disabled:opacity-50"
            >
              {busy ? <div className="h-4 w-4 rounded-full border-2 border-accent/40 border-t-accent animate-spin" /> : <Send className="h-4 w-4" />}
              Classify
            </button>
            <span className="text-xs text-slate-500">with</span>
            <select
              value={model}
              onChange={(e) => { setModel(e.target.value); classify(text, e.target.value); }}
              className="bg-ink-800 border border-ink-600 rounded-lg px-2 py-1.5 text-xs text-slate-200"
            >
              <option value="">champion ({info.champion})</option>
              {info.leaderboard.map((m) => (
                <option key={m.family} value={m.family}>{m.family}</option>
              ))}
            </select>
            {result?.model && <span className="text-[11px] text-slate-500">→ ran <span className="text-accent-cyan">{result.model}</span></span>}
          </div>

          {result && !result.error && (
            <div className="mt-4 animate-fadeUp">
              <div className="flex items-center gap-2 mb-2">
                <ScanText className="h-4 w-4 text-accent" />
                <span className="text-sm text-slate-400">Predicted crime head</span>
              </div>
              <div className="space-y-2">
                {result.predictions.map((p) => (
                  <div key={p.crime_head} className="flex items-center gap-3">
                    <span className="w-52 text-sm truncate" style={{ color: headColor(p.crime_head) }}>{p.crime_head}</span>
                    <div className="flex-1 h-2.5 rounded-full bg-ink-700 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${p.confidence * 100}%`, background: headColor(p.crime_head) }} />
                    </div>
                    <span className="w-12 text-right text-xs font-mono text-slate-300">{(p.confidence * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center gap-2 mb-2">
                <Tags className="h-4 w-4 text-accent-violet" />
                <span className="text-sm text-slate-400">Extracted entities</span>
              </div>
              {Object.keys(result.entities).length === 0 ? (
                <span className="text-xs text-slate-500">No structured entities detected.</span>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(result.entities).flatMap(([type, vals]) =>
                    vals.map((v) => (
                      <span key={type + v} className="badge bg-accent-violet/15 text-accent-violet border border-accent-violet/30">
                        <span className="opacity-60">{type}:</span> {v}
                      </span>
                    )),
                  )}
                </div>
              )}
            </div>
          )}
        </Section>

        {/* model leaderboard */}
        <Section
          title={`Model bake-off (${info.leaderboard.length})`}
          right={<Cpu className="h-4 w-4 text-accent-green" />}
        >
          <div className="flex items-center gap-2 px-1 mb-1 text-[10px] uppercase tracking-wide text-slate-500">
            <span className="w-5" /><span className="w-28">model</span>
            <span className="flex-1">macro-F1 (hold-out)</span><span className="w-9 text-right">acc</span>
          </div>
          <div className="space-y-1.5 max-h-[340px] overflow-y-auto pr-1">
            {info.leaderboard.map((m, i) => {
              const score = m.macro_f1 ?? m.cv_score;
              const max = info.leaderboard[0].macro_f1 ?? info.leaderboard[0].cv_score;
              return (
                <div key={m.family} className="flex items-center gap-2">
                  <span className="w-5 text-[11px] font-mono text-slate-500">{i + 1}</span>
                  <span className="w-28 text-xs text-slate-300 truncate">{m.family}</span>
                  <div className="flex-1 h-2 rounded-full bg-ink-700 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${(score / max) * 100}%`, background: i === 0 ? "#34d399" : "#38bdf8" }} />
                  </div>
                  <span className="w-10 text-right text-[11px] font-mono text-slate-300">{score.toFixed(3)}</span>
                  <span className="w-9 text-right text-[10px] font-mono text-slate-500">
                    {m.accuracy ? `${(m.accuracy * 100).toFixed(0)}%` : ""}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-500 mt-3">
            {info.leaderboard.length} models trained & saved · ranked by hold-out macro-F1 · CV for selection.
          </p>
        </Section>
      </div>

      {/* MO clusters */}
      <div className="card mt-5">
        <div className="flex items-center gap-2 px-5 pt-4 pb-1">
          <Layers3 className="h-4 w-4 text-accent-cyan" />
          <h2 className="text-sm font-semibold text-slate-200">Modus-operandi clusters (unsupervised, from narratives)</h2>
        </div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {clusters.slice(0, 9).map((c) => (
            <div key={c.cluster} className="rounded-xl border border-ink-700 bg-ink-800/40 p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold" style={{ color: headColor(c.dominant_head) }}>
                  {c.dominant_head}
                </span>
                <span className="text-[11px] font-mono text-slate-400">{c.size.toLocaleString()}</span>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {c.top_terms.map((t) => (
                  <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-ink-700 text-slate-300">{t}</span>
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
    <div className="card card-pad">
      <div className="stat-label">{label}</div>
      <div className={`text-2xl font-bold tabular-nums mt-1 ${good ? "text-accent-green" : "text-white"}`}>{value}</div>
      {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
