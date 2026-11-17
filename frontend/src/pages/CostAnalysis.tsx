import { recommendationService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Card, Empty, ErrorBox, PageHeader, SavingsTag, Spinner, Stat, Td, Th } from "../components/common/ui";
import { CostBars } from "../components/charts/charts";
import { mb, usd } from "../utils/format";

export default function CostAnalysis() {
  const { data, error, loading, reload } = useAsync(() => recommendationService.cost(), []);
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error ?? new Error("No data")} onRetry={reload} />;
  const s = data.summary;
  const total = data.rows.reduce((a, r) => a + r.current_monthly_cost, 0);

  return (
    <>
      <PageHeader title="Cost analysis" subtitle={data.disclaimer} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Estimated current cost / month" value={usd(total)} hint="list price, before free allowance" />
        <Stat label="Potential saving / month" value={usd(s.potential_monthly_savings)} hint={s.savings_label} />
        <Stat label="Potential saving / year" value={usd(s.potential_annual_savings)} hint="12 × monthly" />
        <Stat label="At 1M invocations" value={usd(s.savings_at_1m_invocations)} hint="projection, not actual" />
      </div>
      <Card title="Current vs recommended monthly cost" className="mt-6">
        {data.rows.some((r) => r.savings_source !== "none" && r.recommended_monthly_cost !== null) ? <CostBars rows={data.rows} /> : <Empty>No savings estimates yet; functions need more usage history.</Empty>}
      </Card>
      <Card title="Per function" className="mt-6"><div className="overflow-x-auto"><table className="w-full">
        <thead><tr><Th>Function</Th><Th right>Memory</Th><Th right>Current cost</Th><Th right>Recommended cost</Th><Th right>Monthly saving</Th><Th right>Annual saving</Th><Th>Basis</Th></tr></thead>
        <tbody className="divide-y divide-slate-100">
          {data.rows.map((r) => (
            <tr key={r.function_name}><Td>{r.function_name}</Td>
              <Td right>{mb(r.current_memory_mb)} → {mb(r.recommended_memory_mb)}</Td>
              <Td right>{usd(r.current_monthly_cost)}</Td><Td right>{usd(r.recommended_monthly_cost)}</Td>
              <Td right>{usd(r.monthly_savings)}</Td><Td right>{usd(r.annual_savings)}</Td><Td><SavingsTag source={r.savings_source} /></Td></tr>
          ))}</tbody></table></div></Card>
    </>
  );
}
