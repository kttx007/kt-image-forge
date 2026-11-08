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


def style_authority_for_loop() -> Dict[str, Any]:
    tokens = load_tokens()
    anchor = load_brand_anchor()
    direction = load_brand_direction()
    return {
        "set_id": anchor.get("set_id"),
        "direction": direction.get("selected"),
        "rejected": direction.get("rejected") or anchor.get("rejected_direction"),
        "tokens": tokens.get("colors"),
        "typography": tokens.get("typography"),
        "positioning_line": anchor.get("positioning_line"),
        "primary_mode": anchor.get("primary_mode"),
        "secondary_mode": anchor.get("secondary_mode"),
        "rhythm_rule": anchor.get("rhythm_rule"),
        "image_method": anchor.get("image_method"),
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
