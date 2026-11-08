# Architecture

## 1. 为什么是 Loop，不是 Skill

Skill 只负责识别意图和调用入口。真正生产过程需要持久状态、分支、审计、失败恢复、产物哈希和 Provider 切换，因此必须是工程。

```
INPUT
  -> FACT LEDGER
  -> PRODUCT IDENTITY
  -> BUYER TASK MODEL
  -> SALES ARGUMENT
  -> STORYBOARD
  -> STYLE BRANCH
  -> SLOT LOOP
       -> PROVIDER BUNDLE
       -> WHOLE IMAGE GENERATION
       -> FULL SIZE AUDIT
       -> 300PX AUDIT
       -> PASS -> LOCK
       -> FAIL -> LOCAL REPAIR
       -> SAME FAILURE x2 -> NEW BRANCH
  -> HUMAN FREEZE
  -> EXPORT
```

## 2. 双轨渲染

### Commerce Track
主图/详情页默认整图生成，追求整体商业设计完整性。

### Controlled Track
规格表、认证、二维码、安全文字、Pin map、尺寸表等高风险密集事实采用混合或确定性叠加。

两轨共享同一个 Fact Ledger / Product Identity / Style Lineage。

## 3. 状态

planned -> bundled -> generated -> auditing -> repair_requested -> passed -> locked

异常：evidence_blocked / identity_blocked / physical_blocked / branch_required

## 4. 可迁移性

Provider 不参与业务状态，只实现“输入 bundle -> 输出 candidate”的接口。
Codex / Gemini / 豆包 / Accio / Meitu / ComfyUI / Agnes 都可替换，不改 Planner 和 Audit。
