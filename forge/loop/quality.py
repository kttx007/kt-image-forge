"""
Open-source quality metrics absorbed into the LOOP.

Sources:
  - Bambushu/photoclean-pipeline — alpha-edge sharpness + needs_review
  - backblaze rembg-product-background-removal — cutout sidecar metadata
  - ozgursntrk/product-bg-replacement-pipeline — structural fidelity mindset
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

PathLike = Union[str, Path]


def _as_rgba(image) -> "Image.Image":
    from PIL import Image

    if isinstance(image, (str, Path)):
        image = Image.open(image)
    return image.convert("RGBA")


def alpha_edge_sharpness(image: PathLike, threshold: float = 12.0) -> Dict[str, Any]:
    """
    Score alpha-edge sharpness. Low scores → needs_review (photoclean-pipeline idea).
    Uses mean absolute gradient on the alpha channel near the silhouette.
    """
    img = _as_rgba(image)
    alpha = np.array(img.split()[3], dtype=np.float32)
    if alpha.size == 0:
        return {"score": 0.0, "needs_review": True, "reason": "empty_alpha"}

    gy, gx = np.gradient(alpha)
    magnitude = np.sqrt(gx * gx + gy * gy)
    edge_mask = magnitude > 1.0
    if not edge_mask.any():
        return {"score": 0.0, "needs_review": True, "reason": "no_alpha_edge"}

    score = float(magnitude[edge_mask].mean())
    return {
        "score": round(score, 3),
        "needs_review": score < threshold,
        "threshold": threshold,
        "edge_pixels": int(edge_mask.sum()),
    }


def foreground_coverage(image: PathLike, alpha_cutoff: int = 16) -> Dict[str, Any]:
    """Proxy for product presence / rembg cutout coverage."""
    img = _as_rgba(image)
    alpha = np.array(img.split()[3])
    fg = alpha > alpha_cutoff
    coverage = float(fg.mean()) if fg.size else 0.0
    return {
        "coverage": round(coverage, 4),
        "foreground_pixels": int(fg.sum()),
        "width": img.width,
        "height": img.height,
    }


def cutout_sidecar(
    image: PathLike,
    *,
    model: str = "rembg",
    processing_ms: Optional[float] = None,
    edge_threshold: float = 12.0,
) -> Dict[str, Any]:
    """Metadata sidecar for a cutout asset (rembg Cutout Studio pattern)."""
    path = Path(image)
    raw = path.read_bytes() if path.exists() else b""
    edge = alpha_edge_sharpness(path if path.exists() else image, threshold=edge_threshold)
    cov = foreground_coverage(path if path.exists() else image)
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "model": model,
        "processing_ms": processing_ms,
        "dimensions": [cov["width"], cov["height"]],
        "foreground_coverage": cov["coverage"],
        "alpha_edge": edge,
        "needs_review": bool(edge.get("needs_review")),
    }
