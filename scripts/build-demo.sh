#!/usr/bin/env bash
# Build the README demo GIF from three real feishu2ppt acceptance screenshots.
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: build-demo.sh <showcase.png> <layout-gallery.png> <long-table.png> <output.gif>" >&2
  exit 2
fi

command -v magick >/dev/null 2>&1 || {
  echo "ImageMagick is required to rebuild the demo GIF." >&2
  exit 1
}

magick "$1" "$2" "$3" \
  -resize '1200x900>' -gravity center -background '#171827' -extent 1200x900 \
  -set delay 180 -loop 0 "$4"

echo "Created: $4"
