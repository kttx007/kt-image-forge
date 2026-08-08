# kt-image-forge Skill

> 产品像素不可侵犯的电商视觉生产引擎 — MCP + CLI + Skill 三合一

## 何时使用

- 需要生成电商产品主图/场景图/规格图/卖点图
- 需要 AI 生成背景但产品主体不可漂移
- 需要多产品可插拔的视觉生产管线
- 需要 P0 审计（事实/无漂移/视觉）

## 前置条件

1. 安装依赖: `pip install -r requirements.txt`
2. 配置密钥: 复制 `.env.example` 为 `.env`，填入 API 密钥
3. 产品事实卡: 在 `products/<sku>/` 下放置 `facts.yaml` 和 `image_plan.yaml`

## 生图引擎优先级

1. gpt-image-2（中转 API）— 需 KTIF_GPT_IMAGE_API_KEY
2. Agnes（agnes-image-2.1-flash）— 需 KTIF_AGNES_TOKEN
3. Gemini（兜底）— 需 KTIF_GEMINI_API_KEY

引擎失败自动降级，无需人工干预。

## CLI 命令

```bash
# 生成全套图
python cli/kt-image-forge generate c03 /path/to/product.jpg

# 单独抠图
python cli/kt-image-forge cutout /path/to/photo.jpg --output-dir cutouts

# 单独生成 AI 背景
python cli/kt-image-forge bg "premium outdoor background" --output bg.png

# 审计图片
python cli/kt-image-forge audit image.png --sku c03 --bg white

# 列出产品
python cli/kt-image-forge list

# 查看事实卡
python cli/kt-image-forge facts c03
```

## MCP 工具

| 工具 | 描述 |
|------|------|
| generate_images | 生成产品全套图（抠图→场景→合成→审计） |
| generate_bg | 单独生成 AI 背景 |
| cutout_product | 单独抠图 |
| audit_image | 单独审计 |
| list_products | 列出产品 |
| get_facts | 获取事实卡 |

## 核心约束

- **产品像素不可侵犯**: AI 只生成背景/场景/氛围，产品主体永远是真实抠图像素
- **事实冻结**: 图中参数必须与 facts.yaml 一致
- **禁宣称**: forbidden_claims.md 中的词绝不出现
- **确定性合成**: Pillow/OpenCV 代码保证可复现，AI 不参与产品合成
