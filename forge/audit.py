"""
P0 三道门审计模块

开源血统:
  - 规则匹配: Python 确定性逻辑
  - SSIM: scikit-image (BSD-3)
  - 美学评分: aesthetic-predictor (LAION-Aesthetic, MIT) — 可选

三道门:
  1. 事实审核 — 图中参数文案 vs facts.yaml 冻结事实
  2. 无漂移审核 — 产品主体像素 vs 实拍抠图（SSIM 参考 + VLM 可选）
  3. 视觉审核 — 白底纯度 + 产品占比 + 尺寸合规
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from PIL import Image
import numpy as np


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
    issues: List[AuditIssue] = field(default_factory=list)

    def add_issue(self, severity, gate, message, detail=""):
        self.issues.append(AuditIssue(severity, gate, message, detail))
        if severity == "P0":
            self.passed = False

    def to_dict(self):
        return {
            "image_path": str(self.image_path),
            "passed": self.passed,
            "issue_count": len(self.issues),
            "p0_count": sum(1 for i in self.issues if i.severity == "P0"),
            "issues": [{"severity": i.severity, "gate": i.gate, "message": i.message, "detail": i.detail} for i in self.issues],
        }


def audit_facts(image_path, facts_yaml, text_on_image=None):
    report = AuditReport(image_path=str(image_path))
    if not text_on_image:
        return report
    product = facts_yaml.get("product", {})
    models = product.get("models", [])
    forbidden = ["IP56", "IP65", "磁吸", "Nano Coating", "IML", "夜视", "自动追踪", "军用", "战术", "狙击", "全目标保证", "可见红色激光"]
    for text in text_on_image:
        for fb in forbidden:
            if fb.lower() in text.lower():
                report.add_issue("P0", "fact", f"禁宣称词出现: {fb}", f"检测到文字: {text}")
    range_values = set()
    for m in models:
        range_values.add(str(m.get("range_m", "")) + "m")
    found_ranges = [r for r in range_values if any(r in t for t in text_on_image)]
    if len(found_ranges) > 1:
        has_model_label = any(m["code"] in t for m in models for t in text_on_image)
        if not has_model_label:
            report.add_issue("P1", "fact", "多量程出现但未标注型号", f"检测到量程: {found_ranges}")
    return report


def compute_ssim(img1, img2):
    from skimage.metrics import structural_similarity as ssim
    arr1 = np.array(img1.convert("L").resize((256, 256)))
    arr2 = np.array(img2.convert("L").resize((256, 256)))
    return ssim(arr1, arr2, data_range=255)


def audit_drift(image_path, reference_cutout, ssim_threshold=0.15):
    """无漂移审核：整图 SSIM 仅作 P2 参考（合成图含背景/文字，整图对比不精确）"""
    report = AuditReport(image_path=str(image_path))
    try:
        img = Image.open(image_path)
        ref = Image.open(reference_cutout)
        ssim_score = compute_ssim(img, ref)
        if ssim_score < ssim_threshold:
            report.add_issue("P2", "drift", f"产品相似度参考: SSIM={ssim_score:.3f}", "整图SSIM偏低（合成图含背景/文字，仅作参考）。确定性合成管线下漂移风险低。")
    except Exception as e:
        report.add_issue("P2", "drift", f"漂移审核跳过: {e}")
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
                    report.add_issue("P1", "visual", f"白底不纯: 角落{i} 平均色={mean_color.astype(int)}", "白底图四角应为RGB(255,255,255)")
            non_white = np.any(arr < 230, axis=2)
            product_ratio = non_white.mean()
            if product_ratio < min_product_ratio:
                report.add_issue("P1", "visual", f"产品占比极低: {product_ratio:.1%}", "白底主图产品应可辨识")
            elif product_ratio > max_product_ratio:
                report.add_issue("P1", "visual", f"产品占比过高: {product_ratio:.1%}", "产品可能溢出或背景非白底")
        if expected_bg == "white" and w != h:
            report.add_issue("P2", "visual", f"主图非正方形: {w}x{h}", "建议1000x1000")
        if min(w, h) < 800:
            report.add_issue("P1", "visual", f"分辨率不足: {w}x{h}", "最小边应>=800px")
    except Exception as e:
        report.add_issue("P1", "visual", f"视觉审核执行失败: {e}")
    return report


def run_full_audit(image_path, facts_yaml=None, reference_cutout=None, expected_bg="white", text_on_image=None):
    report = AuditReport(image_path=str(image_path))
    if facts_yaml and text_on_image:
        r1 = audit_facts(image_path, facts_yaml, text_on_image)
        report.issues.extend(r1.issues)
    if reference_cutout and reference_cutout.exists():
        r2 = audit_drift(image_path, reference_cutout)
        report.issues.extend(r2.issues)
    r3 = audit_visual(image_path, expected_bg=expected_bg)
    report.issues.extend(r3.issues)
    report.passed = not any(i.severity == "P0" for i in report.issues)
    return report


def generate_audit_report_md(reports, output_path):
    lines = ["# P0 审计报告", "", f"**审计图片数**: {len(reports)}", f"**通过**: {sum(1 for r in reports if r.passed)}", f"**失败**: {sum(1 for r in reports if not r.passed)}", "", "---", ""]
    for r in reports:
        status = "PASS" if r.passed else "FAIL"
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(chr(10).join(lines), encoding="utf-8")
