#!/usr/bin/env python3
"""eyes.py — 多模态理解封装（Codex 的“眼睛”），原生视频输入、不抽帧。

支持两个引擎：
  1. minimax（默认）— MiniMax-M3，OpenAI 兼容接口
     * 图片：image_url（base64 data URI 或公网 URL）
     * 视频：video_url（base64 data URI ≤50MB，或公网 URL；可调 fps/detail）
  2. gemini — Google Gemini 免费档，REST generateContent
     * 图片/视频：inline_data（base64），视频 <100MB 且建议短于 1 分钟

用法:
  python3 eyes.py image <图片路径或URL> "提问" [--provider minimax|gemini]
  python3 eyes.py video <视频路径或URL> "提问" [--provider minimax|gemini] [--fps 1]
  任意命令加 --dry-run 只打印请求体，不发 API，用于自测。

环境变量:
  MINIMAX_API_KEY   使用 minimax 引擎时必需（Token Plan 订阅 Key）
  MINIMAX_API_HOST  默认 https://api.minimaxi.com/v1（国际站可改 https://api.minimax.io/v1）
  MINIMAX_MODEL     默认 MiniMax-M3
  GEMINI_API_KEY    使用 gemini 引擎时必需（https://aistudio.google.com/app/api-keys 免费申请）
  GEMINI_MODEL      默认 gemini-3.5-flash（免费档，可按需改 gemini-3.6-flash 等）

依赖: 仅 Python 标准库。旧版 --frames 抽帧模式需要 ffmpeg，默认不使用。
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


def load_env_file() -> None:
    """自动加载 ~/.codex/ai-eyes.env（不存在或变量已设置时跳过）。"""
    path = os.path.expanduser("~/.codex/ai-eyes.env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                if key.startswith("export "):
                    key = key[len("export "):].strip()
                val = val.strip().strip('"').strip("'")
                if key and val and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


def die(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        die(f"{name} 未设置。请先配置对应引擎的 API Key。")
    return val


def mime_for(filename: str, fallback: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or fallback


def fetch_bytes(path_or_url: str) -> bytes:
    if path_or_url.startswith(("http://", "https://")):
        try:
            with urllib.request.urlopen(path_or_url, timeout=180) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            die(f"下载失败 HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
        except urllib.error.URLError as e:
            die(f"下载失败: {e}")
    if not os.path.isfile(path_or_url):
        die(f"文件不存在: {path_or_url}")
    with open(path_or_url, "rb") as f:
        return f.read()


def basename(path_or_url: str) -> str:
    return os.path.basename(path_or_url.split("?")[0]) or "media.bin"


def is_remote(path_or_url: str) -> bool:
    return path_or_url.startswith(("http://", "https://"))


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def build_minimax_parts(args) -> list[dict]:
    """构造 MiniMax-M3 的 content 数组（text + image_url / video_url）。"""
    parts = []
    name = basename(args.input)
    if args.cmd == "image":
        if is_remote(args.input):
            parts.append({"type": "image_url", "image_url": {"url": args.input}})
        else:
            raw = fetch_bytes(args.input)
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_for(name, 'image/png')};base64,{b64(raw)}"},
            })
    else:
        video = {"type": "video_url", "video_url": {}}
        if is_remote(args.input):
            video["video_url"]["url"] = args.input
        else:
            raw = fetch_bytes(args.input)
            if len(raw) > 50 * 1024 * 1024:
                die("本地视频超过 50MB，MiniMax 不支持 base64 直传。请先上传到公网 URL，或改用 gemini 引擎（<100MB）。")
            video["video_url"]["url"] = f"data:{mime_for(name, 'video/mp4')};base64,{b64(raw)}"
        if getattr(args, "fps", None) is not None:
            video["video_url"]["fps"] = args.fps
        if getattr(args, "detail", None):
            video["video_url"]["detail"] = args.detail
        parts.append(video)
    parts.append({"type": "text", "text": args.prompt})
    return parts


def call_minimax(args, parts: list[dict], dry_run: bool) -> dict:
    body = {
        "model": os.environ.get("MINIMAX_MODEL", "MiniMax-M3"),
        "messages": [{"role": "user", "content": parts}],
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "stream": False,
    }
    if args.thinking:
        body["thinking"] = {"type": "adaptive"}
    if dry_run:
        return {"dry_run": True, "endpoint": "/v1/chat/completions", "body": body}
    req = urllib.request.Request(
        f"{os.environ.get('MINIMAX_API_HOST', 'https://api.minimaxi.com/v1').rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {require_env('MINIMAX_API_KEY')}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        die(f"MiniMax API HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")
    except urllib.error.URLError as e:
        die(f"MiniMax API 请求失败: {e}")


def build_gemini_parts(args) -> list[dict]:
    """构造 Gemini generateContent 的 parts（text + inline_data），原生视频不抽帧。"""
    parts = []
    name = basename(args.input)
    if args.cmd == "image":
        raw = fetch_bytes(args.input)
        parts.append({"inline_data": {"mime_type": mime_for(name, "image/png"), "data": b64(raw)}})
    else:
        raw = fetch_bytes(args.input)
        if len(raw) > 100 * 1024 * 1024:
            die("文件超过 100MB，Gemini inline_data 不支持。请用 Gemini Files API 或先压缩视频。")
        parts.append({"inline_data": {"mime_type": mime_for(name, "video/mp4"), "data": b64(raw)}})
    parts.append({"text": args.prompt})
    return parts


def call_gemini(args, parts: list[dict], dry_run: bool) -> dict:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    body = {"contents": [{"role": "user", "parts": parts}]}
    if dry_run:
        return {"dry_run": True, "endpoint": f"/v1beta/models/{model}:generateContent", "body": body}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={require_env('GEMINI_API_KEY')}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        die(f"Gemini API HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")
    except urllib.error.URLError as e:
        die(f"Gemini API 请求失败: {e}")


def extract_frames(path: str, frames: int, tmpdir: str) -> list[dict]:
    """旧版兜底：ffmpeg 抽帧（仅当用户显式 --frames 时才用）。"""
    if shutil.which("ffmpeg") is None:
        die("未找到 ffmpeg。原生视频模式不需要它；如需抽帧请先 brew install ffmpeg")
    pattern = os.path.join(tmpdir, "frame_%03d.jpg")
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", path, "-vf", "fps=1", "-frames:v", str(frames), "-q:v", "3", pattern],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        die(f"ffmpeg 抽帧失败:\n{proc.stderr[-800:]}")
    out = sorted(os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith(".jpg"))
    if not out:
        die("ffmpeg 未产出任何帧")
    return [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(open(p, 'rb').read())}"}} for p in out]


def main() -> None:
    load_env_file()
    parser = argparse.ArgumentParser(description="多模态理解封装：MiniMax-M3 / Gemini，原生视频输入")
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--provider", choices=["minimax", "gemini"], default="minimax")
    common.add_argument("--max-tokens", type=int, default=8192)
    common.add_argument("--temperature", type=float, default=1.0)
    common.add_argument("--thinking", action="store_true")
    common.add_argument("--dry-run", action="store_true", help="只打印请求体，不发 API")
    common.add_argument("--json", action="store_true", help="输出完整 JSON 响应")

    p_img = sub.add_parser("image", parents=[common], help="理解一张图片")
    p_img.add_argument("input", help="本地路径或 HTTP(S) URL")
    p_img.add_argument("prompt", help="对图片的提问/分析要求")

    p_vid = sub.add_parser("video", parents=[common], help="理解一段视频（默认原生视频输入，不抽帧）")
    p_vid.add_argument("input", help="本地路径或 HTTP(S) URL")
    p_vid.add_argument("prompt", help="对视频的提问/分析要求")
    p_vid.add_argument("--fps", type=float, default=None, help="仅 minimax：视频抽帧率 0.2-5，默认 1")
    p_vid.add_argument("--detail", choices=["low", "default", "high"], default=None, help="仅 minimax：逐帧分辨率")
    p_vid.add_argument("--frames", type=int, default=None, help="旧版兜底：显式指定后用 ffmpeg 抽帧（默认不用）")

    args = parser.parse_args()

    if args.cmd == "video" and args.frames:
        tmpdir = tempfile.mkdtemp(prefix="eyes_")
        try:
            if is_remote(args.input):
                local = os.path.join(tmpdir, "input.mp4")
                with open(local, "wb") as f:
                    f.write(fetch_bytes(args.input))
                path = local
            else:
                path = args.input
            parts = extract_frames(path, args.frames, tmpdir)
            content = parts + [{"type": "text", "text": args.prompt}]
            resp = call_minimax(args, content, args.dry_run)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    elif args.provider == "gemini":
        resp = call_gemini(args, build_gemini_parts(args), args.dry_run)
    else:
        resp = call_minimax(args, build_minimax_parts(args), args.dry_run)

    if args.dry_run:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return
    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return

    if args.provider == "gemini":
        try:
            text = resp["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            text = json.dumps(resp, ensure_ascii=False, indent=2)
    else:
        try:
            text = resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            text = json.dumps(resp, ensure_ascii=False, indent=2)
    print(text)


if __name__ == "__main__":
    main()
