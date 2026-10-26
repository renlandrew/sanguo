"""Effekseer 候选帧图（render.html 传回的横条，每条 6 帧）→ 分组对比图，每个候选一行、带编号（10-25，给用户挑刀气、剑气、矛气和命中）。
用法：<media-venv>/bin/python 三国志/工具/effekseer/sheet.py <帧图目录> <输出目录>
"""
import sys, re, glob, os
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
FONT = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 22); SMALL = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 14)
def key(f):
    m = re.match(r'(\w+?)__(\w+?)(\d*)_(\d+)-(\d+)_', os.path.basename(f)); return m
files = {os.path.basename(f).split('_')[0] + '/' + re.match(r'\w+?__([A-Za-z_]+?\d*)_\d', os.path.basename(f)).group(1): f for f in glob.glob(src + '/*.png')}
GROUPS = [('剑', '剑击（刀气、剑气）', [f't1/Sword{i}' for i in range(1, 23)] + [f't2/Sword{i}' for i in range(1, 7)]),
          ('枪', '枪刺（矛气）', [f't2/Spear{i}' for i in range(1, 5)] + ['ms/Lance3', 'ms/Lance4', 'ms/Lance5']),
          ('爆', '命中冲击', ['ms/Attack1', 'ms/Attack2', 'ms/Attack5', 'ms/Attack6', 'ms/Attack_Impact', 'ms/Impact', 'ms/Wind_Impact'] + [f't1/Blow{i}' for i in range(1, 16)] + [f't2/Blow{i}' for i in range(1, 7)])]
C, LW, COLS = 120, 96, 2
for tag, title, names in GROUPS:
    names = [n for n in names if n in files]; rows = (len(names) + COLS - 1) // COLS
    RW = LW + 6 * C + 24; sheet = Image.new('RGB', (RW * COLS, 56 + rows * (C + 8)), (14, 14, 16)); d = ImageDraw.Draw(sheet)
    d.text((16, 14), f'{title}　共 {len(names)} 个　（Effekseer 官方 CC0 样例，黑底，每行从左到右是一次播放的 6 个时刻）', font=FONT, fill=(235, 225, 200))
    index = []
    for k, n in enumerate(names):
        col, row = k // rows, k % rows; x, y = col * RW, 56 + row * (C + 8)
        strip = Image.open(files[n]).convert('RGB').resize((6 * C, C), Image.Resampling.LANCZOS); sheet.paste(strip, (x + LW, y))
        d.text((x + 10, y + 30), f'{tag}{k + 1}', font=FONT, fill=(255, 210, 120)); d.text((x + 10, y + 64), n.replace('t1/', 'tktk01 ').replace('t2/', 'tktk02 ').replace('ms/', 'MxS '), font=SMALL, fill=(150, 150, 150))
        index.append(f'{tag}{k + 1}\t{n}')
    sheet.save(f'{out}/{tag}_{title.split("（")[0]}.jpg', quality=88); open(f'{out}/{tag}_编号.txt', 'w').write('\n'.join(index) + '\n')
    print(tag, len(names), sheet.size)
