import { Link } from "react-router-dom";
import { recommendationService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Badge, Button, Card, Empty, ErrorBox, PageHeader, SavingsTag, Spinner, StatusBadge, Td, Th } from "../components/common/ui";
import { SOURCE_LABEL, mb, usd } from "../utils/format";

export default function Recommendations() {
  const { data, error, loading, reload } = useAsync(() => recommendationService.list(true), []);
  if (loading) return <Spinner label="Refreshing from CloudWatch / Compute Optimizer…" />;
  if (error || !data) return <ErrorBox error={error ?? new Error("No data")} onRetry={reload} />;

  return (
    <>
      <PageHeader title="Recommendations" subtitle={data.optimizer.message} right={<Button tone="ghost" onClick={() => void reload()}>Refresh</Button>} />
      {data.items.length === 0 ? <Empty>No functions found.</Empty> : (
        <Card>
          <div className="overflow-x-auto"><table className="w-full">
            <thead><tr><Th>Function</Th><Th>Finding</Th><Th right>Current</Th><Th right>Recommended</Th><Th right>Saving / month</Th><Th>Status</Th><Th>Source</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((r) => (
                <tr key={r.function_name} className="align-top">
                  <Td><Link className="text-indigo-600 hover:underline" to={`/functions/${r.function_name}`}>{r.function_name}</Link>
                    <div className="mt-1 max-w-xs text-xs text-slate-500">{r.explanation}</div></Td>
                  <Td>{r.finding}<div className="mt-1 flex flex-wrap gap-1">{r.reason_codes.map((c) => <Badge key={c}>{c}</Badge>)}</div></Td>
                  <Td right>{mb(r.current_memory_mb)}</Td><Td right>{mb(r.recommended_memory_mb)}</Td>
                  <Td right>{usd(r.monthly_savings)}<div className="mt-1"><SavingsTag source={r.savings_source} /></div></Td>
                  <Td><StatusBadge status={r.status} />{r.status !== "optimized" && r.status !== "awaiting_data" && !r.eligible && <div className="mt-1"><Badge tone="red">Blocked by rules</Badge></div>}</Td>
                  <Td className="max-w-[10rem] text-xs text-slate-500">{SOURCE_LABEL[r.source ?? ""] ?? r.source ?? "—"}</Td>
                </tr>
              ))}
            </tbody></table></div>
        </Card>
      )}
    </>
  );
}
