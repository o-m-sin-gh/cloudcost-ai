import { Link } from "react-router-dom";
import { recommendationService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Badge, Card, Empty, ErrorBox, PageHeader, SavingsTag, Spinner, Stat, StatusBadge, Td, Th } from "../components/common/ui";
import { SOURCE_LABEL, mb, usd } from "../utils/format";

export default function Dashboard() {
  const { data, error, loading, reload } = useAsync(() => recommendationService.list(), []);
  if (loading) return <Spinner label="Reading functions and metrics…" />;
  if (error || !data) return <ErrorBox error={error ?? new Error("No data")} onRetry={reload} />;
  const s = data.summary;
  const top = data.items.filter((r) => r.status === "opportunity" && r.eligible);

  return (
    <>
      <PageHeader title="Overview" subtitle="Lambda memory vs. cost vs. performance" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total functions" value={s.total_functions} />
        <Stat label="Analysed" value={s.analysed} hint="have a usable finding" />
        <Stat label="Opportunities" value={s.opportunities} hint={s.opportunities_out_of_scope ? `+${s.opportunities_out_of_scope} outside managed scope` : "in managed scope"} />
        <Stat label="Potential savings / month" value={usd(s.potential_monthly_savings)} hint={s.savings_label} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card title="Compute Optimizer" className="lg:col-span-2">
          <div className="flex items-center gap-2">
            <Badge tone={data.optimizer.status === "ok" && s.data_source === "aws" ? "green" : "amber"}>{s.data_source === "demo" ? "Demo sample" : data.optimizer.status === "ok" ? "AWS recommendations" : "Not available"}</Badge>
            <span className="text-sm text-slate-600">{data.optimizer.message}</span>
          </div>
          {data.optimizer.status !== "ok" && s.data_source !== "demo" && (
            <p className="mt-3 text-sm text-slate-500">Recommendations below come from CloudCost's own fallback rules and are labelled as such. They are not AWS recommendations.</p>
          )}
        </Card>
        <Card title="At production scale">
          <div className="num text-2xl font-semibold">{usd(s.savings_at_1m_invocations)}</div>
          <p className="mt-1 text-xs text-slate-500">projected monthly saving if these functions each ran 1M times. A projection, not actual savings.</p>
        </Card>
      </div>

      <Card title="Opportunities" className="mt-6" right={<Link className="text-sm text-indigo-600 hover:underline" to="/recommendations">All recommendations</Link>}>
        {top.length === 0 ? <Empty>No in-scope opportunities right now.</Empty> : (
          <table className="w-full"><thead><tr><Th>Function</Th><Th>Current</Th><Th>Recommended</Th><Th right>Saving / month</Th><Th>Source</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {top.map((r) => (
                <tr key={r.function_name}>
                  <Td><Link className="text-indigo-600 hover:underline" to={`/functions/${r.function_name}`}>{r.function_name}</Link></Td>
                  <Td>{mb(r.current_memory_mb)}</Td><Td>{mb(r.recommended_memory_mb)}</Td>
                  <Td right>{usd(r.monthly_savings)} <SavingsTag source={r.savings_source} /></Td>
                  <Td className="text-xs text-slate-500">{SOURCE_LABEL[r.source ?? ""] ?? r.source}</Td>
                </tr>
              ))}
            </tbody></table>
        )}
      </Card>
      <Card title="All functions" className="mt-6">
        <table className="w-full"><thead><tr><Th>Function</Th><Th>Status</Th><Th>AWS finding</Th><Th right>Invocations</Th></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {data.items.map((r) => (
              <tr key={r.function_name}><Td>{r.function_name}</Td><Td><StatusBadge status={r.status} /></Td><Td>{r.finding}</Td><Td right>{r.invocations}</Td></tr>
            ))}
          </tbody></table>
      </Card>
    </>
  );
}
