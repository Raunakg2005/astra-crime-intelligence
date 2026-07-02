import { useEffect, useRef, useState } from "react";
import maplibregl, { Map as MLMap, Popup } from "maplibre-gl";
import { Layers, Flame, Building2, Filter, MapPin, Clock, Moon } from "lucide-react";
import { api, Cluster, District, Alert, headColor, HEAD_COLORS } from "../api";
import { PageHeader, Spinner, SeverityBadge } from "../components/ui";

const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    carto: {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution: "© OpenStreetMap © CARTO",
    },
  },
  layers: [{ id: "carto", type: "raster", source: "carto" }],
};

// Karnataka bounding box [west, south, east, north]
const KA_BOUNDS: [number, number, number, number] = [73.6, 11.4, 78.7, 18.6];

type Mode = "districts" | "hotspots";

export default function Geospatial() {
  const mapEl = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const [ready, setReady] = useState(false);

  const [mode, setMode] = useState<Mode>("districts");
  const [headFilter, setHeadFilter] = useState<string>("");
  const [districts, setDistricts] = useState<District[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selected, setSelected] = useState<District | null>(null);
  const [loading, setLoading] = useState(false);

  // init map once
  useEffect(() => {
    if (!mapEl.current || map.current) return;
    const m = new maplibregl.Map({
      container: mapEl.current,
      style: STYLE,
      center: [76.2, 15.0],
      zoom: 6,
      attributionControl: false,
    });
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    const fitKA = () => {
      m.resize();
      m.fitBounds(KA_BOUNDS, { padding: 24, duration: 0 });
    };
    m.on("load", () => {
      setReady(true);
      fitKA();
      // one more fit on the next frame, after the container's final layout settles
      requestAnimationFrame(fitKA);
      setTimeout(fitKA, 250);
    });
    map.current = m;

    // keep canvas sized to its responsive container (no re-fit → respects user zoom)
    const ro = new ResizeObserver(() => m.resize());
    ro.observe(mapEl.current);

    return () => {
      ro.disconnect();
      m.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    api.districts().then(setDistricts);
    api.trends(2.5).then(setAlerts);
  }, []);

  // load hotspots when in hotspot mode / filter changes
  useEffect(() => {
    if (mode !== "hotspots") return;
    setLoading(true);
    api
      .hotspots({ district_id: selected?.district_id, crime_head: headFilter || undefined })
      .then((h) => setClusters(h.clusters))
      .finally(() => setLoading(false));
  }, [mode, headFilter, selected]);

  // render markers
  useEffect(() => {
    if (!ready || !map.current) return;
    const m = map.current;
    markers.current.forEach((mk) => mk.remove());
    markers.current = [];

    if (mode === "districts") {
      const max = Math.max(...districts.map((d) => d.total_cases), 1);
      const alertIds = new Set(alerts.map((a) => a.district_id));
      districts.forEach((d) => {
        if (!d.lat) return;
        const size = 14 + (d.total_cases / max) * 42;
        const el = document.createElement("div");
        el.style.cssText = `width:${size}px;height:${size}px;border-radius:9999px;cursor:pointer;`;
        const col = headColor(d.top_crime_head);
        el.innerHTML = `
          <div style="width:100%;height:100%;border-radius:9999px;background:${col}33;border:2px solid ${col};
               display:grid;place-items:center;color:#fff;font-size:10px;font-weight:700;backdrop-filter:blur(2px)">
            ${d.total_cases}
          </div>
          ${alertIds.has(d.district_id)
            ? `<span style="position:absolute;inset:0;border-radius:9999px;border:2px solid #f43f5e;
                 animation:pulseRing 2s ease-out infinite"></span>`
            : ""}`;
        el.style.position = "relative";
        el.onclick = () => {
          setSelected(d);
          setMode("hotspots");
          m.flyTo({ center: [d.lng, d.lat], zoom: 10.5, duration: 900 });
        };
        const mk = new maplibregl.Marker({ element: el }).setLngLat([d.lng, d.lat]).addTo(m);
        markers.current.push(mk);
      });
    } else {
      const max = Math.max(...clusters.map((c) => c.count), 1);
      clusters.forEach((c) => {
        const size = 16 + (c.count / max) * 46;
        const hot = c.intensity >= 65;
        const col = hot ? "#f43f5e" : c.intensity >= 35 ? "#fb923c" : "#fbbf24";
        const el = document.createElement("div");
        el.style.cssText = `width:${size}px;height:${size}px;position:relative;cursor:pointer;`;
        el.innerHTML = `
          <div style="width:100%;height:100%;border-radius:9999px;background:${col}44;border:2px solid ${col}"></div>
          ${hot ? `<span style="position:absolute;inset:0;border-radius:9999px;border:2px solid ${col};
             animation:pulseRing 2s ease-out infinite"></span>` : ""}`;
        const popup = new Popup({ offset: 14, closeButton: false }).setHTML(
          `<b style="color:#fff">${c.dominant_crime}</b><br/>${c.count} incidents · ${c.district}<br/>
           peak ${c.peak_hour ?? "—"}:00 · ${c.night_share_pct}% night`,
        );
        const mk = new maplibregl.Marker({ element: el })
          .setLngLat([c.lng, c.lat])
          .setPopup(popup)
          .addTo(m);
        el.onmouseenter = () => mk.togglePopup();
        el.onmouseleave = () => mk.togglePopup();
        markers.current.push(mk);
      });
    }
  }, [ready, mode, districts, clusters, alerts]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 md:px-8 pt-6">
        <PageHeader
          title="Geospatial Command Center"
          subtitle="District drill-down · spatiotemporal hotspots (DBSCAN) · red-zone alerts"
          right={
            <div className="flex gap-2">
              <button
                onClick={() => { setMode("districts"); setSelected(null); map.current?.fitBounds(KA_BOUNDS, { padding: 30, duration: 800 }); }}
                className={`chip ${mode === "districts" ? "!border-accent !text-accent" : ""}`}
              >
                <Building2 className="h-3.5 w-3.5" /> Districts
              </button>
              <button
                onClick={() => setMode("hotspots")}
                className={`chip ${mode === "hotspots" ? "!border-accent-red !text-accent-red" : ""}`}
              >
                <Flame className="h-3.5 w-3.5" /> Hotspots
              </button>
            </div>
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px] gap-4 px-6 md:px-8 pb-6">
        {/* map — explicit height so MapLibre fitBounds has a real box to fit into */}
        <div className="card overflow-hidden relative h-[64vh]">
          <div ref={mapEl} className="absolute inset-0" />
          {loading && (
            <div className="absolute top-3 left-3 chip bg-ink-900/80 z-10">
              <div className="h-3 w-3 rounded-full border-2 border-ink-600 border-t-accent animate-spin" />
              clustering…
            </div>
          )}
          {/* legend */}
          <div className="absolute bottom-3 left-3 card card-pad !p-3 z-10 text-[11px] space-y-1">
            <div className="flex items-center gap-2 text-slate-300 font-semibold mb-1">
              <Layers className="h-3.5 w-3.5" /> {mode === "districts" ? "Top crime head" : "Hotspot intensity"}
            </div>
            {mode === "districts"
              ? Object.entries(HEAD_COLORS).slice(0, 5).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: v }} />
                    <span className="text-slate-400">{k.replace("Crimes Against ", "")}</span>
                  </div>
                ))
              : [["#f43f5e", "Critical"], ["#fb923c", "High"], ["#fbbf24", "Elevated"]].map(([v, k]) => (
                  <div key={k} className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: v }} />
                    <span className="text-slate-400">{k}</span>
                  </div>
                ))}
          </div>
        </div>

        {/* right panel */}
        <div className="flex flex-col gap-4 min-h-0 h-[64vh]">
          {mode === "hotspots" && (
            <div className="card card-pad">
              <div className="flex items-center gap-2 stat-label mb-2">
                <Filter className="h-3.5 w-3.5" /> Filter by crime head
              </div>
              <select
                value={headFilter}
                onChange={(e) => setHeadFilter(e.target.value)}
                className="w-full bg-ink-800 border border-ink-600 rounded-lg px-3 py-2 text-sm text-slate-200"
              >
                <option value="">All crime types</option>
                {Object.keys(HEAD_COLORS).map((h) => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
              {selected && (
                <div className="mt-3 text-xs text-slate-400">
                  Drilled into <span className="text-white font-semibold">{selected.district}</span>
                </div>
              )}
            </div>
          )}

          <div className="card flex-1 min-h-0 flex flex-col">
            <div className="px-4 pt-3 pb-2 stat-label">
              {mode === "districts" ? "Red-zone alerts" : `Hotspot clusters (${clusters.length})`}
            </div>
            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
              {mode === "districts"
                ? alerts.map((a, i) => (
                    <div key={i} className="rounded-xl border border-ink-700 bg-ink-800/50 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white">{a.district}</span>
                        <SeverityBadge severity={a.severity} />
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{a.top_subcrime}</div>
                      <div className="text-[11px] font-mono text-accent-red mt-1">
                        z {a.z_score} · {a.recent_count} vs {a.baseline_avg}
                      </div>
                    </div>
                  ))
                : clusters.map((c) => (
                    <div key={c.cluster_id} className="rounded-xl border border-ink-700 bg-ink-800/50 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5 text-accent-red" />
                          {c.dominant_crime}
                        </span>
                        <span className="text-xs font-mono text-slate-300">{c.count}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{c.peak_hour ?? "—"}:00</span>
                        <span className="flex items-center gap-1"><Moon className="h-3 w-3" />{c.night_share_pct}%</span>
                        <span>{c.district}</span>
                      </div>
                      <div className="mt-2 h-1.5 rounded-full bg-ink-700 overflow-hidden">
                        <div className="h-full rounded-full bg-accent-red" style={{ width: `${c.intensity}%` }} />
                      </div>
                    </div>
                  ))}
              {mode === "hotspots" && clusters.length === 0 && !loading && (
                <div className="text-xs text-slate-500 text-center py-8">No clusters for this filter.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
