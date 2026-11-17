import { optimizationService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Card, Empty, ErrorBox, PageHeader, Spinner, StatusBadge, Td, Th } from "../components/common/ui";
import { mb, when } from "../utils/format";

export default function OptimizationHistory() {
  const { data, error, loading, reload } = useAsync(() => optimizationService.history(), []);
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error ?? new Error("No data")} onRetry={reload} />;
  return (
    <>
      <PageHeader title="Optimization history" subtitle="Audit trail of every preview, approval, change and rollback." />
      {data.length === 0 ? <Empty>No optimizations yet.</Empty> : (
        <Card><div className="overflow-x-auto"><table className="w-full">
          <thead><tr><Th>Function</Th><Th>Old</Th><Th>New</Th><Th>Created</Th><Th>Approved</Th><Th>Applied</Th><Th>Status</Th><Th>Verification</Th></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {data.map((r) => (
              <tr key={r.id} className="align-top">
                <Td>{r.function_name}<div className="text-xs text-slate-400">{r.account_id} · {r.region}{r.mode === "demo" ? " · demo" : ""}</div></Td>
                <Td>{mb(r.old_memory_mb)}</Td><Td>{mb(r.new_memory_mb ?? r.target_memory_mb)}</Td>
                <Td className="text-xs">{when(r.created_at)}</Td><Td className="text-xs">{when(r.approved_at)}</Td><Td className="text-xs">{when(r.applied_at)}</Td>
                <Td><StatusBadge status={r.status} />{r.error && <div className="mt-1 max-w-[14rem] text-xs text-rose-600">{r.error}</div>}</Td>
                <Td className="text-xs">{r.verification ? r.verification.verdict.replaceAll("_", " ") : "—"}</Td>
              </tr>))}
          </tbody></table></div></Card>
      )}
    </>
  );
}
