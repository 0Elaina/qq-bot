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
运行时会自动创建并维护 `data/agent_state.db`，保存 LangGraph 短期会话 checkpoint。

## 当前状态

- [已完成] 接入真实 OpenAI 兼容大模型 API（DeepSeek-V4-Flash），成功实现自主 Tool Calling、多轮对话持久化与用户会话隔离，通过 6 大核心场景验收。
- [下一步] 接入 NapCat / OneBot 11 反向 WebSocket 协议适配层（攻坚异步网络事件循环与真实 QQ 消息收发）。

## 我的薄弱模块

- LangGraph State：一次图运行中各节点共同读写的状态；后续会重点说明它如何保存消息与路由结果。
- Tool Calling：模型提出工具调用请求，再由程序执行工具并把结果交回模型的机制。
- 异步事件处理：使用 `async` / `await` 处理 QQ 的持续消息事件，避免等待模型响应时阻塞其他会话。
