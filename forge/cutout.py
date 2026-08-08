"""
抠图精修模块

开源血统:
  - rembg (danielgatis/rembg, MIT) — ONNX 驱动通用抠图
  - Pillow (python-pillow/Pillow, MIT-CMU) — 边缘精修
  - OpenCV (opencv/opencv, Apache 2.0) — alpha bbox 裁剪

管线: rembg 粗抠 → MinFilter 去毛刺 → GaussianBlur 羽化 → alpha bbox 裁剪 → 白底版 + 透明版

前人经验: 本管线脱胎于 compose_real_white_v08.py 中已验证的边缘处理模式
  (MinFilter(3) + GaussianBlur(0.35) 组合在实拍图上表现最优)
"""

import io
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageFilter
import numpy as np


def remove_background(input_path: Path, output_alpha: Optional[Path] = None) -> Image.Image:
    """
    使用 rembg 去除背景，返回 RGBA 图像

    Args:
        input_path: 输入图片路径
        output_alpha: 可选，保存透明版 PNG 的路径

    Returns:
        RGBA PIL Image
    """
    from rembg import remove

    input_bytes = input_path.read_bytes()
    output_bytes = remove(input_bytes)
    img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    if output_alpha:
        output_alpha.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_alpha)

    return img


def refine_edges(alpha_img: Image.Image) -> Image.Image:
    """
    边缘精修：MinFilter 去毛刺 + 轻微 GaussianBlur 羽化

    前人经验: MinFilter(3) 去除 1px 残留杂色，GaussianBlur(0.35) 羽化硬边
    """
    # 分离 alpha 通道
    r, g, b, a = alpha_img.split()

    # MinFilter 去毛刺（取 3x3 最小值，去除散点）
    a_refined = a.filter(ImageFilter.MinFilter(3))

    # 轻微羽化
    a_refined = a_refined.filter(ImageFilter.GaussianBlur(0.35))

    return Image.merge("RGBA", (r, g, b, a_refined))


def alpha_bbox_crop(alpha_img: Image.Image, padding: int = 10) -> Image.Image:
    """
    用 alpha 通道的 bbox 裁剪出产品主体区域

    Args:
        alpha_img: RGBA 图像
        padding: 边距像素

    Returns:
        裁剪后的 RGBA 图像
    """
    a = alpha_img.split()[3]
    bbox = a.getbbox()
    if bbox:
        # 加 padding
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(alpha_img.width, bbox[2] + padding)
        bottom = min(alpha_img.height, bbox[3] + padding)
        return alpha_img.crop((left, top, right, bottom))
    return alpha_img


def make_white_bg(alpha_img: Image.Image, bg_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """
    将透明背景产品图合成到纯白背景上

    Args:
        alpha_img: RGBA 产品图
        bg_color: 背景色 RGB

    Returns:
        RGB 白底图
    """
    bg = Image.new("RGB", alpha_img.size, bg_color)
    bg.paste(alpha_img, mask=alpha_img.split()[3])
    return bg


def process_cutout(
    input_path: Path,
    output_dir: Path,
    name_prefix: str = "product",
) -> dict:
    """
    完整抠图管线：去背景 → 精修边缘 → bbox 裁剪 → 输出透明版 + 白底版

    Args:
        input_path: 实拍原图路径
        output_dir: 输出目录
        name_prefix: 输出文件名前缀

    Returns:
        {"alpha": Path, "white": Path, "size": (w, h)}
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. rembg 去背景
    alpha_img = remove_background(input_path)

    # 2. 边缘精修
    alpha_img = refine_edges(alpha_img)

    # 3. bbox 裁剪
    alpha_img = alpha_bbox_crop(alpha_img, padding=10)

    # 4. 保存透明版
    alpha_path = output_dir / f"{name_prefix}_alpha.png"
    alpha_img.save(alpha_path)

    # 5. 保存白底版
    white_img = make_white_bg(alpha_img)
    white_path = output_dir / f"{name_prefix}_white.png"
    white_img.save(white_path)

    return {
        "alpha": alpha_path,
        "white": white_path,
        "size": alpha_img.size,
    }


def batch_cutout(
    input_dir: Path,
    output_dir: Path,
    naming_map: Optional[dict] = None,
) -> list:
    """
    批量抠图

    Args:
        input_dir: 实拍图目录
        output_dir: 输出目录
        naming_map: {原始文件名: 输出前缀} 映射，None 则用文件名

    Returns:
        [{"alpha": Path, "white": Path, "source": Path}, ...]
    """
    results = []
    for img_path in sorted(input_dir.glob("*.jpg")):
        prefix = naming_map.get(img_path.name, img_path.stem) if naming_map else img_path.stem
        result = process_cutout(img_path, output_dir, prefix)
        result["source"] = img_path
        results.append(result)
    return results
