import { ReactNode, useEffect, useMemo, useState } from "react";
import { FileText, Plus, RotateCcw, Search, X, ChevronLeft, ChevronRight, Loader2, SlidersHorizontal } from "lucide-react";
import { api, FirCreatePayload, FirLookups, FirRow, headColor } from "../api";
import { PageHeader, Spinner } from "../components/ui";

const PAGE_SIZE = 15;

export default function Firs() {
  const [lookups, setLookups] = useState<FirLookups>();
  const [rows, setRows] = useState<FirRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [q, setQ] = useState("");
  const [statusGroup, setStatusGroup] = useState<"" | "open" | "closed">("");
  const [statusId, setStatusId] = useState("");
  const [districtId, setDistrictId] = useState("");
  const [stationId, setStationId] = useState("");
  const [crimeHeadId, setCrimeHeadId] = useState("");
  const [gravityId, setGravityId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => {
    api.firLookups().then(setLookups);
  }, []);

  const stations = useMemo(
    () => lookups?.police_stations.filter((s) => String(s.district_id) === districtId) ?? [],
    [lookups, districtId],
  );

  const load = () => {
    setLoading(true);
    api
      .firs({
        q: q.trim() || undefined,
        status_group: statusGroup || undefined,
        status_id: statusId ? Number(statusId) : undefined,
        district_id: districtId ? Number(districtId) : undefined,
        police_station_id: stationId ? Number(stationId) : undefined,
        crime_head_id: crimeHeadId ? Number(crimeHeadId) : undefined,
        gravity_id: gravityId ? Number(gravityId) : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        page,
        page_size: PAGE_SIZE,
      })
      .then((r) => {
        setRows(r.rows);
        setTotal(r.total);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusGroup, statusId, districtId, stationId, crimeHeadId, gravityId, dateFrom, dateTo]);

  // debounce free-text search
  useEffect(() => {
    const t = setTimeout(() => {
      setPage(1);
      load();
    }, 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const activeFilterCount = [statusGroup, statusId, districtId, stationId, crimeHeadId, gravityId, dateFrom, dateTo].filter(
    Boolean,
  ).length;

  const clearFilters = () => {
    setStatusGroup("");
    setStatusId("");
    setDistrictId("");
    setStationId("");
    setCrimeHeadId("");
    setGravityId("");
    setDateFrom("");
    setDateTo("");
    setQ("");
    setPage(1);
  };

  const toggleStatus = async (row: FirRow) => {
    if (!lookups) return;
    setBusyId(row.case_master_id);
    try {
      if (row.status_group === "Closed") {
        await api.setFirStatus(row.case_master_id, 1); // reopen -> Under Investigation
      } else {
        await api.setFirStatus(row.case_master_id, 3); // close -> Closed - Undetected
      }
      load();
    } finally {
      setBusyId(null);
    }
  };

  const onCreated = () => {
    setShowAdd(false);
    clearFilters();
  };

  return (
    <div className="p-6 md:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        title="FIR Register"
        subtitle="First Information Reports · search, filter, and case-status management"
        right={
          <button
            onClick={() => setShowAdd(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-accent/15 border border-accent/40 text-accent text-sm font-medium hover:bg-accent/25"
          >
            <Plus className="h-4 w-4" /> Add FIR
          </button>
        }
      />

      {/* filters */}
      <div className="card card-pad mb-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="h-4 w-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search crime no, case no, district, station…"
              className="w-full bg-ink-800 border border-ink-600 rounded-xl pl-9 pr-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-accent"
            />
          </div>
          <select
            value={statusGroup}
            onChange={(e) => {
              setStatusGroup(e.target.value as "" | "open" | "closed");
              setPage(1);
            }}
            className="bg-ink-800 border border-ink-600 rounded-xl px-3 py-2 text-sm text-slate-200"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={statusId}
            onChange={(e) => {
              setStatusId(e.target.value);
              setPage(1);
            }}
            className="bg-ink-800 border border-ink-600 rounded-xl px-3 py-2 text-sm text-slate-200"
          >
            <option value="">Any exact status</option>
            {lookups?.statuses.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <select
            value={districtId}
            onChange={(e) => {
              setDistrictId(e.target.value);
              setStationId("");
              setPage(1);
            }}
            className="bg-ink-800 border border-ink-600 rounded-xl px-3 py-2 text-sm text-slate-200"
          >
            <option value="">All districts</option>
            {lookups?.districts.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <select
            value={stationId}
            onChange={(e) => {
              setStationId(e.target.value);
              setPage(1);
            }}
            disabled={!districtId}
            className="bg-ink-800 border border-ink-600 rounded-xl px-3 py-2 text-sm text-slate-200 disabled:opacity-40"
          >
            <option value="">All stations</option>
            {stations.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <span className="text-xs text-slate-500 ml-auto whitespace-nowrap">{total.toLocaleString()} FIRs</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={crimeHeadId}
            onChange={(e) => {
              setCrimeHeadId(e.target.value);
              setPage(1);
            }}
            className="bg-ink-800 border border-ink-600 rounded-xl px-3 py-2 text-sm text-slate-200"
          >
            <option value="">All crime heads</option>
            {lookups?.crime_heads.map((h) => (
              <option key={h.id} value={h.id}>{h.name}</option>
            ))}
          </select>
          <select
            value={gravityId}
            onChange={(e) => {
              setGravityId(e.target.value);
              setPage(1);
            }}
            className="bg-ink-800 border border-ink-600 rounded-xl px-3 py-2 text-sm text-slate-200"
          >
            <option value="">All gravities</option>
            {lookups?.gravities.map((g) => (
              <option key={g.id} value={g.id}>{g.name}</option>
            ))}
          </select>
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <span>Registered</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(1);
              }}
              className="bg-ink-800 border border-ink-600 rounded-xl px-2.5 py-2 text-sm text-slate-200"
            />
            <span>to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(1);
              }}
              className="bg-ink-800 border border-ink-600 rounded-xl px-2.5 py-2 text-sm text-slate-200"
            />
          </div>
          {activeFilterCount > 0 && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white ml-auto"
            >
              <SlidersHorizontal className="h-3.5 w-3.5" /> Clear {activeFilterCount} filter{activeFilterCount > 1 ? "s" : ""}
            </button>
          )}
        </div>
      </div>

      {/* table */}
      <div className="card overflow-hidden">
        {loading && rows.length === 0 ? (
          <Spinner label="Loading FIR register…" />
        ) : rows.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-500">No FIRs match these filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-slate-500 border-b border-ink-700">
                  <th className="px-4 py-3 font-medium">Crime No</th>
                  <th className="px-4 py-3 font-medium">District / Station</th>
                  <th className="px-4 py-3 font-medium">Crime Head</th>
                  <th className="px-4 py-3 font-medium">Gravity</th>
                  <th className="px-4 py-3 font-medium">Registered</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.case_master_id} className="border-b border-ink-800 hover:bg-ink-800/40">
                    <td className="px-4 py-3">
                      <div className="font-mono text-xs text-slate-200">{r.crime_no}</div>
                      <div className="text-[11px] text-slate-500">{r.category}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-slate-200">{r.district}</div>
                      <div className="text-[11px] text-slate-500">{r.police_station}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div style={{ color: headColor(r.crime_head) }} className="text-xs font-medium">{r.crime_head}</div>
                      <div className="text-[11px] text-slate-500">{r.crime_subhead}</div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-300">{r.gravity}</td>
                    <td className="px-4 py-3 text-xs font-mono text-slate-400">{r.registered_date}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`badge ${
                          r.status_group === "Open"
                            ? "bg-accent-amber/15 text-accent-amber border border-accent-amber/30"
                            : "bg-accent-green/15 text-accent-green border border-accent-green/30"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => toggleStatus(r)}
                        disabled={busyId === r.case_master_id}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors disabled:opacity-50 ${
                          r.status_group === "Closed"
                            ? "border-accent-cyan/40 text-accent-cyan hover:bg-accent-cyan/10"
                            : "border-accent-red/40 text-accent-red hover:bg-accent-red/10"
                        }`}
                      >
                        {busyId === r.case_master_id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : r.status_group === "Closed" ? (
                          <RotateCcw className="h-3.5 w-3.5" />
                        ) : (
                          <FileText className="h-3.5 w-3.5" />
                        )}
                        {r.status_group === "Closed" ? "Reopen" : "Close"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* pagination */}
        {total > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-ink-700">
            <span className="text-xs text-slate-500">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-ink-600 text-slate-400 hover:text-white disabled:opacity-30"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-ink-600 text-slate-400 hover:text-white disabled:opacity-30"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {showAdd && lookups && (
        <AddFirModal lookups={lookups} onClose={() => setShowAdd(false)} onCreated={onCreated} />
      )}
    </div>
  );
}

function AddFirModal({
  lookups,
  onClose,
  onCreated,
}: {
  lookups: FirLookups;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [districtId, setDistrictId] = useState("");
  const [stationId, setStationId] = useState("");
  const [headId, setHeadId] = useState("");
  const [subheadId, setSubheadId] = useState("");
  const [gravityId, setGravityId] = useState("");
  const [categoryId, setCategoryId] = useState(String(lookups.categories[0]?.id ?? 1));
  const [incidentFrom, setIncidentFrom] = useState("");
  const [complainantName, setComplainantName] = useState("");
  const [complainantAge, setComplainantAge] = useState("");
  const [complainantGender, setComplainantGender] = useState("");
  const [briefFacts, setBriefFacts] = useState("");
  const [error, setError] = useState<string>();
  const [saving, setSaving] = useState(false);

  const stations = useMemo(
    () => lookups.police_stations.filter((s) => String(s.district_id) === districtId),
    [lookups, districtId],
  );
  const subheads = useMemo(
    () => lookups.crime_subheads.filter((s) => String(s.head_id) === headId),
    [lookups, headId],
  );

  const canSubmit =
    districtId && stationId && headId && subheadId && gravityId && incidentFrom && complainantName.trim() && briefFacts.trim();

  const submit = async () => {
    if (!canSubmit) return;
    setSaving(true);
    setError(undefined);
    const payload: FirCreatePayload = {
      district_id: Number(districtId),
      police_station_id: Number(stationId),
      crime_subhead_id: Number(subheadId),
      gravity_id: Number(gravityId),
      category_id: Number(categoryId),
      incident_from: incidentFrom,
      complainant_name: complainantName.trim(),
      complainant_age: complainantAge ? Number(complainantAge) : undefined,
      complainant_gender_id: complainantGender ? Number(complainantGender) : undefined,
      brief_facts: briefFacts.trim(),
    };
    try {
      await api.createFir(payload);
      onCreated();
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to register FIR.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-ink-700">
          <h2 className="text-sm font-semibold text-slate-100">Register New FIR</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="District *">
              <select
                value={districtId}
                onChange={(e) => {
                  setDistrictId(e.target.value);
                  setStationId("");
                }}
                className="input"
              >
                <option value="">Select district</option>
                {lookups.districts.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Police Station *">
              <select value={stationId} onChange={(e) => setStationId(e.target.value)} className="input" disabled={!districtId}>
                <option value="">Select station</option>
                {stations.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Crime Head *">
              <select
                value={headId}
                onChange={(e) => {
                  setHeadId(e.target.value);
                  setSubheadId("");
                }}
                className="input"
              >
                <option value="">Select crime head</option>
                {lookups.crime_heads.map((h) => (
                  <option key={h.id} value={h.id}>{h.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Crime Sub-Head *">
              <select value={subheadId} onChange={(e) => setSubheadId(e.target.value)} className="input" disabled={!headId}>
                <option value="">Select sub-head</option>
                {subheads.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Gravity *">
              <select value={gravityId} onChange={(e) => setGravityId(e.target.value)} className="input">
                <option value="">Select gravity</option>
                {lookups.gravities.map((g) => (
                  <option key={g.id} value={g.id}>{g.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Category">
              <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} className="input">
                {lookups.categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Incident Date & Time *">
              <input
                type="datetime-local"
                value={incidentFrom}
                onChange={(e) => setIncidentFrom(e.target.value)}
                className="input"
              />
            </Field>
            <Field label="Complainant Name *">
              <input
                value={complainantName}
                onChange={(e) => setComplainantName(e.target.value)}
                placeholder="Full name"
                className="input"
              />
            </Field>
            <Field label="Complainant Age">
              <input
                type="number"
                min={1}
                max={120}
                value={complainantAge}
                onChange={(e) => setComplainantAge(e.target.value)}
                className="input"
              />
            </Field>
            <Field label="Complainant Gender">
              <select value={complainantGender} onChange={(e) => setComplainantGender(e.target.value)} className="input">
                <option value="">Not specified</option>
                <option value="1">Male</option>
                <option value="2">Female</option>
                <option value="3">Transgender</option>
              </select>
            </Field>
          </div>

          <Field label="Brief Facts *">
            <textarea
              value={briefFacts}
              onChange={(e) => setBriefFacts(e.target.value)}
              rows={4}
              placeholder="Describe the incident…"
              className="input resize-none"
            />
          </Field>

          {error && <div className="text-xs text-accent-red">{error}</div>}
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-ink-700">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={!canSubmit || saving}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-accent/15 border border-accent/40 text-accent text-sm font-medium hover:bg-accent/25 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Register FIR
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-wide text-slate-500 mb-1">{label}</span>
      {children}
    </label>
  );
}
