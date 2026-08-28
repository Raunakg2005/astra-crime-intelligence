import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Shield,
  Lock,
  LogIn,
  MapPin,
  Activity,
  Brain,
  Share2,
  ScanText,
  AlertTriangle,
  ChevronRight,
  Mail,
  Phone,
  Building2,
  CheckCircle2,
  ExternalLink,
  Layers,
  Radio,
  Server,
  Database,
  Cpu,
  Send,
  X,
  UserCheck,
  ArrowRight,
  Key
} from "lucide-react";
import Logo from "../components/Logo";

// Mock Karnataka District Hotspots for tactical map HUD preview
const DISTRICT_NODES = [
  { id: "blr", name: "Bengaluru City", top: "68%", left: "62%", firs: "12,480", risk: "CRITICAL", zScore: "+3.8", status: "Red Zone Alert", color: "red" },
  { id: "mys", name: "Mysuru District", top: "82%", left: "52%", firs: "4,120", risk: "HIGH", zScore: "+2.1", status: "Active Cluster", color: "red" },
  { id: "hub", name: "Hubballi-Dharwad", top: "42%", left: "38%", firs: "3,890", risk: "HIGH", zScore: "+1.9", status: "Pattern Spike", color: "cyan" },
  { id: "mng", name: "Mangaluru (DK)", top: "76%", left: "34%", firs: "3,210", risk: "MODERATE", zScore: "+1.2", status: "Nominal", color: "cyan" },
  { id: "bel", name: "Belagavi", top: "28%", left: "32%", firs: "3,740", risk: "HIGH", zScore: "+2.4", status: "Red Zone Alert", color: "red" },
  { id: "kal", name: "Kalaburagi", top: "22%", left: "68%", firs: "2,980", risk: "MODERATE", zScore: "+0.8", status: "Nominal", color: "cyan" },
];

const CAPABILITIES = [
  {
    icon: MapPin,
    title: "Geospatial Command Center",
    tagline: "DBSCAN Spatiotemporal Hotspots",
    desc: "Real-time density clustering across 31 districts. Automatically flags red-zone spikes when category volume deviates significantly from historical baselines.",
    route: "/geospatial",
    badge: "MAPLIBRE GL + DBSCAN",
    accent: "red"
  },
  {
    icon: Share2,
    title: "Link & Network Analysis",
    tagline: "Louvain Co-Offending Graphs",
    desc: "Uncovers hidden criminal syndicates and repeat-offender networks across jurisdictions using graph modularity and Modus Operandi matching.",
    route: "/network",
    badge: "CYTOSCAPE GRAPH",
    accent: "cyan"
  },
  {
    icon: Brain,
    title: "Predictive Intelligence",
    tagline: "Time-Series CV Forecasting",
    desc: "Forecasting next-week high-risk police stations and volume trends using strictly forward-in-time cross-validation and socio-economic overlays.",
    route: "/predictive",
    badge: "XGBoost + Ridge",
    accent: "cyan"
  },
  {
    icon: AlertTriangle,
    title: "Anomaly Radar",
    tagline: "Isolation Forest Deviations",
    desc: "Scans incoming FIR narratives for behavioral anomalies, unusual timing patterns, and uncharacteristic modus operandi deviations.",
    route: "/predictive",
    badge: "ROC-AUC 0.98",
    accent: "red"
  },
  {
    icon: ScanText,
    title: "NLP Crime-Text AI",
    tagline: "18-Model Bake-Off Classifier",
    desc: "Instant crime classification and entity extraction from free-text FIR narratives in English and Kannada transliterations.",
    route: "/nlp",
    badge: "87% MACRO-F1",
    accent: "cyan"
  },
  {
    icon: Activity,
    title: "Trend & Pattern Discovery",
    tagline: "Seasonal & Modus Operandi Alerts",
    desc: "Decomposes complex temporal cycles to detect emerging crime typologies before they escalate into regional surges.",
    route: "/overview",
    badge: "REAL-TIME ALERTS",
    accent: "red"
  }
];

export default function Landing() {
  const navigate = useNavigate();
  const [selectedNode, setSelectedNode] = useState(DISTRICT_NODES[0]);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ 
    badgeId: "inspector.rao@ksp.gov.in", 
    password: "ksp2026demo" 
  });
  const [contactForm, setContactForm] = useState({ name: "", badge: "", district: "", email: "", message: "", category: "General Inquiry" });
  const [submittedContact, setSubmittedContact] = useState(false);

  // Counter simulation
  const [counts, setCounts] = useState({ firs: 0, districts: 0, models: 0, auc: 0 });

  useEffect(() => {
    const timer = setInterval(() => {
      setCounts((prev) => ({
        firs: Math.min(40000, prev.firs + 1200),
        districts: Math.min(31, prev.districts + 1),
        models: Math.min(18, prev.models + 1),
        auc: Math.min(0.98, parseFloat((prev.auc + 0.03).toFixed(2)))
      }));
    }, 40);
    return () => clearInterval(timer);
  }, []);

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowLoginModal(false);
    navigate("/overview");
  };

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedContact(true);
    setTimeout(() => {
      setSubmittedContact(false);
      setContactForm({ name: "", badge: "", district: "", email: "", message: "", category: "General Inquiry" });
    }, 4000);
  };

  return (
    <div className="min-h-screen bg-[#070b16] text-slate-200 font-sans selection:bg-red-600 selection:text-white relative overflow-x-hidden">
      
      {/* Background Ambient Overlay - Tighter Digital GIS Topo & Tactical Crosshair Grid */}
      <div className="fixed inset-0 pointer-events-none z-0 opacity-15 overflow-hidden">



        <svg className="w-full h-full text-cyan-500/25" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="gis-crosshair-pattern-tight" width="56" height="56" patternUnits="userSpaceOnUse">
              {/* Tactical Crosshair Reticles at Tighter Grid Intersections */}
              <path d="M 28,23 V 33 M 23,28 H 33" stroke="currentColor" strokeWidth="0.8" opacity="0.65" />
              <circle cx="28" cy="28" r="5" stroke="currentColor" strokeWidth="0.6" fill="none" opacity="0.35" strokeDasharray="2 2" />
              <circle cx="28" cy="28" r="1.5" className="fill-cyan-400 opacity-90" />

              {/* Faint Tighter Coordinates Grid Lines */}
              <line x1="0" y1="28" x2="56" y2="28" stroke="currentColor" strokeWidth="0.5" opacity="0.25" />
              <line x1="28" y1="0" x2="28" y2="56" stroke="currentColor" strokeWidth="0.5" opacity="0.25" />

              {/* Dense GIS Topo Elevation Contour Curves */}
              <path d="M 0,12 Q 14,2 28,12 T 56,12" stroke="currentColor" strokeWidth="0.6" fill="none" opacity="0.25" strokeDasharray="3 3" />
              <path d="M 0,44 Q 18,52 36,44 T 56,44" stroke="currentColor" strokeWidth="0.6" fill="none" opacity="0.2" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#gis-crosshair-pattern-tight)" />
        </svg>

        {/* Deep Ambient Depth Glows */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-600/10 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-10 w-[500px] h-[500px] bg-sky-600/20 rounded-full blur-3xl" />
        <div className="absolute bottom-10 left-10 w-[450px] h-[450px] bg-cyan-900/20 rounded-full blur-3xl" />
      </div>






      {/* 🔴 HEADER / NAVBAR — Equal Spacing Across All Tabs */}
      <header className="sticky top-0 z-40 bg-[#070b16]/90 backdrop-blur-md border-b border-cyan-900/50 px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <Logo size={38} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-black text-xl tracking-wider text-white">ASTRA</span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium tracking-wide uppercase">
              State Crime Records Bureau · Karnataka State Police
            </p>
          </div>
        </div>

        {/* Navigation Links — Equally Distanced Including Officer Login */}
        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold uppercase tracking-wider text-slate-300">
          <a href="#capabilities" className="hover:text-cyan-400 transition-colors">Capabilities</a>
          <a href="#metrics" className="hover:text-cyan-400 transition-colors">Analytics</a>
          <a href="#contact" className="hover:text-cyan-400 transition-colors">Contact Desk</a>
          <button
            onClick={() => setShowLoginModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#0f172a] border border-red-900/60 text-white hover:bg-cyan-950/80 hover:border-cyan-400 hover:text-cyan-300 transition-all shadow-sm"
          >
            <Lock className="w-3.5 h-3.5 text-red-500" />
            <span>Officer Login</span>
          </button>
        </nav>

      </header>

      {/* 🔴 HERO SECTION */}
      <section className="relative z-10 px-4 lg:px-12 pt-12 pb-16 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          {/* Left Column - Tactical Headlines */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2.5 px-3 py-1 rounded-full bg-slate-900/90 border border-red-900/60 text-slate-200 text-xs font-mono font-semibold uppercase tracking-wider">
              <Radio className="w-3.5 h-3.5 animate-pulse text-red-500" />
              <span><span className="text-red-400 font-bold">CLASSIFIED SYSTEM</span> // LAW ENFORCEMENT INTELLIGENCE</span>
            </div>

            <div className="space-y-2">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-white tracking-tight uppercase leading-[1.1]">
                INTELLIGENCE.<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-cyan-300 to-rose-400">
                  PRECISION. ACTION.
                </span>
              </h1>
              <div className="h-1 w-28 bg-gradient-to-r from-red-500 via-sky-400 to-cyan-400 rounded-full mt-2" />
            </div>

            <p className="text-sm md:text-base text-slate-300 leading-relaxed font-normal max-w-2xl">
              Astra transforms Karnataka State Police's 40,000+ FIR database into actionable spatiotemporal hotspots, co-offending syndicate graphs, and predictive crime risk scores — deployed 100% on Zoho Catalyst.
            </p>

            {/* Quick Action Badges */}
            <div className="pt-2 flex flex-wrap gap-3">
              <button
                onClick={() => setShowLoginModal(true)}
                className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-extrabold uppercase tracking-wider bg-sky-600 hover:bg-sky-500 text-white shadow-xl shadow-sky-950/60 hover:shadow-cyan-500/30 transition-all transform hover:-translate-y-0.5 border border-sky-400/40"
              >
                <Shield className="w-4 h-4 text-cyan-200" />
                <span>Officer Login & Access</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Platform Badges */}
            <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-4 text-xs text-slate-400 font-mono">
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> 31 KA Districts</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-red-400" /> 27-Table Relational Schema</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> Zoho Catalyst Native</span>
            </div>
          </div>

          {/* Right Column - Tactical Frame & HUD Glow for Top-Right Map */}
          <div className="lg:col-span-5 relative flex justify-center items-center animate-float">

            
            {/* Tactical Backdrop Ambient Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-red-600/20 via-sky-600/30 to-blue-600/30 rounded-3xl blur-xl opacity-70 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            {/* Main Tactical Card Container */}
            <div className="relative rounded-2xl bg-[#090e1a]/95 border border-cyan-900/60 p-3.5 shadow-[0_0_40px_rgba(14,165,233,0.2)] max-w-md w-full overflow-hidden group">
              
              {/* Corner Bracket Reticles */}
              <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-red-500 rounded-tl-sm pointer-events-none z-30" />
              <div className="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-cyan-400 rounded-tr-sm pointer-events-none z-30" />
              <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-sky-400 rounded-bl-sm pointer-events-none z-30" />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-sky-400 rounded-br-sm pointer-events-none z-30" />

              {/* Tactical Header Bar */}
              <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-cyan-950/80 font-mono">
                <div className="flex items-center gap-2 text-[11px] font-bold text-cyan-400 tracking-wider">
                  <Radio className="w-3.5 h-3.5 text-red-500 animate-pulse" />
                  <span>LIVE INTEL FEED // KA-CRIME GRID</span>
                </div>
                <span className="text-[9px] font-bold font-mono px-2 py-0.5 rounded bg-red-950/80 text-red-400 border border-red-900/60 tracking-widest">
                  31 DISTRICTS SYNCED
                </span>
              </div>

              {/* Map Display Frame */}
              <div className="relative rounded-xl overflow-hidden border border-slate-800/80 bg-black">
                <img 
                  src="/hero_karnataka_map.png" 
                  alt="Karnataka State Tactical Crime Map" 
                  className="w-full h-auto rounded-xl object-contain opacity-95 group-hover:opacity-100 transition-opacity duration-300"
                />
                {/* Subtle Scanline Texture Overlay */}
                <div className="absolute inset-0 pointer-events-none opacity-10 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[length:100%_4px]" />
              </div>

              {/* Tactical Footer Data Strip */}
              <div className="mt-2.5 pt-2 border-t border-slate-900 flex items-center justify-between font-mono text-[10px] text-zinc-400">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span>SYS STATUS: ONLINE</span>
                </span>
                <span className="text-cyan-400/90 font-bold">DBSCAN Z-SCORE ACTIVE</span>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* 🔴 METRICS STRIP */}
      <section id="metrics" className="relative z-10 border-y border-cyan-950/80 bg-[#080e1b]/80 backdrop-blur-md py-8">
        <div className="max-w-7xl mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            
            <div className="p-4 rounded-xl bg-[#0b1324]/80 border border-cyan-950 hover:border-red-900/50 transition-all">
              <div className="text-3xl lg:text-4xl font-black text-white font-mono tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-red-400 to-cyan-400">
                {counts.firs.toLocaleString()}+
              </div>
              <div className="text-xs uppercase tracking-wider font-bold text-slate-400 mt-1">FIR Records Ingested</div>
              <div className="text-[10px] text-red-400/90 font-mono mt-0.5">27-Table Relational Schema</div>
            </div>

            <div className="p-4 rounded-xl bg-[#0b1324]/80 border border-cyan-950 hover:border-cyan-700/50 transition-all">
              <div className="text-3xl lg:text-4xl font-black text-white font-mono tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-400 to-blue-400">
                {counts.districts}
              </div>
              <div className="text-xs uppercase tracking-wider font-bold text-slate-400 mt-1">KA Police Districts</div>
              <div className="text-[10px] text-cyan-400/80 font-mono mt-0.5">Census 2011 Calibrated</div>
            </div>

            <div className="p-4 rounded-xl bg-[#0b1324]/80 border border-cyan-950 hover:border-red-900/50 transition-all">
              <div className="text-3xl lg:text-4xl font-black text-white font-mono tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-rose-400 to-cyan-300">
                {counts.models}
              </div>
              <div className="text-xs uppercase tracking-wider font-bold text-slate-400 mt-1">NLP Classifiers</div>
              <div className="text-[10px] text-red-400/90 font-mono mt-0.5">87% Macro-F1 Bake-Off</div>
            </div>

            <div className="p-4 rounded-xl bg-[#0b1324]/80 border border-cyan-950 hover:border-cyan-700/50 transition-all">
              <div className="text-3xl lg:text-4xl font-black text-white font-mono tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-400 to-blue-400">
                {counts.auc}
              </div>
              <div className="text-xs uppercase tracking-wider font-bold text-slate-400 mt-1">Anomaly ROC-AUC</div>
              <div className="text-[10px] text-cyan-400/80 font-mono mt-0.5">Isolation Forest Evaluated</div>
            </div>

          </div>
        </div>
      </section>

      {/* 🔴 CAPABILITIES SECTION — Clean Cards Without "Launch Module" */}
      <section id="capabilities" className="relative z-10 py-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider mb-3">
            <Shield className="w-3.5 h-3.5 text-red-500" /> CORE CAPABILITIES
          </div>
          <h2 className="text-3xl md:text-4xl font-black text-white uppercase tracking-tight">
            INTELLIGENCE MODULES & ANALYTICAL PILLARS
          </h2>
          <p className="text-slate-400 text-sm mt-2">
            Designed specifically for law enforcement officers, crime record bureaus, and station commanders.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CAPABILITIES.map((cap, idx) => {
            const isRed = cap.accent === "red";
            return (
              <div
                key={idx}
                className="group relative rounded-2xl bg-[#090f1e]/90 border border-slate-800/80 hover:border-cyan-500/80 p-6 transition-all duration-300 hover:shadow-xl hover:shadow-cyan-950/30 hover:-translate-y-1 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 rounded-xl ${isRed ? "bg-red-950/60 border border-red-900/60 text-red-400" : "bg-cyan-950/80 border border-cyan-800/60 text-cyan-400"} group-hover:bg-cyan-500 group-hover:text-zinc-950 transition-colors`}>
                      <cap.icon className="w-6 h-6" />
                    </div>
                    <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded ${isRed ? "bg-red-950/80 text-red-400 border border-red-900/60" : "bg-slate-900 text-slate-400 border border-slate-800"}`}>
                      {cap.badge}
                    </span>
                  </div>

                  <h3 className="text-lg font-extrabold text-white uppercase tracking-tight group-hover:text-cyan-300 transition-colors">
                    {cap.title}
                  </h3>
                  <div className={`text-xs font-mono ${isRed ? "text-red-400" : "text-cyan-400"} font-semibold mt-0.5 mb-2`}>
                    {cap.tagline}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {cap.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 🔴 CONTACT US / DESK INQUIRY */}
      <section id="contact" className="relative z-10 py-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* Contact Details */}
          <div className="lg:col-span-5 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
              <Mail className="w-3.5 h-3.5 text-red-400" /> OFFICIAL COMMUNICATIONS
            </div>
            <h2 className="text-3xl font-black text-white uppercase tracking-tight">
              STATE CRIME RECORDS BUREAU DESK
            </h2>
            <p className="text-slate-300 text-xs leading-relaxed">
              For law enforcement access requests, station integration support, or analytical query escalations, reach out directly to the SCRB Intelligence Command Desk.
            </p>

            <div className="space-y-4 pt-2 text-xs">
              <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-[#090f1e] border border-slate-800">
                <Building2 className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-white uppercase">SCRB Headquarters</div>
                  <div className="text-zinc-400">Karnataka State Police Headquarters, Nrupatunga Road, Bengaluru - 560001</div>
                </div>
              </div>

              <div className="flex items-center gap-3.5 p-3.5 rounded-xl bg-[#090f1e] border border-slate-800">
                <Phone className="w-5 h-5 text-cyan-400 shrink-0" />
                <div>
                  <div className="font-bold text-white uppercase">Control Room & Emergency</div>
                  <div className="text-zinc-400">Helpline: 112 / SCRB Office: +91 (080) 2294-2100</div>
                </div>
              </div>

              <div className="flex items-center gap-3.5 p-3.5 rounded-xl bg-[#090f1e] border border-slate-800">
                <Mail className="w-5 h-5 text-red-400 shrink-0" />
                <div>
                  <div className="font-bold text-white uppercase">Official Email</div>
                  <div className="text-zinc-400">scrb@ksp.gov.in · astra-intel@ksp.gov.in</div>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Inquiry Form */}
          <div className="lg:col-span-7">
            <div className="rounded-2xl bg-[#090f1e] border border-cyan-900/50 p-6 lg:p-8 shadow-xl">
              <h3 className="text-lg font-black text-white uppercase tracking-tight mb-4 flex items-center gap-2">
                <Send className="w-4 h-4 text-cyan-400" /> TRANSMIT OFFICER INQUIRY
              </h3>

              {submittedContact ? (
                <div className="p-6 rounded-xl bg-cyan-950/60 border border-cyan-800 text-center space-y-2">
                  <CheckCircle2 className="w-10 h-10 text-cyan-400 mx-auto animate-bounce" />
                  <div className="font-extrabold text-white uppercase text-base">Inquiry Transmitted</div>
                  <p className="text-xs text-zinc-300 font-mono">
                    Your transmission has been logged with SCRB Intelligence Command. Reference ticket ID: #KSP-{Math.floor(100000 + Math.random() * 900000)}.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleContactSubmit} className="space-y-4 text-xs font-mono">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-zinc-400 font-bold uppercase mb-1">Officer Name *</label>
                      <input
                        type="text"
                        required
                        value={contactForm.name}
                        onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                        placeholder="Insp. K. Rao"
                        className="w-full px-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 font-bold uppercase mb-1">Badge / Officer ID *</label>
                      <input
                        type="text"
                        required
                        value={contactForm.badge}
                        onChange={(e) => setContactForm({ ...contactForm, badge: e.target.value })}
                        placeholder="KSP-8842-BLR"
                        className="w-full px-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-zinc-400 font-bold uppercase mb-1">District / Unit *</label>
                      <input
                        type="text"
                        required
                        value={contactForm.district}
                        onChange={(e) => setContactForm({ ...contactForm, district: e.target.value })}
                        placeholder="Bengaluru City Police"
                        className="w-full px-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 font-bold uppercase mb-1">Inquiry Category</label>
                      <select
                        value={contactForm.category}
                        onChange={(e) => setContactForm({ ...contactForm, category: e.target.value })}
                        className="w-full px-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                      >
                        <option value="General Inquiry">General Inquiry</option>
                        <option value="Station Integration">Station Data Integration</option>
                        <option value="RBAC Access Request">RBAC Clearance Request</option>
                        <option value="Model Recalibration">Model Recalibration Request</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-zinc-400 font-bold uppercase mb-1">Message / Requirements *</label>
                    <textarea
                      required
                      rows={3}
                      value={contactForm.message}
                      onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                      placeholder="Detail your request or analytical query..."
                      className="w-full px-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-extrabold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-lg shadow-sky-950 border border-sky-400/40"
                  >
                    <Send className="w-4 h-4" />
                    <span>Submit Official Transmission</span>
                  </button>
                </form>
              )}
            </div>
          </div>

        </div>
      </section>

      {/* 🔴 OFFICIAL FOOTER — Cleaned Copyright / Rights Line */}
      <footer className="relative z-10 border-t border-cyan-950 bg-[#050812] py-12 px-4 lg:px-8 text-xs font-mono">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 mb-8">
          
          <div className="md:col-span-5 space-y-3">
            <div className="flex items-center gap-3">
              <Logo size={32} />
              <span className="font-black text-lg tracking-wider text-white">ASTRA</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed max-w-md font-sans">
              Astra — AI-Driven Crime Analytics & Intelligence Platform built for the Karnataka State Police and State Crime Records Bureau (SCRB). Deployed 100% on Zoho Catalyst.
            </p>
            <div className="text-cyan-400 font-bold text-[10px] uppercase">
              Hack2skill Datathon 2026 Submission
            </div>
          </div>

          <div className="md:col-span-3 space-y-2">
            <div className="font-bold text-white uppercase text-xs">Intelligence Modules</div>
            <ul className="space-y-1 text-zinc-400 text-[11px]">
              <li><button onClick={() => setShowLoginModal(true)} className="hover:text-cyan-400">Geospatial Hotspots</button></li>
              <li><button onClick={() => setShowLoginModal(true)} className="hover:text-cyan-400">Link & Network Graph</button></li>
              <li><button onClick={() => setShowLoginModal(true)} className="hover:text-cyan-400">Predictive Crime Risk</button></li>
              <li><button onClick={() => setShowLoginModal(true)} className="hover:text-cyan-400">NLP Crime Classification</button></li>
              <li><button onClick={() => setShowLoginModal(true)} className="hover:text-cyan-400">AI Officer Copilot</button></li>
            </ul>
          </div>

          <div className="md:col-span-4 space-y-2">
            <div className="font-bold text-white uppercase text-xs">Responsible Use Notice</div>
            <p className="text-zinc-400 text-[10px] leading-relaxed font-sans">
              Astra is designed strictly as a law enforcement decision-support tool. Models run on calibrated privacy-preserving synthetic data. Automated individual targeting or predictive enforcement is strictly excluded.
            </p>
          </div>

        </div>

        <div className="max-w-7xl mx-auto pt-6 border-t border-slate-900 flex flex-col md:flex-row items-center justify-between text-zinc-500 text-[10px]">
          <div>Karnataka State Police (KSP) · State Crime Records Bureau (SCRB) · Official Datathon Prototype</div>
          <div className="flex items-center gap-4 mt-2 md:mt-0">
            <span>Zoho Catalyst Managed Stack</span>
            <span>•</span>
            <a href="https://github.com/Raunakg2005/astra-crime-intelligence" target="_blank" rel="noreferrer" className="hover:text-cyan-400 flex items-center gap-1">
              <span>GitHub Repository</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </footer>

      {/* 🔴 OFFICER LOGIN MODAL */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-md rounded-2xl bg-[#090f1e] border border-cyan-500/40 p-6 shadow-2xl space-y-5">
            
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-slate-900 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <Logo size={36} />
              <div>
                <div className="font-black text-lg text-white">ASTRA OFFICER AUTHENTICATION</div>
                <div className="text-[10px] font-mono text-cyan-400 uppercase font-bold flex items-center gap-1">
                  <Shield className="w-3 h-3 text-red-500" /> KSP Security Clearing Portal
                </div>
              </div>
            </div>

            {/* 🔑 DEMO CREDENTIALS BOX */}
            <div className="p-3.5 rounded-xl bg-[#060b17] border border-cyan-500/40 space-y-1.5 font-mono text-[11px]">
              <div className="flex items-center justify-between text-cyan-400 font-bold uppercase text-[10px]">
                <span className="flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-cyan-400" /> Demo Officer Credentials
                </span>
                <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 text-[9px]">READY</span>
              </div>
              <div className="text-zinc-300 flex items-center justify-between pt-1">
                <span>Badge ID:</span>
                <code className="text-cyan-300 font-bold bg-slate-900 px-2 py-0.5 rounded text-[10px]">inspector.rao@ksp.gov.in</code>
              </div>
              <div className="text-zinc-300 flex items-center justify-between">
                <span>Passcode:</span>
                <code className="text-cyan-300 font-bold bg-slate-900 px-2 py-0.5 rounded text-[10px]">ksp2026demo</code>
              </div>
            </div>

            <form onSubmit={handleLoginSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-zinc-400 font-bold uppercase mb-1">Police Badge ID / Email</label>
                <div className="relative">
                  <UserCheck className="w-4 h-4 absolute left-3 top-3 text-cyan-500" />
                  <input
                    type="text"
                    required
                    value={loginForm.badgeId}
                    onChange={(e) => setLoginForm({ ...loginForm, badgeId: e.target.value })}
                    placeholder="inspector.rao@ksp.gov.in"
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-zinc-400 font-bold uppercase mb-1">Passcode / Security Token</label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-cyan-500" />
                  <input
                    type="password"
                    required
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-lg bg-[#060b17] border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-extrabold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-lg shadow-sky-950 border border-sky-400/40"
                >
                  <LogIn className="w-4 h-4 text-cyan-200" />
                  <span>Authenticate & Enter Platform</span>
                </button>
              </div>
            </form>

            <div className="text-[10px] text-zinc-500 font-mono text-center">
              Secured by Catalyst Authentication (RBAC)
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
