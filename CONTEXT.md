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

当前处于纯文档阶段，尚未进入工程实现，因此没有启动命令、端口或可运行服务。

## 当前状态

阶段 0 的文档基线已建立：MVP 范围、QQ 接入方向、Session 隔离规则和 LangGraph 主工作流已确定。下一阶段才实现离线 LangGraph 核心，并先通过模拟消息验收，再接入 NapCat。

## 我的薄弱模块

- LangGraph State：一次图运行中各节点共同读写的状态；后续会重点说明它如何保存消息与路由结果。
- Tool Calling：模型提出工具调用请求，再由程序执行工具并把结果交回模型的机制。
- 异步事件处理：使用 `async` / `await` 处理 QQ 的持续消息事件，避免等待模型响应时阻塞其他会话。
