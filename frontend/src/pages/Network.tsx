import { useEffect, useRef, useState } from "react";
import cytoscape, { Core } from "cytoscape";
import coseBilkent from "cytoscape-cose-bilkent";
import { Users, MapPin, Fingerprint, Network as NetIcon, Crosshair } from "lucide-react";
import { api, Community, Ego, Offender } from "../api";
import { PageHeader, Spinner, Section } from "../components/ui";

cytoscape.use(coseBilkent as any);

export default function NetworkPage() {
  const [offenders, setOffenders] = useState<Offender[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [ego, setEgo] = useState<Ego | null>(null);
  const [meta, setMeta] = useState<{ nodes: number; edges: number }>();
  const cyEl = useRef<HTMLDivElement>(null);
  const cy = useRef<Core | null>(null);

  useEffect(() => {
    api.repeatOffenders(5, 30).then((o) => {
      setOffenders(o);
      if (o[0]) setSelected(o[0].name);
    });
    api.communities(12).then((c) => {
      setCommunities(c.communities);
      setMeta({ nodes: c.n_nodes, edges: c.n_edges });
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    api.ego(selected).then(setEgo);
  }, [selected]);

  // render cytoscape graph
  useEffect(() => {
    if (!ego || !cyEl.current) return;
    cy.current?.destroy();

    // Cap nodes for readability: the ego, its strongest co-accused, and top districts.
    // (A prolific offender can have hundreds of co-accused — a hairball is unreadable.)
    const egoNode = ego.nodes.filter((n) => n.kind === "ego");
    const coAccused = ego.nodes
      .filter((n) => n.kind === "co-accused")
      .sort((a, b) => (b.shared_cases ?? 0) - (a.shared_cases ?? 0))
      .slice(0, 24);
    const districts = ego.nodes
      .filter((n) => n.kind === "location")
      .sort((a, b) => b.cases - a.cases)
      .slice(0, 12);
    const keptIds = new Set([...egoNode, ...coAccused, ...districts].map((n) => n.id));

    const nodes = [...egoNode, ...coAccused, ...districts].map((n) => ({
      data: {
        id: n.id,
        label: n.type === "district" ? n.id.replace("district:", "") : n.id,
        kind: n.kind,
        cases: n.cases,
      },
    }));
    const edges = ego.edges
      .filter((e) => keptIds.has(e.source) && keptIds.has(e.target))
      .map((e, i) => ({
        data: { id: `e${i}`, source: e.source, target: e.target, weight: e.weight, label: e.label },
      }));

    const c = cytoscape({
      container: cyEl.current,
      minZoom: 0.3,
      maxZoom: 2.5,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            color: "#e2e8f0",
            "font-size": 10,
            "font-weight": 600,
            "text-outline-color": "#0b1120",   // readable labels on dark
            "text-outline-width": 2.2,
            "text-valign": "bottom",
            "text-margin-y": 4,
            "background-color": "#38bdf8",
            "border-width": 2,
            "border-color": "#0b1120",
            width: (n: any) => 16 + Math.min(n.data("cases") || 1, 26),
            height: (n: any) => 16 + Math.min(n.data("cases") || 1, 26),
          },
        },
        { selector: 'node[kind="ego"]', style: { "background-color": "#f43f5e", "border-color": "#fb7185", "border-width": 3, "font-size": 12, width: 46, height: 46, "z-index": 20 } },
        { selector: 'node[kind="co-accused"]', style: { "background-color": "#a78bfa" } },
        { selector: 'node[kind="location"]', style: { "background-color": "#34d399", shape: "round-rectangle", "font-size": 9 } },
        {
          selector: "edge",
          style: {
            width: (e: any) => 1.2 + Math.min(e.data("weight") || 1, 6),
            "line-color": "#3b4a63",
            "line-opacity": 0.55,
            "curve-style": "bezier",   // undirected: co-offending is mutual (no arrowheads)
          },
        },
        { selector: "node:selected", style: { "border-color": "#22d3ee", "border-width": 3.5 } },
      ],
      layout: {
        // radial: ego at centre, co-accused in the inner ring, districts on the outer ring
        name: "concentric",
        concentric: (n: any) => (n.data("kind") === "ego" ? 3 : n.data("kind") === "co-accused" ? 2 : 1),
        levelWidth: () => 1,
        minNodeSpacing: 24,
        padding: 26,
        animate: false,
      } as any,
    });
    c.on("tap", "node", (evt) => {
      const id = evt.target.id();
      if (!id.startsWith("district:") && id !== selected) setSelected(id);
    });
    c.ready(() => c.fit(undefined, 30));
    cy.current = c;
    return () => c.destroy();
  }, [ego]);

  return (
    <div className="p-6 md:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        title="Criminal Link & Network Analysis"
        subtitle="Co-offending graph · repeat-offender profiles · Louvain community detection"
        right={
          meta && (
            <div className="chip">
              <NetIcon className="h-3.5 w-3.5 text-accent-violet" />
              {meta.nodes} nodes · {meta.edges} links
            </div>
          )
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-[300px_1fr_320px] gap-5">
        {/* repeat offenders list */}
        <div className="card flex flex-col max-h-[640px]">
          <div className="px-4 pt-3 pb-2 stat-label flex items-center gap-2">
            <Fingerprint className="h-3.5 w-3.5" /> Repeat offenders
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5">
            {offenders.map((o) => (
              <button
                key={o.name}
                onClick={() => setSelected(o.name)}
                className={`w-full text-left rounded-xl p-2.5 border transition-colors ${
                  selected === o.name
                    ? "border-accent-red/50 bg-accent-red/10"
                    : "border-ink-700 bg-ink-800/40 hover:bg-ink-700/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white truncate">{o.name}</span>
                  <span className="text-[11px] font-mono text-accent-red">{o.cases}</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">{o.primary_mo}</div>
                <div className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                  <MapPin className="h-2.5 w-2.5" /> {o.districts} districts
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* graph */}
        <div className="card overflow-hidden relative min-h-[640px]">
          {ego ? (
            <>
              <div className="absolute top-3 left-3 z-10 card card-pad !p-3">
                <div className="flex items-center gap-2 text-sm font-bold text-white">
                  <Crosshair className="h-4 w-4 text-accent-red" /> {ego.ego}
                </div>
                <div className="grid grid-cols-3 gap-3 mt-2 text-center">
                  <Stat v={ego.profile.total_cases} l="cases" />
                  <Stat v={ego.profile.districts} l="districts" />
                  <Stat v={ego.profile.co_offenders} l="co-accused" />
                </div>
                <div className="text-[11px] text-slate-400 mt-2">
                  MO: <span className="text-accent-violet">{ego.profile.primary_mo}</span>
                </div>
              </div>
              <div ref={cyEl} className="absolute inset-0" />
            </>
          ) : (
            <Spinner label="Building ego network…" />
          )}
        </div>

        {/* communities */}
        <div className="card flex flex-col max-h-[640px]">
          <div className="px-4 pt-3 pb-2 stat-label flex items-center gap-2">
            <Users className="h-3.5 w-3.5" /> Organised networks
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
            {communities.map((c) => (
              <div key={c.community_id} className="rounded-xl border border-ink-700 bg-ink-800/40 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-white">Ring #{c.community_id}</span>
                  <span className="badge bg-accent-violet/15 text-accent-violet">{c.size} members</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1.5">
                  {c.total_cases} cases · {c.districts_spanned} districts
                </div>
                <div className="text-[11px] mt-0.5 text-accent-violet">{c.dominant_mo}</div>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {c.members.slice(0, 3).map((m) => (
                    <button
                      key={m}
                      onClick={() => setSelected(m)}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-ink-700 text-slate-300 hover:text-white"
                    >
                      {m}
                    </button>
                  ))}
                  {c.members.length > 3 && (
                    <span className="text-[10px] text-slate-500 px-1">+{c.members.length - 3}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ v, l }: { v: number; l: string }) {
  return (
    <div>
      <div className="text-lg font-bold text-white tabular-nums">{v}</div>
      <div className="text-[9px] uppercase tracking-wide text-slate-500">{l}</div>
    </div>
  );
}
