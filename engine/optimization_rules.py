"""Safety rules that decide whether a memory change may be proposed."""
from __future__ import annotations

LAMBDA_MIN_MB = 128
LAMBDA_MAX_MB = 10240


def validate_change(
    *,
    function_name: str,
    state: str,
    current_mb: int,
    target_mb: int,
    monthly_savings: float | None,
    managed_prefix: str,
    min_monthly_savings: float,
    max_reduction_pct: float,
) -> tuple[bool, list[str]]:
    """Return (allowed, notes). `notes` always explains the decision."""
    notes: list[str] = []
    ok = True

    if managed_prefix and not function_name.startswith(managed_prefix):
        ok = False
        notes.append(f"Function is outside the managed scope (name must start with '{managed_prefix}').")
    if state and state != "Active":
        ok = False
        notes.append(f"Function state is '{state}', not 'Active'.")
    if not (LAMBDA_MIN_MB <= target_mb <= LAMBDA_MAX_MB):
        ok = False
        notes.append(f"Target memory must be between {LAMBDA_MIN_MB} and {LAMBDA_MAX_MB} MB.")
    if target_mb == current_mb:
        ok = False
        notes.append("Target memory equals current memory; nothing to change.")

    if target_mb < current_mb:
        reduction = (current_mb - target_mb) / current_mb * 100
        if reduction > max_reduction_pct:
            ok = False
            notes.append(
                f"Reduction of {reduction:.0f}% exceeds the {max_reduction_pct:.0f}% single-step limit; apply in smaller steps."
            )
        if monthly_savings is not None and monthly_savings < min_monthly_savings:
            ok = False
            notes.append(
                f"Estimated monthly savings ${monthly_savings:.6f} is below the ${min_monthly_savings:.6f} threshold."
            )
        notes.append("Lower memory also lowers CPU; verify duration after applying.")
    elif target_mb > current_mb:
        notes.append("Memory increase: performance-driven change, may raise or lower cost depending on duration.")

    if ok:
        notes.insert(0, "All safety rules passed.")
    return ok, notes
