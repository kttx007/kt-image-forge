"""
事实卡加载器

从 products/<sku>/facts.yaml 加载冻结事实，供审计和排版使用。
"""

import yaml
from pathlib import Path
from typing import Optional


def load_facts(sku: str, products_dir: Optional[Path] = None) -> dict:
    """
    加载产品事实卡

    Args:
        sku: 产品 SKU，如 "c03"
        products_dir: products 目录路径，None 则用项目根下的 products/

    Returns:
        事实卡字典
    """
    if products_dir is None:
        products_dir = Path(__file__).parent.parent / "products"

    facts_path = products_dir / sku / "facts.yaml"
    if not facts_path.exists():
        raise FileNotFoundError(f"事实卡不存在: {facts_path}")

    with open(facts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_image_plan(sku: str, products_dir: Optional[Path] = None) -> list:
    """
    加载图位规划

    Returns:
        图位列表
    """
    if products_dir is None:
        products_dir = Path(__file__).parent.parent / "products"

    plan_path = products_dir / sku / "image_plan.yaml"
    if not plan_path.exists():
        raise FileNotFoundError(f"图位规划不存在: {plan_path}")

    with open(plan_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("images", [])


def load_forbidden_claims(sku: str, products_dir: Optional[Path] = None) -> list:
    """
    加载禁宣称清单

    Returns:
        禁用词列表
    """
    if products_dir is None:
        products_dir = Path(__file__).parent.parent / "products"

    claims_path = products_dir / sku / "forbidden_claims.md"
    if not claims_path.exists():
        return []

    # 从 markdown 表格中提取禁用词
    claims = []
    lines = claims_path.read_text(encoding="utf-8").splitlines()
    in_table = False
    for line in lines:
        if line.startswith("|") and "禁用项" in line:
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" not in line:
            # 提取第一列
            cells = line.split("|")
            if len(cells) >= 2:
                item = cells[1].strip().replace("**", "")
                if item:
                    claims.append(item)
        elif in_table and not line.startswith("|"):
            in_table = False

    return claims
