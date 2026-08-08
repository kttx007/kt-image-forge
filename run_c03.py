#!/usr/bin/env python3
"""
C03 全套图生成脚本

使用已有抠图 + Agnes 引擎（gpt-image-2 降级）生成 6 张主图。
产品主体来自真实抠图，AI 只生成背景/场景。
"""

import sys
import io
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).parent
sys.path.insert(0, str(PROJECT))

import os

from forge.config import ForgeConfig
from forge.pipeline import ForgePipeline
from forge.facts import load_facts, load_image_plan

CUTOUT_ALPHA = Path("/Users/alex/.codex/.chatgpt-projects/g-p-6962239d32088191a084da2effd52bba/outputs/c03_assets/cutouts/C03_FRONT_alpha_v01.png")
CUTOUT_SIDE = Path("/Users/alex/.codex/.chatgpt-projects/g-p-6962239d32088191a084da2effd52bba/outputs/c03_assets/cutouts/C03_SIDE_LEFT_alpha_v01.png")

OUTPUT_DIR = PROJECT / "outputs" / "c03"


def save_image(img, path: Path):
    """保存图片（BytesIO + write_bytes 绕过沙箱限制）"""
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    path.write_bytes(buf.getvalue())


def main():
    cfg = ForgeConfig.from_env()
    pipeline = ForgePipeline(cfg)

    print(f"引擎: {[e.name for e in pipeline._engines]}")
    print(f"输出: {OUTPUT_DIR}")

    facts = load_facts("c03")
    plan = load_image_plan("c03")
    print(f"产品: {facts['product']['sku']}, 图位: {len(plan)}")

    if not CUTOUT_ALPHA.exists():
        print(f"错误: 抠图不存在 {CUTOUT_ALPHA}")
        sys.exit(1)

    product_front = Image.open(CUTOUT_ALPHA).convert("RGBA")
    product_side = Image.open(CUTOUT_SIDE).convert("RGBA") if CUTOUT_SIDE.exists() else product_front
    print(f"抠图: front={product_front.size}, side={product_side.size}")

    image_paths = []
    from forge.compose import (
        compose_white_bg, compose_scene, compose_sellpoint,
        compose_spec_table, make_contact_sheet, DesignSystem
    )

    for item in plan:
        slot = item["slot"]
        name = item["name"]
        img_type = item["type"]
        size_str = item.get("size", "1000x1000")
        w, h = map(int, size_str.split("x"))
        output_size = (w, h)

        print(f"\n{'='*60}")
        print(f"图 {slot}: {name} ({img_type})")

        product = product_front
        if "side" in name.lower() or "scene" in img_type:
            product = product_side

        if img_type == "white_bg":
            ratio = item.get("product_ratio", 0.79)
            img = compose_white_bg(product, output_size, ratio)
            print(f"  白底合成: 产品宽={int(w*ratio)}px on {w}x{h}")

        elif img_type == "scene_compose":
            bg_prompt = item.get("background_prompt", "")
            bg_path = OUTPUT_DIR / "images" / f"{name}_bg.png"
            print(f"  AI背景生成中...")
            bg = pipeline.stage_scene(bg_prompt, bg_path)
            if bg is None:
                print(f"  背景生成失败，用纯色降级")
                bg = Image.new("RGB", output_size, (180, 180, 180))
            pos = item.get("product_position", "center")
            scale = item.get("product_scale", 0.55)
            img = compose_scene(product, bg, output_size, pos, scale)
            print(f"  场景合成: pos={pos}, scale={scale}")

        elif img_type == "sellpoint_compose":
            bg_desc = item.get("background", "")
            bg = None

            if "深色" in bg_desc or "dark" in bg_desc.lower():
                bg_prompt = "Dark premium technology background, deep navy to black gradient, subtle blue tech grid texture, cinematic lighting, no people, no text, no products, high-end commercial"
                bg_path = OUTPUT_DIR / "images" / f"{name}_bg.png"
                print(f"  AI背景生成中 (深色科技)...")
                bg = pipeline.stage_scene(bg_prompt, bg_path)
            elif "户外" in bg_desc or "暖色" in bg_desc:
                bg_prompt = "Warm outdoor sunset background, golden hour lighting, soft bokeh, nature landscape, no people, no text, no products, premium commercial photography backdrop"
                bg_path = OUTPUT_DIR / "images" / f"{name}_bg.png"
                print(f"  AI背景生成中 (户外暖色)...")
                bg = pipeline.stage_scene(bg_prompt, bg_path)

            title = item.get("title", "")
            subtitle = item.get("subtitle", "")
            points = item.get("points", [])
            img = compose_sellpoint(product, bg, title, subtitle, points, output_size)
            print(f"  卖点合成: title='{title[:30]}', {len(points)} points")

        elif img_type == "spec_table":
            specs = [(s[0], s[1]) for s in item.get("specs", [])]
            img = compose_spec_table(specs, product, output_size)
            print(f"  规格表: {len(specs)} rows")

        else:
            print(f"  未知类型: {img_type}, 用白底")
            img = compose_white_bg(product, output_size)

        out_path = OUTPUT_DIR / "images" / f"{slot:02d}_{name}.png"
        save_image(img, out_path)
        image_paths.append(out_path)
        print(f"  -> {out_path.name}")

    # Contact sheet
    print(f"\n{'='*60}")
    images = [Image.open(p) for p in image_paths]
    sheet = make_contact_sheet(images)
    sheet_path = OUTPUT_DIR / "contact_sheet.png"
    save_image(sheet, sheet_path)
    print(f"Contact sheet: {sheet_path}")

    # 审计
    print(f"\n{'='*60}")
    print("P0 审计")
    from forge.audit import run_full_audit, generate_audit_report_md

    audit_reports = []
    for i, (item, img_path) in enumerate(zip(plan, image_paths)):
        bg_type = "white" if item.get("type") == "white_bg" else "any"
        if item.get("audit_gate", "").startswith("visual="):
            bg_type = item["audit_gate"].split("=")[1]

        report = run_full_audit(
            img_path, facts,
            CUTOUT_ALPHA,
            expected_bg=bg_type,
        )
        audit_reports.append(report)
        status = "PASS" if report.passed else "FAIL"
        issues = "; ".join(f"{iss.severity}:{iss.message}" for iss in report.issues[:3])
        print(f"  {status} 图{item['slot']} {item['name']}: {issues or '无问题'}")

    report_path = OUTPUT_DIR / "audit_report.md"
    generate_audit_report_md(audit_reports, report_path)
    print(f"\n审计报告: {report_path}")

    passed = sum(1 for r in audit_reports if r.passed)
    print(f"\n完成: {len(image_paths)} 张图, 审计 {passed}/{len(audit_reports)} 通过")


if __name__ == "__main__":
    main()
