import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, ClipboardList, Cloud, FileText, History, LayoutDashboard, Lightbulb, Settings, Wrench } from "lucide-react";
import { lambdaService } from "../../services/lambdaService";
import { useAsync } from "../../hooks/useAsync";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/functions", label: "Lambda functions", icon: Cloud },
  { to: "/recommendations", label: "Recommendations", icon: Lightbulb },
  { to: "/cost", label: "Cost analysis", icon: BarChart3 },
  { to: "/optimize", label: "Optimization center", icon: Wrench },
  { to: "/history", label: "Optimization history", icon: History },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Shell() {
  const { data: conn, error } = useAsync(() => lambdaService.connection(), []);
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col bg-slate-900 p-4 text-slate-300 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2 text-white">
          <ClipboardList className="h-5 w-5 text-indigo-400" />
          <span className="text-lg font-semibold tracking-tight">CloudCost AI</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"}
              className={({ isActive }) => `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition ${isActive ? "bg-slate-800 text-white" : "hover:bg-slate-800/60"}`}>
              <Icon className="h-4 w-4" />{label}
            </NavLink>
          ))}
        </nav>
        <p className="mt-auto px-2 text-xs text-slate-500">Lambda memory optimization.<br />Runs on your computer.</p>
      </aside>
      <div className="min-w-0 flex-1">
        {conn?.mode === "demo" && (
          <div className="bg-amber-100 px-6 py-2 text-sm text-amber-900">
            <strong>DEMO DATA</strong> — sample functions, not from your AWS account. Set <code>mode: aws</code> in config.yaml to use real data.
          </div>
        )}
        {conn?.mode === "aws" && (
          <div className="bg-emerald-50 px-6 py-2 text-sm text-emerald-900">
            <strong>LIVE AWS</strong> · account {conn.account_id} · {conn.region} ·{" "}
            {conn.writes_enabled ? "changes enabled" : "read-only (changes disabled)"}
          </div>
        )}
        {error && <div className="bg-rose-50 px-6 py-2 text-sm text-rose-800">{error.message}</div>}
        <main className="mx-auto max-w-6xl px-6 py-8"><Outlet /></main>
      </div>
    </div>
  );
}
