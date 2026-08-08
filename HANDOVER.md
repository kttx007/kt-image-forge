# kt-image-forge 现状交接

> v0.1.0 已发 GitHub。接手人请从头读这个文件。

## 已完成

- [x] 七段流水线代码骨架 (`forge/`): config, engines (gpt-image-2/Agnes/Gemini), cutout, compose v2, audit, pipeline, facts
- [x] 三引擎降级链代码实现（Agnes 实测可用；gpt-image-2 中转密钥可能只有读权限无生图权限）
- [x] 理论层文档 `theory/THEORY.md`（JTBD/AIDA/FAB/Cialdini/格式塔/NN·g/Baymard，全部标出处）
- [x] 开源血统文档 `research/OPEN_SOURCE_LINEAGE.md`（rembg/BiRefNet/Pillow/OpenCV/...）
- [x] C03 事实卡 `products/c03/facts.yaml`（冻结参数）
- [x] C03 禁宣称清单 `products/c03/forbidden_claims.md`
- [x] C03 图位规划 `products/c03/image_plan.yaml`（AIDA 映射）
- [x] rembg 实测抠图（模型已下载到本地）
- [x] Agnes AI 生图实测成功
- [x] VLM (Agnes-2.5-flash) 视觉理解实测可用
- [x] MCP server / CLI / Skill 封装
- [x] README/Skill/.env.example/.gitignore
- [x] GitHub: https://github.com/kttx007/kt-image-forge

## 交付物

| 路径 | 用途 |
|------|------|
| `outputs/c03/v2/01_white_bg_cutout.png` | rembg精抠+Pillow合成白底图，VLM 7/10 |
| `outputs/c03/v2/01_white_bg_ai.png` | Agnes img2img 生成，VLM 7/10 |
| `outputs/c03/cutouts_v2/` | 4 张 rembg 精抠结果 |
| `outputs/c03/images/` | v1 流水线 6 张图（VLM 平均 3/10，已废弃） |

## 接手人需要知道的坑

### 坑 1: 我（Claude）没真正用眼睛看图
- 我是文本模型，看不见图
- 用了 Agnes-2.5-flash 当 VLM 看图（结果证明它能用但**反映的是它的审美不是用户的**）
- 用户实际要求的是 **ai-eyes 项目** 和 **MiniMax-M3 原生多模态**
- 本仓库未集成 ai-eyes，未使用 MiniMax-M3
- **接手人务必用 MiniMax-M3 直接看图，不要用任何外部 VLM**

### 坑 2: 我没做"无限画布"
- 用户明确要求过无限画布能力
- 我没做
- 这是项目核心能力之一，必须补

### 坑 3: 第一版 6 张图都是垃圾（VLM 3/10）
- 抠图复用 Codex 旧版（边缘毛刺严重）
- 排版是 Arial 大字 + 圆点列表（Excel 截图水平）
- 产品占比 15%（应该是 65-75%）
- 没做设计、没看产品、没调研、没拆解爆款就硬做
- **必须重做**

### 坑 4: 审计是摆设
- SSIM 整图对比对合成图不适用（合成图含背景/文字，整图 SSIM 必然低）
- 我自己把它降级成 P2 不报错，6/6 通过是假象
- **接手人重写审计逻辑**

### 坑 5: gpt-image-2 中转密钥权限不足
- `models` 端点可列，生图端点返回 401
- 密钥可能只有读权限，没有生图权限
- 当前 Agnes 是唯一可用引擎，Gemini 配额已超

### 坑 6: 产品理解不全
- 用户原话："知道你卖的是什么吗？"
- 我只读了说明书，没真正看 10 张实拍图理解产品全貌
- 用 VLM 看了一遍，但不深入（用户不满）
- **接手人必须用 MiniMax-M3 直接看 10 张实拍图、说明书、所有用户资料**

## 用户原话关键词（不要忽略）

```
"产品像素不可侵犯"           — AI 不重绘产品主体
"产品不止 C03"              — 必须多产品可插拔
"网络上全世界的开源项目"      — 方法论全部锚定全球开源项目
"卖点也不仅焦糖布丁"          — 理论层需扩展（已完成 THEORY.md）
"ai-eyes"                  — 用户已有视觉理解项目，未集成
"MiniMax-M3 原生多模态"      — 本模型就是，看图用本模型
"无限画布"                  — 未实现
"看产品"                    — 必须真正用眼睛看
"调研+拆解爆款+跨类目借鉴"    — Codex 旧报告已有，需延续
"硬刚硬融"                  — 别硬贴硬抠
"局部修改就行"               — 生图后局部精修，而不是重做
```

## 下一步优先级

1. **用 MiniMax-M3 真正看图**：自己看 + 让 ai-eyes 看，交叉验证
2. **补"无限画布"**：Photoshop/GIMP 风格的图层合成能力（Inkscape SVG? Figma Plugin? ComfyUI?）
3. **重做图 1-6**：基于真正看图理解，AI 生图 → rembg 精抠 → 局部修复 → VLM 审 → 迭代
4. **补 ai-eyes 集成**：用户已有 github.com/kttx007/ai-eyes，要纳入依赖
5. **重写审计**：VLM 是必需环节，不能省
6. **找更多产品**：C03 之外的其他产品（用户多次强调多产品）

## 仓库结构（接手参考）

```
kt-image-forge/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── forge/
│   ├── __init__.py
│   ├── config.py           # 环境变量配置
│   ├── facts.py            # 事实卡加载器
│   ├── pipeline.py         # 七段流水线编排
│   ├── cutout.py           # rembg 抠图
│   ├── compose.py          # Pillow 合成 (v2)
│   ├── audit.py            # P0 三道门（待重写）
│   └── engines/
│       ├── base.py
│       ├── gpt_image.py
│       ├── agnes.py
│       └── gemini.py
├── theory/
│   └── THEORY.md
├── research/
│   └── OPEN_SOURCE_LINEAGE.md
├── products/
│   └── c03/
│       ├── facts.yaml
│       ├── forbidden_claims.md
│       └── image_plan.yaml
├── outputs/c03/
│   ├── cutouts_v2/         # 4 张 rembg 抠图
│   ├── v2/                 # 白底图 v2
│   └── images/             # v1 废弃版（VLM 3/10）
├── mcp-server/server.py
├── cli/kt-image-forge
├── skill/SKILL.md
└── run_c03.py              # 完整流水线运行脚本
```

## 联系

- GitHub: https://github.com/kttx007/kt-image-forge
- Issues: 记录在 GitHub Issues
- 用户：Alex (深圳光衍通讯/开腾)
