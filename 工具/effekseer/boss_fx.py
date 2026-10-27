"""首领法术：Effekseer 渲染的序列帧（GPT 贴图）→ 游戏里 fx_boss_<键>.webp/.json（10-27，替换 Veo 录像）。
Veo 黑底录像抠出来带一层灰雾，叠到场景上成一块发亮的长方形（用户：「不行，有明显的正方形」）；Effekseer 是纯黑底，黑的地方透明度就是 0。
每帧：亮度 L＝最亮的通道 → 透明度（软阈值）；颜色按首领的色阶（暗→主色→亮色→白）重新上，Effekseer 样例原来的粉、紫、彩虹都换掉。
整段取一个共同外框，缩到长边 SIZE，8 列打成图集，格式同 cut_vfx.py（drawBossVfx 每秒 20 帧播）。
用法：<media-venv>/bin/python 三国志/工具/effekseer/boss_fx.py <render.html 出的序列帧 png> <首领键> [帧数 N=24] [列数 COLS=8]
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent; OUT = HERE.parents[1] / '原型' / 'img'
SIZE = 768                                                                     # 10-27 用户：「这好像很模糊」——手机上一帧要拉到一千多像素，512 太小
RAMPS = {                                                                      # 暗 → 主色 → 亮色 → 白，和 BOSS_FX 的 col / glow 一致
    'dengmao':   ['#3a2006', '#a8640e', '#e0a23a', '#ffd27a', '#fff6e0'],
    'zhangjiao': ['#1e0838', '#6a2cc0', '#b46cff', '#f4d36a', '#fffbe8'],
    'huzhen':    ['#3a0806', '#9a1c14', '#d8403a', '#ff9a6a', '#fff0e4'],
    'huaxiong':  ['#2a0a04', '#9a2c0c', '#e0601a', '#ffb04a', '#fff4dc'],
    'lijue':     ['#2c1806', '#7c4a14', '#c88a3a', '#ffcf7a', '#fff8e8'],
    'lvbu':      ['#3a0410', '#a4142c', '#e0304a', '#ff8a5a', '#fff0e8'],
}

GAIN = {'huaxiong': .45, 'lvbu': .8, 'dengmao': 1.25, 'lijue': .5, 'zhangjiao': 1.3}                         # 亮度倍数：火墙一整排叠起来会冲成一块白，压一压；邓茂的太淡，提一点

HALO = {'zhangjiao': 1.4}                                                      # 透明度的次方：越大外圈光晕越淡（10-27 用户：张角「其他都清晰，就这个模糊」——紫色光晕太厚）

def ramp(name, L):
    cs = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in RAMPS[name]], np.float32)
    x = np.clip(L, 0, 1) * (len(cs) - 1); i = np.minimum(x.astype(int), len(cs) - 2); f = (x - i)[..., None]
    return cs[i] * (1 - f) + cs[i + 1] * f

src, key = Path(sys.argv[1]), sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 24; COLS = int(sys.argv[4]) if len(sys.argv) > 4 else 8
sheet = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
cw = sheet.shape[1] // COLS; ch = cw; frames = []
for k in range(N):
    c = sheet[(k // COLS) * ch:(k // COLS + 1) * ch, (k % COLS) * cw:(k % COLS + 1) * cw]
    L = c.max(axis=2); L = np.clip((L - .03) / .97 * GAIN.get(key, 1), 0, 1)                         # Effekseer 的黑是真黑，只去一点点压缩噪声
    a = np.clip(L * 1.6, 0, 1) ** HALO.get(key, .85); a = ndi.gaussian_filter(a, .3)
    rgb = ramp(key, L ** .8)
    frames.append(np.dstack([rgb, a * 255]).astype(np.uint8))
al = np.stack([f[..., 3] > 10 for f in frames]); ys, xs = np.where(al.any(axis=0))
cy, cx = ch / 2, cw / 2; hy, hx = max(cy - ys.min(), ys.max() + 1 - cy), max(cx - xs.min(), xs.max() + 1 - cx)   # 外框按中心对称，锚点在中心
y0, y1, x0, x1 = int(cy - hy), int(cy + hy), int(cx - hx), int(cx + hx)
h, w = y1 - y0, x1 - x0; k = SIZE / max(h, w); W, H = max(1, round(w * k)), max(1, round(h * k))
atlas = Image.new('RGBA', (W * min(COLS, N), H * -(-N // COLS))); rects = []
for j, f in enumerate(frames):
    im = Image.fromarray(f[max(0, y0):y1, max(0, x0):x1], 'RGBA').resize((W, H), Image.Resampling.LANCZOS)
    x, y = (j % COLS) * W, (j // COLS) * H; atlas.paste(im, (x, y)); rects.append([x, y, W, H])
meta = {'stand': max(W, H), 'loop': False, 'src': 'effekseer', 'anims': {'play': {'rects': rects, 'anchor': [W / 2, H / 2]}}}
atlas.save(OUT / f'fx_boss_{key}.webp', quality=88, method=6); (OUT / f'fx_boss_{key}.json').write_text(json.dumps(meta))
print(key, N, '帧', f'{W}x{H}', '图集', atlas.size, (OUT / f'fx_boss_{key}.webp').stat().st_size // 1024, 'KB')
