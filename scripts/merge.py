from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _merge_values(base: Any, patch: Any, path: str, changes: List[Tuple[str, Any, Any]]) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = deepcopy(base)
        for k, v in patch.items():
            child_path = f"{path}.{k}" if path else k
            if k not in merged:
                merged[k] = deepcopy(v)
                changes.append((child_path, None, v))
            else:
                merged[k] = _merge_values(merged[k], v, child_path, changes)
        return merged

    if isinstance(base, list) and isinstance(patch, list):
        merged_list = list(base)
        for item in patch:
            if item not in merged_list and item not in ("", None):
                merged_list.append(item)
        if merged_list != base:
            changes.append((path, base, merged_list))
        return merged_list

    if patch in ("", None, [], {}):
        return base

    if patch != base:
        changes.append((path, base, patch))
    return patch


def merge_memo_v2(v1: Dict[str, Any], onboarding_patch: Dict[str, Any]) -> tuple[Dict[str, Any], List[Tuple[str, Any, Any]]]:
    v2 = deepcopy(v1)
    changes: List[Tuple[str, Any, Any]] = []

    # enforce account/version identity
    onboarding_patch = deepcopy(onboarding_patch)
    onboarding_patch["account_id"] = v1.get("account_id", onboarding_patch.get("account_id", ""))
    onboarding_patch["version"] = "v2"

    v2 = _merge_values(v2, onboarding_patch, "", changes)
    v2["version"] = "v2"
    v2["last_updated_utc"] = datetime.now(timezone.utc).isoformat()

    # Recompute unknowns from final merged state so resolved fields are not kept as unknown.
    unknowns = []
    if not v2.get("company_name"):
        unknowns.append("company_name not explicitly stated")
    bh = v2.get("business_hours", {})
    if not bh.get("days") or not bh.get("start") or not bh.get("end") or not bh.get("timezone"):
        unknowns.append("business_hours incomplete (days/start/end/timezone)")
    if not v2.get("emergency_definition"):
        unknowns.append("emergency_definition not clearly specified")
    er = v2.get("emergency_routing_rules", {})
    if not er.get("primary_contacts"):
        unknowns.append("emergency_routing_rules contacts not found")
    tr = v2.get("call_transfer_rules", {})
    if tr.get("timeout_seconds") is None:
        unknowns.append("call_transfer_rules timeout not specified")
    if tr.get("retries") is None:
        unknowns.append("call_transfer_rules retries not specified")
    v2["questions_or_unknowns"] = unknowns

    return v2, changes


def changes_to_markdown(account_id: str, changes: List[Tuple[str, Any, Any]]) -> str:
    lines = [f"# Change Log: {account_id} v1 -> v2", ""]
    if not changes:
        lines.append("No effective changes were detected. Output regenerated deterministically.")
        return "\n".join(lines) + "\n"

    lines.append("| Field | Old Value | New Value |")
    lines.append("|---|---|---|")
    for field, old, new in changes:
        old_s = str(old).replace("|", "\\|")
        new_s = str(new).replace("|", "\\|")
        lines.append(f"| `{field}` | `{old_s}` | `{new_s}` |")
    lines.append("")
    lines.append("Notes:")
    lines.append("- Only explicitly extracted onboarding data is applied.")
    lines.append("- Empty onboarding values do not overwrite existing values.")
    return "\n".join(lines) + "\n"
