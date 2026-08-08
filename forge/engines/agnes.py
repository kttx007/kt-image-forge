"""
Agnes 生图引擎

通过 Agnes API Hub 调用 agnes-image-2.1-flash。
开源血统: agnes-mcp (github.com/kttx007/agnes-mcp) 封装的 API 接口

API 规范:
  Base URL: https://apihub.agnes-ai.com
  Endpoint: /v1/images/generations
  Model: agnes-image-2.1-flash
  支持 text2img / img2img / compose
"""

import base64
import requests
from pathlib import Path
from typing import Optional
from .base import ImageEngine, GenerationResult


class AgnesEngine(ImageEngine):
    """Agnes 生图引擎"""

    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[Path] = None,
        reference_image: Optional[Path] = None,
    ) -> GenerationResult:
        url = f"{self.base_url}/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }

        # img2img / compose 模式
        if reference_image and reference_image.exists():
            img_b64 = base64.b64encode(reference_image.read_bytes()).decode()
            body["extra_body"] = {
                "image": [img_b64],
                "response_format": "b64_json",
            }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=300)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("data", [])
            if not items:
                return GenerationResult(
                    success=False,
                    error="No images returned",
                    engine_name=self.name,
                )

            first = items[0]

            # b64_json 响应
            if first.get("b64_json"):
                img_bytes = base64.b64decode(first["b64_json"])
            # URL 响应
            elif first.get("url"):
                img_resp = requests.get(first["url"], timeout=120)
                img_resp.raise_for_status()
                img_bytes = img_resp.content
            else:
                return GenerationResult(
                    success=False,
                    error="No b64_json or url in response",
                    engine_name=self.name,
                )

            if output_path is None:
                output_path = Path(f"output_{self.name}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(img_bytes)

            return GenerationResult(
                success=True,
                image_path=output_path,
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
            url = f"{self.base_url}/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
