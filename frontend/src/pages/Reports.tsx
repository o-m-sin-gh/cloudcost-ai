import { useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { reportService } from "../services/recommendationService";
import { useAsync } from "../hooks/useAsync";
import { Button, Card, ErrorBox, PageHeader, Spinner } from "../components/common/ui";

export default function Reports() {
  const { data, error, loading, reload, setData } = useAsync(() => reportService.list(), []);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<Error | null>(null);
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error ?? new Error("No data")} onRetry={reload} />;

  async function generate() {
    setBusy(true); setErr(null);
    try { setData(await reportService.generate()); } catch (e) { setErr(e as Error); } finally { setBusy(false); }
  }
  return (
    <>
      <PageHeader title="Reports" subtitle="CSV and JSON exports, saved in the project's reports/ folder." right={<Button disabled={busy} onClick={generate}><RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} />Generate / refresh</Button>} />
      {err && <div className="mb-4"><ErrorBox error={err} /></div>}
      <Card><ul className="divide-y divide-slate-100">
        {data.map((f) => (
          <li key={f.name} className="flex items-center justify-between py-3 text-sm">
            <div><div className="font-medium">{f.name}</div><div className="text-xs text-slate-500">{f.exists ? `${f.size_bytes} bytes` : "not generated yet"}</div></div>
            {f.exists ? <a className="inline-flex items-center gap-1 text-indigo-600 hover:underline" href={`/api/reports/${f.name}`}><Download className="h-4 w-4" />Download</a> : <span className="text-xs text-slate-400">—</span>}
          </li>))}
      </ul></Card>
    </>
  );
}
