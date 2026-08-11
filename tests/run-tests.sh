#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py' -v

INSTALL_HOME="$(mktemp -d "${TMPDIR:-/tmp}/feishu2ppt-install-test.XXXXXX")"
mkdir -p "$INSTALL_HOME/.codex/skills/feishu2ppt" "$INSTALL_HOME/.claude/skills/feishu2ppt"
printf 'old' > "$INSTALL_HOME/.codex/skills/feishu2ppt/old-marker"
printf 'old' > "$INSTALL_HOME/.claude/skills/feishu2ppt/old-marker"
HOME="$INSTALL_HOME" bash "$ROOT/scripts/install.sh" >/dev/null
test -L "$INSTALL_HOME/.codex/skills/feishu2ppt"
test -L "$INSTALL_HOME/.claude/skills/feishu2ppt"
test "$(readlink "$INSTALL_HOME/.codex/skills/feishu2ppt")" = "$INSTALL_HOME/.agents/skills/feishu2ppt"
find "$INSTALL_HOME/.codex/skills" -maxdepth 2 -type f -name old-marker -path '*runtime-backup*' | grep -q .
find "$INSTALL_HOME/.claude/skills" -maxdepth 2 -type f -name old-marker -path '*runtime-backup*' | grep -q .
echo "Installer upgrade test passed"

if command -v officecli >/dev/null 2>&1; then
  WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/feishu2ppt-test.XXXXXX")"
  cp "$ROOT/examples/sample-manifest.json" "$WORKDIR/fetch_manifest.json"
  python3 "$ROOT/scripts/run.py" plan \
    --source-xml "$ROOT/examples/sample-feishu.xml" \
    --workdir "$WORKDIR" >/dev/null
  python3 "$ROOT/scripts/run.py" render \
    --plan "$WORKDIR/deck.json" \
    --output "$WORKDIR/showcase.pptx" \
    --approve-plan >/dev/null
  officecli validate "$WORKDIR/showcase.pptx"
  echo "E2E passed: $WORKDIR/showcase.pptx"

  python3 "$ROOT/tests/build_layout_gallery.py" \
    --skill-root "$ROOT" --output "$WORKDIR/layout-gallery.json"
  python3 "$ROOT/scripts/run.py" render \
    --plan "$WORKDIR/layout-gallery.json" \
    --output "$WORKDIR/layout-gallery.pptx" \
    --approve-plan >/dev/null
  officecli validate "$WORKDIR/layout-gallery.pptx"
  officecli view "$WORKDIR/layout-gallery.pptx" issues --json | grep -q '"count": 0'
  test -s "$WORKDIR/preview-grid.png"
  python3 - "$WORKDIR/preview-grid.png" <<'PY'
import struct
import sys
with open(sys.argv[1], "rb") as handle:
    handle.seek(16)
    width, height = struct.unpack(">II", handle.read(8))
assert width == 1600 and height >= 1600, (width, height)
PY
  echo "20-layout gallery passed: $WORKDIR/layout-gallery.pptx"

  python3 "$ROOT/tests/build_chart_gallery.py" --output "$WORKDIR/chart-gallery.json"
  python3 "$ROOT/scripts/run.py" render \
    --plan "$WORKDIR/chart-gallery.json" \
    --output "$WORKDIR/chart-gallery.pptx" \
    --approve-plan >/dev/null
  officecli validate "$WORKDIR/chart-gallery.pptx"
  officecli view "$WORKDIR/chart-gallery.pptx" issues --json | grep -q '"count": 0'
  officecli view "$WORKDIR/chart-gallery.pptx" text | grep -q '目标组合图'
  echo "12-chart gallery passed: $WORKDIR/chart-gallery.pptx"

  python3 - "$WORKDIR/long-table.xml" <<'PY'
import sys
from pathlib import Path
rows = "".join(f"<tr><td>{i}</td><td>项目{i}</td></tr>" for i in range(1, 31))
Path(sys.argv[1]).write_text(
    "<title>长表格分页</title><h2>项目明细</h2><p>版式：表格</p>"
    f"<table><tr><th>序号</th><th>项目</th></tr>{rows}</table>",
    encoding="utf-8",
)
PY
  python3 "$ROOT/scripts/run.py" plan \
    --source-xml "$WORKDIR/long-table.xml" \
    --workdir "$WORKDIR/long-table-files" >/dev/null
  python3 - "$WORKDIR/long-table-files/deck.json" <<'PY'
import json
import sys
plan = json.load(open(sys.argv[1], encoding="utf-8"))
tables = [slide for slide in plan["slides"] if slide["type"] == "table"]
assert [len(slide["rows"]) for slide in tables] == [12, 12, 6]
assert all(slide["headers"] == ["序号", "项目"] for slide in tables)
PY
  python3 "$ROOT/scripts/run.py" render \
    --plan "$WORKDIR/long-table-files/deck.json" \
    --output "$WORKDIR/long-table.pptx" \
    --approve-plan >/dev/null
  officecli validate "$WORKDIR/long-table.pptx"
  officecli view "$WORKDIR/long-table.pptx" text | grep -q '项目30'
  echo "Long-table pagination passed: $WORKDIR/long-table.pptx"
else
  echo "SKIP E2E: officecli is not installed"
fi

if python3 "$ROOT/scripts/run.py" all --help >/dev/null 2>&1; then
  echo "ERROR: one-shot all command must not be available" >&2
  exit 1
fi
echo "Two-stage CLI gate passed"
