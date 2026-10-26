"""Effekseer 选定特效 → 三国主题的帧动画图集（10-25，用户：「按你推荐的接……可以的话，编辑一下，符合主题」）。
源：三国志/美术/特效/Effekseer选定/*.png（render.html 渲染的黑底序列帧，16 帧 4×4，每帧 256）。
每帧这样改：
  1. 黑底上的光 → 亮度 L（最亮的通道）；透明度从 L 来（同 vfx/cut_paint.py 的「光」）。
  2. 换色：按 L 查人物色阶（关羽青、张飞火、刘备蓝／金），最亮处发白——原样例是粉、彩虹、青，和人物对不上。
  3. 墨晕：光的外形大幅模糊，用墨色淡淡垫一层，不偏移（10-25 第一版往右下偏、浓度 .62，用户看了说「特效像贴图」——偏移的墨像贴纸黑边）。
     亮度靠游戏里压暗背景、再用「变亮」叠一遍，不靠描边。
  4. 个别改形：剑17 原样是平底的半圆光罩、下面还压一块规则椭圆光盘——用一个圆从下面挖掉，只留月牙刀光（不留直边）；
     爆13 的光丝很细很密，先糊开一点（不要密集）；剑17、剑26 中间原来一整块死白，增益、发白阈值调低，留出色阶；
     剑22 原样是一面带平行光条的直边光幕（AGENTS.md 禁用规则光板、平行光条），极坐标弯成一道偃月刀弧，配青龙偃月刀。
输出：三国志/原型/img/fb/<名>.webp（4×4，每帧 SIZE）+ img/fb/fb.json（帧数、列数、帧边长、锚点、画里「朝前」的方向、默认时长）。
用法：<media-venv>/bin/python 三国志/工具/effekseer/theme.py [只重做的名字 …]
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / '美术' / '特效' / 'Effekseer选定'
OUT = HERE.parents[1] / '原型' / 'img' / 'fb'
OUT.mkdir(parents=True, exist_ok=True)
SIZE, COLS = 256, 4
INK = np.array([29, 26, 23], np.float32) / 255
RAMPS = {
    'jade':  ['#08281d', '#0f5a3b', '#23a06a', '#7fe0b0', '#f2fff8'],
    'fire':  ['#2a0805', '#7c180a', '#d2401a', '#ff9a45', '#fff2d6'],
    'azure': ['#08203a', '#16538e', '#3a98e2', '#a6dbff', '#f5fbff'],
    'gold':  ['#2e1d05', '#7d520e', '#d39a2a', '#f7d470', '#fffaea'],
}
def hexrgb(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
def ramp(name, t):
    r = np.stack([hexrgb(h) for h in RAMPS[name]]); x = np.clip(t, 0, 1) * (len(r) - 1); i = np.minimum(len(r) - 2, np.floor(x).astype(int)); f = (x - i)[..., None]
    return r[i] * (1 - f) + r[i + 1] * f
_noise = None
def noise(seed):
    rng = np.random.default_rng(seed); n = ndi.gaussian_filter(rng.random((SIZE, SIZE)), 9, mode='wrap'); return (n - n.min()) / (n.max() - n.min())

def frames(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255
    return [a[(k // COLS) * SIZE:(k // COLS + 1) * SIZE, (k % COLS) * SIZE:(k % COLS + 1) * SIZE] for k in range(16)]

def warp_crescent(f, span=(-168, -12), r0=.13, r1=.47, cy=.8):      # 整道弧收在一帧里，两头不碰帧边（碰了会切出直边）
    """直边光幕 → 偃月弧：源图横向 → 角度，竖向（上沿亮边）→ 半径（外沿）。两头和内沿羽化。"""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32); cx, cyy = SIZE / 2, SIZE * cy
    dx, dy = xx - cx, yy - cyy; r = np.hypot(dx, dy) / SIZE; th = np.degrees(np.arctan2(dy, dx))
    u = (th - span[0]) / (span[1] - span[0])
    thick = (r1 - r0) * np.clip(np.maximum(np.sin(np.pi * np.clip(u, 0, 1)), 0) ** .8 * (.75 + .5 * np.clip(u, 0, 1)), .02, 1)   # 月牙：两头尖、中间偏前最厚（等宽的弧像一道圆环）
    v = (r1 - r) / np.minimum(thick, r1 - r0)
    ok = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    sx = np.clip(u * (SIZE - 1), 0, SIZE - 1); sy = np.clip(v * (SIZE - 1), 0, SIZE - 1)
    out = np.stack([ndi.map_coordinates(f[..., c], [sy, sx], order=1) for c in range(3)], -1)
    feather = np.clip(np.minimum(u, 1 - u) / .06, 0, 1) * np.clip((1 - v) / .3, 0, 1)       # 两头再收一点、内沿虚
    return out * (ok * feather)[..., None]

def theme(f, prof, gain=1.6, hot0=.72, blur=0, ink=.16, seed=1, mask=None, clo=None, top=.85):
    L = np.clip((f.max(axis=2) - .02) / .98, 0, 1)
    if blur: L = ndi.gaussian_filter(L, blur)
    if mask is not None: L = L * mask
    a = np.clip(L * gain, 0, 1) ** 1.1                                                              # 边缘软一点，不是一块剪出来的形
    col = ramp(prof, .15 + .85 * np.clip(L * gain / 1.9, 0, 1) ** .75)
    if clo is not None:                                                                             # 原样亮成一片的（剑17、剑26）：只拿亮部里的明暗变化去查色阶，最顶上也不到白
        luma = f[..., 0] * .3 + f[..., 1] * .55 + f[..., 2] * .15
        if blur: luma = ndi.gaussian_filter(luma, blur)
        L = np.clip((luma - clo) / (1 - clo), 0, 1); col = ramp(prof, .2 + top * L ** .9)
    hot = np.clip((L - hot0) / (1 - hot0), 0, 1)[..., None]; col = col * (1 - hot) + hot                 # 最亮处发白
    ia = np.clip(ndi.gaussian_filter(a, 7) * 1.4, 0, 1) * ink                                        # 淡墨晕，不偏移、不成边
    oa = a + ia * (1 - a)
    rgb = (col * a[..., None] + INK * (ia * (1 - a))[..., None]) / np.maximum(oa, 1e-4)[..., None]
    return np.dstack([rgb, oa])

def carve(cx, cy, r, sy=.85, soft=.04):
    """挖掉一个圆（月牙的内弧）"""
    y, x = np.mgrid[0:SIZE, 0:SIZE] / SIZE; return np.clip((np.hypot(x - cx, (y - cy) / sy) - r) / soft, 0, 1)

def build(name, src, prof, anchor, fwd, dur, warp=False, mask_y=None, mask=None, seed=1, **look):
    fs = frames(SRC / src); outs = []
    for k, f in enumerate(fs):
        if warp: f = warp_crescent(f)
        m = None
        if mask_y:                                                                                     # 按高度淡掉（剑17 的地面光盘）
            y = np.arange(SIZE)[:, None] / SIZE; m = np.clip((mask_y[1] - y) / (mask_y[1] - mask_y[0]), 0, 1) * np.ones((1, SIZE))
        if mask is not None: m = mask if m is None else m * mask
        outs.append(theme(f, prof, seed=seed + k, mask=m, **look))
    atlas = np.zeros((SIZE * 4, SIZE * COLS, 4), np.float32)
    for k, o in enumerate(outs): atlas[(k // COLS) * SIZE:(k // COLS + 1) * SIZE, (k % COLS) * SIZE:(k % COLS + 1) * SIZE] = o
    Image.fromarray((np.clip(atlas, 0, 1) * 255 + .5).astype(np.uint8), 'RGBA').save(OUT / f'{name}.webp', quality=88, method=6)
    return {'n': 16, 'cols': COLS, 'size': SIZE, 'anchor': anchor, 'fwd': fwd, 'dur': dur}

UP, LEFT = -math.pi / 2, math.pi
META = {}
import sys
ONLY = set(sys.argv[1:])
build0 = build
def build(name, *a, **k):
    if ONLY and name not in ONLY: return json.loads((OUT / 'fb.json').read_text())[name]
    return build0(name, *a, **k)
for nm, prof in [('hit_jade', 'jade'), ('hit_fire', 'fire'), ('hit_azure', 'azure'), ('hit_gold', 'gold')]:
    META[nm] = build(nm, '爆13_Blow6.png', prof, [.5, .5], 0, .34, blur=1.3, gain=1.4, hot0=.93); META[nm]['n'] = 9   # 爆13 后半段又爆一次，命中只用头一爆                                    # 命中（爆13），按出手的人上色
META['dao'] = build('dao', '剑17_Sword17.png', 'jade', [.55, .42], UP, .5, mask_y=(.56, .64), mask=carve(.56, .74, .31), gain=1.0, hot0=.96, clo=.5, top=.72)         # 关羽刀气（剑17）：月牙朝前
META['yanyue'] = build('yanyue', '剑22_Sword22.png', 'jade', [.5, .58], UP, .7, warp=True, blur=.8)          # 青龙斩（剑22 弯成偃月）
META['mao'] = build('mao', '枪2_Spear2.png', 'fire', [.48, .37], UP, .32)                          # 张飞矛气（枪2）：锚在矛尖
META['bao'] = build('bao', '剑26_tktk02Sword4.png', 'fire', [.5, .5], 0, .5, gain=1.0, hot0=.95, clo=.45, top=.75)                        # 张飞命中、一喝（剑26）
for nm, prof in [('shuang_azure', 'azure'), ('shuang_gold', 'gold')]:
    META[nm] = build(nm, '剑16_Sword16.png', prof, [.24, .5], LEFT, .5)                             # 双股剑（剑16）：扇形剑光收成交叉，锚在交叉点
for nm, prof in [('jianhen_azure', 'azure'), ('jianhen_gold', 'gold')]:
    META[nm] = build(nm, '剑20_Sword20.png', prof, [.5, .5], 0, .4)                                 # 刘备剑气命中（剑20）
(OUT / 'fb.json').write_text(json.dumps(META, ensure_ascii=False))
for k in META:
    if not ONLY or k in ONLY: print(k, (OUT / f'{k}.webp').stat().st_size // 1024, 'KB')
