"""Store program loader — P1 12×14 / 83 SKU contract from governance/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance"
DATA = GOV / "data"


def load_json(name: str) -> Dict[str, Any]:
    path = GOV / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_data_json(name: str) -> Any:
    path = DATA / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry() -> Dict[str, Any]:
    return load_json("PRODUCTION_REGISTRY.json")


def load_program_summary() -> Dict[str, Any]:
    return load_json("PROGRAM_SUMMARY.json")


def load_p1_models() -> Dict[str, Any]:
    return load_data_json("p1_twelve_models.json")


def load_listing_matrix() -> Dict[str, Any]:
    return load_data_json("listing_execution_matrix_12_models.json")


def load_model_sample_matrix() -> List[Dict[str, Any]]:
    return load_data_json("model_sample_matrix.json")


def load_slot_plan() -> Dict[str, Any]:
    # Prefer Drive-mirrored canonical name; fall back to snake_case alias.
    for name in ("MATERIAL_SCENE_SLOT_PLAN.json", "material_scene_slot_plan.json"):
        path = DATA / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("MATERIAL_SCENE_SLOT_PLAN.json")


def list_p1_model_ids() -> List[str]:
    summary = load_program_summary()
    models = summary.get("p1_models")
    if models:
        return list(models)
    return [row["model"] for row in load_p1_models()["rows"]]


def get_model_row(model: str) -> Dict[str, Any]:
    for row in load_p1_models()["rows"]:
        if row["model"] == model:
            return row
    raise KeyError(f"unknown_p1_model:{model}")


def sample_sku_for_model(model: str) -> str:
    summary = load_program_summary()
    samples = summary.get("p1_sample_skus") or {}
    if model in samples:
        return samples[model]
    return get_model_row(model)["sample_sku"]


def expected_slot_ids(summary: Dict[str, Any] | None = None) -> List[str]:
    summary = summary or load_program_summary()
    mains = [f"M{i:02d}" for i in range(1, int(summary["mains_per_model"]) + 1)]
    details = [f"D{i:02d}" for i in range(1, int(summary["details_per_model"]) + 1)]
    return mains + details


def _slot_purpose_map() -> Dict[str, Dict[str, str]]:
    plan = load_slot_plan()
    sequence = plan.get("sequence") or plan.get("mains") or []
    return {item["slot"]: item for item in sequence if "slot" in item}


def build_default_job_skeleton(
    sku: str,
    style: Dict[str, Any] | None = None,
    *,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a LOOP job with the standard 14 slots for one SKU / P1 model."""
    from forge.brand import hard_style_avoids, style_authority_for_loop

    summary = load_program_summary()
    kinds = summary.get("slot_kinds_default") or {}
    brand = load_json("BRAND_SYSTEM_ANCHOR.json")
    authority = style_authority_for_loop()
    model_row: Dict[str, Any] | None = None
    if model:
        model_row = get_model_row(model)
    else:
        # Infer model when sku matches a sample SKU.
        for mid, sample in (summary.get("p1_sample_skus") or {}).items():
            if sample == sku or mid == sku:
                model = mid
                model_row = get_model_row(mid)
                break

    style = style or {
        "name": brand.get("set_id") or authority.get("set_id"),
        "keywords": [
            brand.get("brand_base"),
            brand.get("primary_mode"),
            brand.get("secondary_mode"),
            (model_row or {}).get("positioning_zh"),
        ],
        "avoid": hard_style_avoids()
        + ["cheap sci-fi", "warm-white oversized number template"],
        "tokens": authority.get("tokens") or brand.get("frozen_tokens"),
        "style_reference_only": True,
    }

    purposes = _slot_purpose_map()
    boundary = (model_row or {}).get("configuration_boundary")
    slots = []
    for sid in expected_slot_ids(summary):
        purpose = purposes.get(sid) or {}
        message = purpose.get("purpose") or f"{sku} {sid} — material-led, one claim"
        if model_row and sid == "M01":
            message = (
                f"{model_row.get('positioning_zh') or sku}: "
                f"{purpose.get('purpose') or 'recognizable product'}"
            )
        slots.append(
            {
                "id": sid,
                "kind": kinds.get(sid, "normal_detail"),
                "role": "hook" if sid == "M01" else ("macro" if sid.startswith("M") else "detail"),
                "buyer_question": purpose.get("purpose")
                or f"What should slot {sid} prove for {sku}?",
                "dominant_message": message,
                "mode": purpose.get("mode"),
                "copy_limit": purpose.get("copy_limit"),
                "slot_rule": purpose.get("rule"),
                "claim_ids": [],
            }
        )

    product: Dict[str, Any] = {"sku": sku}
    if model:
        product["model"] = model
    if model_row:
        product["family"] = model_row.get("family")
        product["primary_keyword"] = model_row.get("primary_keyword")
        product["configuration_boundary"] = boundary

    return {
        "job_id": f"{model or sku}-p1-set",
        "product": product,
        "style": style,
        "product_identity": [
            {
                "rule": "Preserve buyer-visible housing geometry, apertures, ports, buttons, screen, labels.",
                "scopes": ["*"],
            },
            {
                "rule": "Modules are bare boards — never invent finished housing.",
                "scopes": ["*"] if (model_row or {}).get("family") == "module" else [],
            },
        ],
        "physical_rules": [
            {
                "rule": "Active laser scenes: small-emitter origin, device-axis alignment, opaque target.",
                "scopes": ["M04", "D03", "D04"],
            }
        ],
        "claims": [],
        "slots": slots,
        "program": {
            "p1_models_target": summary["p1_models_target"],
            "slots_per_model": summary["slots_per_model"],
            "configuration_boundary": boundary,
        },
    }


def build_p1_job_for_model(model: str, style: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build LOOP job for a named P1 model using its sample SKU."""
    sku = sample_sku_for_model(model)
    return build_default_job_skeleton(sku, style=style, model=model)


def validate_program_counts() -> Dict[str, Any]:
    reg = load_registry()
    summary = load_program_summary()
    scope = reg["scope"]
    models = list_p1_model_ids()
    listing = load_listing_matrix()
    samples = load_model_sample_matrix()
    ok = (
        scope["models"] == summary["p1_models_target"]
        and scope["main_images_per_model"] == summary["mains_per_model"]
        and scope["detail_images_per_model"] == summary["details_per_model"]
        and scope["required_product_images"] == summary["p1_image_slots"]
        and summary["p1_image_slots"]
        == summary["p1_models_target"] * summary["slots_per_model"]
        and len(models) == summary["p1_models_target"]
        and len(listing.get("rows") or []) == summary["p1_models_target"]
        and len(samples) == summary["p1_models_target"]
    )
    return {
        "ok": ok,
        "p1_image_slots": summary["p1_image_slots"],
        "expected_slots_per_model": len(expected_slot_ids(summary)),
        "p1_model_ids": models,
        "accepted_complete_sets": summary.get("accepted_complete_sets", 0),
        "public_release": reg.get("public_release", False),
    }
