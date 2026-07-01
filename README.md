# MulCat 用户版使用指南

MulCat 是一个 Windows 桌面启动器，用来管理和启动多个 Claude / Codex 命令行配置。

普通用户不需要安装 Python、Node.js，也不需要自己构建前端。请直接在 GitHub Release 页面下载已经打包好的 Windows 安装包。

## 下载与启动

1. 打开本项目的 GitHub Release 页面。
2. 下载最新版本的 Windows 安装包，例如 `MulCatSetup.exe`。
3. 双击安装包，按提示完成安装。
4. 安装完成后，从开始菜单或桌面快捷方式启动 `MulCat`。

如果你下载的是便携版压缩包 `MulCat-windows.zip`，请先解压，然后在解压后的文件夹里双击运行：

```text
MulCat.exe
```

便携版注意：请不要只复制单个 `MulCat.exe`。发布包中的 `_internal` 文件夹也必须和 `MulCat.exe` 放在一起。

首次启动后，软件会在安装目录或便携版目录中创建本地运行数据目录：

```text
profiles/
scripts/
```

这些目录用于保存你的个人配置和生成的 PowerShell 启动脚本。

## 使用前准备

MulCat 只是启动器，不会替你安装 Claude 或 Codex CLI。

请先确保你已经安装并能在 PowerShell 中运行：

```powershell
claude
```

或：

```powershell
codex
```

推荐同时安装 Windows Terminal，这样 MulCat 可以在新的终端标签页中启动对应配置。

## 创建 Claude 配置

1. 打开 MulCat。
2. 左侧选择 `Claude`。
3. 点击右上角 `+`。
4. 填写配置名称、工作目录、Base URL、Auth Token 和模型名称。
5. 根据需要开启或关闭：
   - `--dangerously-skip-permissions`
   - `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`
   - `CLAUDE_CODE_USE_POWERSHELL_TOOL`
6. 点击 `保存并生成 PS1`。
7. 回到配置列表，点击启动按钮。

保存后，MulCat 会生成类似这样的脚本：

```powershell
$env:ANTHROPIC_BASE_URL = '...'
$env:ANTHROPIC_AUTH_TOKEN = '...'
$env:ANTHROPIC_MODEL = '...'

claude '--dangerously-skip-permissions'
```

这些环境变量只作用于本次启动的进程，不会写入系统环境变量。

## 创建 Codex 配置

1. 打开 MulCat。
2. 左侧选择 `Codex`。
3. 点击右上角 `+`。
4. 填写 API Key 环境变量名、API Key、Provider、Base URL、模型和 `wire_api`。
5. 根据需要设置：
   - `--ignore-user-config`
   - `model_reasoning_effort`
   - `disable_response_storage`
   - `features.apps`
6. 点击 `保存并生成 PS1`。
7. 点击启动按钮。

Codex 配置会生成环境变量和 `codex -c ...` 参数，例如：

```powershell
$env:CUSTOM_API_KEY = '...'

codex `
  '--ignore-user-config' `
  '-c' `
  'model_provider="custom"' `
  '-c' `
  'model="gpt-5"'
```

## 直接编辑 PS1

每个配置卡片上都有一个脚本编辑按钮。

点击后可以直接编辑对应的 `.ps1` 文件。这个功能适合临时调试、添加额外参数，或使用 MulCat 暂时还没有提供表单项的高级配置。

注意：如果之后再次在配置弹窗中点击 `保存并生成 PS1`，MulCat 会根据 JSON 配置重新生成脚本，并覆盖你手动编辑的 `.ps1`。

## 配置文件保存在哪里

用户版会把你的真实配置保存在安装目录或便携版目录下：

```text
profiles/
scripts/
```

其中：

- `profiles/` 保存 JSON 配置。
- `scripts/` 保存生成或手动编辑的 PowerShell 脚本。

如果你想备份自己的配置，只需要备份这两个目录。

## 隐私说明

MulCat 发布包不包含任何个人 profile、script、API Key 或私有 Base URL。

你的 API Key 和 Auth Token 只会保存在你本机的 `profiles/` 和 `scripts/` 目录中。请不要把这些文件提交到公开仓库，也不要在截图中泄露。

## 常见问题

### 双击后没有启动 Claude 或 Codex

请先在普通 PowerShell 中测试：

```powershell
claude
codex
```

如果命令不存在，说明对应 CLI 还没有安装或没有加入 PATH。

### 启动后终端一闪而过

检查生成的 `.ps1` 脚本内容，确认工作目录存在、Base URL 正确、Token 没有多余空格。

### 如何迁移到另一台电脑

1. 在新电脑下载并安装 MulCat。
2. 安装 Claude / Codex CLI。
3. 复制旧电脑的 `profiles/` 和 `scripts/` 到新电脑的 MulCat 目录。

# MulCat 开发者版使用指南

如果你是开发者，想从源码运行或修改 MulCat，请使用下面的流程。

## 环境要求

请先安装：

- Windows 或 macOS
- Python 3.10 或更高版本
- Node.js 18 或更高版本
- Windows Terminal，推荐安装
- PowerShell 7，macOS 端启动 profile 时需要 `pwsh`
- 已安装并可在命令行中运行的 `claude` 或 `codex`

## 项目结构

MulCat 现在按 UI、共享逻辑、平台适配分层：

```text
desktop_ui/       React UI，只通过 pywebview API 调后端
mulcat_core/      共享业务逻辑：配置读写、脚本生成、脚本解析、桌面 API 桥
windows/          Windows 启动方式和无法跨平台共用的适配代码
mac/              macOS 启动方式和无法跨平台共用的适配代码
```

Windows 和 macOS 共用 `mulcat_core/` 中的 profile/schema/script 逻辑。平台目录只放窗口启动、剪贴板、打开目录、终端拉起这类系统差异代码。

## 从源码运行

Windows：

```powershell
cd D:\path\to\MulCat
pip install -r requirements.txt

cd desktop_ui
npm install
npm run build
cd ..

python -m windows.main
```

也可以运行：

```powershell
.\windows\start_desktop_client.bat
```

macOS：

```bash
cd /path/to/MulCat
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

cd desktop_ui
npm install
npm run build
cd ..

.venv/bin/python -m mac.main
```

也可以运行：

```bash
./mac/start_desktop_client.command
```

仓库同时提供了 `requirement.txt` 作为兼容文件，内容与 `requirements.txt` 一致。

## 开发前端

启动 Vite 开发服务器：

```powershell
cd desktop_ui
npm run dev
```

然后在另一个终端中运行桌面壳。

Windows：

```powershell
cd D:\path\to\MulCat
$env:MULCAT_UI_DEV_URL = "http://127.0.0.1:5173"
python -m windows.main
```

macOS：

```bash
cd /path/to/MulCat
export MULCAT_UI_DEV_URL="http://127.0.0.1:5173"
.venv/bin/python -m mac.main
```

## 打包说明

普通用户建议使用 Release 中已经打包好的版本。

开发者如果需要自行打包，需要先构建前端，再使用 PyInstaller：

Windows：

```powershell
cd desktop_ui
npm install
npm run build
cd ..

pyinstaller --noconfirm --clean --windowed --name MulCat --add-data "desktop_ui/dist;desktop_ui/dist" windows/main.py
```

macOS：

```bash
cd desktop_ui
npm install
npm run build
cd ..

pyinstaller --noconfirm --clean --windowed --name MulCat --add-data "desktop_ui/dist:desktop_ui/dist" mac/main.py
```

打包结果会出现在：

```text
dist/MulCat/MulCat.exe
```

## Git 与本地配置

`profiles/` 和 `scripts/` 是本地运行数据目录。

项目已经配置 `.gitignore`：

- `profiles/` 中真实 JSON 不会进入 Git。
- `scripts/` 中真实 PS1 不会进入 Git。
- 只保留 `.gitkeep` 来维持目录结构。

示例文件放在：

```text
examples/
```

请不要使用 `git add -f profiles/...` 或 `git add -f scripts/...` 强制提交真实配置。
