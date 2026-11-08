"""
Visual Factory Loop — ported from Codex visual-factory-loop / guangyan-visual-loop.

Hard gates: fact_truth, product_identity, physical_truth, locked_slot_immutability.
Commerce default: whole_image_generation. Dense facts: hybrid / deterministic.
"""

from .planner import HARD_GATES, choose_render_mode, compile_slot_brief, plan_job
from .audit_gates import audit_candidate, infer_repair_scope, next_after_failure
from .engine import create_run, prepare_slot, record_audit, lock_slot, run_status
from .bundle import build_manual_web_bundle
from .quality import alpha_edge_sharpness, foreground_coverage, cutout_sidecar

__all__ = [
    "HARD_GATES",
    "choose_render_mode",
    "compile_slot_brief",
    "plan_job",
    "audit_candidate",
    "infer_repair_scope",
    "next_after_failure",
    "create_run",
    "prepare_slot",
    "record_audit",
    "lock_slot",
    "run_status",
    "build_manual_web_bundle",
    "alpha_edge_sharpness",
    "foreground_coverage",
    "cutout_sidecar",
]
