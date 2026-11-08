"""Brand DesignOS helpers — tokens + style authority for LOOP briefs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_tokens() -> Dict[str, Any]:
    return json.loads((ROOT / "brand" / "tokens.json").read_text(encoding="utf-8"))


def load_brand_anchor() -> Dict[str, Any]:
    return json.loads((ROOT / "governance" / "BRAND_SYSTEM_ANCHOR.json").read_text(encoding="utf-8"))


def load_brand_direction() -> Dict[str, Any]:
    return json.loads((ROOT / "governance" / "BRAND_DIRECTION_APPROVAL.json").read_text(encoding="utf-8"))


def frozen_color_tokens(tokens: Dict[str, Any] | None = None) -> Dict[str, str]:
    """Resolve LOOP-facing frozen colors from DesignOS draft or anchor aliases."""
    tokens = tokens or load_tokens()
    if isinstance(tokens.get("colors"), dict) and tokens["colors"].get("brand_blue"):
        return dict(tokens["colors"])
    if isinstance(tokens.get("frozen_colors"), dict) and tokens["frozen_colors"].get("brand_blue"):
        return dict(tokens["frozen_colors"])
    brand = tokens.get("brand") or {}
    return {
        "brand_blue": brand.get("primary") or "#2260AB",
        "accent_orange": brand.get("accent") or "#FF840C",
        "neutral_silver": brand.get("silver") or "#B7B7B7",
        "graphite": brand.get("panel") or "#56555D",
    }


def typography_tokens(tokens: Dict[str, Any] | None = None) -> Dict[str, str]:
    tokens = tokens or load_tokens()
    if isinstance(tokens.get("typography"), dict):
        return dict(tokens["typography"])
    brand = tokens.get("brand") or {}
    return {
        "latin": brand.get("fontLatin") or "Inter",
        "cjk": brand.get("fontCJK") or "Noto Sans CJK SC / 思源黑体",
    }


def style_authority_for_loop() -> Dict[str, Any]:
    tokens = load_tokens()
    anchor = load_brand_anchor()
    direction = load_brand_direction()
    return {
        "set_id": anchor.get("set_id"),
        "direction": direction.get("selected"),
        "rejected": direction.get("rejected") or anchor.get("rejected_direction"),
        "tokens": frozen_color_tokens(tokens),
        "typography": typography_tokens(tokens),
        "positioning_line": anchor.get("positioning_line"),
        "primary_mode": anchor.get("primary_mode"),
        "secondary_mode": anchor.get("secondary_mode"),
        "rhythm_rule": anchor.get("rhythm_rule"),
        "image_method": anchor.get("image_method"),
        "style_intelligence": {
            "reference_role": "style_reference",
            "do_not_use_as_identity": True,
            "maturity": "experimental_validated_main_image",
        },
    }


def hard_style_avoids() -> List[str]:
    direction = load_brand_direction()
    anchor = load_brand_anchor()
    return [
        x
        for x in [
            direction.get("rejected"),
            anchor.get("rejected_direction"),
            "rainbow palette",
            "collage as default",
            "fiber fusion splicer imagery",
        ]
        if x
    ]


def style_reference_migration_policy() -> Dict[str, Any]:
    """V3.1 Style Intelligence — what may migrate from external visual refs."""
    return {
        "reference_role": "style_reference",
        "do_not_use_as_identity": True,
        "allow": [
            "camera",
            "composition",
            "lighting",
            "materials",
            "space",
            "typography behavior",
            "information density",
            "visual rhythm",
            "thumbnail logic",
            "visual proof mechanism",
        ],
        "forbid": [
            "product identity",
            "structure",
            "facts",
            "claims",
            "certifications",
            "logo",
            "model",
            "ports",
            "buttons",
            "UI",
            "performance",
            "price",
            "warranty",
            "availability",
            "unsupported accessories",
        ],
        "maturity": "experimental_validated_main_image",
        "authority": "docs/visual-factory-os/STYLE_INTELLIGENCE_LAYER_V3_1.md",
    }
