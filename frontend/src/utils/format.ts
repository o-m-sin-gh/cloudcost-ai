export function usd(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const a = Math.abs(v);
  const digits = a >= 1 ? 2 : a >= 0.01 ? 4 : 6;
  return `${v < 0 ? "-" : ""}$${a.toFixed(digits)}`;
}
export const mb = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `${v} MB`);
export const ms = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `${Math.round(v)} ms`);
export const when = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleString() : "—");
export const day = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export const SOURCE_LABEL: Record<string, string> = {
  "aws-compute-optimizer": "AWS Compute Optimizer",
  "cloudcost-heuristic": "CloudCost fallback (not from AWS)",
  "demo-sample": "Demo sample",
};
