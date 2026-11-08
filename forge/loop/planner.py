"""Slot planner — Constraint Budget + render routing (visual-factory-loop)."""

from __future__ import annotations

from typing import Any, Dict, List

HARD_GATES = (
    "fact_truth",
    "product_identity",
    "physical_truth",
    "locked_slot_immutability",
)

DETERMINISTIC_KINDS = {"spec_table", "legal", "qr", "exact_identifier"}
HYBRID_KINDS = {"dense_fact_detail", "pin_map", "dimension_diagram"}


def choose_render_mode(slot: Dict[str, Any]) -> str:
    kind = slot.get("kind") or "normal_detail"
    if kind in DETERMINISTIC_KINDS:
        return "deterministic_overlay"
    if kind in HYBRID_KINDS:
        return "hybrid_generation"
    return "whole_image_generation"


def _scoped(rules: List[Dict[str, Any]], slot_id: str) -> List[Dict[str, Any]]:
    out = []
    for rule in rules or []:
        scopes = rule.get("scopes")
        if not scopes or slot_id in scopes or "*" in scopes:
            out.append(rule)
    return out


def compile_slot_brief(job: Dict[str, Any], slot_id: str) -> Dict[str, Any]:
    slots = job.get("slots") or []
    slot = next((s for s in slots if s.get("id") == slot_id), None)
    if slot is None:
        raise ValueError("unknown_slot")

    claims_by_id = {c["id"]: c for c in (job.get("claims") or []) if "id" in c}
    claims = [claims_by_id[i] for i in (slot.get("claim_ids") or []) if i in claims_by_id]
    hard_facts: List[Any] = []
    for claim in claims:
        hard_facts.extend(claim.get("evidence") or [])

    return {
        "job_id": job.get("job_id"),
        "slot_id": slot.get("id"),
        "role": slot.get("role"),
        "buyer_question": slot.get("buyer_question"),
        "dominant_message": slot.get("dominant_message"),
        "exact_copy": slot.get("exact_copy") or [],
        "claims": claims,
        "render_mode": choose_render_mode(slot),
        "style": job.get("style"),
        "hard_constraints": {
            "facts": hard_facts,
            "identity": _scoped(job.get("product_identity") or [], slot_id),
            "physics": _scoped(job.get("physical_rules") or [], slot_id),
        },
        "creative_freedom": {
            "composition": "open",
            "lighting": "open",
            "scenario": "open_if_fact_compatible",
            "typography": "open",
            "camera_language": "open",
        },
    }


def plan_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": job.get("job_id"),
        "hard_gates": list(HARD_GATES),
        "slots": [
            {
                "id": s.get("id"),
                "role": s.get("role"),
                "render_mode": choose_render_mode(s),
                "status": s.get("status") or "planned",
            }
            for s in (job.get("slots") or [])
        ],
    }
