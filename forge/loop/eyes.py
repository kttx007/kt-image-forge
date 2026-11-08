"""
Thin bridge to ai-eyes (MiniMax-M3 / Gemini) for visual audit.

Does not invent a parallel VLM path. Prefer vendor/ai-eyes/eyes.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Optional

VENDOR_EYES = Path(__file__).resolve().parents[2] / "vendor" / "ai-eyes" / "eyes.py"


def load_eyes_module():
    if not VENDOR_EYES.exists():
        raise FileNotFoundError(
            f"ai-eyes not found at {VENDOR_EYES}. Clone github.com/kttx007/ai-eyes into vendor/ai-eyes."
        )
    spec = importlib.util.spec_from_file_location("kt_ai_eyes", VENDOR_EYES)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load ai-eyes module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kt_ai_eyes"] = mod
    spec.loader.exec_module(mod)
    return mod


def understand_image(
    image_path: str,
    prompt: str,
    *,
    provider: str = "minimax",
    dry_run: bool = False,
) -> str:
    """Ask MiniMax-M3 (default) or Gemini to describe / audit an image."""
    eyes = load_eyes_module()
    # eyes.py CLI helpers are argparse-based; call request builders if present,
    # otherwise shell out through its main entrypoints via dry-run-safe path.
    if dry_run:
        return f"[dry-run] provider={provider} image={image_path} prompt={prompt}"

    # Prefer programmatic path if available
    if hasattr(eyes, "run_image"):
        return eyes.run_image(image_path, prompt, provider=provider)

    # Fallback: invoke as CLI module
    import subprocess

    cmd = [
        sys.executable,
        str(VENDOR_EYES),
        "image",
        image_path,
        prompt,
        "--provider",
        provider,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "eyes failed")
    return proc.stdout.strip()


def product_identity_prompt(sku: str, invariants: Optional[list] = None) -> str:
    inv = invariants or [
        "silhouette/proportions",
        "holes/apertures/ports",
        "buttons/screen/labels",
        "seams/housing geometry",
        "logo/model identity",
    ]
    bullets = "\n".join(f"- {x}" for x in inv)
    return (
        f"You are auditing SKU {sku} product identity for ecommerce.\n"
        f"Check buyer-visible structure only (not microscopic texture):\n{bullets}\n"
        "Reply with PASS or FAIL and a short evidence list. Soft aesthetic comments last."
    )
