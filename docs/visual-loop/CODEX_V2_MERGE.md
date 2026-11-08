# Codex V2 Merge Decision

## 吸收

从 Codex V2 / visual-factory-loop 包吸收：
- 可恢复状态机
- historical replay / per-slot repair / lock / freeze
- Product Identity contract
- Use Physics contract
- Set Lineage
- Specification Track
- dense facts / deterministic fallback
- exception-driven factory
- real J13S / JC02 regression cases

## 保留本工程原有优势

- 只有 4 个全局硬门
- Constraint Budget
- Provider-neutral manual web handoff
- whole-image generation 作为 Commerce 默认
- creative freedom 明确属于软层
- feedback promotion 防止一次反馈污染长期记忆
- kt-image-forge 的 rembg 抠图 + 引擎降级链 + 产品 facts.yaml

## 不原样合并

- SKILL.md 与 Generated Master SOP 中重复的执行条款
- 案例脚本里的本机绝对路径
- 针对单一模型/API 的私有提示词写法
- 一次性审美偏好
- 旧阶段已经被后续实验推翻的规则（例如默认怀疑所有营销资产、白底硬模板）

## 最终单一来源

- Machine truth: `contracts/` + `forge/loop/`
- Human operating truth: `docs/visual-loop/OPERATING_CONTRACT.md`
- Runtime truth: Python state machine and tests
- Skill: thin router only
