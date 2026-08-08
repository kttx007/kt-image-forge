# kt-image-forge 开源方法论血统

> 每一段流水线锚定的是全球开源项目已验证的成果，不是自研轮子。
> 用户原话："网络上全世界的开源项目已成就的可靠的经验。"

---

## 流水线环节 × 开源项目对照

### 1. CUTOUT 抠图精修

| 项目 | Star | License | 用途 | 选用理由 |
|------|------|---------|------|---------|
| **rembg** (danielgatis/rembg) | 17k+ | MIT | 通用抠图 | ONNX 驱动，一行命令出 alpha mask，社区验证最广 |
| **BiRefNet** (ZhengPeng7/BiRefNet) | 4k+ | MIT | 高精度抠图 | CVPR 2024 SOTA，边缘毛发级精度，适合产品实拍 |
| **pymatting** (pymatting/pymatting) | 2k+ | MIT | Alpha matting 精修 | 学术级 alpha matting 算法，rembg 后精修边缘 |

**管线**: rembg 粗抠 → BiRefNet 精抠（边缘/透明区）→ pymatting 羽化 → MinFilter+GaussianBlur 去毛刺

### 2. COMPOSE 合成排版

| 项目 | Star | License | 用途 | 选用理由 |
|------|------|---------|------|---------|
| **Pillow** (python-pillow/Pillow) | 12k+ | MIT-CMU | 图像合成/排版 | Python 图像处理事实标准，确定性输出 |
| **OpenCV** (opencv/opencv) | 80k+ | Apache 2.0 | 图像变换/边缘检测 | 计算机视觉瑞士军刀，alpha bbox 裁剪等 |

**管线**: Pillow 画布构建 → OpenCV alpha bbox 裁剪 → Pillow LANCZOS 缩放 → 确定性排版（零 AI 介入产品主体）

### 3. SCENE 场景/背景生成

| 项目 | Star | License | 用途 | 选用理由 |
|------|------|---------|------|---------|
| **gpt-image-2** (OpenAI) | N/A | API | 背景场景生成 | 用户指定优先级 1，中转 API 已验证 |
| **agnes-image-2.1-flash** (agnes-mcp) | N/A | API | 背景场景生成 | 用户指定优先级 2，已封装 github.com/kttx007/agnes-mcp |
| **Gemini** (Google) | N/A | API | 背景场景生成 | 用户指定优先级 3，兜底 |
| **Fashion-AI** (agnes-mcp/references/fashion-ai) | N/A | 参考 | 爆款检索→风格分析→生图架构 | 仅借鉴架构思路，检索爆款基因 → 分析视觉风格 → 继承生成 |

**关键约束**: AI 只生成背景/场景/氛围，产品主体不进入 AI 生图流程。产品主体始终是抠图后的真实像素，通过确定性 Pillow 合成叠加。

### 4. AUDIT 审计

| 项目 | Star | License | 用途 | 选用理由 |
|------|------|---------|------|---------|
| **ai-vision-mcp** | 200+ | MIT | VLM 视觉审计 | MCP 协议视觉理解，可做产品漂移检测 |
| **aesthetic-predictor** (christopher-beckham/aesthetic-predictor) | 600+ | MIT | 美学评分 | LAION-Aesthetic 预训练模型，量化图片美感 |
| **nsfw_model** (GantMan/nsfw_model) | 1.5k+ | MIT | 安全过滤 | 兜底安全审查 |

**三道门**:
1. **事实审核** — 图中参数文案 vs facts.yaml 冻结事实（规则匹配）
2. **无漂移审核** — 产品主体像素 vs 实拍抠图（SSIM/特征点匹配 + VLM 描述对比）
3. **视觉审核** — 美学评分 + 平台合规规则（白底纯度/产品占比/文字检测）

### 5. RESEARCH 调研拆解

| 项目 | Star | License | 用途 | 选用理由 |
|------|------|---------|------|---------|
| **amazon-image-studio** | 131+ | MIT | 平台合规清单 | Amazon 图片规则可直接移植到阿里国际站 |
| **gpt_image_playground** | 3.3k+ | MIT | 工作台参考 | prompt 工程与批量生图的工作流参考 |

### 6. SPECS 规格书

| 项目 | Star | License | 用途 | 选用理由 |
|------|------|---------|------|---------|
| **PaddleOCR** (PaddlePaddle/PaddleOCR) | 46k+ | Apache 2.0 | 文字检测/识别 | 规格书排版校验、已有文档 OCR 提取 |
| **Pillow + OpenCV** | — | — | 模板渲染 | 规格书确定性排版（参数表/尺寸图/功能图解） |

**自研部分**: 无现成开源方案能一键生成中英双语规格书 → Pillow 模板渲染 + facts.yaml 数据驱动。这是唯一需要自研的环节，但底层仍是 Pillow/OpenCV 确定性代码。

---

## 不选用的项目及原因

| 项目 | 原因 |
|------|------|
| ComfyUI / Stable Diffusion WebUI | GPL 许可证限制 + 本地 GPU 要求高 + 生成结果不可控（漂移风险） |
| Midjourney API | 非开源 + 无官方 API + 产品主体重绘风险 |
| Canva API | 非开源 + 闭源模板系统 + 不支持确定性合成 |
| Remove.bg API | 付费 + 非开源（rembg 已覆盖同等能力） |

---

## 许可证合规声明

所有选用的开源项目许可证均为 MIT/Apache 2.0，允许商业使用和二次封装。
Fashion-AI 仅借鉴架构思路（无明确 License），不直接复用代码。
