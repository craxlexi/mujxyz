#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p frames-webp
for source in frames/frame-*.png; do
  name="$(basename "${source%.png}")"
  ffmpeg -y -loglevel error -i "$source" \
    -vf 'crop=925:305:20:120,eq=contrast=1.1:saturation=1.3:brightness=-0.02,format=rgba' \
    -c:v libwebp -q:v 94 -preset photo "frames-webp/$name.webp"
done
