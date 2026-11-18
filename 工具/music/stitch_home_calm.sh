#!/bin/bash
# 11-18 用户：「主页音乐换一首更轻的琴，古筝，不要太强的印象，太强反而容易听腻」
# Lyria 2 一次只出 30 秒左右：music.json 里 home_3（古筝）、home_4（古琴）、home_5（琴筝合奏）三段，
# 按 古琴 → 古筝 → 合奏 用 5 秒交叉淡化接成一首约 88 秒的 原型/music/home_calm.mp3，提 6 dB 再限幅（平均约 -19 dB，比原 home_1 的 -14.7 dB 轻）。
# 生成：PATH=~/google-cloud-sdk/bin:$PATH PROJECT=<有赠金的项目> CAP_USD=0.3 python3 lyria.py home_3 home_4 home_5   （在放 lyria.py、music.json 的目录跑，出 out/*.wav）
# 用法：bash stitch_home_calm.sh <out 目录>
F=$(python3 -c "import imageio_ffmpeg as i;print(i.get_ffmpeg_exe())"); W="${1:-out}"; D="$(cd "$(dirname "$0")/../.." && pwd)/原型/music"
T="silenceremove=start_periods=1:start_threshold=-55dB,areverse,silenceremove=start_periods=1:start_threshold=-55dB,areverse"
"$F" -v error -y -i "$W/home_4.wav" -i "$W/home_3.wav" -i "$W/home_5.wav" -filter_complex "[0]${T}[a];[1]${T}[b];[2]${T}[c];[a][b]acrossfade=d=5:c1=tri:c2=tri[ab];[ab][c]acrossfade=d=5:c1=tri:c2=tri,volume=6dB,alimiter=limit=0.92[o]" -map "[o]" -ar 44100 -ac 2 -b:a 80k "$D/home_calm.mp3"
