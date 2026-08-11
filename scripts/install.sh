#!/usr/bin/env bash
# Install feishu2ppt into a common skill directory and link configured runtimes.
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON_ROOT="${AGENT_SKILLS_ROOT:-$HOME/.agents/skills}"
TARGET="$COMMON_ROOT/feishu2ppt"

mkdir -p "$COMMON_ROOT"
if [[ "$SOURCE_DIR" != "$TARGET" ]]; then
  if [[ -e "$TARGET" ]]; then
    mv "$TARGET" "$TARGET.backup.$(date +%Y%m%d%H%M%S)"
  fi
  cp -R "$SOURCE_DIR" "$TARGET"
fi

roots=("${CODEX_SKILLS_ROOT:-$HOME/.codex/skills}" "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}")
if [[ -n "${WORKBUDDY_SKILLS_ROOT:-}" ]]; then
  roots+=("$WORKBUDDY_SKILLS_ROOT")
fi

for root in "${roots[@]}"; do
  mkdir -p "$root"
  link="$root/feishu2ppt"
  if [[ "$link" == "$TARGET" ]]; then
    continue
  fi
  if [[ -L "$link" ]] && [[ "$(readlink "$link")" == "$TARGET" ]]; then
    continue
  fi
  if [[ -e "$link" || -L "$link" ]]; then
    backup="$link.runtime-backup.$(date +%Y%m%d%H%M%S)"
    mv "$link" "$backup"
    echo "Backed up stale runtime entry: $backup"
  fi
  ln -s "$TARGET" "$link"
  [[ -L "$link" ]] && [[ "$(readlink "$link")" == "$TARGET" ]] || {
    echo "ERROR: runtime entry verification failed: $link" >&2
    exit 1
  }
done

echo "Installed: $TARGET"
