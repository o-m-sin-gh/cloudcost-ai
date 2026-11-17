import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CostRow, SeriesPoint } from "../../types";
import { day } from "../../utils/format";

const AX = { fontSize: 11, fill: "#64748b" };

export function InvocationsChart({ series }: { series: SeriesPoint[] }) {
  const data = series.map((p) => ({ d: day(p.ts), Invocations: p.invocations, Errors: p.errors }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="d" tick={AX} /><YAxis tick={AX} allowDecimals={false} /><Tooltip />
        <Bar dataKey="Invocations" fill="#6366f1" radius={[3, 3, 0, 0]} /><Bar dataKey="Errors" fill="#f43f5e" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DurationChart({ series }: { series: SeriesPoint[] }) {
  const data = series.map((p) => ({ d: day(p.ts), Average: p.avg_duration_ms, Maximum: p.max_duration_ms }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="d" tick={AX} /><YAxis tick={AX} unit=" ms" width={64} /><Tooltip /><Legend />
        <Line dataKey="Average" stroke="#6366f1" strokeWidth={2} dot={false} /><Line dataKey="Maximum" stroke="#f59e0b" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CostBars({ rows }: { rows: CostRow[] }) {
  const data = rows
    .filter((r) => r.recommended_monthly_cost !== null && r.savings_source !== "none")
    .map((r) => ({ name: r.function_name.replace("cloudcost-demo-", ""), Current: r.current_monthly_cost, Recommended: r.recommended_monthly_cost }));
  if (!data.length) return null;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="name" tick={AX} /><YAxis tick={AX} tickFormatter={(v: number) => `$${v}`} width={72} />
        <Tooltip formatter={(v: number) => `$${v.toFixed(6)}`} /><Legend />
        <Bar dataKey="Current" fill="#94a3b8" radius={[3, 3, 0, 0]} /><Bar dataKey="Recommended" fill="#6366f1" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
