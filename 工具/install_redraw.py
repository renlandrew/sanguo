"""10-26 全部重画（用户：「我感觉你要全部重新画一次，大片色块要统一风格。人物背影就将就吧，城墙要画」）：
把收图站收到的 N_<键>.jpg（ChatGPT 重画的）按类处理进游戏，原图存 美术/重画/，旧的游戏图备份到 美术/重画/旧/。
  wall → make_scene wall；bg* → make_scene bg；story_guan/liu/zhang/zhangjiao、pt_* → matte_portrait（抠成透明立绘）；
  item_* → matte_ui；story_s*、story_oath 等剧情图、room_*、map_* → 缩成 720 宽 jpg；wpn_* → matte_weapons 五把；trio → 原样（主页整张铺）。
用法：<media-venv>/bin/python 三国志/工具/install_redraw.py <收图目录> [键 …]（不给键就处理目录里全部 N_*.jpg）
"""
import os, shutil, subprocess, sys
from pathlib import Path
from PIL import Image
R = Path(__file__).resolve().parents[1]; IMG = R / '原型' / 'img'; ART = R / '美术' / '重画'; OLD = ART / '旧'
ART.mkdir(parents=True, exist_ok=True); OLD.mkdir(exist_ok=True)
PY = sys.executable; T = R / '工具'; os.environ.setdefault('ERODE', '1')                  # 立绘边缘收 1 像素去白边
src = Path(sys.argv[1]); keys = sys.argv[2:] or sorted(p.stem[2:] for p in src.glob('N_*.jpg'))

def backup(name):
    for p in IMG.glob(name + '.*'):
        if not (OLD / p.name).exists(): shutil.copy2(p, OLD / p.name)

def run(*a): print(subprocess.run([PY, *map(str, a)], capture_output=True, text=True).stdout.strip().splitlines()[-1:])

def jpg720(p, name):
    im = Image.open(p).convert('RGB'); im.resize((720, round(720 * im.height / im.width)), Image.Resampling.LANCZOS).save(IMG / f'{name}.jpg', quality=85, optimize=True)

for k in keys:
    p = src / f'N_{k}.jpg'
    if not p.exists(): print('没有', k); continue
    dst = ART / f'{k}.jpg'; shutil.move(str(p), dst); print('==', k)
    if k == 'wall': backup('wall'); run(T / 'make_scene.py', 'wall', dst, IMG / 'wall.png')
    elif k.startswith('bg'): backup(k); run(T / 'make_scene.py', 'bg', dst, IMG / f'{k}.jpg')
    elif k.startswith('pt_') or k in ('story_guan', 'story_liu', 'story_zhang', 'story_zhangjiao'):
        name = k[3:] if k.startswith('pt_') else k; backup(k)
        run(T / 'matte_portrait.py', dst, name)
        if not k.startswith('pt_'): shutil.move(IMG / f'pt_{name}.png', IMG / f'{k}.png')
    elif k.startswith('item_'): backup(k); run(T / 'matte_ui.py', dst, 160, k)
    elif k.startswith('wpn_'):
        for i in range(1, 6): backup(f'{k}{i}')
        run(T / 'matte_weapons.py', dst, k, 640, 5)
    elif k == 'trio': backup('trio'); Image.open(dst).convert('RGB').save(IMG / 'trio.jpg', quality=88)
    else: backup(k); jpg720(dst, k)
