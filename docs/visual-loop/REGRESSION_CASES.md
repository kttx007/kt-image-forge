# Regression Cases

这些案例不是更多 Prompt 禁令，而是用于回归测试和审计训练的真实失败样本。

## JC02

- **M02 尺寸轴**：数值本身正确但轴向错误仍属于 physical_truth fail。27.5 / 25 / 12.8 必须和真实长轴、高度、厚度语义绑定。
- **M04 孔位漂移**：视觉好看不能覆盖 housing / hole / recess 明显变化；属于 product_identity fail。
- **D09 IP 范围**：`IPX7 lens only` 若被画成整机淋水/防水场景，属于 physical/fact scope fail。
- **D10 模型补条件**：模型擅加 ambient light、reflectivity、update rate 等看似合理条件，属于 fact_truth fail。
- **D11 密集规格**：精确规格必须逐行核对；必要时走 hybrid / deterministic。

## J13S

- **D03 测量轴**：产品方向、发射端、目标和测量轴必须符合真实物理。
- **D08 USB/充电**：多次近似生成仍错误时，不继续无限局修；使用真实参考或新 branch。
- **D11 电池数量**：没有证据的 AAA 数量不得由模型补全。
- **Style Lineage**：Interior Quotation Set 与 International Blue/Black Set 即使同 SKU，也不能因为文件名接近而混用。

## 经验晋升

案例中只有“错误模式”可成为审计规则；具体色彩、构图、风格不得从单一案例晋升为全局规范。
