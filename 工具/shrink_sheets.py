"""把图集按游戏里实际显示的大小缩好（10-30 用户：「还是会玩着玩着就自动刷新页面」——手机 Chrome/Safari 内存不够把页面杀了）。
原来游戏里先解码整张大原图、再按显示大小另画一份缩小的，两份都在内存里；现在文件本身就是显示大小，游戏直接用。
- 兵种、敌将图集（含 _back）：目标站高 = 守关.html FOES 里用到这张图的最大 sh × 3.2（同 SHEET_PX）
- 敌将华彩 fx_boss_*：× FX_BOSS；刘关张大招特写 ult_guan/zhang/liu：× ULT
json 里的 stand、rects、anchor（ult 的 w、h）跟着缩。已经缩过的（比目标大不到 3%）跳过，重切图集后再跑一遍即可。
用法：<media-venv>/bin/python 三国志/工具/shrink_sheets.py [--dry]
"""
import json, re, sys
from pathlib import Path
from PIL import Image
IMG = Path(__file__).resolve().parents[1] / '原型' / 'img'; HTML = IMG.parent / '守关.html'
FX_BOSS, ULT = .7, .75
DRY = '--dry' in sys.argv
src = HTML.read_text(encoding='utf-8'); body = src[src.index('const FOES = {'):]; body = body[:body.index('\n};')]
px = {}
for line in body.splitlines():
    sh = re.search(r'\bsh: *([\d.]+)', line)
    if not sh: continue
    sheet = re.search(r"\bsheet: *'(\w+)'", line); alt = re.search(r"\balt: *'(\w+)'", line)
    for k in filter(None, [sheet and sheet[1], alt and alt[1], sheet and sheet[1] + '_back']):
        px[k] = max(px.get(k, 0), float(sh[1]) * 3.2)

def image_of(k):
    for ext in ('webp', 'png'):
        if (IMG / f'{k}.{ext}').exists(): return IMG / f'{k}.{ext}'

def scale_file(k, s, fix, size=None):
    im_p, js_p = image_of(k), IMG / f'{k}.json'
    if not im_p or not js_p.exists() or s > .97: return 0
    im = Image.open(im_p); w, h = im.size; nw, nh = size(w, h, s) if size else (round(w * s), round(h * s))
    before = w * h * 4 / 1e6; print(f'{k:16} ×{s:.2f}  {w}×{h} → {nw}×{nh}  {before:.0f} → {nw * nh * 4 / 1e6:.0f} MB')
    if DRY: return before - nw * nh * 4 / 1e6
    j = json.loads(js_p.read_text()); fix(j, s)
    im = im.convert('RGBA').resize((nw, nh), Image.LANCZOS)
    if im_p.suffix == '.webp': im.save(im_p, 'WEBP', quality=88, method=6)
    else: im.save(im_p, optimize=True)
    js_p.write_text(json.dumps(j, separators=(', ', ': ')))
    return before - nw * nh * 4 / 1e6

def fix_sheet(j, s):
    j['stand'] = round(j['stand'] * s, 2)
    for a in j['anims'].values():
        a['rects'] = [[round(x * s), round(y * s), round((x + w) * s) - round(x * s), round((y + h) * s) - round(y * s)] for x, y, w, h in a['rects']]   # 按格线取整，相邻两格不重叠不漏缝
        if 'anchor' in a: a['anchor'] = [round(v * s, 1) for v in a['anchor']]

def fix_ult(j, s):
    j['w'] = round(j['w'] * s); j['h'] = round(j['h'] * s)

saved = 0
for k, p in sorted(px.items()):
    js_p = IMG / f'{k}.json'
    if js_p.exists(): saved += scale_file(k, max(.3, p / json.loads(js_p.read_text())['stand']), fix_sheet)
for p in sorted(IMG.glob('fx_boss_*.json')):
    j = json.loads(p.read_text()); s = FX_BOSS * j.get('full', j['stand']) / j['stand']
    j0 = j
    def fix_boss(j, s): fix_sheet(j, s); j['full'] = j0.get('full', j0['stand'])
    saved += scale_file(p.stem, s, fix_boss)
for k in ('guan', 'zhang', 'liu'):
    p = IMG / f'ult_{k}.json'; j = json.loads(p.read_text()); s = ULT * j.get('full', j['h']) / j['h']
    def fix_u(jj, s, full=j.get('full', j['h'])): fix_ult(jj, s); jj['full'] = full
    cols, rows = j['cols'], -(-j['n'] // j['cols'])
    saved += scale_file(f'ult_{k}', s, fix_u, lambda w, h, s, j=j, c=cols: (round(j['w'] * s) * c, round(h * s)) if h != j['h'] * rows else (round(j['w'] * s) * c, round(j['h'] * s) * rows))   # 格子取整后正好铺满
print(f'省 {saved:.0f} MB（解码后）')
