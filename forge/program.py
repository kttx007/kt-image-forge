"""Store program loader — P1 12×14 / 83 SKU contract from governance/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance"


def load_json(name: str) -> Dict[str, Any]:
    path = GOV / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry() -> Dict[str, Any]:
    return load_json("PRODUCTION_REGISTRY.json")


def load_program_summary() -> Dict[str, Any]:
    return load_json("PROGRAM_SUMMARY.json")


def expected_slot_ids(summary: Dict[str, Any] | None = None) -> List[str]:
    summary = summary or load_program_summary()
    mains = [f"M{i:02d}" for i in range(1, int(summary["mains_per_model"]) + 1)]
    details = [f"D{i:02d}" for i in range(1, int(summary["details_per_model"]) + 1)]
    return mains + details


def build_default_job_skeleton(sku: str, style: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Create a LOOP job with the standard 14 slots for one SKU."""
    summary = load_program_summary()
    kinds = summary.get("slot_kinds_default") or {}
    brand = load_json("BRAND_SYSTEM_ANCHOR.json")
    style = style or {
        "name": brand.get("set_id"),
        "keywords": [brand.get("brand_base"), brand.get("primary_mode"), brand.get("secondary_mode")],
        "avoid": [brand.get("rejected_direction"), "cheap sci-fi", "warm-white oversized number template"],
        "tokens": brand.get("frozen_tokens"),
    }
    slots = []
    for sid in expected_slot_ids(summary):
        slots.append(
            {
                "id": sid,
                "kind": kinds.get(sid, "normal_detail"),
                "role": "hook" if sid == "M01" else ("macro" if sid.startswith("M") else "detail"),
                "buyer_question": f"What should slot {sid} prove for {sku}?",
                "dominant_message": f"{sku} {sid} — material-led, one claim",
                "claim_ids": [],
            }
        )
    return {
        "job_id": f"{sku}-p1-set",
        "product": {"sku": sku},
        "style": style,
        "product_identity": [
            {
                "rule": "Preserve buyer-visible housing geometry, apertures, ports, buttons, screen, labels.",
                "scopes": ["*"],
            }
        ],
        "physical_rules": [
            {
                "rule": "Active laser scenes: small-emitter origin, device-axis alignment, opaque target.",
                "scopes": ["M04", "D03", "D04"],
            }
        ],
        "claims": [],
        "slots": slots,
    }


def validate_program_counts() -> Dict[str, Any]:
    reg = load_registry()
    summary = load_program_summary()
    scope = reg["scope"]
    ok = (
        scope["models"] == summary["p1_models_target"]
        and scope["main_images_per_model"] == summary["mains_per_model"]
        and scope["detail_images_per_model"] == summary["details_per_model"]
        and scope["required_product_images"] == summary["p1_image_slots"]
        and summary["p1_image_slots"]
        == summary["p1_models_target"] * summary["slots_per_model"]
    )
    return {
        "ok": ok,
        "p1_image_slots": summary["p1_image_slots"],
        "expected_slots_per_model": len(expected_slot_ids(summary)),
        "accepted_complete_sets": summary.get("accepted_complete_sets", 0),
        "public_release": reg.get("public_release", False),
    }
