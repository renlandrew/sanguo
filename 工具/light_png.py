"""黑底上画的光（ChatGPT）→ 带透明度的光 PNG（10-25 结算页徽章后的神光：用户「后面的光旋转还需要更游戏化，不是HTML化」）。
和 vfx/add_paint.py 同一套「光」转换：四边亮度的 95 分位当黑底，越亮越不透明（增益 GAIN），颜色按透明度反算回去；整张缩到 SIZE 见方，不裁。
用法：<media-venv>/bin/python 三国志/工具/light_png.py <图> <名> [边长 720] [增益 1.6]
输出 原型/img/<名>.png
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
src, name = Path(sys.argv[1]), sys.argv[2]
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 720
GAIN = float(sys.argv[4]) if len(sys.argv) > 4 else 1.6
im = Image.open(src).convert('RGB'); im = im.resize((SIZE, round(im.height * SIZE / im.width)), Image.Resampling.LANCZOS)
a = np.asarray(im).astype(np.float32); v = a.max(axis=2)
floor = float(np.percentile(np.concatenate([v[:8].ravel(), v[-8:].ravel(), v[:, :8].ravel(), v[:, -8:].ravel()]), 95)) + 4
alpha = np.clip((v - floor) / (255 - floor) * GAIN, 0, 1) ** .85
col = np.clip((a - floor * (1 - alpha[..., None])) / np.maximum(alpha[..., None], .06), 0, 255)
out = Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), 'RGBA')
dst = HERE.parent / '原型' / 'img' / f'{name}.png'; out.save(dst, optimize=True)
print(dst.name, out.size, dst.stat().st_size // 1024, 'KB', 'floor', round(floor))
