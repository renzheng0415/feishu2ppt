# Setup and Authorization

## 1. Prerequisites

- Python 3.11+
- Node.js 18+
- `lark-cli`（已验证：`@larksuite/cli 1.0.60`；更新版本需重新跑诊断）
- `officecli`（已验证：`1.0.143`；更新版本需重新跑测试）
- `ffmpeg`（可选；用于从视频自动提取 PPT 封面，缺失时视频仍可嵌入）

Check:

```bash
python3 --version
node --version
lark-cli -v
officecli --version
ffmpeg -version
```

## 2. Install lark-cli

```bash
npm install -g @larksuite/cli
```

The package is the official Lark/Feishu CLI. Do not substitute similarly named community CLIs.

## 3. Configure lark-cli

First-time application setup:

```bash
lark-cli config init --new
```

This is interactive. The agent should start it, inspect the output, and stop only when the user must open the Feishu developer page or confirm login. Never print an App Secret.

## 4. Authorize document access

Use user identity and minimum document/drive scopes:

```bash
lark-cli auth login --domain docs --domain drive --no-wait --json
```

The agent must:

1. Read `verification_url` and `device_code` from the JSON.
2. Generate a QR code with `lark-cli auth qrcode <verification_url> --output <file.png>`.
3. Show the unchanged URL and QR code to the user.
4. End the turn and wait for the user to confirm authorization.
5. In the next turn, run `lark-cli auth login --device-code <device_code>` itself.

Do not start blocking polling before the user sees the authorization URL.

Verify:

```bash
lark-cli auth status --json --verify
```

The user identity must be available and verified. Bot identity alone cannot read the user's private documents.

## 5. Install officecli

以下命令来自 OfficeCLI 官方安装入口。公开发布或升级依赖后，必须重新执行 `bash tests/run-tests.sh`，不能只检查版本号。

macOS/Linux:

```bash
curl -fsSL https://d.officecli.ai/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://d.officecli.ai/install.ps1 | iex
```

Verify with `officecli --version`.

## 6. Common failures

- `lark-cli_missing`: install `@larksuite/cli` globally and reopen the terminal.
- `configured=false`: run `lark-cli config init --new`.
- `authorized=false`: start the split-flow authorization above.
- `permission_violations`: authorize the missing user scope; do not switch to bot identity.
- media download 403: refresh user authorization and verify `docs:document.media:download`.
- OfficeCLI command not found: reopen the terminal or add its install directory to `PATH`.
- `ffmpeg_optional.installed=false`: 视频仍会嵌入，但静态预览可能显示为空白；安装 ffmpeg 后重新执行计划阶段即可补齐封面。
