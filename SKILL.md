---
name: feishu2ppt
description: "把飞书云文档转换为可编辑的高级 PowerPoint。适用于用户给出飞书 Docx/Wiki 链接并要求生成提报 PPT、汇报 PPT、培训课件，或将飞书文字、图片、视频、表格和数据自动排版为 PPTX。包含 lark-cli 配置诊断、文档与素材读取、先审方案再渲染、23 套主题、20 种内容版式、12 种原生图表、微软雅黑字体、OfficeCLI 生成、校验和视觉质检。可安装到 Codex、Claude Code、WorkBuddy 及其他支持 Agent Skills 的智能体。不用于只导出飞书原文、编辑源文档或未经用户确认直接渲染成稿。"
metadata:
  version: "1.0.0"
---

# Feishu2PPT

把飞书文档作为团队协作的内容真源，输出可编辑 `.pptx`。默认字体为 `Microsoft YaHei`（微软雅黑）。

## 必须遵守

- 飞书读取优先使用 `lark-cli docs +fetch --as user`，素材使用 `docs +media-download`。
- 不保存、复制或输出用户的 App Secret、access token 或其他凭据。
- 使用本 Skill 自带脚本，不依赖安装机器上的绝对路径或其他私有 Skill。
- 自动生成的 `deck.json` 只是初稿。生成前必须检查页面结论、版式、图表和素材对应关系，必要时编辑该文件。
- 完成标准：PPT 已生成、`officecli validate` 通过、`view issues` 为 0、整稿缩略图经过视觉检查。
- 不把进程成功或 HTTP 200 当成 PPT 质量验收。

## 工作流

### 1. 环境诊断

```bash
python3 "$SKILL_ROOT/scripts/doctor.py"
```

如果 `ready` 为 false，读取 [setup.md](references/setup.md)，由智能体完成可代办的安装与授权发起；登录和浏览器确认交给用户。

### 2. 检查飞书文档结构

读取 [authoring-contract.md](references/authoring-contract.md)。默认约定：

- 文档标题 → PPT 封面标题。
- 一级标题 → 章节转场。
- 二级标题 → 一页 PPT。
- 二级标题下的段落、列表、图片、视频和表格 → 该页内容。
- 数字表格 → 原生图表；非数字表格 → 原生表格。
- 原生表格每页最多 12 行，超出后自动拆成续页并重复表头。

如果原文不符合约定，先报告结构问题；不要擅自改写飞书原文。必要时可在本地 `deck.json` 调整分页和布局。

### 3. 先给风格

读取 [style-catalog.md](references/style-catalog.md)，根据受众和内容推荐 3 套，默认首选放第一。用户已指定风格时直接使用，不重复询问。

推荐默认值：

- 通用提报：`vercel_minimal`（极简纯白）
- 房地产项目：`realestate_gold` 或 `architectural_sand`
- 经营汇报：`executive_navy`
- 数据报告：`data_journalism`
- 产品发布：`apple_keynote`

### 4. 生成并审查页面计划

```bash
python3 "$SKILL_ROOT/scripts/run.py" plan \
  --doc "飞书文档 URL 或 token" \
  --theme "vercel_minimal" \
  --workdir "/绝对路径/提报文件-files"
```

其中 `$SKILL_ROOT` 表示智能体实际安装后的 `feishu2ppt` 目录，不要求用户手动设置环境变量。

计划阶段保留：

- `<文件名>-files/source.xml`：飞书原始结构快照。
- `<文件名>-files/assets/`：图片、视频和画板素材。
- `<文件名>-files/deck.json`：可快速修改的页面配置。
- `<文件名>-files/plan-preview.md`：供用户快速审查的页面清单。
- `<文件名>-files/plan-report.json`：结构和内容校验报告。

必须先向用户展示主题、页数、章节、页面标题、版式、图表与素材分配。用户确认后才进入渲染；未确认不得代填 `--approve-plan`。

### 5. 用户确认后渲染

```bash
python3 "$SKILL_ROOT/scripts/run.py" render \
  --plan "/绝对路径/提报文件-files/deck.json" \
  --output "/绝对路径/提报文件.pptx" \
  --approve-plan
```

渲染后保留：

- `<文件名>-files/preview-grid.png`：整稿视觉检查图。

### 6. 内容设计复核

生成前后必须检查：

1. 每页只有一个核心结论，标题与正文一致。
2. 相邻页面不要连续使用相同卡片版式。
3. 图片、视频与所在页标题有关，不把素材当装饰。
4. 图表形式与数据关系匹配；精确查值用表格，趋势和差异用图表。
5. 图表右侧必须写出业务结论，不只重复数值。
6. 字体为微软雅黑，标题不低于 36pt，正文不低于 18pt。

## 局部重做

需要修改风格、版式或图表时，优先编辑 `deck.json` 后只重跑：

```bash
python3 "$SKILL_ROOT/scripts/run.py" render \
  --plan "/路径/deck.json" \
  --output "/路径/输出.pptx" \
  --approve-plan
```

然后重新执行校验和截图检查。已有输出会先生成 `.bak` 备份。

## 跨智能体安装

- macOS/Linux：`bash scripts/install.sh`
- Windows：`powershell -ExecutionPolicy Bypass -File scripts/install.ps1`

安装器以 `~/.agents/skills/feishu2ppt` 为公共真源，并为 Codex、Claude Code 建立入口。WorkBuddy 使用 `WORKBUDDY_SKILLS_ROOT` 指向它真实的 Skill 根目录；其他兼容 Agent Skills 的智能体可设置对应根目录或复制完整文件夹。未验证的运行时不得写成“已支持”。

## 边界

- 不负责修改原飞书文档，除非用户明确要求。
- 飞书内嵌电子表格或多维表格只会识别引用；需要下钻数据时应调用对应飞书 Sheets/Base 能力后再写入 `deck.json`。
- 浏览器只用于飞书首次登录或 CLI 无法覆盖的授权步骤。
- 未提供真实飞书链接时，只能报告本地 XML 到 PPTX 链路已验证，不能报告飞书授权与在线读取已验证。
