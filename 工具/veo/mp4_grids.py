# -*- coding: utf-8 -*-
"""11-18 Veo 视频 → cut_generals.py 要的帧图：每条 40 帧（0.2–3.45 秒，每秒 12 帧），8 列 × 5 行拼一张 jpg。
原来在 Cloud Shell 里切再取回，现在视频整包拿回本机用 imageio_ffmpeg 自带的 ffmpeg 切。
用法：python3 三国志/工具/veo/mp4_grids.py <视频目录> <输出帧图目录> [每帧宽 432]
"""
import subprocess, sys, io
from pathlib import Path
import imageio_ffmpeg
from PIL import Image
src, dst = Path(sys.argv[1]), Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
FW = int(sys.argv[3]) if len(sys.argv) > 3 else 432   # 第二章帧图每帧 432×768
FF = imageio_ffmpeg.get_ffmpeg_exe()
for mp in sorted(src.glob('*.mp4')):
    out = dst / f'{mp.stem}.jpg'
    if out.exists(): continue
    raw = subprocess.run([FF, '-v', 'error', '-ss', '0.2', '-i', str(mp), '-vf', f'fps=12,scale={FW}:-2', '-frames:v', '40', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    frames, i = [], 0
    while True:
        j = raw.find(b'\x89PNG', i + 1)
        frames.append(Image.open(io.BytesIO(raw[i:j if j > 0 else None])).convert('RGB'))
        if j < 0: break
        i = j
    w, h = frames[0].size; grid = Image.new('RGB', (w * 8, h * 5), (128, 128, 128))
    for k, f in enumerate(frames[:40]): grid.paste(f, ((k % 8) * w, (k // 8) * h))
    grid.save(out, quality=92); print(out.name, len(frames), '帧')
