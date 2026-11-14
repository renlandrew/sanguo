"""11-13 讨伐：按招录的动作 → 图集（接 cut_hunt.py 的抠底和排版）。
视频在 美术/讨伐/视频/<键><形态>_m<招>.mp4；没录的那一招（巨灵 m0 震地、蛟 m0 喷水）沿用原来那条 <键><形态>_act.mp4。
出 原型/img/monv_<键><形态>_m<招>.webp，并把 原型/img/monv_<键>.json 改成 [形态][招] 的表，每项带 sheet（图集文件名，不含 monv_ 前缀）。
MARK 是每条的 [蓄力起, 打到, 收完]（图集帧号，24 帧一条），看抽帧定的。
用法：python3 工具/veo/cut_hunt_move.py [键 …]
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; R = HERE.parents[1]; SRC = R / '美术' / '讨伐' / '视频'; OUT = R / '原型' / 'img'
g = {'__file__': str(HERE / 'cut_hunt.py')}; exec((HERE / 'cut_hunt.py').read_text(encoding='utf-8').split('\nfor k in (sys.argv[1:] or MARK):')[0], g); matte = g['matte']
STEP, COLS = 4, 6
SCALES = {'juling': .62, 'shanjun': .8, 'jiao': .9}
OLD = {('juling', 0): '_act', ('jiao', 0): '_act'}      # 这两招用原来那条
MARK = json.loads((HERE / 'hunt_move_mark.json').read_text()) if (HERE / 'hunt_move_mark.json').exists() else {}
DEF = [6, 12, 19]
for k in (sys.argv[1:] or SCALES):
    forms = []
    for n in (1, 2, 3):
        rows3 = []
        for mi in (0, 1, 2):
            suf = OLD.get((k, mi), f'_m{mi}'); src = SRC / f'{k}{n}{suf}.mp4'
            name = f'monv_{k}{n}' if suf == '_act' else f'monv_{k}{n}_m{mi}'
            mark = MARK.get(f'{k}_{mi}', DEF)
            if suf == '_act':   # 原来那条已经切好，读回它的格子信息
                old = json.loads((OUT / f'monv_{k}.json').read_text()); o = old[n - 1] if isinstance(old, list) else old['forms'][n - 1][0]
                rows3.append({**{q: o[q] for q in ('n', 'cols', 'fw', 'fh', 'ax', 'ay', 'h0')}, 'mark': o.get('mark', mark), 'sheet': f'{k}{n}'}); continue
            cap = cv2.VideoCapture(str(src)); fr = []
            while True:
                ok, f = cap.read()
                if not ok: break
                fr.append(f)
            if not fr: print('缺', src.name); continue
            fr = [matte(f) for f in fr[::STEP]]; al = np.max([f[..., 3] for f in fr], axis=0) > 40
            ys, xs = np.where(al); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            a0 = fr[0][..., 3] > 40; y0s, x0s = np.where(a0); foot, top, cx = y0s.max() + 1, y0s.min(), (x0s.min() + x0s.max() + 1) / 2
            S = SCALES[k]; fw, fh = round((x1 - x0) * S), round((y1 - y0) * S); rr = -(-len(fr) // COLS); sheet = Image.new('RGBA', (fw * COLS, fh * rr))
            for j, f in enumerate(fr): sheet.alpha_composite(Image.fromarray(f[y0:y1, x0:x1]).resize((fw, fh), Image.Resampling.LANCZOS), ((j % COLS) * fw, (j // COLS) * fh))
            dst = OUT / f'{name}.webp'; sheet.save(dst, quality=86, method=6)
            rows3.append({'n': len(fr), 'cols': COLS, 'fw': fw, 'fh': fh, 'ax': round((cx - x0) * S, 1), 'ay': round((foot - y0) * S, 1), 'h0': round((foot - top) * S, 1), 'mark': mark, 'sheet': name[5:]})
            print(k, n, 'm' + str(mi), len(fr), '帧', (fw, fh), dst.stat().st_size // 1024, 'KB', rows3[-1]['mark'])
        forms.append(rows3)
    (OUT / f'monv_{k}.json').write_text(json.dumps({'forms': forms}))
