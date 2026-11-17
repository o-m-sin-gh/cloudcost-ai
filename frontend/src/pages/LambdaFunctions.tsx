import { Link } from "react-router-dom";
import { lambdaService } from "../services/lambdaService";
import { recommendationService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Badge, Card, ErrorBox, PageHeader, Spinner, StatusBadge, Td, Th } from "../components/common/ui";
import { mb, when } from "../utils/format";

export default function LambdaFunctions() {
  const inv = useAsync(() => lambdaService.functions(), []);
  const rec = useAsync(() => recommendationService.list(), []);
  if (inv.loading) return <Spinner />;
  if (inv.error || !inv.data) return <ErrorBox error={inv.error ?? new Error("No data")} onRetry={inv.reload} />;
  const status = new Map(rec.data?.items.map((r) => [r.function_name, r.status]));

  return (
    <>
      <PageHeader title="Lambda functions" subtitle={`${inv.data.meta.count} function(s) in ${inv.data.meta.region}`} />
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full"><thead><tr><Th>Function</Th><Th>Runtime</Th><Th right>Memory</Th><Th right>Timeout</Th><Th>Arch</Th><Th>State</Th><Th>Last modified</Th><Th>Finding</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {inv.data.functions.map((f) => (
                <tr key={f.name}>
                  <Td><Link className="text-indigo-600 hover:underline" to={`/functions/${f.name}`}>{f.name}</Link>{!f.managed && <span className="ml-2"><Badge>read-only scope</Badge></span>}</Td>
                  <Td>{f.runtime}</Td><Td right>{mb(f.memory_mb)}</Td><Td right>{f.timeout_s}s</Td><Td>{f.architecture}</Td>
                  <Td><Badge tone={f.state === "Active" ? "green" : "amber"}>{f.state}</Badge></Td>
                  <Td className="text-xs text-slate-500">{when(f.last_modified)}</Td>
                  <Td>{status.get(f.name) ? <StatusBadge status={status.get(f.name)!} /> : "…"}</Td>
                </tr>
              ))}
            </tbody></table>
        </div>
      </Card>
    </>
  );
}
