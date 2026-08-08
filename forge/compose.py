"""
合成排版模块 v2 — 设计驱动

开源血统:
  - Pillow (python-pillow/Pillow, MIT-CMU) — 确定性图像合成
  - OpenCV (opencv/opencv, Apache 2.0) — 图像变换

设计系统:
  - 标题: DIN Alternate Bold (工业科技感)
  - 正文: Avenir Next (现代干净)
  - 色彩: Apple-style 灰度体系 + 产品橙点缀
  - 层次: 投影/渐变/圆角面板
"""

from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np


class DesignSystem:
    """设计系统 v2"""

    # 色彩体系（Apple-style 灰度 + 产品橙）
    INK = (29, 29, 31)           # 主文字 — Apple 深灰
    MUTED = (134, 134, 139)      # 次文字 — Apple 灰
    ORANGE = (241, 137, 34)      # 强调色 — 产品橙
    ORANGE_SOFT = (241, 137, 34, 40)  # 柔和橙
    WHITE = (255, 255, 255)
    BG_LIGHT = (245, 245, 247)   # 浅灰背景
    BG_GRAD_TOP = (250, 250, 252)
    BG_GRAD_BOT = (235, 235, 238)
    DARK_BG = (26, 26, 30)       # 深色背景
    DARK_BG2 = (38, 38, 44)
    PANEL_BG = (255, 255, 255, 240)
    LINE = (220, 220, 225)

    # 字体路径
    FONT_TITLE = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
    FONT_BODY = "/System/Library/Fonts/Avenir Next.ttc"
    FONT_BODY_REG = "/System/Library/Fonts/Avenir.ttc"

    # 字号
    FS_HERO = 52
    FS_TITLE = 36
    FS_SUB = 20
    FS_BODY = 15
    FS_SMALL = 12

    PADDING = 50

    @classmethod
    def font_title(cls, size=None):
        size = size or cls.FS_TITLE
        try:
            return ImageFont.truetype(cls.FONT_TITLE, size)
        except:
            return ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", size)

    @classmethod
    def font_body(cls, size=None, bold=False):
        size = size or cls.FS_BODY
        path = cls.FONT_BODY if bold else cls.FONT_BODY_REG
        try:
            return ImageFont.truetype(path, size)
        except:
            return ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", size)


def _draw_gradient_bg(size, top_color, bot_color):
    """绘制垂直渐变背景"""
    w, h = size
    bg = Image.new("RGB", (w, h))
    pixels = bg.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top_color[0] * (1 - t) + bot_color[0] * t)
        g = int(top_color[1] * (1 - t) + bot_color[1] * t)
        b = int(top_color[2] * (1 - t) + bot_color[2] * t)
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return bg


def _draw_product_shadow(canvas, product_box, intensity=80):
    """在产品下方绘制柔和椭圆投影"""
    x1, y1, x2, y2 = product_box
    cx = (x1 + x2) // 2
    sy = y2 + 5
    sw = (x2 - x1) // 2 + 30
    sh = 25

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse([cx - sw, sy - sh//2, cx + sw, sy + sh//2], fill=(0, 0, 0, intensity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    if canvas.mode != "RGBA":
        canvas = canvas.convert("RGBA")
    return Image.alpha_composite(canvas, shadow)


def _rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def compose_white_bg(
    product_alpha: Image.Image,
    output_size: Tuple[int, int] = (1000, 1000),
    product_width_ratio: float = 0.72,
) -> Image.Image:
    """白底主图 — 产品大、居中、底部投影"""
    w, h = output_size
    # 微妙渐变背景（不是死白）
    bg = _draw_gradient_bg(output_size, (252, 252, 254), (244, 244, 246))

    # 产品缩放
    target_w = int(w * product_width_ratio)
    pw, ph = product_alpha.size
    scale = target_w / pw
    new_h = int(ph * scale)
    product = product_alpha.resize((target_w, new_h), Image.LANCZOS)

    # 居中偏下（视觉重心）
    px = (w - target_w) // 2
    py = int((h - new_h) * 0.45)

    # 投影
    bg = _draw_product_shadow(bg.convert("RGBA"), (px, py, px + target_w, py + new_h))

    # 粘贴产品
    bg.paste(product, (px, py), mask=product.split()[3])
    return bg.convert("RGB")


def compose_scene(
    product_alpha: Image.Image,
    background: Image.Image,
    output_size: Tuple[int, int] = (1000, 1000),
    product_position: str = "bottom_center",
    product_scale: float = 0.50,
) -> Image.Image:
    """场景图 — AI 背景 + 产品叠加 + 投影"""
    w, h = output_size
    bg = background.resize(output_size, Image.LANCZOS).convert("RGBA")

    target_w = int(w * product_scale)
    pw, ph = product_alpha.size
    scale = target_w / pw
    new_h = int(ph * scale)
    product = product_alpha.resize((target_w, new_h), Image.LANCZOS)

    if "bottom" in product_position:
        px = (w - target_w) // 2
        py = h - new_h - 60
    elif product_position == "right":
        px = w - target_w - 60
        py = (h - new_h) // 2
    else:
        px = (w - target_w) // 2
        py = (h - new_h) // 2

    # 投影
    bg = _draw_product_shadow(bg, (px, py, px + target_w, py + new_h), intensity=60)
    bg.paste(product, (px, py), mask=product.split()[3])
    return bg.convert("RGB")


def compose_sellpoint(
    product_alpha: Image.Image,
    background: Optional[Image.Image],
    title: str,
    subtitle: str,
    points: List[str],
    output_size: Tuple[int, int] = (1000, 1000),
    product_side: str = "left",
    bg_style: str = "light",
) -> Image.Image:
    """卖点图 — 设计感排版：大标题 + 编号卖点 + 品牌色装饰线"""
    w, h = output_size

    if background:
        bg = background.resize(output_size, Image.LANCZOS).convert("RGBA")
        # 半透明面板
        panel_w = int(w * 0.42)
        panel_x = 0 if product_side == "right" else w - panel_w
        panel = Image.new("RGBA", (panel_w, h), (255, 255, 255, 235))
        bg.paste(panel, (panel_x, 0), mask=panel)
    elif bg_style == "dark":
        bg = Image.new("RGBA", output_size, DesignSystem.DARK_BG + (255,))
        # 渐变
        grad = _draw_gradient_bg(output_size, DesignSystem.DARK_BG, DesignSystem.DARK_BG2)
        bg = Image.alpha_composite(bg, grad.convert("RGBA"))
    else:
        bg = Image.new("RGBA", output_size, (255, 255, 255, 255))
        grad = _draw_gradient_bg(output_size, DesignSystem.BG_GRAD_TOP, DesignSystem.BG_GRAD_BOT)
        bg = Image.alpha_composite(bg, grad.convert("RGBA"))

    # 产品（占55%，大）
    product_w = int(w * 0.50)
    pw, ph = product_alpha.size
    scale = product_w / pw
    new_h = int(ph * scale)
    product = product_alpha.resize((product_w, new_h), Image.LANCZOS)

    if product_side == "left":
        px = DesignSystem.PADDING
        tx = w // 2 + 30
    else:
        px = w - product_w - DesignSystem.PADDING
        tx = DesignSystem.PADDING + 20

    py = (h - new_h) // 2
    bg = _draw_product_shadow(bg, (px, py, px + product_w, py + new_h))
    bg.paste(product, (px, py), mask=product.split()[3])

    # 文字颜色
    text_color = DesignSystem.WHITE if bg_style == "dark" else DesignSystem.INK
    sub_color = DesignSystem.ORANGE
    muted_color = (180, 180, 185) if bg_style == "dark" else DesignSystem.MUTED

    draw = ImageDraw.Draw(bg)
    f_hero = DesignSystem.font_title(DesignSystem.FS_HERO)
    f_sub = DesignSystem.font_body(DesignSystem.FS_SUB, bold=True)
    f_body = DesignSystem.font_body(DesignSystem.FS_BODY)

    # 橙色装饰线
    draw.rectangle([tx, DesignSystem.PADDING + 10, tx + 40, DesignSystem.PADDING + 13], fill=DesignSystem.ORANGE)

    # 标题
    draw.text((tx, DesignSystem.PADDING + 25), title, fill=text_color, font=f_hero)

    # 副标题
    sub_y = DesignSystem.PADDING + 25 + DesignSystem.FS_HERO + 12
    draw.text((tx, sub_y), subtitle, fill=sub_color, font=f_sub)

    # 卖点（编号式，不是圆点）
    y_cursor = sub_y + DesignSystem.FS_SUB + 35
    for i, pt in enumerate(points):
        # 编号
        num = f"0{i+1}"
        draw.text((tx, y_cursor), num, fill=DesignSystem.ORANGE, font=f_hero)
        # 卖点文字
        draw.text((tx + 55, y_cursor + 8), pt, fill=text_color, font=f_body)
        y_cursor += DesignSystem.FS_BODY + 28

    return bg.convert("RGB")


def compose_spec_table(
    specs: List[Tuple[str, str]],
    product_alpha: Optional[Image.Image] = None,
    output_size: Tuple[int, int] = (1000, 1000),
) -> Image.Image:
    """规格图 — 卡片式布局，不是 Excel 表格"""
    w, h = output_size
    bg = _draw_gradient_bg(output_size, DesignSystem.BG_GRAD_TOP, DesignSystem.BG_GRAD_BOT)

    # 产品缩略图（右上角，带圆角面板背景）
    if product_alpha:
        thumb_w = int(w * 0.38)
        pw, ph = product_alpha.size
        scale = thumb_w / pw
        new_h = int(ph * scale)
        thumb = product_alpha.resize((thumb_w, new_h), Image.LANCZOS)
        tx = w - thumb_w - DesignSystem.PADDING
        ty = DesignSystem.PADDING + 20
        bg = _draw_product_shadow(bg.convert("RGBA"), (tx, ty, tx + thumb_w, ty + new_h), intensity=30)
        bg.paste(thumb, (tx, ty), mask=thumb.split()[3])
        bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    f_header = DesignSystem.font_title(DesignSystem.FS_TITLE)
    f_label = DesignSystem.font_body(DesignSystem.FS_BODY, bold=True)
    f_value = DesignSystem.font_body(DesignSystem.FS_BODY)

    # 标题 + 橙色线
    table_x = DesignSystem.PADDING
    table_y = DesignSystem.PADDING + 10
    draw.rectangle([table_x, table_y, table_x + 40, table_y + 3], fill=DesignSystem.ORANGE)
    draw.text((table_x, table_y + 15), "SPECIFICATIONS", fill=DesignSystem.INK, font=f_header)
    table_y += DesignSystem.FS_TITLE + 35

    # 卡片式参数列表
    col_w = int((w - DesignSystem.PADDING * 2 - 20) * 0.5)
    row_h = 42
    for i, (label, value) in enumerate(specs):
        col = i % 2
        row = i // 2
        cx = table_x + col * (col_w + 20)
        cy = table_y + row * row_h

        # 卡片背景
        _rounded_rect(draw, [cx, cy, cx + col_w, cy + row_h - 8], radius=8,
                      fill=(255, 255, 255), outline=DesignSystem.LINE, width=1)

        # 参数名
        draw.text((cx + 15, cy + 8), label, fill=DesignSystem.MUTED, font=f_label)
        # 参数值
        draw.text((cx + 15, cy + 24), value, fill=DesignSystem.INK, font=f_value)

    return bg


def make_contact_sheet(images: List[Image.Image], cols: int = 3, thumb_size: Tuple[int, int] = (320, 320)) -> Image.Image:
    """Contact sheet — 带间距和标签"""
    rows = (len(images) + cols - 1) // cols
    gap = 15
    sheet_w = cols * thumb_size[0] + (cols + 1) * gap
    sheet_h = rows * thumb_size[1] + (rows + 1) * gap
    sheet = Image.new("RGB", (sheet_w, sheet_h), (240, 240, 245))

    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        x = col * (thumb_size[0] + gap) + gap
        y = row * (thumb_size[1] + gap) + gap
        thumb = img.resize(thumb_size, Image.LANCZOS)
        sheet.paste(thumb, (x, y))

    return sheet
