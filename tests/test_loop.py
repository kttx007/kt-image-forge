"""Parity tests with vendor visual-factory-loop/core/test/loop.test.mjs."""

from forge.loop import (
    choose_render_mode,
    create_run,
    record_audit,
    lock_slot,
    prepare_slot,
    run_status,
    compile_slot_brief,
    build_manual_web_bundle,
    HARD_GATES,
)


JOB = {
    "job_id": "t",
    "slots": [{"id": "M01", "kind": "main_image", "role": "hook", "buyer_question": "What is it?", "dominant_message": "Hero"}],
}


def test_whole_image_is_default_for_commerce():
    assert choose_render_mode(JOB["slots"][0]) == "whole_image_generation"


def test_dense_structured_information_routes_hybrid():
    assert choose_render_mode({"kind": "pin_map"}) == "hybrid_generation"
    assert choose_render_mode({"kind": "dimension_diagram"}) == "hybrid_generation"
    assert choose_render_mode({"kind": "spec_table"}) == "deterministic_overlay"


def test_hard_failure_requests_local_repair_first_branch_second():
    run = create_run(JOB)
    r = record_audit(
        run,
        "M01",
        {"checks": {"fact_truth": True, "product_identity": False, "physical_truth": True}},
    )
    assert r["action"] == "local_repair"
    r = record_audit(
        run,
        "M01",
        {"checks": {"fact_truth": True, "product_identity": False, "physical_truth": True}},
    )
    assert r["action"] == "new_branch"
    assert run["slots"]["M01"]["status"] == "branch_required"


def test_passed_slot_can_lock():
    run = create_run(JOB)
    record_audit(
        run,
        "M01",
        {
            "checks": {"fact_truth": True, "product_identity": True, "physical_truth": True},
            "soft_score": 75,
        },
    )
    lock_slot(run, "M01", {"sha256": "abc"})
    assert run["slots"]["M01"]["status"] == "locked"
    assert run_status(run)["locked"] == 1


def test_locked_slot_is_immutable():
    run = create_run(JOB)
    record_audit(
        run,
        "M01",
        {"checks": {"fact_truth": True, "product_identity": True, "physical_truth": True}},
    )
    lock_slot(run, "M01", {"sha256": "abc"})
    try:
        prepare_slot(JOB, run, "M01")
        assert False, "expected locked_slot_immutable"
    except ValueError as e:
        assert str(e) == "locked_slot_immutable"


def test_constraint_budget_only_scoped_physics():
    job = {
        "job_id": "jc02",
        "style": {"name": "bright"},
        "claims": [{"id": "C01", "claim": "range", "evidence": ["ledger only"]}],
        "product_identity": [{"rule": "holes", "scopes": ["*"]}],
        "physical_rules": [
            {"rule": "27.5 long axis", "scopes": ["M02"]},
            {"rule": "laser axis", "scopes": ["M01"]},
        ],
        "slots": [
            {"id": "M01", "kind": "main_image", "role": "hook", "claim_ids": ["C01"], "buyer_question": "q", "dominant_message": "m"},
        ],
    }
    brief = compile_slot_brief(job, "M01")
    assert brief["render_mode"] == "whole_image_generation"
    assert brief["hard_constraints"]["facts"] == ["ledger only"]
    assert len(brief["hard_constraints"]["physics"]) == 1
    assert brief["hard_constraints"]["physics"][0]["rule"] == "laser axis"
    assert set(HARD_GATES) == {
        "fact_truth",
        "product_identity",
        "physical_truth",
        "locked_slot_immutability",
    }


def test_manual_web_bundle_contains_creative_freedom():
    job = {
        "job_id": "t",
        "style": {"name": "x"},
        "claims": [],
        "slots": [{"id": "M01", "kind": "main_image", "role": "hook", "buyer_question": "q", "dominant_message": "Hero"}],
        "product_assets": [{"id": "a"}],
    }
    bundle = build_manual_web_bundle(job, "M01")
    assert "CREATIVE FREEDOM" in bundle["prompt"]
    assert bundle["references"]["product_assets"][0]["id"] == "a"
