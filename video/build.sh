#!/usr/bin/env bash
# usage: build.py-style helper (bash): ./build.sh S1 [quality_dir]   -> out/S1_captions.mp4 + out/S1.mp4 + out/S1.srt
set -e
cd "$(dirname "$0")"
N=$1; Q=${2:-720p30}
mod=$(echo $N | tr 'S' 's')
SRC=media/videos/$mod/$Q/$N.mp4
mkdir -p out
cp captions/$N.srt out/$N.srt
cp $SRC out/$N.mp4
ffmpeg -y -v error -i $SRC -vf "subtitles=captions/$N.srt:force_style='FontName=Adwaita Sans,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H99000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=12,Alignment=2'" -c:v libx264 -preset veryfast -crf 20 -c:a copy out/${N}_captions.mp4
ls -la out/$N*
