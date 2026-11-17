import { useState } from "react";
import { lambdaService } from "../services/lambdaService";
import { settingsService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Badge, Button, Card, ErrorBox, PageHeader, Spinner } from "../components/common/ui";
import { when } from "../utils/format";
import type { Connection } from "../types";

export default function SettingsPage() {
  const s = useAsync(() => settingsService.get(), []);
  const [conn, setConn] = useState<Connection | null>(null);
  const [err, setErr] = useState<Error | null>(null);
  const [msg, setMsg] = useState("");
  const [form, setForm] = useState<{ region: string; lookback_days: number; min: number } | null>(null);

  if (s.loading) return <Spinner />;
  if (s.error || !s.data) return <ErrorBox error={s.error ?? new Error("No data")} onRetry={s.reload} />;
  const f = form ?? { region: s.data.region, lookback_days: s.data.lookback_days, min: s.data.min_monthly_savings_usd };

  async function test() {
    setErr(null);
    try { setConn(await lambdaService.connection()); } catch (e) { setErr(e as Error); setConn(null); }
  }
  async function save() {
    setErr(null); setMsg("");
    try {
      await settingsService.update({ region: f.region, lookback_days: f.lookback_days, min_monthly_savings_usd: f.min });
      setMsg("Saved."); await s.reload(); setForm(null);
    } catch (e) { setErr(e as Error); }
  }
  const input = "w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm";

  return (
    <>
      <PageHeader title="Settings" />
      {err && <div className="mb-4"><ErrorBox error={err} /></div>}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="AWS connection" right={<Button tone="ghost" onClick={test}>Test connection</Button>}>
          {conn ? (
            <dl className="grid grid-cols-3 gap-y-2 text-sm">
              <dt className="text-slate-500">Status</dt><dd className="col-span-2"><Badge tone="green">Connected</Badge> <Badge tone={conn.mode === "aws" ? "green" : "amber"}>{conn.mode === "aws" ? "live AWS" : "demo data"}</Badge></dd>
              <dt className="text-slate-500">Account</dt><dd className="num col-span-2">{conn.account_id}</dd>
              <dt className="text-slate-500">Identity</dt><dd className="col-span-2 break-all">{conn.arn}</dd>
              <dt className="text-slate-500">Region</dt><dd className="col-span-2">{conn.region}</dd>
              <dt className="text-slate-500">Last success</dt><dd className="col-span-2">{when(conn.last_successful_connection)}</dd>
            </dl>
          ) : <p className="text-sm text-slate-500">Press “Test connection” to verify your AWS profile.</p>}
        </Card>
        <Card title="Analysis settings">
          <div className="space-y-3 text-sm">
            <label className="block">Region<input className={input} value={f.region} onChange={(e) => setForm({ ...f, region: e.target.value })} /></label>
            <label className="block">Analysis period (days)<input className={input} type="number" min={1} max={60} value={f.lookback_days} onChange={(e) => setForm({ ...f, lookback_days: Number(e.target.value) })} /></label>
            <label className="block">Minimum monthly saving (USD)<input className={input} type="number" step="0.000001" min={0} value={f.min} onChange={(e) => setForm({ ...f, min: Number(e.target.value) })} /></label>
            <div className="flex items-center gap-3"><Button onClick={save}>Save</Button><span className="text-emerald-700">{msg}</span></div>
          </div>
        </Card>
        <Card title="Safety controls (edit config.yaml)" className="lg:col-span-2">
          <ul className="space-y-1 text-sm text-slate-600">
            <li>Mode: <b>{s.data.mode}</b> · Real AWS changes: <b>{s.data.allow_writes ? "enabled" : "disabled"}</b></li>
            <li>Only functions named <code>{s.data.managed_prefix}*</code> can be changed.</li>
            <li>Largest allowed single-step memory cut: {s.data.max_reduction_pct}%.</li>
          </ul>
        </Card>
      </div>
    </>
  );
}
