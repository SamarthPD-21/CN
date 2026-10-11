#!/bin/bash
# usage: qa.sh s1 S1 [interval]
cd "$(dirname "$0")"
.venv/bin/manim -ql --disable_caching $1.py $2 2>&1 | grep -E "Error|error|Traceback|s[0-9]\.py|common.py|IndexError|Rendered" | head -20
f=media/videos/$1/480p15/$2.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 $f
rm -f qa/$2_*.png
ffmpeg -v error -i $f -vf "fps=1/${3:-12},scale=640:360,tile=3x4" -frames:v 99 qa/$2_%02d.png
ls qa | grep $2_ | wc -l
