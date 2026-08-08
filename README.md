# kt-image-forge

> 产品像素不可侵犯的电商视觉生产引擎

## 核心理念

AI 只做背景/场景/氛围/排版，产品主体永远来自真实实拍抠图。一根线都不许 AI 重绘。

## 架构

```
forge/           Python 核心包
  engines/       生图引擎（gpt-image-2 → Agnes → Gemini 降级链）
  cutout.py      抠图精修（rembg + Pillow 边缘处理）
  compose.py     确定性合成排版（Pillow/OpenCV，零 AI 介入产品主体）
  audit.py       P0 三道门审计（事实/无漂移/视觉）
  pipeline.py    七段流水线编排
  facts.py       事实卡加载器
  config.py      配置管理（密钥从环境变量读取）

theory/          理论框架（JTBD/AIDA/FAB/Cialdini/格式塔/NN·g/Baymard）
research/        开源方法论血统（每环节锚定全球开源项目）
products/        可插拔产品事实卡
  c03/           C03 多功能激光测距望远镜（首个实例）
    facts.yaml         冻结事实卡（全参数）
    forbidden_claims   禁宣称清单
    image_plan.yaml    图位规划（AIDA 映射）

mcp-server/      MCP Server（任何 AI 工具可调）
cli/             CLI 工具
```

## 七段流水线

1. **FACTS** — 加载产品冻结事实卡
2. **RESEARCH** — 全球爆款拆解 + 跨类目借鉴
3. **HOOKS** — 多理论卖点挖掘（JTBD/AIDA/FAB/Cialdini）
4. **CUTOUT** — 抠图精修（rembg + MinFilter + GaussianBlur）
5. **SCENE** — AI 背景/场景生成（gpt-image-2 → Agnes → Gemini）
6. **COMPOSE** — 确定性合成排版（Pillow/OpenCV）
7. **AUDIT** — P0 三道门审计（事实/无漂移/视觉）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置密钥
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 3. 生成产品全套图
python run_c03.py
# 或用 CLI
python cli/kt-image-forge generate c03 /path/to/product.jpg

# 4. 单独抠图
python cli/kt-image-forge cutout /path/to/photo.jpg --output-dir cutouts

# 5. 单独审计
python cli/kt-image-forge audit /path/to/image.png --sku c03 --bg white
```

## 多产品支持

在 `products/` 下新建产品目录，添加 `facts.yaml` 和 `image_plan.yaml`：

```
products/
  c03/          # 已有
    facts.yaml
    image_plan.yaml
  k5/           # 新产品
    facts.yaml
    image_plan.yaml
```

管线自动适配，无需改代码。

## 理论根基

| 理论 | 出处 | 在图位中的应用 |
|------|------|---------------|
| JTBD | Christensen (2016) | 卖点图以任务场景为核心 |
| AIDA | Strong (1925) | 6张主图的职责链映射 |
| FAB | Hutton (1984) | 卖点矩阵 Feature→Advantage→Benefit |
| Cialdini 六原则 | Cialdini (1984) | 信任图权威原则 |
| 格式塔 | Wertheimer (1923) | 合成排版接近性/图底关系 |
| NN/g 眼动 | Nielsen (2006) | 核心信息置左上热点区 |
| Baymard 电商 | Baymard Institute | 6张图=最优数量/白底+场景缺一不可 |

## 开源血统

| 环节 | 项目 | License |
|------|------|---------|
| 抠图 | rembg (17k★) | MIT |
| 抠图 | BiRefNet (4k★) | MIT |
| 合成 | Pillow (12k★) | MIT-CMU |
| 合成 | OpenCV (80k★) | Apache 2.0 |
| 审计 | scikit-image | BSD-3 |
| 审计 | aesthetic-predictor | MIT |
| 规格书 | PaddleOCR (46k★) | Apache 2.0 |

详见 [research/OPEN_SOURCE_LINEAGE.md](research/OPEN_SOURCE_LINEAGE.md)

## MCP 集成

```json
{
  "mcpServers": {
    "kt-image-forge": {
      "command": "python3",
      "args": ["/path/to/kt-image-forge/mcp-server/server.py"]
    }
  }
}
```

## License

MIT
