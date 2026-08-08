"""
合成排版模块

开源血统:
  - Pillow (python-pillow/Pillow, MIT-CMU) — 确定性图像合成
  - OpenCV (opencv/opencv, Apache 2.0) — 图像变换

核心原则: 产品主体是真实抠图像素，AI 不参与合成。确定性代码保证可复现。

前人经验: 排版体系脱胎于 finalize_image2_main_set_v2.py 已验证的视觉规范
  INK=(25,36,38) / MUTED=(82,96,96) / ORANGE=(241,137,34)
  字号梯度: 48px > 24px > 14px（三级，符合视觉层级理论）
"""

from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np


# ── 设计系统常量 ──
class DesignSystem:
    """设计系统：颜色、字体、间距、尺寸"""

    INK = (25, 36, 38)
    MUTED = (82, 96, 96)
    ORANGE = (241, 137, 34)
    WHITE = (255, 255, 255)
    PANEL_BG = (255, 255, 255, 230)

    MAIN_IMAGE_SIZE = (1000, 1000)
    DETAIL_IMAGE_SIZE = (750, 750)
    POSTER_SIZE = (800, 800)
    HERO_SIZE = (1920, 800)

    FONT_FAMILY = "Arial"

    FS_TITLE = 48
    FS_SUBTITLE = 24
    FS_BODY = 14

    PADDING = 40
    PANEL_RADIUS = 12

    @classmethod
    def get_font(cls, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        try:
            path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold \
                else "/System/Library/Fonts/Supplemental/Arial.ttf"
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            try:
                path = "/System/Library/Fonts/Helvetica.ttc"
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                return ImageFont.load_default()


def compose_white_bg(
    product_alpha: Image.Image,
    output_size: Tuple[int, int] = DesignSystem.MAIN_IMAGE_SIZE,
    product_width_ratio: float = 0.79,
) -> Image.Image:
    """白底主图合成（图1）— 纯白背景，产品居中，无文字"""
    canvas = Image.new("RGB", output_size, DesignSystem.WHITE)
    target_w = int(output_size[0] * product_width_ratio)
    w, h = product_alpha.size
    scale = target_w / w
    new_h = int(h * scale)
    product_resized = product_alpha.resize((target_w, new_h), Image.LANCZOS)
    x = (output_size[0] - target_w) // 2
    y = (output_size[1] - new_h) // 2
    canvas.paste(product_resized, (x, y), mask=product_resized.split()[3])
    return canvas


def compose_scene(
    product_alpha: Image.Image,
    background: Image.Image,
    output_size: Tuple[int, int] = DesignSystem.MAIN_IMAGE_SIZE,
    product_position: str = "center",
    product_scale: float = 0.55,
) -> Image.Image:
    """场景图合成（图2）— AI 背景 + 真实产品叠加"""
    bg = background.resize(output_size, Image.LANCZOS).convert("RGB")
    target_w = int(output_size[0] * product_scale)
    w, h = product_alpha.size
    scale = target_w / w
    new_h = int(h * scale)
    product_resized = product_alpha.resize((target_w, new_h), Image.LANCZOS)

    if product_position in ("center", "bottom_center"):
        x = (output_size[0] - target_w) // 2
        y = (output_size[1] - new_h) // 2
        if product_position == "bottom_center":
            y = output_size[1] - new_h - DesignSystem.PADDING
    elif product_position == "bottom":
        x = (output_size[0] - target_w) // 2
        y = output_size[1] - new_h - DesignSystem.PADDING
    elif product_position == "right":
        x = output_size[0] - target_w - DesignSystem.PADDING
        y = (output_size[1] - new_h) // 2
    else:
        x = (output_size[0] - target_w) // 2
        y = (output_size[1] - new_h) // 2

    # 阴影
    shadow = Image.new("RGBA", output_size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [x + 20, y + new_h - 10, x + target_w - 20, y + new_h + 30],
        fill=(0, 0, 0, 60)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    bg_rgba = bg.convert("RGBA")
    bg_rgba = Image.alpha_composite(bg_rgba, shadow)
    bg_rgba.paste(product_resized, (x, y), mask=product_resized.split()[3])
    return bg_rgba.convert("RGB")


def compose_sellpoint(
    product_alpha: Image.Image,
    background: Optional[Image.Image],
    title: str,
    subtitle: str,
    points: List[str],
    output_size: Tuple[int, int] = DesignSystem.MAIN_IMAGE_SIZE,
    product_side: str = "left",
) -> Image.Image:
    """卖点图合成 — 产品 + 排版文案 (FAB 框架 + 格式塔接近性)"""
    if background:
        canvas = background.resize(output_size, Image.LANCZOS).convert("RGBA")
        # 半透明白面板 — 用 paste 而非 alpha_composite（尺寸可能不同）
        panel_w = int(output_size[0] * 0.45)
        panel_x = 0 if product_side == "right" else output_size[0] - panel_w
        panel = Image.new("RGBA", (panel_w, output_size[1]), DesignSystem.PANEL_BG)
        canvas.paste(panel, (panel_x, 0), mask=panel)
    else:
        canvas = Image.new("RGBA", output_size, DesignSystem.WHITE + (255,))

    # 产品缩放到 45% 宽度
    product_w = int(output_size[0] * 0.45)
    w, h = product_alpha.size
    scale = product_w / w
    new_h = int(h * scale)
    product_resized = product_alpha.resize((product_w, new_h), Image.LANCZOS)

    if product_side == "left":
        px = DesignSystem.PADDING
        tx = output_size[0] // 2 + 20
    else:
        px = output_size[0] - product_w - DesignSystem.PADDING
        tx = DesignSystem.PADDING + 20

    py = (output_size[1] - new_h) // 2
    canvas.paste(product_resized, (px, py), mask=product_resized.split()[3])

    # 文字排版
    draw = ImageDraw.Draw(canvas)
    font_title = DesignSystem.get_font(DesignSystem.FS_TITLE)
    font_sub = DesignSystem.get_font(DesignSystem.FS_SUBTITLE)
    font_body = DesignSystem.get_font(DesignSystem.FS_BODY, bold=False)

    # 标题
    draw.text((tx, DesignSystem.PADDING + 20), title, fill=DesignSystem.INK, font=font_title)
    # 副标题
    draw.text((tx, DesignSystem.PADDING + 20 + DesignSystem.FS_TITLE + 10), subtitle,
              fill=DesignSystem.ORANGE, font=font_sub)

    # 卖点列表
    y_cursor = DesignSystem.PADDING + 20 + DesignSystem.FS_TITLE + 10 + DesignSystem.FS_SUBTITLE + 30
    for pt in points:
        draw.ellipse([tx, y_cursor + 5, tx + 8, y_cursor + 13], fill=DesignSystem.ORANGE)
        draw.text((tx + 16, y_cursor), pt, fill=DesignSystem.INK, font=font_body)
        y_cursor += DesignSystem.FS_BODY + 16

    return canvas.convert("RGB")


def compose_spec_table(
    specs: List[Tuple[str, str]],
    product_alpha: Optional[Image.Image] = None,
    output_size: Tuple[int, int] = DesignSystem.MAIN_IMAGE_SIZE,
) -> Image.Image:
    """规格图合成 — 参数表 + 产品缩略图 (FAB Feature 层 + 视觉层级三级)"""
    canvas = Image.new("RGB", output_size, DesignSystem.WHITE)
    draw = ImageDraw.Draw(canvas)

    font_header = DesignSystem.get_font(DesignSystem.FS_SUBTITLE)
    font_label = DesignSystem.get_font(DesignSystem.FS_BODY)
    font_value = DesignSystem.get_font(DesignSystem.FS_BODY, bold=False)

    # 产品缩略图（右上角）
    if product_alpha:
        thumb_w = int(output_size[0] * 0.35)
        w, h = product_alpha.size
        scale = thumb_w / w
        new_h = int(h * scale)
        thumb = product_alpha.resize((thumb_w, new_h), Image.LANCZOS)
        tx = output_size[0] - thumb_w - DesignSystem.PADDING
        ty = DesignSystem.PADDING
        canvas.paste(thumb, (tx, ty), mask=thumb.split()[3])

    # 表格
    table_x = DesignSystem.PADDING
    table_y = DesignSystem.PADDING + 10
    col_label_w = int((output_size[0] - DesignSystem.PADDING * 2) * 0.4)
    col_value_x = table_x + col_label_w + 20
    row_h = 36

    draw.text((table_x, table_y), "SPECIFICATIONS", fill=DesignSystem.INK, font=font_header)
    table_y += DesignSystem.FS_SUBTITLE + 20

    for label, value in specs:
        draw.text((table_x, table_y), label, fill=DesignSystem.MUTED, font=font_label)
        draw.text((col_value_x, table_y), value, fill=DesignSystem.INK, font=font_value)
        draw.line(
            [(table_x, table_y + row_h - 8), (output_size[0] - DesignSystem.PADDING, table_y + row_h - 8)],
            fill=(230, 230, 230), width=1
        )
        table_y += row_h

    return canvas


def make_contact_sheet(images: List[Image.Image], cols: int = 3, thumb_size: Tuple[int, int] = (300, 300)) -> Image.Image:
    """生成 contact sheet（预览总览图）"""
    rows = (len(images) + cols - 1) // cols
    sheet_w = cols * thumb_size[0] + (cols + 1) * 10
    sheet_h = rows * thumb_size[1] + (rows + 1) * 10
    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 245, 245))

    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        x = col * (thumb_size[0] + 10) + 10
        y = row * (thumb_size[1] + 10) + 10
        thumb = img.resize(thumb_size, Image.LANCZOS)
        sheet.paste(thumb, (x, y))

    return sheet
