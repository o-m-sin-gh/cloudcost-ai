import type { ReactNode } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { ApiError } from "../../services/api";

export function Card({ title, right, children, className = "" }: { title?: string; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {(title || right) && (
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-700">{title}</h2>
          {right}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="num mt-2 text-3xl font-semibold text-slate-900">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

const TONES: Record<string, string> = {
  green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  amber: "bg-amber-50 text-amber-800 ring-amber-200",
  red: "bg-rose-50 text-rose-700 ring-rose-200",
  blue: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  gray: "bg-slate-100 text-slate-600 ring-slate-200",
};
export function Badge({ tone = "gray", children }: { tone?: keyof typeof TONES; children: ReactNode }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}>{children}</span>;
}

export const STATUS_TONE: Record<string, keyof typeof TONES> = {
  optimized: "green", opportunity: "blue", increase_suggested: "amber", awaiting_data: "gray",
  previewed: "gray", approved: "blue", applied: "green", rejected: "gray", failed: "red", rolled_back: "amber",
};
export const STATUS_TEXT: Record<string, string> = {
  optimized: "Optimized", opportunity: "Opportunity", increase_suggested: "Increase suggested", awaiting_data: "Awaiting data",
  previewed: "Previewed", approved: "Approved", applied: "Applied", rejected: "Rejected", failed: "Failed", rolled_back: "Rolled back",
};
export const StatusBadge = ({ status }: { status: string }) => <Badge tone={STATUS_TONE[status] ?? "gray"}>{STATUS_TEXT[status] ?? status}</Badge>;

export function SavingsTag({ source }: { source: string }) {
  if (source === "aws") return <Badge tone="green">AWS figure</Badge>;
  if (source === "estimated") return <Badge tone="amber">Estimate</Badge>;
  return <Badge>None</Badge>;
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" />{label}</div>
  );
}

export function ErrorBox({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  const notes = error instanceof ApiError ? error.notes : [];
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
      <div className="flex items-start gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><div>
        <div className="font-medium">{error.message}</div>
        {notes.length > 0 && <ul className="mt-1 list-disc pl-5">{notes.map((n) => <li key={n}>{n}</li>)}</ul>}
        {onRetry && <button onClick={onRetry} className="mt-2 text-xs font-medium underline">Try again</button>}
      </div></div>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">{children}</div>;
}

export function PageHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div><h1 className="text-2xl font-semibold text-slate-900">{title}</h1>{subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}</div>
      {right}
    </div>
  );
}

export function Button({ children, onClick, tone = "primary", disabled, type = "button" }: {
  children: ReactNode; onClick?: () => void; tone?: "primary" | "ghost" | "danger"; disabled?: boolean; type?: "button" | "submit";
}) {
  const styles = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700",
    ghost: "bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50",
    danger: "bg-rose-600 text-white hover:bg-rose-700",
  }[tone];
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${styles}`}>
      {children}
    </button>
  );
}

export const Th = ({ children, right }: { children?: ReactNode; right?: boolean }) =>
  <th className={`px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500 ${right ? "text-right" : "text-left"}`}>{children}</th>;
export const Td = ({ children, right, className = "" }: { children?: ReactNode; right?: boolean; className?: string }) =>
  <td className={`num px-3 py-2.5 text-sm ${right ? "text-right" : ""} ${className}`}>{children}</td>;
