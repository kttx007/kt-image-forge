from forge.program import (
    build_default_job_skeleton,
    expected_slot_ids,
    load_registry,
    validate_program_counts,
)
from forge.loop import choose_render_mode, create_run, plan_job
from forge.brand import hard_style_avoids, style_authority_for_loop


def test_registry_drive_authorities_present():
    reg = load_registry()
    drives = reg["drive_authorities"]
    assert "codex_laser_store" in drives
    assert "brand_design_os" in drives
    assert drives["codex_laser_store"].endswith("1anOjVul_RUxNkBRgS55Fgvimg0fx8AcR")
    assert drives["brand_design_os"].endswith("1D9pw5pspSKHtINSahkGOnCO8PTXtrjEY")


def test_program_counts_consistent():
    result = validate_program_counts()
    assert result["ok"] is True
    assert result["p1_image_slots"] == 168
    assert result["expected_slots_per_model"] == 14
    assert result["accepted_complete_sets"] == 0
    assert result["public_release"] is False


def test_default_job_has_fourteen_slots_and_routes():
    job = build_default_job_skeleton("C03")
    assert len(job["slots"]) == 14
    assert expected_slot_ids() == [s["id"] for s in job["slots"]]
    assert choose_render_mode(job["slots"][0]) == "whole_image_generation"
    # D06 is dense_fact_detail → hybrid
    d06 = next(s for s in job["slots"] if s["id"] == "D06")
    assert choose_render_mode(d06) == "hybrid_generation"
    run = create_run(job)
    assert run["plan"]["job_id"] == "C03-p1-set"
    assert len(run["slots"]) == 14
    assert plan_job(job)["hard_gates"]


def test_brand_authority_rejects_warm_white_template():
    style = style_authority_for_loop()
    avoids = hard_style_avoids()
    assert style["tokens"]["brand_blue"] == "#2260AB"
    assert any("warm-white" in a.lower() or "warm white" in a.lower() or "暖白" in a or "warm-white" in str(style["rejected"]).lower() for a in avoids + [style["rejected"]])
