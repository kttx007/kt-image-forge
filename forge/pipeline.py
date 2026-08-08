"""
七段流水线编排

forge facts → research → hooks → cutout → scene → compose → audit

每段可独立运行，也可串联执行。
引擎失败自动降级（gpt-image-2 → agnes → gemini）。
"""

import json
from pathlib import Path
from typing import Optional, List
from PIL import Image

from .config import ForgeConfig
from .engines.base import ImageEngine, GenerationResult
from .engines.gpt_image import GPTImageEngine
from .engines.agnes import AgnesEngine
from .engines.gemini import GeminiEngine
from .cutout import process_cutout, refine_edges, alpha_bbox_crop, make_white_bg
from .compose import (
    DesignSystem, compose_white_bg, compose_scene,
    compose_sellpoint, compose_spec_table, make_contact_sheet,
)
from .audit import run_full_audit, generate_audit_report_md, AuditReport
from .facts import load_facts, load_image_plan, load_forbidden_claims


class ForgePipeline:
    """七段流水线"""

    def __init__(self, config: Optional[ForgeConfig] = None):
        self.config = config or ForgeConfig.from_env()
        self._engines: List[ImageEngine] = []
        self._init_engines()

    def _init_engines(self):
        """初始化引擎（按优先级）"""
        for ec in self.config.engines:
            if ec.name == "gpt-image-2":
                self._engines.append(GPTImageEngine(ec))
            elif ec.name == "agnes":
                self._engines.append(AgnesEngine(ec))
            elif ec.name == "gemini":
                self._engines.append(GeminiEngine(ec))

    def generate_with_fallback(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[Path] = None,
    ) -> GenerationResult:
        """
        按优先级尝试引擎，失败自动降级
        """
        for engine in self._engines:
            result = engine.generate(prompt, size, quality, output_path)
            if result.success:
                return result
            print(f"  [引擎降级] {engine.name} 失败: {result.error}")

        return GenerationResult(
            success=False,
            error="所有引擎均失败",
            engine_name="none",
        )

    # ── Stage 1: CUTOUT ──
    def stage_cutout(
        self,
        input_image: Path,
        output_dir: Path,
        name_prefix: str = "product",
    ) -> dict:
        """抠图精修"""
        print(f"[CUTOUT] {input_image.name} → {name_prefix}")
        return process_cutout(input_image, output_dir, name_prefix)

    # ── Stage 2: SCENE (AI 背景生成) ──
    def stage_scene(
        self,
        prompt: str,
        output_path: Path,
        size: str = "1024x1024",
    ) -> Optional[Image.Image]:
        """AI 场景/背景生成（不包含产品主体）"""
        print(f"[SCENE] 生成背景: {prompt[:60]}...")
        result = self.generate_with_fallback(prompt, size=size, output_path=output_path)
        if result.success and result.image_path:
            return Image.open(result.image_path)
        print(f"  [SCENE] 失败: {result.error}")
        return None

    # ── Stage 3: COMPOSE ──
    def stage_compose(
        self,
        plan_item: dict,
        product_alpha: Image.Image,
        output_dir: Path,
    ) -> Path:
        """合成排版"""
        name = plan_item["name"]
        img_type = plan_item["type"]
        size_str = plan_item.get("size", "1000x1000")
        w, h = map(int, size_str.split("x"))
        output_size = (w, h)

        print(f"[COMPOSE] {plan_item['slot']}. {name} ({img_type})")

        if img_type == "white_bg":
            ratio = plan_item.get("product_ratio", 0.79)
            img = compose_white_bg(product_alpha, output_size, ratio)

        elif img_type == "scene_compose":
            bg_prompt = plan_item.get("background_prompt", "")
            bg_path = output_dir / f"{name}_bg.png"
            bg = self.stage_scene(bg_prompt, bg_path)
            if bg is None:
                # 降级：用纯色背景
                bg = Image.new("RGB", output_size, (200, 200, 200))
            pos = plan_item.get("product_position", "center")
            scale = plan_item.get("product_scale", 0.55)
            img = compose_scene(product_alpha, bg, output_size, pos, scale)

        elif img_type == "sellpoint_compose":
            bg_desc = plan_item.get("background", "")
            bg_path = output_dir / f"{name}_bg.png"

            # 尝试 AI 背景
            bg = None
            if "户外" in bg_desc or "outdoor" in bg_desc.lower():
                bg_prompt = f"Premium product photography background, {bg_desc}, cinematic lighting, no people, no text, high-end commercial style"
                bg = self.stage_scene(bg_prompt, bg_path)
            elif "深色" in bg_desc or "dark" in bg_desc.lower():
                bg_prompt = f"Dark premium technology background, gradient from deep navy to black, subtle tech texture, cinematic lighting, no people, no text"
                bg = self.stage_scene(bg_prompt, bg_path)

            title = plan_item.get("title", "")
            subtitle = plan_item.get("subtitle", "")
            points = plan_item.get("points", [])
            img = compose_sellpoint(product_alpha, bg, title, subtitle, points, output_size)

        elif img_type == "spec_table":
            specs = [(s[0], s[1]) for s in plan_item.get("specs", [])]
            img = compose_spec_table(specs, product_alpha, output_size)

        else:
            print(f"  [COMPOSE] 未知类型: {img_type}")
            img = compose_white_bg(product_alpha, output_size)

        output_path = output_dir / f"{plan_item['slot']:02d}_{name}.png"
        img.save(output_path, "PNG")
        print(f"  → {output_path.name}")
        return output_path

    # ── Stage 4: AUDIT ──
    def stage_audit(
        self,
        image_path: Path,
        facts: dict,
        reference_cutout: Path,
        expected_bg: str = "white",
        text_on_image: Optional[List[str]] = None,
    ) -> AuditReport:
        """P0 三道门审计"""
        print(f"[AUDIT] {image_path.name}")
        return run_full_audit(image_path, facts, reference_cutout, expected_bg, text_on_image)

    # ── 完整流水线 ──
    def run_full(
        self,
        sku: str,
        source_image: Path,
        output_dir: Path,
    ) -> dict:
        """
        完整七段流水线

        Args:
            sku: 产品 SKU
            source_image: 实拍原图路径
            output_dir: 输出目录

        Returns:
            {"cutout": dict, "images": [Path], "audit": [AuditReport], "contact_sheet": Path}
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # 加载事实与规划
        facts = load_facts(sku)
        plan = load_image_plan(sku)
        forbidden = load_forbidden_claims(sku)
        print(f"[FACTS] SKU={sku}, 规划 {len(plan)} 张图, 禁宣称 {len(forbidden)} 条")

        # Stage 1: CUTOUT
        cutout_result = self.stage_cutout(source_image, output_dir / "cutouts", sku)
        product_alpha = Image.open(cutout_result["alpha"]).convert("RGBA")

        # Stage 2+3: SCENE + COMPOSE (逐图)
        image_paths = []
        audit_reports = []
        for item in plan:
            img_path = self.stage_compose(item, product_alpha, output_dir / "images")
            image_paths.append(img_path)

            # Stage 4: AUDIT
            bg_type = "white" if item.get("type") == "white_bg" else "any"
            if item.get("audit_gate", "").startswith("visual="):
                bg_type = item["audit_gate"].split("=")[1]

            report = self.stage_audit(
                img_path, facts,
                cutout_result["alpha"],
                expected_bg=bg_type,
            )
            audit_reports.append(report)
            status = "✅" if report.passed else "❌"
            print(f"  {status} {'; '.join(i.message for i in report.issues[:3])}")

        # Contact sheet
        images = [Image.open(p) for p in image_paths]
        sheet = make_contact_sheet(images)
        sheet_path = output_dir / "contact_sheet.png"
        sheet.save(sheet_path)

        # 审计报告
        report_path = output_dir / "audit_report.md"
        generate_audit_report_md(audit_reports, report_path)

        print(f"\n[DONE] {len(image_paths)} 张图, 审计 {'全通过' if all(r.passed for r in audit_reports) else '有问题'}")
        print(f"  Contact sheet: {sheet_path}")
        print(f"  Audit report: {report_path}")

        return {
            "cutout": cutout_result,
            "images": image_paths,
            "audit": audit_reports,
            "contact_sheet": sheet_path,
            "audit_report": report_path,
        }
