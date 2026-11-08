"""Hard-gate audit decisions and repair policy (visual-factory-loop)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

HARD = ("fact_truth", "product_identity", "physical_truth")


def audit_candidate(
    checks: Optional[Dict[str, bool]] = None,
    soft_score: float = 0,
) -> Dict[str, Any]:
    checks = checks or {}
    failed_hard = [k for k in HARD if checks.get(k) is False]
    if failed_hard:
        return {
            "decision": "reject",
            "failed_hard_gates": failed_hard,
            "repair_scope": infer_repair_scope(failed_hard),
        }
    return {
        "decision": "pass",
        "failed_hard_gates": [],
        "soft_score": soft_score,
        "note": "pass_with_style_review" if soft_score < 60 else "pass",
    }


def infer_repair_scope(failures: List[str]) -> str:
    if "fact_truth" in failures:
        return "information_region"
    if "product_identity" in failures:
        return "product_region"
    if "physical_truth" in failures:
        return "physical_relation_region"
    return "current_slot"


def next_after_failure(previous_failures: Optional[List[str]] = None, current_failure: str = "") -> str:
    previous_failures = previous_failures or []
    same = sum(1 for x in previous_failures if x == current_failure)
    return "new_branch" if same >= 1 else "local_repair"
