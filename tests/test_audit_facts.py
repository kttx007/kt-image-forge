"""Fact audit must follow MARKETING_FREEDOM_LOOP evidence ladder, not blanket bans."""

from forge.audit import audit_facts, classify_claim_text


FACTS = {
    "product": {
        "models": [
            {"code": "C03-15", "range_m": 1500},
            {"code": "C03-20", "range_m": 2000},
        ]
    }
}


def test_confirmed_capabilities_are_not_auto_banned():
    # IP65 / magnet / WiFi are confirmed allowed marketing claims for C03.
    report = audit_facts(
        "x.png",
        FACTS,
        text_on_image=["IP65 weather sealed", "Magnetic mount", "WiFi APP"],
    )
    assert report.passed
    assert not any("禁宣称" in i.message for i in report.issues)


def test_false_upgrades_still_fail():
    report = audit_facts(
        "x.png",
        FACTS,
        text_on_image=["Thermal imaging night vision", "IP68 diving", "Auto tracking"],
    )
    assert not report.passed
    assert any(i.severity == "P0" for i in report.issues)


def test_claim_classifier_labels():
    assert classify_claim_text("IP65") == "allowed_confirmed"
    assert classify_claim_text("thermal imaging") == "false_claim"
    assert classify_claim_text("IP56") == "false_claim"
