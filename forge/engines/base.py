"""
生图引擎基类

设计原则：
- 每个引擎实现统一接口 generate()
- 引擎只负责生成背景/场景/氛围，不触碰产品主体
- 失败自动降级到下一个引擎（由 pipeline 编排）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class GenerationResult:
    """生图结果"""
    success: bool
    image_path: Optional[Path] = None
    revised_prompt: Optional[str] = None  # API 返回的修正后 prompt
    error: Optional[str] = None
    engine_name: str = ""


class ImageEngine(ABC):
    """生图引擎抽象基类"""

    def __init__(self, config):
        self.name = config.name
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.model = config.model

    @abstractmethod
    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[Path] = None,
        reference_image: Optional[Path] = None,
    ) -> GenerationResult:
        """
        生成图片

        Args:
            prompt: 场景/背景描述 prompt（不含产品主体）
            size: 尺寸，如 "1024x1024", "1536x1024", "1024x1536"
            quality: "high" | "standard"
            output_path: 输出路径，None 则自动生成
            reference_image: 参考图（用于风格引导，不是产品主体）

        Returns:
            GenerationResult
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """检查引擎是否可用"""
        ...
