"""Recoverable slot state machine — plan → bundle → audit → lock."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .audit_gates import audit_candidate, next_after_failure
from .planner import compile_slot_brief, plan_job


def create_run(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "0.1",
        "job_id": job.get("job_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan": plan_job(job),
        "slots": {
            s["id"]: {
                "status": "planned",
                "attempts": 0,
                "failures": [],
                "locked": False,
            }
            for s in (job.get("slots") or [])
        },
    }


def prepare_slot(job: Dict[str, Any], run: Dict[str, Any], slot_id: str) -> Dict[str, Any]:
    state = run["slots"].get(slot_id)
    if state is None:
        raise ValueError("unknown_slot")
    if state.get("locked"):
        raise ValueError("locked_slot_immutable")
    state["status"] = "bundled"
    return compile_slot_brief(job, slot_id)


def record_audit(run: Dict[str, Any], slot_id: str, audit_input: Dict[str, Any]) -> Dict[str, Any]:
    state = run["slots"].get(slot_id)
    if state is None:
        raise ValueError("unknown_slot")
    result = audit_candidate(
        checks=audit_input.get("checks") or {},
        soft_score=audit_input.get("soft_score") or 0,
    )
    state["attempts"] = int(state.get("attempts") or 0) + 1

    if result["decision"] == "pass":
        state["status"] = "passed"
        return result

    failure = (result.get("failed_hard_gates") or ["soft"])[0]
    action = next_after_failure(state.get("failures") or [], failure)
    state.setdefault("failures", []).append(failure)
    state["status"] = "branch_required" if action == "new_branch" else "repair_requested"
    out = dict(result)
    out["action"] = action
    return out


def lock_slot(run: Dict[str, Any], slot_id: str, artifact: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    state = run["slots"].get(slot_id)
    if not state or state.get("status") != "passed":
        raise ValueError("slot_not_passed")
    state["locked"] = True
    state["status"] = "locked"
    state["artifact"] = artifact or {}
    return state


def run_status(run: Dict[str, Any]) -> Dict[str, int]:
    values = list((run.get("slots") or {}).values())
    return {
        "total": len(values),
        "locked": sum(1 for x in values if x.get("locked")),
        "blocked": sum(1 for x in values if x.get("status") == "branch_required"),
        "pending": sum(1 for x in values if not x.get("locked")),
    }
