"""特效 Veo 录像（黑底）→ 原型用的透明逐帧图集（10-25，make_vfx_pack.py 录的）。

输入：<帧图目录>/fx<序号>_<键>.jpg，每张是一条视频按 PLAN 里的帧数截出来的网格（列数、格子大小见 GRID），在浏览器里从 Cloud Storage 的视频截出来。
做法：黑底按亮度转透明——每帧先减掉底噪（四边像素里亮度的 90 分位），亮度 v 映成透明度 a（软阈值，亮芯全不透明、暗的光晕半透明），
      颜色除以 a 还原（这样贴在浅色背景上也是原来的颜色，不会发灰）；整段取一个共同外框，缩到长边 SIZE，打成图集。
输出：原型/img/fx_<键>.png + .json（同敌人图集的格式：anims.play 的 rects，anchor 记中心或底边中点，loop 表示飞行时循环播）。
用法：<media-venv>/bin/python 三国志/工具/veo/cut_vfx.py <帧图目录> [键 ...]
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]); OUT = HERE.parents[1] / '原型' / 'img'
GRID = {'cols': 8, 'rows': 5}                      # 截图网格：8 列 5 行 40 帧（0.2–3.45 秒，每秒 12 帧）
# 每个键：取哪几帧、长边缩到多少像素、锚点（center 中心 / bottom 底边中点）、是否循环（飞行的）
PLAN = {
    'blade':    {'frames': list(range(14, 30)), 'size': 192, 'anchor': 'center', 'loop': True},
    'bladehit': {'frames': list(range(0, 24)), 'size': 192, 'anchor': 'center', 'loop': False},
    'dragon':   {'frames': list(range(0, 40)), 'size': 384, 'anchor': 'center', 'loop': False},
    'spear':    {'frames': list(range(0, 24)), 'size': 256, 'anchor': 'bottom', 'loop': False},
    'roar':     {'frames': list(range(0, 40)), 'size': 384, 'anchor': 'bottom', 'loop': False},
    'twinqi':   {'frames': list(range(14, 30)), 'size': 160, 'anchor': 'center', 'loop': True},
    'flysword': {'frames': list(range(14, 30)), 'size': 192, 'anchor': 'center', 'loop': True},
    'cross':    {'frames': list(range(0, 24)), 'size': 192, 'anchor': 'center', 'loop': False},
    # 10-27 敌方首领重招（make_bossfx_pack.py）：一次性，长边 384，整段 40 帧取前 32
    **{k: {'frames': list(range(0, 32)), 'size': 384, 'anchor': 'center', 'loop': False} for k in ('boss_dengmao', 'boss_zhangjiao', 'boss_huzhen', 'boss_huaxiong', 'boss_lijue', 'boss_lvbu')},
    'boss_lijue': {'frames': list(range(0, 20)), 'size': 384, 'anchor': 'center', 'loop': False},
    # 10-27 魔兽风法术第二批（make_spellfx_pack.py）
    'sp_sigil_purple': {'frames': list(range(4, 36)), 'size': 320, 'anchor': 'center', 'loop': False},
    'sp_arcs': {'frames': list(range(0, 32)), 'size': 256, 'anchor': 'center', 'loop': False},
    'sp_face': {'frames': list(range(0, 32)), 'size': 320, 'anchor': 'center', 'loop': False},
    'sp_dome': {'frames': list(range(2, 34)), 'size': 384, 'anchor': 'bottom', 'loop': False},
    'sp_spears': {'frames': list(range(0, 32)), 'size': 384, 'anchor': 'bottom', 'loop': False},
    'sp_sigil_gold': {'frames': list(range(2, 34)), 'size': 320, 'anchor': 'center', 'loop': False},   # 后半段月牙合成整圈（不要完整圆环），只取前 20 帧
}

def cells(path):
    sheet = np.asarray(Image.open(path).convert('RGB')).astype(np.float32); ch, cw = sheet.shape[0] // GRID['rows'], sheet.shape[1] // GRID['cols']
    return [sheet[(i // GRID['cols']) * ch:(i // GRID['cols'] + 1) * ch, (i % GRID['cols']) * cw:(i % GRID['cols'] + 1) * cw] for i in range(GRID['cols'] * GRID['rows'])]

def unblack(rgb):
    v = rgb.max(axis=2)
    edge = np.concatenate([v[:4].ravel(), v[-4:].ravel(), v[:, :4].ravel(), v[:, -4:].ravel()])
    floor = min(60.0, float(np.percentile(edge, 90)) + 4)                          # 底噪：四边的亮度，压缩出来的黑不是纯黑
    x = np.clip((v - floor) / (255 - floor), 0, 1)
    a = np.clip(x * 1.8, 0, 1) ** .9                                               # 软阈值：亮芯全不透明，暗的光晕半透明
    a = ndi.gaussian_filter(a, .5)
    col = np.clip((rgb - floor * (1 - x[..., None])) / np.maximum(a[..., None], .08), 0, 255)   # 颜色还原
    return np.dstack([col, a * 255]).astype(np.uint8)

for key in (sys.argv[2:] or list(PLAN)):
    srcs = list(SRC.glob(f'fx[0-9]_{key}.jpg'))
    if not srcs: print(key, '没有帧图，跳过'); continue
    P = PLAN[key]; cs = cells(srcs[0])
    frames = [unblack(cs[i]) for i in P['frames']]
    al = np.stack([f[..., 3] > 18 for f in frames]); ys, xs = np.where(al.any(axis=0))
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    if P['anchor'] == 'center':                                                    # 中心锚点：外框按画面中心对称，飞行时转起来不偏
        cy, cx = frames[0].shape[0] / 2, frames[0].shape[1] / 2
        hy, hx = max(cy - y0, y1 - cy), max(cx - x0, x1 - cx); y0, y1, x0, x1 = int(cy - hy), int(cy + hy), int(cx - hx), int(cx + hx)
    h, w = y1 - y0, x1 - x0; k = P['size'] / max(h, w); W, H = max(1, round(w * k)), max(1, round(h * k))
    PER = 8; AW = W * min(PER, len(frames)); AH = H * -(-len(frames) // PER)
    atlas = Image.new('RGBA', (AW, AH)); rects = []
    for j, f in enumerate(frames):
        pad = np.zeros((h, w, 4), np.uint8); sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(f.shape[0], y1), min(f.shape[1], x1)
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = f[sy0:sy1, sx0:sx1]
        im = Image.fromarray(pad, 'RGBA').resize((W, H), Image.Resampling.LANCZOS)
        x, y = (j % PER) * W, (j // PER) * H; atlas.paste(im, (x, y)); rects.append([x, y, W, H])
    anchor = [W / 2, H / 2] if P['anchor'] == 'center' else [W / 2, H]
    meta = {'stand': max(W, H), 'loop': P['loop'], 'anims': {'play': {'rects': rects, 'anchor': anchor}}}
    atlas.save(OUT / f'fx_{key}.png', optimize=True); (OUT / f'fx_{key}.json').write_text(json.dumps(meta))
    print(key, len(frames), '帧', f'{W}x{H}', '图集', atlas.size, (OUT / f'fx_{key}.png').stat().st_size // 1024, 'KB')
