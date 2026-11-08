# 开源吸收清单（2026-11-08 合并轮）

本轮不是“再列一堆名字”，而是把已验证机制并进 `forge/loop` / `forge/audit` / `forge/loop/quality`。

## 已并入本仓库的自有 Codex 工程

| 来源 | 吸收点 | 落地 |
|------|--------|------|
| Drive `visual-factory-loop` | 四硬门、可恢复状态机、Constraint Budget、整图默认、局部返修×2→新分支、locked immutability | `forge/loop/*` + `vendor/visual-factory-loop` |
| Drive `guangyan-visual-loop` | 完整 generated master、reference roles、hash freeze、300px 可读性 | `docs/visual-loop/*` |
| `GENERATED_MASTER_PRODUCTION_LOOP.md` | Stage A–H SOP + set lineage | `docs/visual-loop/GENERATED_MASTER_PRODUCTION_LOOP.md` |
| `ai-eyes` | MiniMax-M3 / Gemini 原生看图（不抽帧） | `vendor/ai-eyes/eyes.py` + `forge/loop/eyes.py` |
| JC02 / J13S 回归 | 尺寸轴向、孔位漂移、IP 作用范围、模型补条件、Style Lineage | `docs/visual-loop/REGRESSION_CASES.md` + tests |

## 外部开源吸收

| 项目 | License | 吸收什么 | 不吸收什么 |
|------|---------|----------|------------|
| [Bambushu/photoclean-pipeline](https://github.com/Bambushu/photoclean-pipeline) | MIT | alpha-edge sharpness → `needs_review` | 整站批处理 UI |
| [backblaze-b2-samples/rembg-product-background-removal](https://github.com/backblaze-b2-samples/rembg-product-background-removal) | MIT | cutout sidecar（model/hash/coverage） | B2 存储绑定 |
| [ozgursntrk/product-bg-replacement-pipeline](https://github.com/ozgursntrk/product-bg-replacement-pipeline) | — | 产品像素不重生 + 结构忠实度审计思路 | SD/ControlNet 本地 GPU 链 |
| [tan-yong-sheng/ai-vision-mcp](https://github.com/tan-yong-sheng/ai-vision-mcp) | MIT | MCP 视觉审计备选路径（已在 ai-eyes 研究） | 不替代 MiniMax-M3 |
| rembg / Pillow / OpenCV | MIT/Apache | 既有 cutout/compose | — |

## 明确不并入全局硬规则的东西

见 `docs/visual-loop/ANTI_POLLUTION.md`：固定卡片布局、固定产品占比、固定深色/科技蓝模板、像素级全图锁、一次审美偏好晋升全局。
