"""Provider-neutral manual web handoff bundle."""

from __future__ import annotations

import json
from typing import Any, Dict

from .planner import compile_slot_brief


def build_manual_web_bundle(job: Dict[str, Any], slot_id: str) -> Dict[str, Any]:
    brief = compile_slot_brief(job, slot_id)
    prompt = "\n".join(
        [
            "# TASK",
            str(brief.get("dominant_message") or ""),
            "",
            "# BUYER QUESTION",
            str(brief.get("buyer_question") or ""),
            "",
            "# RENDER MODE",
            str(brief.get("render_mode")),
            "",
            "# STYLE DNA",
            json.dumps(brief.get("style"), ensure_ascii=False, indent=2),
            "",
            "# VERIFIED CLAIMS",
            json.dumps(brief.get("claims"), ensure_ascii=False, indent=2),
            "",
            "# HARD CONSTRAINTS — only these are mandatory",
            json.dumps(brief.get("hard_constraints"), ensure_ascii=False, indent=2),
            "",
            "# CREATIVE FREEDOM",
            "You are free to choose composition, lighting, camera language, typography and scene details when they do not conflict with verified facts, product identity or physical truth.",
            "",
            "# OUTPUT",
            "Generate one complete commercial image. Do not generate an empty background for later assembly unless the render mode explicitly requests deterministic/hybrid output.",
        ]
    )
    return {
        "prompt": prompt,
        "facts": brief["hard_constraints"]["facts"],
        "references": {
            "product_assets": job.get("product_assets") or [],
            "style_references": job.get("style_references") or [],
        },
        "return_instructions": (
            "Save the generated image as candidate.png in this slot bundle. "
            "Do not overwrite locked masters. Then return to the Loop and run audit."
        ),
    }
