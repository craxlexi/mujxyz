#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p frames-webp
for source in frames-png/frame-*.png; do
  name="$(basename "${source%.png}")"
  ffmpeg -y -loglevel error -i "$source" \
    -vf 'scale=1600:533:force_original_aspect_ratio=decrease:flags=lanczos,pad=1600:533:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba' \
    -c:v libwebp -q:v 90 -preset photo "frames-webp/$name.webp"
done
