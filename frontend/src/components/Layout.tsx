import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  MapPinned,
  Share2,
  Brain,
  ScanText,
  FileText,
  MessageCircle,
  Circle,
  Sun,
  Moon,
} from "lucide-react";
import Logo from "./Logo";
import { api } from "../api";
import { useTheme } from "../theme";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/geospatial", label: "Geospatial", icon: MapPinned },
  { to: "/network", label: "Link Analysis", icon: Share2 },
  { to: "/predictive", label: "Predictive AI", icon: Brain },
  { to: "/nlp", label: "NLP Text AI", icon: ScanText },
  { to: "/firs", label: "FIR Register", icon: FileText },
  { to: "/chat", label: "Assistant", icon: MessageCircle },
];

export default function Layout() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [range, setRange] = useState<string>("");
  const { theme, toggle } = useTheme();

  useEffect(() => {
    api
      .kpis()
      .then((k) => {
        setOnline(true);
        setRange(`${k.data_from} → ${k.data_to}`);
      })
      .catch(() => setOnline(false));
  }, []);

  return (
    <div className="flex h-full">
      {/* sidebar */}
      <aside className="w-64 shrink-0 border-r border-ink-700 bg-ink-900/60 flex flex-col">
        <div className="px-5 py-5 flex items-center gap-3 border-b border-ink-700">
          <Logo size={40} />
          <div>
            <div className="font-extrabold tracking-tight text-white leading-none text-lg">ASTRA</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400 mt-1">
              KSP Crime Intelligence
            </div>
          </div>
        </div>

        <nav className="p-3 space-y-1 flex-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}
            >
              <n.icon className="h-[18px] w-[18px]" />
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-ink-700 space-y-3">
          {/* theme toggle */}
          <div className="flex items-center rounded-xl bg-ink-800 border border-ink-700 p-0.5">
            <button
              onClick={() => theme !== "dark" && toggle()}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[11px] font-medium transition-colors ${
                theme === "dark" ? "bg-ink-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Moon className="h-3.5 w-3.5" /> Dark
            </button>
            <button
              onClick={() => theme !== "light" && toggle()}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[11px] font-medium transition-colors ${
                theme === "light" ? "bg-ink-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sun className="h-3.5 w-3.5" /> Light
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <Circle
              className={`h-2.5 w-2.5 ${
                online ? "fill-accent-green text-accent-green" : "fill-accent-red text-accent-red"
              }`}
            />
            <span className="text-slate-400">
              {online === null ? "Connecting…" : online ? "Analytics online" : "API offline"}
            </span>
          </div>
          {range && <div className="text-[10px] text-slate-500 font-mono">{range}</div>}
          <div className="text-[10px] text-slate-600">Deployed on Zoho Catalyst</div>
        </div>
      </aside>

      {/* main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
