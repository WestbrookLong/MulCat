# MulCat 使用指南

MulCat 是一个 Windows 桌面启动器，用来管理和启动多个 Claude / Codex 命令行配置。

它的核心思路是：

- 在界面里维护结构化配置。
- 保存配置后生成对应的 PowerShell 脚本。
- 启动时实际运行生成的 `.ps1` 脚本。
- API Key、Auth Token、Base URL 等信息只作为进程级环境变量传给当前启动的终端，不写入系统环境变量。

## 适用场景

- 同时使用多个 Claude Code 账号或中转 API。
- 同时使用多个 Codex provider / model / base_url。
- 希望用图形界面快速选择配置并打开终端。
- 希望保留 `.ps1` 脚本的可读性和可手动编辑能力。

## 环境要求

请先安装：

- Windows
- Python 3.10 或更高版本
- Node.js 18 或更高版本
- Windows Terminal，推荐安装，用于打开新的终端标签页
- 已安装并可在命令行中运行的 `claude` 或 `codex`

## 快速开始

首次使用时，在项目目录中安装依赖并构建前端：

```powershell
cd D:\path\to\MulCat
pip install -r requirements.txt

cd desktop_ui
npm install
npm run build
cd ..
```

然后启动桌面端：

```powershell
.\start_desktop_client.bat
```

如果启动失败或窗口闪退，可以运行调试版本：

```powershell
.\start_desktop_client_debug.bat
```

## 创建配置

打开 MulCat 后：

1. 在左侧选择 `Claude` 或 `Codex`。
2. 点击右上角的 `+` 创建新配置。
3. 填写名称、工作目录、Base URL、模型和 Key 等信息。
4. 点击 `保存并生成 PS1`。
5. 在配置卡片上点击启动按钮。

保存后，MulCat 会把 JSON 配置写入：

```text
profiles/
```

并生成实际运行的 PowerShell 脚本：

```text
scripts/
```

## Claude 配置说明

Claude 配置主要会生成这些环境变量：

```text
ANTHROPIC_BASE_URL
ANTHROPIC_AUTH_TOKEN
ANTHROPIC_MODEL
ANTHROPIC_DEFAULT_SONNET_MODEL
ANTHROPIC_DEFAULT_OPUS_MODEL
ANTHROPIC_DEFAULT_HAIKU_MODEL
API_TIMEOUT_MS
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC
CLAUDE_CODE_USE_POWERSHELL_TOOL
```

如果开启 `--dangerously-skip-permissions`，生成脚本会在启动 Claude 时附加该参数。

## Codex 配置说明

Codex 配置由两部分组成：

- API Key 环境变量，例如 `CUSTOM_API_KEY`
- `codex -c ...` 参数，例如 `model_provider`、`model`、`base_url`、`wire_api`

常见配置项包括：

```text
--ignore-user-config
model_provider
model
model_reasoning_effort
disable_response_storage
features.apps
model_providers.<provider>.base_url
model_providers.<provider>.env_key
model_providers.<provider>.wire_api
```

## 直接编辑 PS1

每个配置卡片上都有一个脚本编辑按钮。

点击后可以直接编辑对应的 `.ps1` 文件。这个功能适合临时调试或添加高级启动参数。

注意：如果之后再次在配置弹窗中点击 `保存并生成 PS1`，MulCat 会根据 JSON 配置重新生成脚本，并覆盖你手动编辑的 `.ps1`。

## 示例配置

示例文件放在：

```text
examples/
```

你可以参考示例创建自己的配置。真实配置请放在：

```text
profiles/
scripts/
```

## 隐私与 Git 提交

`profiles/` 和 `scripts/` 是本地运行数据目录。

项目已经配置 `.gitignore`：

- `profiles/` 中真实 JSON 不会进入 Git。
- `scripts/` 中真实 PS1 不会进入 Git。
- 只保留 `.gitkeep` 来维持目录结构。

请不要使用 `git add -f profiles/...` 或 `git add -f scripts/...` 强制提交真实配置。

## 常用命令

安装 Python 依赖：

```powershell
pip install -r requirements.txt
```

仓库同时提供了 `requirement.txt` 作为兼容文件，内容与 `requirements.txt` 一致。

安装前端依赖：

```powershell
cd desktop_ui
npm install
```

构建前端：

```powershell
npm run build
```

启动桌面端：

```powershell
cd ..
python desktop_client.py
```

或者：

```powershell
.\start_desktop_client.bat
```

## 常见问题

### 打开后是黑屏

请确认已经执行：

```powershell
cd desktop_ui
npm run build
```

如果仍然黑屏，请运行：

```powershell
.\start_desktop_client_debug.bat
```

查看控制台输出。

### 点击启动没有反应

请确认：

- `claude` 或 `codex` 已经安装。
- 在普通 PowerShell 中可以直接运行 `claude` 或 `codex`。
- Windows Terminal 可用。
- 配置里的工作目录存在。

### GitHub 会不会上传我的 Key

默认不会。真实配置文件和生成脚本都在 `.gitignore` 中。

但不要强制添加这些文件，也不要把真实 Key 写入 README、issue、截图或示例文件。
