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

上述技术仅为已确认的设计选择，当前尚未安装依赖、创建工程代码、配置模型密钥或接入 QQ。

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

- [已完成] 接入 NapCat / OneBot 11 反向 WebSocket 协议适配层与 FastAPI 网关服务（`qq-bot-server`），实现非阻塞后台并发派发与生命周期优雅停机，服务验收通过。
- [下一步] 本地运行 NapCat 联调，或补齐 DESIGN.md 规划的本地笔记查询 Tool。

## 我的薄弱模块

- LangGraph State：一次图运行中各节点共同读写的状态；后续会重点说明它如何保存消息与路由结果。
- Tool Calling：模型提出工具调用请求，再由程序执行工具并把结果交回模型的机制。
- 异步事件处理：使用 `async` / `await` 处理 QQ 的持续消息事件，避免等待模型响应时阻塞其他会话。
