# 本地 CLI 个人助手 MVP

这是一个本地单用户命令行个人助手。

当前 MVP 固定为：

- 交互方式：CLI
- 模型提供商：智谱 API
- 数据存储：本地 SQLite
- 工具能力：`add_todo`、`list_todos`、`save_memory`、`get_memory`
- 动作协议：`respond` / `tool_call`

不做 Web、多入口、多 Agent、RAG、Shell 执行。

## 环境要求

- Python `3.11+`
- 可访问智谱 API

## 安装依赖

```powershell
python -m pip install -r requirements.txt
```

## 配置方式

1. 复制 `.env.example` 为 `.env`
2. 修改其中的真实配置

示例：

```env
ZHIPUAI_API_KEY=your-real-api-key
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
ZHIPUAI_MODEL=glm-4-flash
AGENT_DB_PATH=data/agent.db
```

程序启动时会自动读取项目根目录下的 `.env`。
如果系统环境变量里已经设置了同名配置，则系统环境变量优先。

## 启动 CLI

```powershell
python -m app.cli.main
```

可用命令：

- `/help`：显示帮助
- `/clear`：清空当前会话历史
- `/exit`：退出程序

## 数据文件

默认数据库位置：

```text
data/agent.db
```

数据库中固定包含四张表：

- `messages`
- `todos`
- `memories`
- `traces`

## 运行测试

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests -p "test_*.py" -v
```

## 真实智谱联调

默认测试不会访问真实网络。
如果你已经配置好真实智谱环境，并且想手动做一轮联调，可以运行：

```powershell
$env:RUN_REAL_ZHIPU_SMOKE='1'
python -m unittest tests.test_real_smoke -v
```

这个联调会验证两件事：

- 至少跑通一轮普通直接回答
- 四个工具都能真实执行并落库：`save_memory`、`get_memory`、`add_todo`、`list_todos`

## 相关文档

- `docs/personal-assistant-agent-cli-architecture.md`：当前唯一有效的架构文档
- `docs/personal-assistant-agent-mvp.md`：当前 MVP 范围、完成标准和验收建议
