#!/usr/bin/env python3
"""Run feishu2ppt as an explicit plan gate followed by verified rendering."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from doctor import report
from validate_plan import has_placeholder


HERE = Path(__file__).resolve().parent


def execute(args, allow_failure=False):
    proc = subprocess.run(args, text=True, capture_output=True)
    if proc.returncode and not allow_failure:
        raise RuntimeError(proc.stderr or proc.stdout)
    return proc


def plan_preview(plan, target):
    lines = [f"# {plan.get('title', 'PPT 计划')}", "", f"主题：`{plan.get('theme')}`", ""]
    for index, slide in enumerate(plan.get("slides", []), 1):
        title = slide.get("title") or slide.get("statement") or slide.get("quote") or "无标题"
        lines.append(f"## {index:02d}. {title}")
        lines.append(f"版式：`{slide.get('type')}`")
        if slide.get("insight"):
            lines.append(f"结论：{slide['insight']}")
        if slide.get("media"):
            lines.append(f"媒体：{len(slide['media'])} 个")
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")


def create_plan(args, workdir):
    health = report()
    if not health["officecli"]["installed"]:
        raise SystemExit("officecli 未安装。请先按 references/setup.md 安装。")
    if args.doc:
        if not health["lark_cli"]["installed"] or not health["lark_auth"]["authorized"]:
            raise SystemExit("飞书 CLI 尚未配置或授权。请先按 references/setup.md 完成配置。")
        execute([sys.executable, str(HERE / "fetch_feishu.py"), "--doc", args.doc, "--workdir", str(workdir)])
        source_xml = workdir / "source.xml"
        manifest = workdir / "fetch_manifest.json"
    else:
        source_xml = Path(args.source_xml).expanduser().resolve()
        manifest = workdir / "fetch_manifest.json"
        if not manifest.exists():
            manifest.write_text('{"media": []}', encoding="utf-8")

    plan = workdir / "deck.json"
    parse_command = [
        sys.executable, str(HERE / "parse_document.py"), "--source", str(source_xml),
        "--manifest", str(manifest), "--output", str(plan),
    ]
    if args.theme:
        parse_command.extend(["--theme", args.theme])
    execute(parse_command)
    report_path = workdir / "plan-report.json"
    check = execute([sys.executable, str(HERE / "validate_plan.py"), "--plan", str(plan),
                     "--report", str(report_path)], allow_failure=True)
    deck = json.loads(plan.read_text(encoding="utf-8"))
    preview = workdir / "plan-preview.md"
    plan_preview(deck, preview)
    result = json.loads((check.stdout or report_path.read_text(encoding="utf-8")))
    result.update({"plan": str(plan), "plan_preview": str(preview), "report": str(report_path)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if check.returncode:
        raise SystemExit(check.returncode)
    return plan


def render_plan(plan, output, workdir, approved):
    if not approved:
        raise SystemExit("渲染已停止：请先检查 deck.json 与 plan-preview.md，再显式添加 --approve-plan。")
    check = execute([sys.executable, str(HERE / "validate_plan.py"), "--plan", str(plan)], allow_failure=True)
    if check.returncode:
        print(check.stdout or check.stderr)
        raise SystemExit(check.returncode)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, candidate_name = tempfile.mkstemp(
        prefix=f".{output.stem}-candidate-", suffix=".pptx", dir=output.parent,
    )
    os.close(fd)
    os.unlink(candidate_name)
    candidate = Path(candidate_name)
    try:
        execute([sys.executable, str(HERE / "render_ppt.py"), str(plan), str(candidate)])
        validation = execute(["officecli", "validate", str(candidate)]).stdout.strip()
        issues_raw = execute(["officecli", "view", str(candidate), "issues", "--json"]).stdout
        issues = json.loads(issues_raw).get("data", {}).get("count", 0)
        if issues:
            raise SystemExit(f"PPT 问题扫描发现 {issues} 个问题，拒绝替换正式文件。")
        text_dump = execute(["officecli", "view", str(candidate), "text"]).stdout
        if has_placeholder(text_dump):
            raise SystemExit("PPT 中仍有占位文案，拒绝替换正式文件。")
        deck = json.loads(plan.read_text(encoding="utf-8"))
        page_count = 1 + len(deck.get("slides", []))
        grid = workdir / "preview-grid.png"
        grid_height = max(1200, ((page_count + 3) // 4) * 260 + 40)
        execute(["officecli", "view", str(candidate), "screenshot", "--page", f"1-{page_count}",
                 "--grid", "4", "--screenshot-height", str(grid_height), "--out", str(grid)])
        if output.exists():
            shutil.copy2(output, str(output) + ".bak")
        os.replace(candidate, output)
    finally:
        if candidate.exists():
            candidate.unlink()
    result = {"success": True, "output": str(output), "plan": str(plan), "preview": str(grid),
              "slides": page_count, "validation": validation, "issues": 0,
              "requires_visual_review": True}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def add_source_args(parser):
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--doc")
    source.add_argument("--source-xml")
    parser.add_argument("--theme")
    parser.add_argument("--workdir", required=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    plan_cmd = sub.add_parser("plan")
    add_source_args(plan_cmd)
    render_cmd = sub.add_parser("render")
    render_cmd.add_argument("--plan", required=True)
    render_cmd.add_argument("--output", required=True)
    render_cmd.add_argument("--workdir")
    render_cmd.add_argument("--approve-plan", action="store_true")
    args = parser.parse_args()

    if args.phase == "plan":
        workdir = Path(args.workdir).expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        create_plan(args, workdir)
    else:
        plan = Path(args.plan).expanduser().resolve()
        workdir = Path(args.workdir).expanduser().resolve() if args.workdir else plan.parent
        render_plan(plan, Path(args.output).expanduser().resolve(), workdir, args.approve_plan)


if __name__ == "__main__":
    main()
