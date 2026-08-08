"""
gpt-image-2 中转引擎

通过 OpenAI 兼容接口调用 gpt-image-2 模型。
API 参考: https://platform.openai.com/docs/api-reference/images

开源血统: OpenAI Images API 标准接口规范
"""

import base64
import requests
from pathlib import Path
from typing import Optional
from .base import ImageEngine, GenerationResult


class GPTImageEngine(ImageEngine):
    """gpt-image-2 中转引擎"""

    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[Path] = None,
        reference_image: Optional[Path] = None,
    ) -> GenerationResult:
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "b64_json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            img_b64 = data["data"][0].get("b64_json")
            if not img_b64:
                # 有些中转返回 url
                img_url = data["data"][0].get("url")
                if img_url:
                    img_resp = requests.get(img_url, timeout=120)
                    img_resp.raise_for_status()
                    img_bytes = img_resp.content
                else:
                    return GenerationResult(
                        success=False,
                        error="No b64_json or url in response",
                        engine_name=self.name,
                    )
            else:
                img_bytes = base64.b64decode(img_b64)

            if output_path is None:
                output_path = Path(f"output_{self.name}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(img_bytes)

            revised = data["data"][0].get("revised_prompt")

            return GenerationResult(
                success=True,
                image_path=output_path,
                revised_prompt=revised,
                engine_name=self.name,
            )

        except requests.exceptions.HTTPError as e:
            err_body = ""
            try:
                err_body = resp.text[:500]
            except Exception:
                pass
            return GenerationResult(
                success=False,
                error=f"HTTP {e}: {err_body}",
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
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
