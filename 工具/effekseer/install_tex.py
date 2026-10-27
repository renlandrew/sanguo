"""GPT 画的特效贴图（纯黑底白光）→ 替换 Effekseer 样例里的同名贴图（10-27 首领法术改用 Effekseer + GPT 贴图）。
按原贴图的尺寸和格式输出：原图带透明的，出白色 + 透明度＝亮度；原图不带透明的（叠加混合），出灰度 RGB。
亮度先减掉黑底底噪，再整体拉到最亮处为白，这样贴图外面是真的黑／真的透明，渲染出来没有灰雾方框。
用法：python3 install_tex.py <GPT 图> <要替换的贴图路径> [...更多替换路径]
"""
import sys
import numpy as np
from PIL import Image

src = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
v = src.max(axis=2)
floor = float(np.percentile(v, 35)) + 6                                      # 黑底占大半，取三分之一分位当底噪
v = np.clip((v - floor) / max(1.0, float(np.percentile(v, 99.7)) - floor), 0, 1)
for dst in sys.argv[2:]:
    old = Image.open(dst); size = old.size; alpha = old.mode in ('RGBA', 'LA') or (old.mode == 'P' and 'transparency' in old.info)
    L = Image.fromarray((v * 255).astype(np.uint8), 'L').resize(size, Image.Resampling.LANCZOS)
    if alpha: out = Image.merge('RGBA', (Image.new('L', size, 255),) * 3 + (L,))
    else: out = Image.merge('RGB', (L, L, L))
    out.save(dst); print(dst, size, 'RGBA' if alpha else 'RGB')
