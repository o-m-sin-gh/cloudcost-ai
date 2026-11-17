import { useState } from "react";
import { Check, FlaskConical, Play, RotateCcw, ShieldCheck, X } from "lucide-react";
import { optimizationService, recommendationService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Badge, Button, Card, Empty, ErrorBox, PageHeader, SavingsTag, Spinner, StatusBadge, Td, Th } from "../components/common/ui";
import { mb, usd, when } from "../utils/format";
import type { OptRecord } from "../types";

export default function OptimizationCenter() {
  const rec = useAsync(() => recommendationService.list(), []);
  const hist = useAsync(() => optimizationService.history(), []);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<Error | null>(null);

  async function run(key: string, fn: () => Promise<unknown>) {
    setBusy(key); setErr(null);
    try { await fn(); await Promise.all([hist.reload(), rec.reload()]); }
    catch (e) { setErr(e as Error); }
    finally { setBusy(null); }
  }

  if (rec.loading || hist.loading) return <Spinner />;
  if (rec.error || !rec.data) return <ErrorBox error={rec.error ?? new Error("No data")} onRetry={rec.reload} />;

  const open = (hist.data ?? []).filter((r) => ["previewed", "approved", "applied"].includes(r.status));
  const busyFns = new Set(open.map((r) => r.function_name));
  const candidates = rec.data.items.filter((r) => r.eligible && !busyFns.has(r.function_name));

  return (
    <>
      <PageHeader title="Optimization center" subtitle="Every change goes: dry-run → approve → apply → verify (→ roll back if needed). Dry-run is always first." />
      {err && <div className="mb-4"><ErrorBox error={err} /></div>}

      <Card title="Ready for a dry-run">
        {candidates.length === 0 ? <Empty>No eligible recommendations right now.</Empty> : (
          <table className="w-full"><thead><tr><Th>Function</Th><Th right>Change</Th><Th right>Saving / month</Th><Th /></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {candidates.map((r) => (
                <tr key={r.function_name}>
                  <Td>{r.function_name}<div className="text-xs text-slate-500">{r.status === "increase_suggested" ? "Performance-driven increase" : "Cost-driven reduction"}</div></Td>
                  <Td right>{mb(r.current_memory_mb)} → {mb(r.recommended_memory_mb)}</Td>
                  <Td right>{r.savings_source === "none" ? <span className="text-xs text-slate-500">cost impact verified after applying</span> : <>{usd(r.monthly_savings)} <SavingsTag source={r.savings_source} /></>}</Td>
                  <Td right><Button tone="ghost" disabled={busy !== null} onClick={() => run(r.function_name, () => optimizationService.dryRun(r.function_name))}><FlaskConical className="h-4 w-4" />Dry-run</Button></Td>
                </tr>
              ))}</tbody></table>
        )}
      </Card>

      <h2 className="mb-3 mt-8 text-sm font-semibold uppercase tracking-wide text-slate-500">In progress</h2>
      {open.length === 0 ? <Empty>Nothing in progress. Run a dry-run above to start.</Empty> : (
        <div className="space-y-4">{open.map((r) => <RecordCard key={r.id} r={r} busy={busy} run={run} />)}</div>
      )}
    </>
  );
}

function RecordCard({ r, busy, run }: { r: OptRecord; busy: string | null; run: (k: string, f: () => Promise<unknown>) => Promise<void> }) {
  const b = busy !== null;
  const v = r.verification;
  return (
    <Card title={r.function_name} right={<StatusBadge status={r.status} />}>
      <div className="grid gap-4 text-sm md:grid-cols-2">
        <div className="space-y-1">
          <div>Memory: <b>{mb(r.old_memory_mb)}</b> → <b>{mb(r.target_memory_mb)}</b></div>
          <div className="text-slate-500">Source: {r.recommendation_source ?? "manual"} · Est. saving {usd(r.estimated_monthly_savings)}/month</div>
          {r.mode === "demo" && <Badge tone="amber">demo — no real AWS change</Badge>}
          {r.status === "previewed" && (
            <div className="mt-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
              <div className="mb-1 font-medium">Dry-run: nothing has been changed. Applying would call:</div>
              <ul className="list-disc pl-4">{r.dry_run.aws_calls_that_would_run.map((c) => <li key={c} className="break-all">{c}</li>)}</ul>
            </div>
          )}
          <ul className="list-disc pl-5 text-xs text-slate-500">{r.rule_notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </div>
        <div>
          {v && (
            <div className="rounded-lg border border-slate-200 p-3">
              <div className="mb-1 flex items-center gap-2 font-medium"><ShieldCheck className="h-4 w-4 text-indigo-600" />Verification: <Badge tone={v.verdict === "improved" ? "green" : v.verdict === "awaiting_data" ? "gray" : "amber"}>{v.verdict.replaceAll("_", " ")}</Badge></div>
              {v.avg_duration_ms && v.cost_per_1000_invocations ? (
                <ul className="num text-xs text-slate-600">
                  <li>Avg duration: {Math.round(v.avg_duration_ms.before)} → {Math.round(v.avg_duration_ms.after)} ms ({v.avg_duration_ms.change_pct}%)</li>
                  <li>Cost / 1,000 invocations: {usd(v.cost_per_1000_invocations.before)} → {usd(v.cost_per_1000_invocations.after)} ({v.cost_per_1000_invocations.change_pct}%)</li>
                </ul>
              ) : null}
              <p className="mt-1 text-xs text-slate-500">{v.message}</p>
            </div>
          )}
          {r.applied_at && <div className="mt-2 text-xs text-slate-500">Applied {when(r.applied_at)}</div>}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
        {r.status === "previewed" && <>
          <Button disabled={b} onClick={() => run(r.id, () => optimizationService.approve(r.id))}><Check className="h-4 w-4" />Approve</Button>
          <Button tone="ghost" disabled={b} onClick={() => run(r.id, () => optimizationService.reject(r.id))}><X className="h-4 w-4" />Reject</Button></>}
        {r.status === "approved" && <>
          <Button disabled={b} onClick={() => { if (window.confirm(`Change ${r.function_name} from ${r.old_memory_mb} MB to ${r.target_memory_mb} MB?`)) void run(r.id, () => optimizationService.apply(r.id)); }}><Play className="h-4 w-4" />Apply change</Button>
          <Button tone="ghost" disabled={b} onClick={() => run(r.id, () => optimizationService.reject(r.id))}><X className="h-4 w-4" />Reject</Button></>}
        {r.status === "applied" && <>
          <Button disabled={b} onClick={() => run(r.id, () => optimizationService.verify(r.id))}><ShieldCheck className="h-4 w-4" />Verify performance</Button>
          <Button tone="danger" disabled={b} onClick={() => { if (window.confirm(`Restore ${r.function_name} to ${r.old_memory_mb} MB?`)) void run(r.id, () => optimizationService.rollback(r.id)); }}><RotateCcw className="h-4 w-4" />Roll back</Button></>}
      </div>
    </Card>
  );
}
