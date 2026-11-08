from forge.program import (
    build_default_job_skeleton,
    build_p1_job_for_model,
    expected_slot_ids,
    list_p1_model_ids,
    load_listing_matrix,
    load_model_sample_matrix,
    load_registry,
    load_slot_plan,
    sample_sku_for_model,
    validate_program_counts,
)
from forge.loop import choose_render_mode, create_run, plan_job
from forge.brand import (
    hard_style_avoids,
    style_authority_for_loop,
    style_reference_migration_policy,
)


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
    assert result["p1_model_ids"] == [
        "J14",
        "J13S",
        "J13",
        "J12",
        "J1S",
        "J1",
        "C01",
        "C02",
        "C03",
        "M01",
        "M03",
        "JC02-1",
    ]


def test_twelve_model_matrices_aligned():
    models = list_p1_model_ids()
    listing = load_listing_matrix()
    samples = load_model_sample_matrix()
    assert len(models) == 12
    assert [r["model"] for r in listing["rows"]] == models
    assert [r["model"] for r in samples] == models
    assert sample_sku_for_model("C03") == "C03-20"
    assert sample_sku_for_model("JC02-1") == "JC02-1-12A"
    plan = load_slot_plan()
    assert plan["set_id"].startswith("GUANGYAN-B2B-MATERIAL-SCENE")
    assert len(plan["sequence"]) == 6


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


def test_p1_job_wires_model_boundary_and_slot_purpose():
    job = build_p1_job_for_model("C03")
    assert job["product"]["model"] == "C03"
    assert job["product"]["sku"] == "C03-20"
    assert "7x optical" in job["product"]["configuration_boundary"]
    assert job["slots"][0]["mode"] == "Material-led studio"
    assert job["style"]["style_reference_only"] is True
    module_job = build_p1_job_for_model("M03")
    assert module_job["product"]["family"] == "module"
    bare = [r for r in module_job["product_identity"] if "bare boards" in r["rule"].lower()]
    assert bare and bare[0]["scopes"] == ["*"]


def test_brand_authority_rejects_warm_white_template():
    style = style_authority_for_loop()
    avoids = hard_style_avoids()
    assert style["tokens"]["brand_blue"] == "#2260AB"
    assert style["tokens"]["accent_orange"] == "#FF840C"
    blob = " ".join(avoids + [str(style["rejected"])]).lower()
    assert "warm-white" in blob or "warm white" in blob or "暖白" in blob


def test_style_intelligence_forbids_identity_migration():
    policy = style_reference_migration_policy()
    assert policy["reference_role"] == "style_reference"
    assert policy["do_not_use_as_identity"] is True
    assert "product identity" in policy["forbid"]
    assert "lighting" in policy["allow"]
