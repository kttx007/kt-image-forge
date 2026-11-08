# Visual Factory Operating Contract

这是 Visual Factory Loop 唯一的人类可读权威执行合同。其他说明文档不得复制一套新的规则体系。

## 1. 输入

每个任务至少关联：
- Factory Job
- Fact Ledger
- Product Identity
- Use Physics（无相关物理要求时可为空）
- Buyer Task / Claims
- Style Branch
- Product assets / reference roles

未知内容保持 `pending_confirmation`，不自动变成营销文案。

## 2. Fact Ledger

事实按条目管理，而不是把某份 PDF 永久定义为唯一真相。

建议来源优先级：
1. 本任务中用户明确确认的当前型号/版本事实
2. 当前正式规格书、说明书、工程图、测试记录
3. 当前受控产品数据库 / Fact Card
4. 历史冻结手册
5. 官网 / 店铺既有营销内容
6. 竞品 / 行业常识只能用于研究，不得作为本产品事实

发生冲突时进入 `conflicts[]`，在解决前相关 claim 不可对外。

## 3. Product Identity

只锁买家可见且能定义产品身份的关键项：
- silhouette / proportions
- holes / apertures / ports / connectors
- buttons / screens / labels / model identity
- critical seams / housing geometry
- wire / connector relationship when relevant

不要求像素级一致。正常肉眼难辨的纹理、反光、微小渲染差异允许存在。

## 4. Physical Truth

只在相关槽位加载相关物理规则。物理规则不是全局 Prompt 禁令；它们按 slot scope 注入。

## 5. Commercial Compile

Planner 编译 buyer_question / purchase_barrier / dominant_claim / evidence / visual_proof。
主图数量动态；常见 6 槽只是参考，不是硬模板。

## 6. Style Branch

一套图共享 set_id / branch_id / style_authority / product_truth / fact_contract。
审美意见默认只属于当前 Style Branch。只有跨 ≥2 SKU 验证、硬错误、或用户永久要求才能晋升。

## 7. Render Routing

- main_image / normal_detail / poster → whole_image_generation
- dimension_diagram / pin_map / dense_fact_detail → hybrid_generation
- spec_table / legal / qr / exact_identifier → deterministic_overlay

## 8. Constraint Budget

每个生成槽位只向模型传三类约束：买家任务、相关硬事实/身份/物理、少量高风险错误。禁止把几十条全局禁令复制到每张图。

## 9. Audit

全局硬门：fact_truth / product_identity / physical_truth / locked_slot_immutability
渠道门：300px readability / dimensions / text overflow / naming
软审美分数不单独硬拒绝。

## 10. Recovery

- fact/text only → repair information region
- product identity only → repair product region
- physics only → repair related physical region
- whole creative fail → new creative branch
同类局部修复连续失败两次 → new branch。已锁槽位永不参与其他槽位重跑。

## 11. Specification Track

facts → page plan → page image → audit → lock pages → assemble PDF → render-back audit

## 12. Set Lineage

最终资产记录 set_id / branch_id / slot_id / SHA-256 / fact / product truth / style / audit / supersedes。
主图与详情页只有在同一 Style Lineage 下才进入同一个干净交付包。

## 13. Human Boundary

必须人工：未解决事实冲突、无法判断的关键产品身份、高风险物理歧义、最终 human freeze、正式 PDF、对外发布。
其余 plan/generate/audit/local repair/lock 可自动进行。
