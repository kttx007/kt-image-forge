# STYLE_INTELLIGENCE_LAYER｜V3.1

Drive 正本：https://docs.google.com/document/d/1tAQIr7sbePJhoS4uQRG-S3jtEncbZxjRV0EzPjpnp0M  
所属：KT Visual Factory OS V3.1（`1b2GV1yIBxjotunOsn77TR2l737kt_Aoy`）

## 定位

可选视觉知识检索层，**不是**事实引擎，**不是**第二 Prompt Compiler。

## 外部案例固定

| 字段 | 值 |
|------|-----|
| `reference_role` | `style_reference` |
| `do_not_use_as_identity` | `true` |

## 允许迁移

camera / composition / lighting / materials / space / typography behavior / information density / visual rhythm / thumbnail logic / visual proof mechanism

## 禁止迁移

product identity / structure / facts / claims / certifications / logo / model / ports / buttons / UI / performance / price / warranty / availability / unsupported accessories

## 成熟度

`experimental_validated_main_image`

- 已验证：主图小样有正向证据
- 未全面验证：卖点图、技术信息图、跨 Provider、全品类长期生产

## Controlled Experiment

锁 Product Truth、P0、Buyer Task、Channel/Slot、Identity、canvas、copy budget、first-pass count、audit rubric。  
只改变 Style 来源机制。  
匿名候选后评 Hard Gate + Commercial + Thumbnail。

## 本仓接线

- 运行时策略：`forge.brand.style_reference_migration_policy()`
- LOOP style 字段：`style.style_reference_only = true`（见 `forge.program.build_default_job_skeleton`）
- Brand Book tokens 仍属 DesignOS；Style Intelligence 不覆盖冻结色与产品事实
