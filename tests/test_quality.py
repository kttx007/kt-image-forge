"""Open-source quality metric smoke tests (no rembg/GPU required)."""

from pathlib import Path

import numpy as np
from PIL import Image

from forge.loop.quality import alpha_edge_sharpness, foreground_coverage, cutout_sidecar


def _make_cutout(tmp_path: Path) -> Path:
    arr = np.zeros((128, 128, 4), dtype=np.uint8)
    arr[32:96, 32:96] = [40, 40, 40, 255]
    path = tmp_path / "cutout.png"
    Image.fromarray(arr, mode="RGBA").save(path)
    return path


def test_alpha_edge_and_coverage(tmp_path):
    path = _make_cutout(tmp_path)
    edge = alpha_edge_sharpness(path, threshold=1.0)
    cov = foreground_coverage(path)
    assert edge["edge_pixels"] > 0
    assert edge["score"] > 0
    assert 0.2 < cov["coverage"] < 0.4
    side = cutout_sidecar(path, model="synthetic")
    assert side["sha256"]
    assert side["dimensions"] == [128, 128]
    assert "alpha_edge" in side
