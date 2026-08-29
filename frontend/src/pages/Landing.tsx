import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Shield,
  Lock,
  MapPin,
  Share2,
  BrainCircuit,
  Radar,
  FileSearch,
  LineChart,
  CheckCircle2,
  Radio,
  Building2,
  Phone,
  Mail,
  X,
  Sparkles,
  ExternalLink,
  ArrowUpRight,
  Globe,
  Printer,
} from "lucide-react";
import Logo from "../components/Logo";
import heroKarnatakaMap from "../assets/hero_karnataka_map.png";

export default function Landing() {
  const navigate = useNavigate();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginEmail, setLoginEmail] = useState("inspector.rao@ksp.gov.in");
  const [loginPasscode, setLoginPasscode] = useState("ksp2026demo");

  // Contact Desk Form State removed
  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/overview");
  };

  return (
    <div className="min-h-screen bg-[#070b16] text-slate-100 font-sans tactical-grid-bg relative overflow-x-hidden selection:bg-sky-500 selection:text-white">
      {/* Ambient Radial Glow Background Filters */}
      <div className="absolute top-0 left-1/4 w-80 h-80 bg-sky-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[400px] h-[400px] bg-rose-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-[450px] h-[450px] bg-sky-600/10 rounded-full blur-[110px] pointer-events-none" />

      {/* ------------------------------------------------------------- */}
      {/* NAVIGATION HEADER */}
      {/* ------------------------------------------------------------- */}
      <header className="sticky top-0 z-40 bg-[#070b16]/90 backdrop-blur-md border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Bureau Tag */}
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => navigate("/")}>
            <Logo size={34} />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold tracking-wider text-base text-white font-mono">
                  ASTRA
                </span>
              </div>
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-medium leading-none">
                State Crime Records Bureau · Karnataka State Police
              </p>
            </div>
          </div>

          {/* 4 Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-6">
            <a
              href="#capabilities"
              className="text-xs font-semibold tracking-wide text-slate-300 hover:text-sky-400 transition-colors uppercase"
            >
              Capabilities
            </a>
            <a
              href="#metrics"
              className="text-xs font-semibold tracking-wide text-slate-300 hover:text-sky-400 transition-colors uppercase"
            >
              Analytics
            </a>
            <a
              href="#contact"
              className="text-xs font-semibold tracking-wide text-slate-300 hover:text-sky-400 transition-colors uppercase"
            >
              Contact Desk
            </a>

            {/* Officer Login Action Button (Compact & Sleek) */}
            <button
              onClick={() => setShowLoginModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 shadow-md shadow-sky-950/40 border border-sky-400/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Lock className="w-3.5 h-3.5 text-sky-200" />
              <span>Officer Login</span>
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-sky-400"></span>
              </span>
            </button>
          </nav>
        </div>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* HERO SECTION */}
      {/* ------------------------------------------------------------- */}
      <section className="relative pt-8 pb-14 md:pt-14 md:pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Headline & Controls */}
          <div className="lg:col-span-7 space-y-6">
            {/* Prominent Shiny Metallic Gold Kannada Motto Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-gradient-to-r from-amber-950/90 via-yellow-900/60 to-amber-950/90 border border-yellow-400/70 shadow-[0_0_20px_rgba(245,158,11,0.35)] text-sm sm:text-base font-extrabold tracking-wide relative overflow-hidden backdrop-blur-md">
              {/* Shimmer Light Sweep Effect */}
              <div className="absolute inset-0 w-1/2 h-full bg-gradient-to-r from-transparent via-yellow-300/30 to-transparent skew-x-12 animate-gold-shimmer pointer-events-none" />
              <Shield className="w-4 h-4 text-yellow-400 shrink-0 filter drop-shadow-[0_0_6px_rgba(250,204,21,0.9)]" />
              <span className="bg-gradient-to-r from-yellow-200 via-amber-300 to-yellow-100 bg-clip-text text-transparent font-extrabold tracking-wide drop-shadow-sm">
                ನಿಖರ ವಿಶ್ಲೇಷಣೆ • ತಡೆರಹಿತ ಸುರಕ್ಷತೆ
              </span>
            </div>

            {/* Headline (Compact & Elegant) */}
            <div className="space-y-2">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-[1.15]">
                <span className="text-white block">INTELLIGENCE.</span>
                <span className="bg-gradient-to-r from-sky-400 via-sky-300 to-rose-400 bg-clip-text text-transparent block">
                  PRECISION. ACTION.
                </span>
              </h1>
              <div className="h-1 w-20 bg-gradient-to-r from-sky-400 to-rose-500 rounded-full mt-2" />
            </div>

            {/* Subtitle (Smaller font size) */}
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-xl font-normal">
              Astra transforms Karnataka State Police's{" "}
              <span className="text-sky-300 font-semibold">40,000+ FIR database</span> into
              actionable spatiotemporal hotspots, co-offending syndicate graphs, and predictive
              crime risk scores
            </p>

            {/* Primary Action Button (Compact Size) */}
            <div className="pt-1 flex items-center gap-3">
              <button
                onClick={() => setShowLoginModal(true)}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 shadow-md shadow-sky-950/60 border border-sky-400/40 transition-all hover:translate-y-[-1px] active:translate-y-[0]"
              >
                <Shield className="w-4 h-4 text-sky-200" />
                <span>OFFICER LOGIN & ACCESS</span>
                <ArrowUpRight className="w-4 h-4 text-sky-200" />
              </button>
            </div>

            {/* Platform Metric Chips */}
            <div className="pt-3 flex flex-wrap items-center gap-3 border-t border-slate-800/80">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
                <span>31 KA Districts</span>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-rose-400" />
                <span>27-Table Relational Schema</span>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
                <span>Zoho Catalyst Native</span>
              </div>
            </div>
          </div>

          {/* Right Column: Floating Tactical Topo Map Frame */}
          <div className="lg:col-span-5 relative">
            <div className="animate-float">
              {/* Dual Glow Layer (Sky Blue only) */}
              <div className="absolute -inset-1 bg-sky-500/15 rounded-2xl blur-lg opacity-75 pointer-events-none" />

              {/* Tactical Outer Container */}
              <div className="relative border border-sky-500/40 bg-black rounded-xl overflow-hidden shadow-xl shadow-sky-950/80">
                {/* 4 Corner Reticle Brackets */}
                <div className="absolute top-2 left-2 w-3.5 h-3.5 border-t-2 border-l-2 border-sky-400 z-20 pointer-events-none" />
                <div className="absolute top-2 right-2 w-3.5 h-3.5 border-t-2 border-r-2 border-sky-400 z-20 pointer-events-none" />
                <div className="absolute bottom-2 left-2 w-3.5 h-3.5 border-b-2 border-l-2 border-sky-400 z-20 pointer-events-none" />
                <div className="absolute bottom-2 right-2 w-3.5 h-3.5 border-b-2 border-r-2 border-sky-400 z-20 pointer-events-none" />

                {/* Header Strip */}
                <div className="px-3.5 py-2 bg-black border-b border-sky-900/50 flex items-center justify-between z-10 relative">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-sky-300">
                    <Radio className="w-3 h-3 text-rose-400 animate-pulse" />
                    <span className="font-bold tracking-wider">LIVE INTEL FEED // KA-CRIME GRID</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase bg-rose-500/20 text-rose-300 border border-rose-500/40">
                    31 DISTRICTS SYNCED
                  </span>
                </div>

                {/* Map Image Displayed from imported PNG Asset */}
                <div className="relative bg-black h-[360px] sm:h-[400px] w-full flex items-center justify-center p-1 overflow-hidden group cursor-pointer">
                  <img
                    src={heroKarnatakaMap}
                    alt="Karnataka Crime Grid Map"
                    className="w-full h-full object-contain scale-[1.12] relative z-10 transition-transform duration-500 ease-out group-hover:scale-[1.35]"
                  />
                </div>

                {/* Footer System Status Bar */}
                <div className="px-3.5 py-2 bg-black border-t border-sky-900/50 flex items-center justify-between text-[10px] font-mono">
                  <div className="flex items-center gap-1.5 text-slate-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-ping" />
                    <span className="font-semibold text-rose-400">SYS STATUS: ONLINE</span>
                  </div>
                  <span className="text-sky-400 font-bold tracking-wide">
                    DBSCAN Z-SCORE ACTIVE
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* LIVE METRICS STRIP SECTION */}
      {/* ------------------------------------------------------------- */}
      <section id="metrics" className="py-8 bg-[#0a1022]/90 border-y border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-sky-500/50 transition-all">
              <div className="text-2xl sm:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-sky-200 font-mono">
                40,000+
              </div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mt-1">
                Ingested FIRs (Statewide CCTNS)
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-rose-500/50 transition-all">
              <div className="text-2xl sm:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-rose-500 to-rose-300 font-mono">
                31
              </div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mt-1">
                KA District Headquarters
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-sky-500/50 transition-all">
              <div className="text-2xl sm:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-sky-200 font-mono">
                18
              </div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mt-1">
                IPC / BNS AI Classifiers
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-rose-500/50 transition-all">
              <div className="text-2xl sm:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-rose-400 to-sky-400 font-mono">
                0.98
              </div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mt-1">
                ROC-AUC Hotspot Accuracy
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 6 CORE CAPABILITY CARDS */}
      {/* ------------------------------------------------------------- */}
      <section id="capabilities" className="py-14 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-2 mb-10">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-sky-950 border border-sky-500/30 text-sky-400 text-[10px] font-mono uppercase tracking-widest">
            <Sparkles className="w-3 h-3" />
            <span>ASTRA CORE CAPABILITIES</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            TACTICAL INTELLIGENCE MODULES
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm max-w-xl mx-auto">
            AI-Powered Law Enforcement Architecture Designed for State Crime Records Bureau (SCRB) & District Headquarters.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="group rounded-xl bg-slate-900/80 border border-slate-800 p-5 hover:border-sky-500/50 hover:bg-slate-900 transition-all duration-300 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 group-hover:scale-105 transition-transform">
                  <MapPin className="w-4 h-4" />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-950 text-sky-300 border border-sky-800">
                  DBSCAN Z-Score
                </span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-sky-300 transition-colors">
                Geospatial Command & Hotspots
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Spatiotemporal density clustering identifying high-risk crime corridors, hot beats, and time-windowed patrol vectors across all 31 KA districts.
              </p>
            </div>
          </div>

          <div className="group rounded-xl bg-slate-900/80 border border-slate-800 p-5 hover:border-rose-500/50 hover:bg-slate-900 transition-all duration-300 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 group-hover:scale-105 transition-transform">
                  <Share2 className="w-4 h-4" />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-800">
                  GNN Syndicate
                </span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-rose-300 transition-colors">
                Co-Offending Link Network
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Graph neural network analysis uncovering criminal gang syndicates, shared modus operandi, key facilitators, and hidden co-offending connections.
              </p>
            </div>
          </div>

          <div className="group rounded-xl bg-slate-900/80 border border-slate-800 p-5 hover:border-sky-500/50 hover:bg-slate-900 transition-all duration-300 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 group-hover:scale-105 transition-transform">
                  <BrainCircuit className="w-4 h-4" />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-950 text-sky-300 border border-sky-800">
                  XGBoost ML
                </span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-sky-300 transition-colors">
                Predictive AI Risk Engine
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                XGBoost & Random Forest ML engines predicting repeat offender risk scores, bail breach likelihood, and future crime probability by station beat.
              </p>
            </div>
          </div>

          <div className="group rounded-xl bg-slate-900/80 border border-slate-800 p-5 hover:border-rose-500/50 hover:bg-slate-900 transition-all duration-300 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 group-hover:scale-105 transition-transform">
                  <Radar className="w-4 h-4" />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-800">
                  Isolation Forest
                </span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-rose-300 transition-colors">
                Anomaly Radar & Outlier Detector
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Statistical algorithms isolating abnormal FIR registration spikes, irregular MO shifts, and unexpected crime surge anomalies in real time.
              </p>
            </div>
          </div>

          <div className="group rounded-xl bg-slate-900/80 border border-slate-800 p-5 hover:border-sky-500/50 hover:bg-slate-900 transition-all duration-300 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 group-hover:scale-105 transition-transform">
                  <FileSearch className="w-4 h-4" />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-950 text-sky-300 border border-sky-800">
                  BERT NLP Engine
                </span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-sky-300 transition-colors">
                NLP Text AI & BNS Classification
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Multi-lingual BERT models parsing Kannada & English FIR narratives to auto-classify sections under Bharatiya Nyaya Sanhita (BNS) & IPC.
              </p>
            </div>
          </div>

          <div className="group rounded-xl bg-slate-900/80 border border-slate-800 p-5 hover:border-sky-500/50 hover:bg-slate-900 transition-all duration-300 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 group-hover:scale-105 transition-transform">
                  <LineChart className="w-4 h-4" />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-950 text-sky-300 border border-sky-800">
                  Time-Series ML
                </span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-sky-300 transition-colors">
                Trend Discovery & Longitudinal Analytics
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Longitudinal temporal analysis highlighting seasonal surge patterns, day-of-week crime frequency, and multi-year crime trajectory shifts.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* CONTACT DESK (OFFICIAL GOVERNMENT CONTACT) */}
      {/* ------------------------------------------------------------- */}
      <section id="contact" className="py-12 bg-[#060a16] border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Card Container - Sleek & Professional */}
          <div className="bg-[#090f20]/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden space-y-6">
            {/* Top Pill Badge */}
            <div>
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-amber-500/30 text-slate-200 text-xs font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                <span>Official Government Contact</span>
              </span>
            </div>

            {/* Header Block: Left Emblem Seal + Title & Subtitle */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              {/* Karnataka Police Emblem / Shield Box */}
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-amber-950/25 border border-amber-500/40 flex flex-col items-center justify-center text-center shrink-0 shadow-sm p-2">
                <Shield className="w-6 h-6 text-amber-400" />
                <span className="text-[7px] font-mono font-bold uppercase text-amber-300/90 tracking-tighter mt-0.5">KSP HQ</span>
              </div>

              {/* Title & Subtitle */}
              <div className="space-y-0.5">
                <h3 className="text-base sm:text-lg md:text-xl font-bold text-white tracking-wide leading-snug">
                  Director-General & Inspector General of Police, Karnataka State
                </h3>
                <p className="text-xs sm:text-sm text-slate-400 font-medium">
                  Karnataka State Police Headquarters
                </p>
              </div>
            </div>

            {/* Contact Details Items Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-5 border-t border-slate-800/80">
              {/* EMAIL */}
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-sky-400 shrink-0">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    EMAIL
                  </div>
                  <a
                    href="mailto:police@ksp.gov.in"
                    className="text-xs sm:text-sm font-semibold text-sky-400 hover:text-sky-300 hover:underline transition-colors font-mono"
                  >
                    police@ksp.gov.in
                  </a>
                </div>
              </div>

              {/* PHONE */}
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-sky-400 shrink-0">
                  <Phone className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    PHONE
                  </div>
                  <div className="text-xs sm:text-sm font-semibold text-slate-200 font-mono leading-tight">
                    080-22942111<br />
                    080-22942777
                  </div>
                </div>
              </div>

              {/* FAX */}
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-sky-400 shrink-0">
                  <Printer className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    FAX
                  </div>
                  <div className="text-xs sm:text-sm font-semibold text-slate-200 font-mono">
                    080-22215911
                  </div>
                </div>
              </div>

              {/* WEBSITE */}
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-sky-400 shrink-0">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    WEBSITE
                  </div>
                  <a
                    href="https://ksp.karnataka.gov.in"
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs sm:text-sm font-semibold text-sky-400 hover:text-sky-300 hover:underline transition-colors font-mono"
                  >
                    ksp.karnataka.gov.in
                  </a>
                </div>
              </div>
            </div>

            {/* Address Row at Bottom */}
            <div className="pt-4 border-t border-slate-800/80 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/80 text-sky-400 shrink-0">
                <MapPin className="w-4 h-4" />
              </div>
              <p className="text-xs sm:text-sm text-slate-300 font-medium leading-relaxed">
                No.2, Nrupathunga Road, Bangalore – 560 001, Karnataka, India
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* FOOTER (MATCHING USER SCREENSHOT EXACTLY) */}
      {/* ------------------------------------------------------------- */}
      <footer className="bg-[#040711] border-t border-slate-800/80 pt-10 pb-6 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Column 1: ASTRA Overview */}
            <div className="md:col-span-5 space-y-3">
              <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => navigate("/")}>
                <Logo size={24} />
                <span className="font-extrabold text-base text-white font-mono tracking-wider">
                  ASTRA
                </span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed max-w-sm">
                Astra — AI-Driven Crime Analytics & Intelligence Platform built for the Karnataka State Police and State Crime Records Bureau (SCRB). Deployed 100% on Zoho Catalyst.
              </p>
              <div className="pt-1">
                <a
                  href="#contact"
                  className="font-mono text-[11px] font-bold text-sky-400 hover:text-sky-300 tracking-wider uppercase"
                >
                  HACK2SKILL DATATHON 2026 SUBMISSION
                </a>
              </div>
            </div>

            {/* Column 2: Intelligence Modules */}
            <div className="md:col-span-3 space-y-2">
              <h4 className="font-mono text-[11px] font-bold tracking-wider text-slate-300 uppercase">
                INTELLIGENCE MODULES
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-400">
                <li>
                  <a href="#capabilities" className="hover:text-slate-200 transition-colors">
                    Geospatial Hotspots
                  </a>
                </li>
                <li>
                  <a href="#capabilities" className="hover:text-slate-200 transition-colors">
                    Link & Network Graph
                  </a>
                </li>
                <li>
                  <a href="#capabilities" className="hover:text-slate-200 transition-colors">
                    Predictive Crime Risk
                  </a>
                </li>
                <li>
                  <a href="#capabilities" className="hover:text-slate-200 transition-colors">
                    NLP Crime Classification
                  </a>
                </li>
                <li>
                  <a href="#capabilities" className="hover:text-slate-200 transition-colors">
                    AI Officer Copilot
                  </a>
                </li>
              </ul>
            </div>

            {/* Column 3: Responsible Use Notice */}
            <div className="md:col-span-4 space-y-2">
              <h4 className="font-mono text-[11px] font-bold tracking-wider text-slate-300 uppercase">
                RESPONSIBLE USE NOTICE
              </h4>
              <p className="text-slate-400 text-xs leading-relaxed">
                Astra is designed strictly as a law enforcement decision-support tool. Models run on calibrated privacy-preserving synthetic data. Automated individual targeting or predictive enforcement is strictly excluded.
              </p>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-4 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-[10px] text-slate-500">
            <div>
              Karnataka State Police (KSP) · State Crime Records Bureau (SCRB) · Official Datathon Prototype
            </div>
            <div className="flex items-center gap-3 text-slate-400">
              <span>Zoho Catalyst Managed Stack</span>
              <span>·</span>
              <a
                href="https://github.com/Raunakg2005/astra-crime-intelligence"
                target="_blank"
                rel="noreferrer"
                className="hover:text-slate-200 transition-colors inline-flex items-center gap-1"
              >
                <span>GitHub Repository</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* ------------------------------------------------------------- */}
      {/* OFFICER LOGIN MODAL */}
      {/* ------------------------------------------------------------- */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0b1329] border border-sky-500/40 rounded-xl shadow-2xl max-w-sm w-full p-5 relative text-left space-y-4">
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-3.5 right-3.5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-950 border border-rose-500/30 text-rose-400 text-[10px] font-mono font-bold">
                <Shield className="w-3 h-3" />
                <span>RESTRICTED ACCESS</span>
              </div>
              <h3 className="text-lg font-extrabold text-white">ASTRA OFFICER AUTHENTICATION</h3>
              <p className="text-[11px] text-slate-400">
                State Crime Records Bureau (SCRB) & District Police Command Portal
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-sky-500/30 text-[11px] space-y-1 font-mono">
              <div className="text-sky-300 font-bold flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-sky-400" />
                <span>PRE-FILLED DEMO CREDENTIALS</span>
              </div>
              <div className="text-slate-300">
                Email: <span className="text-white font-bold">{loginEmail}</span>
              </div>
              <div className="text-slate-300">
                Passcode: <span className="text-white font-bold">{loginPasscode}</span>
              </div>
            </div>

            <form onSubmit={handleLoginSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Officer Badge / Official Email
                </label>
                <input
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Security Passcode
                </label>
                <input
                  type="password"
                  required
                  value={loginPasscode}
                  onChange={(e) => setLoginPasscode(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-lg text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 shadow-md shadow-sky-950/50 flex items-center justify-center gap-1.5 transition-all"
              >
                <Shield className="w-3.5 h-3.5" />
                <span>AUTHENTICATE & ENTER COMMAND CENTER</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
