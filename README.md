# Agent Workflow Platform · 多智能体工作流平台

> 个人开源对标 Dify / Langflow 的轻量级多智能体工作流编排引擎。

## 核心特性

- **节点编排**：Start / Tool / LLM / Conditional / HumanConfirm / End 六类节点
- **条件路由**：按状态键路由到不同分支，支持多条件表达式
- **人工确认节点**：执行到该节点暂停，CLI 交互确认或自动审批，状态可持久化恢复
- **Function Calling / 工具调用**：工具注册表带 JSON Schema 描述，LLM 可按需选择工具
- **执行日志与状态回溯**：每步快照落盘（JSON），支持从任意检查点恢复重放
- **一键容器化**：附 Dockerfile 与 docker-compose.yml

## 快速开始

```bash
python workflow_engine.py examples/content_review.json   # 跑示例工作流
python examples/content_review.py                        # 编程式定义并执行
```

## 示例：内容审核工作流

```
Start → 生成文案(LLM) → 敏感词检查(Tool) → [路由]
        ├─ 命中敏感词 → 人工确认(HumanConfirm) → 改写
        └─ 未命中     → End(发布)
```

## 技术栈

Python 3.10+，核心引擎零依赖；LLM 节点可选接入 DeepSeek / 通义千问 API。

## 路线图

- [x] 节点编排与条件路由
- [x] 人工确认节点与状态回溯
- [x] 工具注册与 Function Calling
- [ ] Web 可视化画布
- [ ] MCP 工具协议接入

## License

MIT
