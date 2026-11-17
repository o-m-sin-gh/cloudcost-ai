import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { lambdaService } from "../services/lambdaService";
import { useAsync } from "../hooks/useAsync";
import { Badge, Card, Empty, ErrorBox, PageHeader, SavingsTag, Spinner, Stat, StatusBadge } from "../components/common/ui";
import { DurationChart, InvocationsChart } from "../components/charts/charts";
import { SOURCE_LABEL, mb, ms, usd } from "../utils/format";

export default function FunctionDetails() {
  const { name = "" } = useParams();
  const { data, error, loading, reload } = useAsync(() => lambdaService.detail(name), [name]);
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error ?? new Error("No data")} onRetry={reload} />;
  const { function: fn, metrics: m, analysis: a } = data;

  return (
    <>
      <Link to="/functions" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800"><ArrowLeft className="h-4 w-4" />Functions</Link>
      <PageHeader title={fn.name} subtitle={`${fn.runtime} · ${fn.architecture} · ${fn.memory_mb} MB · ${fn.timeout_s}s timeout`} right={a && <StatusBadge status={a.status} />} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Invocations" value={m.invocations} hint={`last ${Math.round(m.period_days)} days`} />
        <Stat label="Avg duration" value={ms(m.avg_duration_ms)} hint={`max ${ms(m.max_duration_ms)}`} />
        <Stat label="Errors / throttles" value={`${m.errors} / ${m.throttles}`} />
        <Stat label="Peak memory used" value={mb(m.max_memory_used_mb)} hint={m.memory_utilization_pct !== null ? `${m.memory_utilization_pct}% of configured` : "from REPORT log lines"} />
      </div>
      {m.invocations === 0 ? <div className="mt-6"><Empty>No invocations in this window yet. Metrics appear after the function runs.</Empty></div> : (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card title="Invocations per day"><InvocationsChart series={m.series} /></Card>
          <Card title="Duration"><DurationChart series={m.series} /></Card>
        </div>
      )}
      <Card title="Recommendation" className="mt-6">
        {!a ? <Empty>No analysis available.</Empty> : (
          <div className="space-y-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="blue">{a.finding}</Badge>
              {a.reason_codes.map((c) => <Badge key={c}>{c}</Badge>)}
              <span className="text-xs text-slate-500">Source: {SOURCE_LABEL[a.source ?? ""] ?? a.source ?? "none"}</span>
            </div>
            <p>{a.explanation}</p>
            {a.recommended_memory_mb && <p>Current <b>{mb(a.current_memory_mb)}</b> → recommended <b>{mb(a.recommended_memory_mb)}</b></p>}
            {a.monthly_savings !== null && <p>Estimated monthly saving: <b className="num">{usd(a.monthly_savings)}</b> <SavingsTag source={a.savings_source} /></p>}
            <p className="text-slate-500">{a.action}</p>
            <ul className="list-disc pl-5 text-slate-500">{a.rule_notes.map((n) => <li key={n}>{n}</li>)}</ul>
            {a.eligible && <Link className="inline-block text-indigo-600 hover:underline" to="/optimize">Go to Optimization center →</Link>}
          </div>
        )}
      </Card>
    </>
  );
}
