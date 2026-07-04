import { useEffect, useRef, useState } from "react";
import maplibregl, { Map as MLMap, Popup } from "maplibre-gl";
import { Filter, Flame, Layers, MapPin, Search, X } from "lucide-react";
import { api, Alert, District, GeoPlace, IncidentFC, HEAD_COLORS, headColor } from "../api";
import { PageHeader, SeverityBadge } from "../components/ui";
import { useTheme } from "../theme";

// Karnataka bounding box [west, south, east, north]
const KA_BOUNDS: [number, number, number, number] = [73.6, 11.4, 78.7, 18.6];

// Theme-aware basemap.
//  * LIGHT → OpenStreetMap standard: the densest free basemap — labels VILLAGES, areas,
//    localities and STREET names right down to street level (CARTO/others thin out).
//  * DARK  → CARTO "dark_all": dark-themed with town/district labels (free dark tiles are
//    sparser at village level; a keyed provider like MapTiler gives a dense dark map).
// Incident layers render on top. No glyphs — cluster counts are DOM labels.
const CARTO = (style: string) =>
  ["a", "b", "c"].map((s) => `https://${s}.basemaps.cartocdn.com/${style}/{z}/{x}/{y}.png`);
const OSM = ["a", "b", "c"].map((s) => `https://${s}.tile.openstreetmap.org/{z}/{x}/{y}.png`);
const mapStyle = (theme: "dark" | "light"): maplibregl.StyleSpecification => ({
  version: 8,
  sources: {
    base: theme === "light"
      ? { type: "raster", tileSize: 256, maxzoom: 19, attribution: "© OpenStreetMap contributors", tiles: OSM }
      : { type: "raster", tileSize: 256, attribution: "© OpenStreetMap © CARTO", tiles: CARTO("dark_all") },
  },
  layers: [{ id: "carto-base", type: "raster", source: "base" }],
});

// crime-head -> colour, as a MapLibre "match" expression for the point layer
const headColorExpr: any = [
  "match", ["get", "head"],
  ...Object.entries(HEAD_COLORS).flatMap(([k, v]) => [k, v]),
  "#94a3b8",
];

const EMPTY: IncidentFC = { type: "FeatureCollection", features: [], count: 0 };

export default function Geospatial() {
  const mapEl = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const all = useRef<IncidentFC>(EMPTY);       // full dataset, filtered client-side
  const built = useRef(false);
  const countMarkers = useRef<Record<string, maplibregl.Marker>>({});
  const districts = useRef<District[]>([]);
  const labelMarkers = useRef<maplibregl.Marker[]>([]);
  const labelsBuilt = useRef(false);
  const firstTheme = useRef(true);
  const [headFilter, setHeadFilter] = useState("");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [places, setPlaces] = useState<GeoPlace[]>([]);
  const [searching, setSearching] = useState(false);
  const { theme } = useTheme();

  // District-name labels (glyph-free DOM markers) — the basemap's own labels are too
  // faint at state zoom, so we render our own from the district centroids. Hidden when
  // zoomed in past street level to avoid clutter.
  const addLabels = () => {
    const m = map.current;
    if (!m || !m.isStyleLoaded() || labelsBuilt.current || districts.current.length === 0) return;
    labelsBuilt.current = true;
    for (const d of districts.current) {
      if (d.lat == null) continue;
      const el = document.createElement("div");
      el.className = "district-label";
      el.textContent = d.district;
      labelMarkers.current.push(new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([d.lng, d.lat]).addTo(m));
    }
    updateLabelVisibility();
  };
  const updateLabelVisibility = () => {
    const z = map.current?.getZoom() ?? 0;
    const show = z <= 9.5;
    for (const mk of labelMarkers.current) mk.getElement().style.opacity = show ? "1" : "0";
  };

  const flyToDistrict = (d: District) => {
    setQuery(""); setPlaces([]);
    map.current?.flyTo({ center: [d.lng, d.lat], zoom: 9.2, duration: 900 });
  };

  // pick a sensible zoom for the granularity of an OSM place result
  const zoomForType = (t: string) => {
    if (/(road|residential|pedestrian|street|footway|path|track|service|primary|secondary|tertiary)/.test(t)) return 14.5;
    if (/(neighbourhood|suburb|quarter|hamlet|village|locality|isolated_dwelling|allotments)/.test(t)) return 13;
    if (/town/.test(t)) return 11.5;
    if (/(city|municipality|county|state_district)/.test(t)) return 10;
    return 12.5;
  };
  const flyToPlace = (p: GeoPlace) => {
    setQuery(""); setPlaces([]);
    map.current?.flyTo({ center: [p.lng, p.lat], zoom: zoomForType(p.type), duration: 900 });
  };

  // Idempotently add the incident source + layers to the live, style-loaded map.
  // Called from the map's own 'load' handler AND after data arrives (whichever is
  // last) — this sidesteps the StrictMode double-mount / style-not-ready race that
  // was leaving the layers unattached (blank map).
  const buildLayers = () => {
    const m = map.current;
    if (!m || !m.isStyleLoaded() || built.current || all.current.features.length === 0) return;
    built.current = true;

    m.addSource("incidents", {
      type: "geojson", data: all.current as any,
      cluster: true, clusterRadius: 46, clusterMaxZoom: 13,
    });

    // heatmap glow at low zoom (fades out as clusters take over) — inserted BELOW the
    // labels reference layer so place/road names stay readable on top of the data.
    m.addLayer({
      id: "inc-heat", type: "heatmap", source: "incidents", maxzoom: 11,
      paint: {
        "heatmap-weight": 0.6,
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 4, 0.6, 11, 2],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 4, 12, 11, 26],
        "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 7, 0.55, 11, 0],
        "heatmap-color": [
          "interpolate", ["linear"], ["heatmap-density"],
          0, "rgba(0,0,0,0)", 0.2, "#1d4ed8", 0.4, "#22d3ee",
          0.6, "#fbbf24", 0.8, "#fb923c", 1, "#f43f5e",
        ],
      },
    });

    // clustered circles (size + colour by point count)
    m.addLayer({
      id: "clusters", type: "circle", source: "incidents", filter: ["has", "point_count"],
      paint: {
        "circle-color": ["step", ["get", "point_count"], "#38bdf8", 50, "#22d3ee", 200, "#fbbf24", 600, "#f43f5e"],
        "circle-radius": ["step", ["get", "point_count"], 15, 50, 20, 200, 26, 600, 34],
        "circle-opacity": 0.85,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#0b1120",
      },
    });
    // individual incidents (real coordinates) — visible once declustered on zoom-in
    m.addLayer({
      id: "inc-point", type: "circle", source: "incidents", filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": headColorExpr,
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 3, 14, 5, 17, 8],
        "circle-stroke-width": 1,
        "circle-stroke-color": "#0b1120",
        "circle-opacity": 0.9,
      },
    });

    // interactions
    m.on("click", "clusters", (e) => {
      const f = e.features?.[0];
      if (!f) return;
      const src = m.getSource("incidents") as maplibregl.GeoJSONSource;
      src.getClusterExpansionZoom((f.properties as any).cluster_id).then((z) => {
        m.easeTo({ center: (f.geometry as any).coordinates, zoom: z + 0.3, duration: 600 });
      });
    });
    m.on("click", "inc-point", (e) => {
      const f = e.features?.[0];
      if (!f) return;
      const p = f.properties as any;
      new Popup({ offset: 12, closeButton: false })
        .setLngLat((f.geometry as any).coordinates)
        .setHTML(
          `<div style="min-width:170px">
             <b style="color:#fff">${p.crime}</b>
             <div style="color:#94a3b8;margin-top:2px">${p.head}</div>
             <div style="margin-top:6px;color:#cbd5e1">${p.district} · ${p.date}</div>
             <div style="color:#64748b;font-family:monospace;font-size:10px;margin-top:2px">${p.cn}</div>
           </div>`,
        )
        .addTo(m);
    });
    for (const layer of ["clusters", "inc-point"]) {
      m.on("mouseenter", layer, () => (m.getCanvas().style.cursor = "pointer"));
      m.on("mouseleave", layer, () => (m.getCanvas().style.cursor = ""));
    }

    // glyph-free cluster-count labels: DOM markers synced to rendered clusters
    // (the official MapLibre HTML-cluster pattern — no external glyph dependency).
    const updateCounts = () => {
      // getSource first: isSourceLoaded() THROWS if the source is absent (which it is
      // during the theme-swap window, before buildLayers re-adds it) → console spam.
      if (!m.getSource("incidents") || !m.isSourceLoaded("incidents")) return;
      const feats = m.querySourceFeatures("incidents");
      const present: Record<string, boolean> = {};
      for (const f of feats) {
        const p = f.properties as any;
        if (!p.cluster) continue;
        const id = String(p.cluster_id);
        present[id] = true;
        if (!countMarkers.current[id]) {
          const el = document.createElement("div");
          el.className = "cluster-count";
          el.textContent = p.point_count_abbreviated;
          countMarkers.current[id] = new maplibregl.Marker({ element: el })
            .setLngLat((f.geometry as any).coordinates)
            .addTo(m);
        }
      }
      for (const id in countMarkers.current) {
        if (!present[id]) { countMarkers.current[id].remove(); delete countMarkers.current[id]; }
      }
    };
    m.on("render", updateCounts);
  };

  // ---- init map once ----
  useEffect(() => {
    if (!mapEl.current || map.current) return;
    const m = new maplibregl.Map({
      container: mapEl.current, style: mapStyle(theme),
      center: [76.2, 15.0], zoom: 6, minZoom: 4, attributionControl: false,
    });
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    const fitKA = () => { m.resize(); m.fitBounds(KA_BOUNDS, { padding: 24, duration: 0 }); };
    m.on("load", () => { fitKA(); requestAnimationFrame(fitKA); setTimeout(fitKA, 250); buildLayers(); addLabels(); });
    m.on("zoom", updateLabelVisibility);
    map.current = m;
    const ro = new ResizeObserver(() => m.resize());
    ro.observe(mapEl.current);
    return () => {
      ro.disconnect();
      Object.values(countMarkers.current).forEach((mk) => mk.remove());
      labelMarkers.current.forEach((mk) => mk.remove());
      countMarkers.current = {}; labelMarkers.current = []; labelsBuilt.current = false;
      m.remove(); map.current = null; built.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- load data, then build layers ----
  useEffect(() => {
    api.trends(2.5).then(setAlerts);
    api.districts().then((d) => { districts.current = d; addLabels(); });
    api.incidents().then((fc) => { all.current = fc; setCount(fc.count); setLoading(false); buildLayers(); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- crime-head filter -> update source data ----
  useEffect(() => {
    const src = map.current?.getSource("incidents") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    const filtered: IncidentFC = headFilter
      ? { type: "FeatureCollection", count: 0,
          features: all.current.features.filter((f) => f.properties.head === headFilter) }
      : all.current;
    src.setData(filtered as any);
  }, [headFilter]);

  // ---- theme change -> swap ONLY the basemap raster source+layer, in place ----
  // The old approach called m.setStyle(), which WIPES every custom source/layer + all DOM
  // markers, then re-added them on the `styledata` event — a race that intermittently left
  // the map with just the basemap and no data/markers (the bug). Here we remove and re-add
  // only the `base` raster source + `carto-base` layer; the `incidents` source, every data
  // layer, and all DOM markers (cluster counts, district labels) are never touched, so they
  // can't disappear. The markers restyle themselves via the `.light` CSS-variable flip.
  useEffect(() => {
    const m = map.current;
    if (firstTheme.current) { firstTheme.current = false; return; }   // init effect owns first paint
    if (!m) return;
    const swapBase = () => {
      if (!m.isStyleLoaded()) { m.once("styledata", swapBase); return; }
      const spec = mapStyle(theme).sources.base;
      if (m.getLayer("carto-base")) m.removeLayer("carto-base");
      if (m.getSource("base")) m.removeSource("base");
      m.addSource("base", spec as any);
      // re-insert the basemap UNDER the data layers so incidents/labels stay on top
      const firstData = ["inc-heat", "clusters", "inc-point"].find((id) => m.getLayer(id));
      m.addLayer({ id: "carto-base", type: "raster", source: "base" }, firstData);
    };
    swapBase();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme]);

  // ---- debounced free-text place search (villages / areas / streets via OSM) ----
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) { setPlaces([]); setSearching(false); return; }
    setSearching(true);
    const t = setTimeout(() => {
      api.geocode(q)
        .then(setPlaces)
        .catch(() => setPlaces([]))
        .finally(() => setSearching(false));
    }, 320);
    return () => clearTimeout(t);
  }, [query]);

  const matchedDistricts = query
    ? districts.current.filter((d) => d.district.toLowerCase().includes(query.toLowerCase())).slice(0, 5)
    : [];

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 md:px-8 pt-6">
        <PageHeader
          title="Geospatial Command Center"
          subtitle="Live incident map · zoom to drill from hotspot clusters to exact locations · red-zone alerts"
          right={
            <div className="chip">
              <MapPin className="h-3.5 w-3.5 text-accent" /> {count.toLocaleString()} incidents
            </div>
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px] gap-4 px-6 md:px-8 pb-6">
        {/* map */}
        <div className="card overflow-hidden relative h-[64vh]">
          <div ref={mapEl} className="absolute inset-0" />
          {loading && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 chip bg-ink-900/80 z-10">
              <div className="h-3 w-3 rounded-full border-2 border-ink-600 border-t-accent animate-spin" />
              loading incidents…
            </div>
          )}

          {/* location search */}
          <div className="absolute top-3 left-3 z-20 w-56">
            <div className="card !bg-ink-900/90 !p-2 flex items-center gap-2">
              <Search className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search village, area, district…"
                className="bg-transparent text-xs text-slate-200 placeholder:text-slate-500 outline-none w-full"
              />
              {query && (
                <button onClick={() => { setQuery(""); setPlaces([]); }} className="shrink-0">
                  <X className="h-3.5 w-3.5 text-slate-500 hover:text-white" />
                </button>
              )}
            </div>
            {query && (
              <div className="mt-1 card !bg-ink-900/95 max-h-64 overflow-y-auto py-1">
                {matchedDistricts.length > 0 && (
                  <>
                    <div className="px-3 pt-1 pb-0.5 text-[9px] font-semibold uppercase tracking-wider text-slate-500">
                      Districts
                    </div>
                    {matchedDistricts.map((d) => (
                      <button
                        key={d.district_id}
                        onClick={() => flyToDistrict(d)}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-ink-700/60 flex items-center justify-between"
                      >
                        <span className="flex items-center gap-2 truncate">
                          <MapPin className="h-3 w-3 text-accent shrink-0" /> {d.district}
                        </span>
                        <span className="text-[10px] text-slate-500 shrink-0">{d.total_cases}</span>
                      </button>
                    ))}
                  </>
                )}

                {places.length > 0 && (
                  <>
                    <div className="px-3 pt-1.5 pb-0.5 text-[9px] font-semibold uppercase tracking-wider text-slate-500">
                      Places
                    </div>
                    {places.map((p, i) => (
                      <button
                        key={`${p.name}-${i}`}
                        onClick={() => flyToPlace(p)}
                        className="w-full text-left px-3 py-1.5 hover:bg-ink-700/60 flex items-center gap-2"
                      >
                        <MapPin className="h-3 w-3 text-accent shrink-0" />
                        <span className="min-w-0 flex-1">
                          <span className="block text-xs text-slate-200 truncate">{p.name}</span>
                          {p.context && (
                            <span className="block text-[10px] text-slate-500 truncate">{p.context}</span>
                          )}
                        </span>
                        <span className="text-[9px] uppercase tracking-wide text-slate-600 shrink-0">
                          {p.type.replace(/_/g, " ")}
                        </span>
                      </button>
                    ))}
                  </>
                )}

                {searching && places.length === 0 && (
                  <div className="px-3 py-2 text-[11px] text-slate-500 flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full border-2 border-ink-600 border-t-accent animate-spin" />
                    searching places…
                  </div>
                )}
                {!searching && matchedDistricts.length === 0 && places.length === 0 && (
                  <div className="px-3 py-2 text-[11px] text-slate-500">No matching place</div>
                )}
              </div>
            )}
          </div>

          {/* crime-head filter */}
          <div className="absolute top-3 right-3 z-10">
            <div className="card !bg-ink-900/85 card-pad !p-2 flex items-center gap-2">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <select
                value={headFilter}
                onChange={(e) => setHeadFilter(e.target.value)}
                className="bg-ink-800 border border-ink-600 rounded-lg px-2 py-1.5 text-xs text-slate-200"
              >
                <option value="">All crime types</option>
                {Object.keys(HEAD_COLORS).map((h) => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>
          </div>

          {/* legend */}
          <div className="absolute bottom-3 left-3 card !bg-ink-900/85 card-pad !p-3 z-10 text-[11px] space-y-1">
            <div className="flex items-center gap-2 text-slate-300 font-semibold mb-1">
              <Layers className="h-3.5 w-3.5" /> Crime type
            </div>
            {Object.entries(HEAD_COLORS).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: v }} />
                <span className="text-slate-400">{k.replace("Crimes Against ", "").replace("Offences ", "")}</span>
              </div>
            ))}
            <div className="flex items-center gap-2 pt-1 mt-1 border-t border-ink-700">
              <Flame className="h-3 w-3 text-accent-red" />
              <span className="text-slate-400">clusters = density · zoom in for exact spots</span>
            </div>
          </div>
        </div>

        {/* red-zone alerts */}
        <div className="flex flex-col gap-4 min-h-0 h-[64vh]">
          <div className="card flex-1 min-h-0 flex flex-col">
            <div className="px-4 pt-3 pb-2 stat-label">Red-zone alerts (emerging spikes)</div>
            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
              {alerts.length === 0 && (
                <div className="text-xs text-slate-500 text-center py-8">No active spikes.</div>
              )}
              {alerts.map((a, i) => (
                <button
                  key={i}
                  onClick={() => { setHeadFilter(a.crime_head); map.current?.fitBounds(KA_BOUNDS, { padding: 24, duration: 700 }); }}
                  className="w-full text-left rounded-xl border border-ink-700 bg-ink-800/50 p-3 hover:border-accent-red/40"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white">{a.district}</span>
                    <SeverityBadge severity={a.severity} />
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {a.top_subcrime} · <span style={{ color: headColor(a.crime_head) }}>{a.crime_head}</span>
                  </div>
                  <div className="text-[11px] font-mono text-accent-red mt-1">
                    z {a.z_score} · {a.recent_count} vs {a.baseline_avg}{a.ratio ? ` · ×${a.ratio}` : ""}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
