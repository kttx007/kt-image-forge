# 多模态“眼睛”方案：让 Codex 看懂图片与视频

## 一、问题

Codex 会话里能直接看本地图片（`view_image`），但：
- 视频看不了（需要抽帧理解）
- 远程 URL 图片/视频不方便直接看
- 需要把“看图结论”结构化喂给业务流程（询盘图片、社媒截图、产品图、竞品素材）

需要一个**理解层**：输入图片/视频 + 提问 → 输出文字分析。

## 二、结论：原生视频理解（不抽帧），双引擎

| 维度 | MiniMax-M3 | Gemini（免费档） | agnes-2.0-flash |
|------|-----------|-----------------|-----------------|
| 图片理解 | ✅ 原生 | ✅ 原生 | ✅（CLI 可走） |
| 视频理解 | ✅ 原生（video_url） | ✅ 原生（File API / inline / YouTube） | ❌ |
| 是否抽帧 | 否 | 否 | — |
| 上下文 | 1M | 1M（Flash 档） | 较小 |
| 你有会员 | ✅ Token Plan | 免费 Key（AI Studio 可申请） | 未确认 |
| 官方 MCP | ✅ `minimax-coding-plan-mcp` | 社区项目 `ai-vision-mcp` | 无理解工具 |

官方依据：
- MiniMax-M3 是多模态旗舰模型，原生支持文本、图片、视频输入（https://platform.minimax.io/docs/api-reference/text-chat-openai）
- MiniMax OpenAI 兼容接口的视频参数：content part `video_url`，支持 base64 data URL（≤50MB）/ 公网 URL / `mm_file://`（≤512MB），可调 `fps`(0.2-5) 与 `detail`
- Token Plan MCP 提供 `understand_image` 工具（https://platform.minimaxi.com/docs/guides/token-plan-mcp-guide）
- Gemini API 原生视频理解：File API（免费档 2GB）/ inline（<100MB）/ YouTube URL（https://ai.google.dev/gemini-api/docs/video-understanding）
- Gemini 免费档：新账号默认 Free Tier，可访问免费模型并有对应速率限制（https://ai.google.dev/gemini-api/docs/billing）
- Agnes：只有 CLI 图片理解，**无视频理解**，不作为眼睛候选

## 三、方案 A（推荐，零配置改动）：本地封装 eyes.py（双引擎）

**不修改任何 Codex 配置**，我在终端直接调用即可。

```bash
# MiniMax-M3（你的 Token Plan，默认引擎）
export MINIMAX_API_KEY=你的TokenPlan订阅Key
python3 eyes/eyes.py image ./产品图.jpg "这是什么产品？列出画面文字"
python3 eyes/eyes.py video ./demo.mp4 "总结视频内容"           # 原生 video_url，不抽帧

# Gemini 免费档
export GEMINI_API_KEY=你的AI Studio Key
python3 eyes/eyes.py video ./demo.mp4 "总结视频内容" --provider gemini

# 自测（不发 API，只打印请求体）
python3 eyes/eyes.py video ./demo.mp4 "测试" --dry-run
```

实现要点（eyes/eyes.py）：
- 纯 Python 标准库（urllib + base64），零 pip 依赖，Python 3.9 可用
- minimax 引擎：图片 `image_url`；视频 `video_url`（官方文档参数，base64 ≤50MB / 公网 URL，可调 fps/detail）
- gemini 引擎：图片/视频 `inline_data`（视频 <100MB 且建议 <1 分钟；更大文件建议用 Gemini Files API）
- `--frames N` 仅为旧版兜底（需 ffmpeg），默认不使用
- 环境变量：`MINIMAX_API_KEY`、`MINIMAX_API_HOST`（默认 `https://api.minimaxi.com/v1`）、`MINIMAX_MODEL`（默认 `MiniMax-M3`）、`GEMINI_API_KEY`、`GEMINI_MODEL`（默认 `gemini-3.5-flash`）

## 四、方案 B（推荐开源项目）：ai-vision-mcp（Gemini 原生视频）

仓库：https://github.com/tan-yong-sheng/ai-vision-mcp（MIT，npm 包 `ai-vision-mcp`，71★ / 15 fork，2026-08-07 仍更新）

能力：
- `analyze_video`：本地视频（≤50MB 内联 / >50MB 走 Gemini Files API）、公网视频 URL、YouTube URL 直接分析
- `analyze_image` / `compare_images` / `detect_objects` / `audit_design`
- 自带 CLI：`ai-vision analyze-video <source> --prompt "..."`，以及 Claude/Cursor/VS Code MCP 配置

已放入本项目：`vendors/ai-vision-mcp/`（源码副本，MIT）

注意：**Node 环境**才能跑（本机暂未装 Node）。装好 Node 后：

```bash
cd vendors/ai-vision-mcp
npm install
export GEMINI_API_KEY=你的Key
export IMAGE_PROVIDER=google VIDEO_PROVIDER=google
npx tsx src/cli/index.ts analyze-video ./demo.mp4 --prompt "总结视频内容"
```

也可以直接 `npx -y ai-vision-mcp` 在支持 MCP 的客户端里使用。

## 五、方案 C（未来可选）：官方 Token Plan MCP

官方包：`uvx minimax-coding-plan-mcp -y`，工具 `web_search` + `understand_image`。

接入 Codex（需要**用户批准后**才改配置，目前未启用）：

```toml
# ~/.codex/config.toml（示例，未应用）
[mcp_servers.minimax]
command = "uvx"
args = ["minimax-coding-plan-mcp", "-y"]
env = { MINIMAX_API_KEY = "你的Key", MINIMAX_API_HOST = "https://api.minimaxi.com" }
```

优势：工具原生出现在 Codex 工具列表，我不用再走终端。

## 六、key 获取

### MiniMax（Token Plan）

1. 登录 https://platform.minimaxi.com（国内）或 https://platform.minimax.io（国际）
2. 订阅管理 > Token Plan，查看订阅 Key

### Gemini（免费档）

1. 打开 https://aistudio.google.com/app/api-keys，创建 API Key
2. 新账号默认 Free Tier，flash 系列模型可用，有速率限制；视频 File API 免费档上限 2GB

## 七、红线

- 客户 PII（姓名/邮箱/电话/聊天记录）不发给任何外部模型
- 内部知识库文件（kttx/knowledge-base/）不用于对外输出
- Key 不入 Git、不入文档、不在聊天里明文回显

## 四、方案 B（未来可选）：官方 Token Plan MCP

官方包：`uvx minimax-coding-plan-mcp -y`，工具 `web_search` + `understand_image`。

接入 Codex（需要**用户批准后**才改配置，目前未启用）：

```toml
# ~/.codex/config.toml（示例，未应用）
[mcp_servers.minimax]
command = "uvx"
args = ["minimax-coding-plan-mcp", "-y"]
env = { MINIMAX_API_KEY = "你的Key", MINIMAX_API_HOST = "https://api.minimaxi.com" }
```

优势：工具原生出现在 Codex 工具列表，我不用再走终端。

## 五、方案 C（备选）：npm minimax-vision-mcp-server

`npx -y minimax-vision-mcp-server`，工具 `minimax_vision_understand`，支持本地/远程图片，模型默认 MiniMax-M3。适合不想用官方包的场景。

## 六、key 获取

1. 登录 https://platform.minimaxi.com（国内）或 https://platform.minimax.io（国际）
2. 订阅管理 > Token Plan，查看订阅 Key
3. 设置环境变量 `MINIMAX_API_KEY`，不要写进仓库或聊天

## 七、红线

- 客户 PII（姓名/邮箱/电话/聊天记录）不发给任何外部模型
- 内部知识库文件（kttx/knowledge-base/）不用于对外输出
- Key 不入 Git、不入文档、不在聊天里明文回显
