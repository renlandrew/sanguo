"""只给衣服换色（11-02 用户：弓手「只染衣服，脸手不变」）：原来游戏里整张图 hue-rotate，脸、手、弓都变蓝。
按色相挑出饱和的黄/土黄（衣服、头巾），换成目标色相、亮度略压；肤色（饱和度低）、棕裤、弓不动。边缘按饱和度软过渡。
有同名 .json（图集）时每帧最下面 22% 不换，免得草鞋也变色。
用法：<media-venv>/bin/python 三国志/工具/recolor_cloth.py <图> <输出> [目标色相°=195] [亮度×=.8]
"""
import sys
import numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]; H2 = float(sys.argv[3]) / 360 if len(sys.argv) > 3 else 195 / 360; VK = float(sys.argv[4]) if len(sys.argv) > 4 else .8
im = Image.open(src).convert('RGBA'); a = np.asarray(im).astype(np.float32) / 255; rgb = a[..., :3]
hsv = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).convert('HSV')).astype(np.float32) / 255
h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
hm = np.clip(1 - np.maximum(0, np.maximum(28 - h, h - 62)) / 6, 0, 1)          # 色相 28–62°（黄、土黄马甲），两头 6° 渐出
sm = np.clip((s - .40) / .15, 0, 1); vm = np.clip((v - .18) / .1, 0, 1)        # 够饱和才算衣服（肤色饱和度低）；太暗的不动
m = hm * sm * vm
import json, os
js = os.path.splitext(src)[0] + '.json'                                          # 草鞋和马甲同色：每帧最下面 22% 不换（脚）
if os.path.exists(js):
    for A in json.load(open(js))['anims'].values():
        for x, y, w, hh in A['rects']: m[y + int(hh * .78):y + hh, x:x + w] = 0
nh = np.full_like(h, H2 * 255); nv = np.clip(v * VK, 0, 1) * 255; ns = np.clip(s * .7, 0, 1) * 255
new = np.asarray(Image.fromarray(np.dstack([nh, ns, nv]).astype(np.uint8), 'HSV').convert('RGB')).astype(np.float32) / 255
res = rgb * (1 - m[..., None]) + new * m[..., None]
Image.fromarray((np.dstack([res, a[..., 3:]]) * 255).round().astype(np.uint8), 'RGBA').save(out, optimize=True)
print(out, '换色像素占比', round(float((m > .5).sum() / max(1, (a[..., 3] > .1).sum())), 3))
