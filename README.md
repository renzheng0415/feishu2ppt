# Feishu2PPT

> 在飞书里共同写，在 PowerPoint 里专业交付。

Feishu2PPT reads a Feishu/Lark document, preserves its text, images, video and data structure, produces a reviewable slide plan, and renders a natively editable `.pptx` with OfficeCLI.

Current release: `1.0.0`. Explicit CLI theme choices override document defaults; mixed pages preserve every body block, table and media asset; media caches are keyed by source identity; long tables paginate with repeated headers; missing media, malformed layouts and invalid chart values fail at the plan gate; upgrades repair stale runtime entries; a candidate PPTX must pass every quality check before atomically replacing the final file.

## When to use it

- A project team writes proposals together in Feishu but delivers PowerPoint.
- A consulting or advertising team needs repeatable decks from structured documents.
- A document contains tables that should become editable charts rather than screenshots.

## What it delivers

- Original Feishu XML snapshot and downloaded media.
- Reviewable `deck.json`, `plan-preview.md`, and validation report.
- Editable PowerPoint with 23 themes, 20 layout routes and 12 native chart recipes.
- Full-deck preview grid, OpenXML validation, issue scan and placeholder gate.

![Feishu2PPT demo](assets/demo.gif)

![Feishu2PPT showcase](assets/showcase.png)

## Install

From an extracted folder:

```bash
npx skills add /path/to/feishu2ppt -g --all
```

Or use the bundled runtime installers:

```bash
# macOS / Linux
bash scripts/install.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

The installers support `AGENT_SKILLS_ROOT`, `CODEX_SKILLS_ROOT`, `CLAUDE_SKILLS_ROOT`, and optional `WORKBUDDY_SKILLS_ROOT` environment overrides.

After installation, say:

```text
使用 feishu2ppt 把这份飞书文档做成可编辑的提报 PPT。先推荐 3 套风格并生成页面计划，未经我确认不要渲染：<飞书文档链接>
```

## First run

Read `references/setup.md` and run:

```bash
python3 scripts/doctor.py
```

The skill uses the official `@larksuite/cli` with user authorization. Credentials remain in the CLI's own credential store and are never copied into the skill.
`ffmpeg` is optional and is used only to generate visible poster frames for embedded videos.

## Two-stage workflow

Generate and validate the plan:

```bash
python3 scripts/run.py plan \
  --doc "https://example.feishu.cn/docx/xxx" \
  --theme data_journalism \
  --workdir ./output/project-files
```

Review `deck.json`, `plan-preview.md`, and `plan-report.json`. Then render explicitly:

```bash
python3 scripts/run.py render \
  --plan ./output/project-files/deck.json \
  --output ./output/project.pptx \
  --approve-plan
```

The renderer refuses to proceed when the plan has missing content, unknown themes, broken media, malformed tables, inconsistent chart dimensions, or placeholder text.

完整中文使用说明、飞书写作模板和三个可复用案例见 [docs/QUICKSTART_ZH.md](docs/QUICKSTART_ZH.md)。不登录飞书的本地演示文件见 [examples/README.md](examples/README.md)。

## Feishu authoring contract

- Document title: deck cover.
- Heading 1: chapter divider.
- Heading 2: one slide.
- Heading 3: grouped point within a slide.
- Paragraphs and lists: slide content.
- Images and videos: media on the current slide.
- Numeric tables: editable charts; other tables remain editable tables.

See `references/authoring-contract.md` for directives such as `图表：折线图`, `版式：表格`, `结论：...`, and `来源：...`.

## Safety boundaries

- It does not modify the source Feishu document.
- Rendering requires an explicit plan approval flag.
- Direct media URLs must use HTTPS and are limited to 50 MB.
- Existing PPTX output is backed up before replacement.
- A successful process or green OpenXML check is not enough; the preview grid still requires visual inspection.

## Verification

```bash
bash tests/run-tests.sh
```

The release gate covers 33 unit tests, more than 2,000 malformed-plan type mutations, all 20 layouts in a live editable deck, all native chart recipes, mixed text/table/media pages, character-and-line-budget prose pagination, proportional text-box sizing, bounded gallery leads, video posters, 30-row table pagination, current Lark `src` media tokens, distinct URL-only media mapping, media magic-byte normalization, prompt-template false-positive protection, media cache replacement, private-network URL rejection, stale runtime upgrades, atomic publishing and the mandatory two-command approval flow.

## Compatibility

- Codex and Claude Code: supported through standard Agent Skills folders.
- WorkBuddy and other runtimes: set their real Skill root through `WORKBUDDY_SKILLS_ROOT` or install with `npx skills add` when supported.
- macOS/Linux installer: tested.
- Windows installer and video codec behavior: implemented but still marked unverified until the Windows acceptance run is completed.

## License

MIT. External tools such as Lark CLI and OfficeCLI retain their own licenses and installation terms.
