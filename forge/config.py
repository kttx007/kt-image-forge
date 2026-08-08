"""
配置管理：密钥从环境变量读取，绝不入仓库。

环境变量:
  KTIF_GPT_IMAGE_BASE_URL  - gpt-image-2 中转 base URL
  KTIF_GPT_IMAGE_API_KEY   - gpt-image-2 中转密钥
  KTIF_AGNES_TOKEN         - Agnes Token Plan 密钥
  KTIF_GEMINI_API_KEY      - Gemini API 密钥
  KTIF_PRODUCT_DIR         - 产品资料根目录（默认 ~/Downloads）
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EngineConfig:
    """单个生图引擎配置"""
    name: str
    base_url: str
    api_key: str
    model: str
    priority: int  # 数字越小优先级越高


@dataclass
class ForgeConfig:
    """全局配置"""
    engines: list = field(default_factory=list)
    product_root: Path = Path(os.environ.get("KTIF_PRODUCT_DIR", str(Path.home() / "Downloads")))
    output_root: Path = Path(os.environ.get("KTIF_OUTPUT_DIR", str(Path.cwd() / "outputs")))
    project_root: Path = Path(__file__).parent.parent

    @classmethod
    def from_env(cls) -> "ForgeConfig":
        """从环境变量加载配置"""
        engines = []

        # 1. gpt-image-2（最高优先级）
        gpt_key = os.environ.get("KTIF_GPT_IMAGE_API_KEY", "")
        gpt_url = os.environ.get("KTIF_GPT_IMAGE_BASE_URL", "https://api.puretokensx.com/v1")
        if gpt_key:
            engines.append(EngineConfig(
                name="gpt-image-2",
                base_url=gpt_url,
                api_key=gpt_key,
                model="gpt-image-2",
                priority=1,
            ))

        # 2. Agnes（次优先级）
        agnes_key = os.environ.get("KTIF_AGNES_TOKEN", "")
        if agnes_key:
            engines.append(EngineConfig(
                name="agnes",
                base_url="https://apihub.agnes-ai.com",
                api_key=agnes_key,
                model="agnes-image-2.1-flash",
                priority=2,
            ))

        # 3. Gemini（兜底）
        gemini_key = os.environ.get("KTIF_GEMINI_API_KEY", "")
        if gemini_key:
            engines.append(EngineConfig(
                name="gemini",
                base_url="https://generativelanguage.googleapis.com",
                api_key=gemini_key,
                model="gemini-2.0-flash-exp-image-generation",
                priority=3,
            ))

        return cls(engines=engines)

    def get_engine(self, name: Optional[str] = None) -> Optional[EngineConfig]:
        """获取指定引擎或最高优先级引擎"""
        if name:
            for e in self.engines:
                if e.name == name:
                    return e
            return None
        return self.engines[0] if self.engines else None
