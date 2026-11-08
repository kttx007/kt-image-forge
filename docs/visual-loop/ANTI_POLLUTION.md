# Anti-Pollution Rules

目标：约束错误，不约束创造力。

## Constraint Budget

每个槽位最多向生成模型传 3 类约束：
1. 本图必须表达的目标
2. 与本图相关的硬事实/产品不变量
3. 本图禁止出现的少量高风险错误

不要把全局几十条禁令复制到每个 Prompt。

## Hard vs Soft

### Hard
- verified facts
- critical product identity
- physical truth
- exact regulated/structured information

### Soft
- composition / color / camera / lighting / typography / scenario / copy rhythm

Soft 失败不自动 REJECT，除非影响商业理解或缩略图表现。

## Creative Freedom

Planner 输出“why / what / proof”，而不是规定每一个视觉元素怎么画。

## Retry Policy

- 事实/文字问题：只修信息区
- 产品明显结构错误：只修产品区
- 物理关系错误：只修相关视觉关系
- 同类失败连续 2 次：停止局部修复，开新 branch
- 已锁槽位不参与重跑

## Avoid Feedback Poisoning

只有满足以下条件的经验才晋升为长期规则：
- 至少跨 2 个 SKU 重复出现；或
- 属于事实/物理/身份硬错误；或
- 用户明确要求永久采用。

一次审美偏好只写进当前 Style Branch，不写进全局规则。
