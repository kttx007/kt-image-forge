#!/usr/bin/env python3
"""
kt-image-forge MCP Server

MCP (Model Context Protocol) server that exposes the forge pipeline
to any AI tool that supports MCP (Claude, GPT, etc.)

Tools:
  generate_images  — 生成产品全套图（抠图→场景→合成→审计）
  generate_bg      — 单独生成 AI 背景/场景
  cutout_product   — 单独抠图
  audit_image      — 单独审计图片
  list_products    — 列出可用产品
  get_facts        — 获取产品事实卡
"""

import json
import sys
import os
from pathlib import Path

# 项目根
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from forge.config import ForgeConfig
from forge.facts import load_facts, load_image_plan


def handle_request(request: dict) -> dict:
    """处理 MCP 请求"""
    method = request.get("method", "")
    req_id = request.get("id")

    # initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "kt-image-forge", "version": "0.1.0"},
            },
        }

    # tools/list
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "generate_images",
                        "description": "Generate full image set for a product (6 main images + audit). Uses cutout + AI background + Pillow compose.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sku": {"type": "string", "description": "Product SKU (e.g. 'c03')"},
                                "source_image": {"type": "string", "description": "Path to product photo for cutout"},
                                "output_dir": {"type": "string", "description": "Output directory (optional)"},
                            },
                            "required": ["sku", "source_image"],
                        },
                    },
                    {
                        "name": "generate_bg",
                        "description": "Generate AI background/scene image (no product). Product is composited separately.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "description": "Background scene description"},
                                "size": {"type": "string", "description": "Image size, e.g. '1024x1024'", "default": "1024x1024"},
                                "output_path": {"type": "string", "description": "Output file path"},
                            },
                            "required": ["prompt", "output_path"],
                        },
                    },
                    {
                        "name": "cutout_product",
                        "description": "Remove background from product photo using rembg. Outputs alpha (transparent) and white background versions.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input_path": {"type": "string", "description": "Path to product photo"},
                                "output_dir": {"type": "string", "description": "Output directory"},
                                "name_prefix": {"type": "string", "description": "Output filename prefix", "default": "product"},
                            },
                            "required": ["input_path", "output_dir"],
                        },
                    },
                    {
                        "name": "audit_image",
                        "description": "Run P0 three-gate audit (fact check / drift check / visual check) on an image.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "image_path": {"type": "string", "description": "Path to image to audit"},
                                "sku": {"type": "string", "description": "Product SKU for facts"},
                                "reference_cutout": {"type": "string", "description": "Path to reference cutout for drift check"},
                                "expected_bg": {"type": "string", "description": "Expected background: 'white', 'scene', or 'any'", "default": "any"},
                            },
                            "required": ["image_path"],
                        },
                    },
                    {
                        "name": "list_products",
                        "description": "List all available product SKUs.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "get_facts",
                        "description": "Get product facts card (frozen specifications).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sku": {"type": "string", "description": "Product SKU"},
                            },
                            "required": ["sku"],
                        },
                    },
                ]
            },
        }

    # tools/call
    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        try:
            result = call_tool(tool_name, args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def call_tool(name: str, args: dict) -> dict:
    """执行工具调用"""
    if name == "list_products":
        products_dir = PROJECT_ROOT / "products"
        skus = [d.name for d in products_dir.iterdir() if d.is_dir() and (d / "facts.yaml").exists()]
        return {"skus": skus}

    if name == "get_facts":
        sku = args["sku"]
        facts = load_facts(sku)
        return {"facts": facts}

    if name == "generate_bg":
        from forge.pipeline import ForgePipeline
        cfg = ForgeConfig.from_env()
        pipeline = ForgePipeline(cfg)
        prompt = args["prompt"]
        size = args.get("size", "1024x1024")
        output_path = Path(args["output_path"])
        result = pipeline.generate_with_fallback(prompt, size=size, output_path=output_path)
        return {"success": result.success, "path": str(result.image_path) if result.image_path else None, "error": result.error}

    if name == "cutout_product":
        from forge.cutout import process_cutout
        input_path = Path(args["input_path"])
        output_dir = Path(args["output_dir"])
        prefix = args.get("name_prefix", "product")
        result = process_cutout(input_path, output_dir, prefix)
        return {k: str(v) if isinstance(v, Path) else v for k, v in result.items()}

    if name == "audit_image":
        from forge.audit import run_full_audit
        image_path = Path(args["image_path"])
        sku = args.get("sku")
        ref = Path(args["reference_cutout"]) if "reference_cutout" in args else None
        bg = args.get("expected_bg", "any")
        facts = load_facts(sku) if sku else None
        report = run_full_audit(image_path, facts, ref, expected_bg=bg)
        return report.to_dict()

    if name == "generate_images":
        from forge.pipeline import ForgePipeline
        sku = args["sku"]
        source = Path(args["source_image"])
        output_dir = Path(args.get("output_dir", str(PROJECT_ROOT / "outputs" / sku)))
        cfg = ForgeConfig.from_env()
        pipeline = ForgePipeline(cfg)
        result = pipeline.run_full(sku, source, output_dir)
        return {
            "images": [str(p) for p in result["images"]],
            "contact_sheet": str(result["contact_sheet"]),
            "audit_report": str(result["audit_report"]),
            "audit_passed": sum(1 for r in result["audit"] if r.passed),
            "audit_total": len(result["audit"]),
        }

    raise ValueError(f"Unknown tool: {name}")


def main():
    """MCP stdio server main loop"""
    import sys
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stderr.write(f"Invalid JSON: {line}\n")
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    main()
