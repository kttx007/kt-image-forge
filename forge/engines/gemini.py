"""
Gemini 生图引擎（兜底）

通过 Google Generative Language API 调用 gemini-2.0-flash-exp-image-generation。
开源血统: Google Gemini API 官方规范

API 规范:
  Base URL: https://generativelanguage.googleapis.com
  Endpoint: /v1beta/models/{model}:generateContent
"""

import base64
import requests
from pathlib import Path
from typing import Optional
from .base import ImageEngine, GenerationResult


class GeminiEngine(ImageEngine):
    """Gemini 生图引擎（兜底）"""

    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[Path] = None,
        reference_image: Optional[Path] = None,
    ) -> GenerationResult:
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        content_parts = [{"text": prompt}]

        # 参考图
        if reference_image and reference_image.exists():
            img_b64 = base64.b64encode(reference_image.read_bytes()).decode()
            content_parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_b64,
                }
            })

        payload = {
            "contents": [{"parts": content_parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
            },
        }

        try:
            resp = requests.post(url, json=payload, params=params, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            # 从响应中提取图片
            candidates = data.get("candidates", [])
            if not candidates:
                return GenerationResult(
                    success=False,
                    error="No candidates in response",
                    engine_name=self.name,
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inline_data" in part:
                    img_b64 = part["inline_data"]["data"]
                    img_bytes = base64.b64decode(img_b64)

                    if output_path is None:
                        output_path = Path(f"output_{self.name}.png")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(img_bytes)

                    return GenerationResult(
                        success=True,
                        image_path=output_path,
                        engine_name=self.name,
                    )

            return GenerationResult(
                success=False,
                error="No image data in response parts",
                engine_name=self.name,
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                engine_name=self.name,
            )

    def health_check(self) -> bool:
        try:
            url = f"{self.base_url}/v1beta/models"
            params = {"key": self.api_key}
            resp = requests.get(url, params=params, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
