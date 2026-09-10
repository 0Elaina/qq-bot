# QQ LangGraph Agent Bot — 项目上下文

## 项目简介

这是一个基于 QQ 的小型 AI Agent Bot，用于练习 LangChain、LangGraph、Tool Calling、会话状态和 Python 异步事件处理。学习效果与开发效率优先，不追求生产级复杂度。

## 技术栈

- 计划语言：Python。
- Agent 基础：LangChain（模型、消息和 Tool）。
- 工作流：LangGraph（State、Node、Edge、Conditional Edge）。
- QQ 接入：NapCat + OneBot 11。
- 持久化：SQLite。
- 模型：支持 Tool Calling 的低成本 OpenAI 兼容云 API。

上述技术栈已全部在工程代码中落地实现，并完成真实网络端到端验收。

## 启动方式

离线模拟运行命令：
```powershell
.venv\Scripts\qq-bot
# 或
.venv\Scripts\python -c "import qq_bot; qq_bot.main()"
```

NapCat 实时网关服务运行命令：
```powershell
uv run qq-bot-server
# 或
.venv\Scripts\python -m qq_bot.server
```
NapCat 反向 WebSocket 连接地址：`ws://127.0.0.1:8080/onebot/v11/ws`。
运行时会自动创建并维护 `data/agent_state.db`，保存 LangGraph 短期会话 checkpoint。

## 当前状态

- [已完成] 离线 LangGraph 核心架构、AST 安全计算器与 5 大用例验收。
- [已完成] 接入真实 OpenAI 兼容大模型 API（DeepSeek-V4-Flash），实现自主 Tool Calling、多轮持久化记忆与用户会话隔离。
- [已完成] 接入 NapCat / OneBot 11 反向 WebSocket 协议适配层与 FastAPI 网关服务（`qq-bot-server`），全链路真机联调验收通过。
- [已完成] 项目收尾、废弃代码清理、.env.example 模板与 README.md 撰写，已成功推送到 GitHub 远程仓库。
- [已完成] 傲娇猫娘个性化人设定制：独立提示词管理（`prompts/persona.md`）与 `model_node` 动态无状态注入，真机联调验收通过。
- [已完成] 核心工具库全量完成 LLM-Native 现代化升级：集成 Python Code Interpreter 代码解释器、Bangumi 统一番剧检索与现实时钟工具，全链路真机联调验收通过。
- [已完成] 长效记忆与主人画像系统（Long-Term Memory）：实现 `MemoryRepository` 异步持久化层（`data/bot.db`），打通 `record_user_memory` 与 `forget_user_memory` 双 LLM-Native 工具，实现零状态污染的动态 SystemMessage 注入、跨群聊/私聊用户偏好打通与跨用户隐私隔离，离线仿真全场景验收通过。
- [已完成] 害羞胆小软萌小猫娘人设升级与多模态二次元语音系统：重塑 `prompts/persona.md`，实现基于 Fish Audio 的纯内存 Base64 异步音频直发工具 `send_voice_message`，完成“纯日语原声语音 + 1:1 语义同步中文文本”的双语协同模式。
- [当前阶段] 进行 NapCat 端到端真机联调与多场景互动验证。



## 我的薄弱模块

- LangGraph State：一次图运行中各节点共同读写的状态；后续会重点说明它如何保存消息与路由结果。
- Tool Calling：模型提出工具调用请求，再由程序执行工具并把结果交回模型的机制。
- 异步事件处理：使用 `async` / `await` 处理 QQ 的持续消息事件，避免等待模型响应时阻塞其他会话。
