#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p aligned
# Align the tip of the dome to the same point in every source image.
xs=(14 26 36 56 97 99 114 130 127 144 188 225 278)
ys=(4 23 29 29 33 32 34 38 33 35 39 39 38)
for i in $(seq 0 12); do
  printf -v name '%03d' "$i"
  ffmpeg -y -loglevel error \
    -i "../photo-turn/frames-png/frame-$name.png" \
    -vf "pad=2500:800:${xs[$i]}:${ys[$i]}:color=black@0,scale=1600:512:flags=lanczos,format=rgba" \
    -frames:v 1 "aligned/frame-$name.png"
done
ffmpeg -y -loglevel error -i aligned/frame-000.png -frames:v 1 \
  -c:v libwebp -q:v 90 poster.webp

# Interpolate the photographed views. The alpha channel is interpolated on its
# own so background pixels do not create coloured fringes along the building.
ffmpeg -y -loglevel error -framerate 8 -i aligned/frame-%03d.png \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=0.375,split[rgb][a];color=c=black:s=1600x512:r=8:d=2[bg];[bg][rgb]overlay=shortest=1:format=auto,format=yuv420p,minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1[video];[a]alphaextract,format=yuv420p,minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,extractplanes=y,lut=y='clip((val-16)*255/219,0,255)'[mask];[video][mask]alphamerge,format=yuva420p[out]" \
  -map '[out]' -c:v libvpx-vp9 -lossless 1 -g 5 \
  -pix_fmt yuva420p -auto-alt-ref 0 muj-turn-alpha.webm
