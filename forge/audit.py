"""
P0 审计模块 — 对齐 visual-factory-loop 四道硬门 + MARKETING_FREEDOM_LOOP

硬门:
  1. fact_truth — 宣称必须有证据梯队支持；禁止明确虚假/跨技术夸张
  2. product_identity — 买家可见结构不得明显漂移（肉眼标准，非整图 SSIM）
  3. physical_truth — 轴向/发射端/目标终止等物理关系
  4. locked_slot_immutability — 已锁槽位不重做（由 forge.loop 状态机执行）

开源血统:
  - 规则匹配: Python 确定性逻辑
  - SSIM: scikit-image (BSD-3) — 仅作参考，不再单独硬拒绝合成图
  - alpha-edge: photoclean-pipeline 思路
  - VLM: ai-eyes / MiniMax-M3（可选）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image

# Confirmed-allowed C03 marketing terms (evidence ladder 1-3). Not a ban list.
ALLOWED_CONFIRMED = {
    "ip65",
    "磁吸",
    "magnetic",
    "wifi",
    "app",
    "pip",
    "picture-in-picture",
    "画中画",
    "7x",
    "auto focus",
    "autofocus",
}

# Explicit false / over-claim terms. Keep short — Constraint Budget.
FALSE_CLAIMS = {
    "ip56": "wrong IP rating; confirmed is IP65",
    "ip67": "upgrade not confirmed",
    "ip68": "upgrade not confirmed",
    "thermal": "thermal imaging not a product capability",
    "thermal imaging": "thermal imaging not a product capability",
    "热成像": "thermal imaging not a product capability",
    "军用": "military-grade night vision not confirmed",
    "战术": "tactical framing prohibited",
    "狙击": "sniper framing prohibited",
    "自动追踪": "auto tracking not confirmed",
    "auto tracking": "auto tracking not confirmed",
    "可见红色激光": "905nm Class 1 must not be shown as visible red beam",
    "visible red laser": "905nm Class 1 must not be shown as visible red beam",
}


@dataclass
class AuditIssue:
    severity: str
    gate: str
    message: str
    detail: str = ""


@dataclass
class AuditReport:
    image_path: str
    passed: bool = True
    decision: str = "PASS — Strong"
    issues: List[AuditIssue] = field(default_factory=list)

    def add_issue(self, severity, gate, message, detail=""):
        self.issues.append(AuditIssue(severity, gate, message, detail))
        if severity == "P0":
            self.passed = False

    def to_dict(self):
        return {
            "image_path": str(self.image_path),
            "passed": self.passed,
            "decision": self.decision,
            "issue_count": len(self.issues),
            "p0_count": sum(1 for i in self.issues if i.severity == "P0"),
            "issues": [
                {
                    "severity": i.severity,
                    "gate": i.gate,
                    "message": i.message,
                    "detail": i.detail,
                }
                for i in self.issues
            ],
        }


def classify_claim_text(text: str) -> str:
    lower = text.lower()
    for term in FALSE_CLAIMS:
        if term in lower:
            return "false_claim"
    for term in ALLOWED_CONFIRMED:
        if term in lower:
            return "allowed_confirmed"
    return "neutral"


def audit_facts(image_path, facts_yaml, text_on_image=None):
    report = AuditReport(image_path=str(image_path))
    if not text_on_image:
        return report

    product = (facts_yaml or {}).get("product", {})
    models = product.get("models", [])

    for text in text_on_image:
        label = classify_claim_text(text)
        if label == "false_claim":
            matched = next(t for t in FALSE_CLAIMS if t in text.lower())
            report.add_issue(
                "P0",
                "fact_truth",
                f"虚假/越界宣称: {matched}",
                f"检测到文字: {text} — {FALSE_CLAIMS[matched]}",
            )

    range_values = {f"{m.get('range_m')}m" for m in models if m.get("range_m") is not None}
    found_ranges = [r for r in range_values if any(r in t for t in text_on_image)]
    if len(found_ranges) > 1:
        has_model_label = any(m.get("code", "") in t for m in models for t in text_on_image)
        if not has_model_label:
            report.add_issue(
                "P1",
                "fact_truth",
                "多量程出现但未标注型号",
                f"检测到量程: {found_ranges}",
            )
    return report


def compute_ssim(img1, img2):
    from skimage.metrics import structural_similarity as ssim

    arr1 = np.array(img1.convert("L").resize((256, 256)))
    arr2 = np.array(img2.convert("L").resize((256, 256)))
    return ssim(arr1, arr2, data_range=255)


def audit_drift(image_path, reference_cutout, ssim_threshold=0.15):
    """
    Identity reference helper only.

    Whole-image SSIM is NOT a hard gate for composed masters (background/text inflate diff).
    Use product-region / VLM / human inspection for product_identity.
    """
    report = AuditReport(image_path=str(image_path))
    try:
        img = Image.open(image_path)
        ref = Image.open(reference_cutout)
        ssim_score = compute_ssim(img, ref)
        report.add_issue(
            "P2",
            "product_identity",
            f"整图 SSIM 参考={ssim_score:.3f}",
            "合成图含背景/文字时整图 SSIM 必然偏低；不作为硬拒绝。请用产品区或 ai-eyes 审计。",
        )
        if ssim_score < ssim_threshold:
            # Keep informational — do not flip passed
            pass
    except Exception as e:
        report.add_issue("P2", "product_identity", f"漂移参考跳过: {e}")
    return report


def audit_visual(image_path, expected_bg="white", min_product_ratio=0.03, max_product_ratio=0.95):
    report = AuditReport(image_path=str(image_path))
    try:
        img = Image.open(image_path).convert("RGB")
        arr = np.array(img)
        h, w = arr.shape[:2]
        if expected_bg == "white":
            corners = [arr[0:20, 0:20], arr[0:20, -20:], arr[-20:, 0:20], arr[-20:, -20:]]
            for i, corner in enumerate(corners):
                mean_color = corner.mean(axis=(0, 1))
                if mean_color.mean() < 240:
                    report.add_issue(
                        "P1",
                        "channel",
                        f"白底不纯: 角落{i} 平均色={mean_color.astype(int)}",
                        "白底图四角应为RGB(255,255,255)",
                    )
            non_white = np.any(arr < 230, axis=2)
            product_ratio = non_white.mean()
            if product_ratio < min_product_ratio:
                report.add_issue("P1", "channel", f"产品占比极低: {product_ratio:.1%}", "白底主图产品应可辨识")
            elif product_ratio > max_product_ratio:
                report.add_issue("P1", "channel", f"产品占比过高: {product_ratio:.1%}", "产品可能溢出或背景非白底")
        if expected_bg == "white" and w != h:
            report.add_issue("P2", "channel", f"主图非正方形: {w}x{h}", "建议1000x1000")
        if min(w, h) < 800:
            report.add_issue("P1", "channel", f"分辨率不足: {w}x{h}", "最小边应>=800px")
    except Exception as e:
        report.add_issue("P1", "channel", f"视觉审核执行失败: {e}")
    return report


def decide_audit_label(report: AuditReport) -> str:
    """Map to MARKETING_FREEDOM_LOOP decision vocabulary."""
    if any(i.severity == "P0" and i.gate == "product_identity" for i in report.issues):
        return "FAIL — Product Drift"
    if any(i.severity == "P0" and i.gate in {"fact_truth", "fact"} for i in report.issues):
        return "FAIL — False Claim"
    if any(i.severity == "P0" for i in report.issues):
        return "FAIL — False Claim"
    if any(i.severity == "P1" for i in report.issues):
        return "REVIEW — Claim Boundary"
    if any(i.severity == "P2" for i in report.issues):
        return "PASS — Safe but Weak"
    return "PASS — Strong"


def run_full_audit(
    image_path,
    facts_yaml=None,
    reference_cutout=None,
    expected_bg="white",
    text_on_image=None,
):
    report = AuditReport(image_path=str(image_path))
    if facts_yaml and text_on_image:
        r1 = audit_facts(image_path, facts_yaml, text_on_image)
        report.issues.extend(r1.issues)
    if reference_cutout and Path(reference_cutout).exists():
        r2 = audit_drift(image_path, reference_cutout)
        report.issues.extend(r2.issues)
    if expected_bg != "any":
        r3 = audit_visual(image_path, expected_bg=expected_bg)
        report.issues.extend(r3.issues)
    report.passed = not any(i.severity == "P0" for i in report.issues)
    report.decision = decide_audit_label(report)
    return report


def generate_audit_report_md(reports, output_path):
    lines = [
        "# P0 审计报告",
        "",
        f"**审计图片数**: {len(reports)}",
        f"**通过**: {sum(1 for r in reports if r.passed)}",
        f"**失败**: {sum(1 for r in reports if not r.passed)}",
        "",
        "---",
        "",
    ]
    for r in reports:
        status = getattr(r, "decision", None) or ("PASS" if r.passed else "FAIL")
        lines.append(f"## {Path(r.image_path).name} — {status}")
        lines.append("")
        if not r.issues:
            lines.append("无问题。")
        else:
            lines.append("| 严重级 | 审计门 | 问题 |")
            lines.append("|--------|--------|------|")
            for issue in r.issues:
                lines.append(f"| {issue.severity} | {issue.gate} | {issue.message} |")
        lines.append("")
        lines.append("---")
        lines.append("")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
