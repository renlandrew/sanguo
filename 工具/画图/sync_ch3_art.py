# -*- coding: utf-8 -*-
"""11-18 第三章：按 原型/img 里已经装好的图，改 守关.html 里两处清单——
  STORY_S3（哪些关的剧情图画好了，开篇 c3 也算），MAP_ALIAS 里第三章借图的底图（画好的就不再借）。重跑安全。
用法：python3 工具/画图/sync_ch3_art.py
"""
import re
from pathlib import Path
R = Path(__file__).resolve().parents[2]; P = R / '原型' / '守关.html'; IMG = R / '原型' / 'img'
s = P.read_text(encoding='utf-8')
ids = sorted(int(p.stem[7:]) for p in IMG.glob('story_s*.jpg') if p.stem[7:].isdigit() and int(p.stem[7:]) > 60)
s, n1 = re.subn(r"const STORY_S3 = new Set\(\[[^\]]*\]\);", f"const STORY_S3 = new Set([{', '.join(map(str, ids))}]);", s)
m = re.search(r"(/\* 11-18 第三章底图没画前先借 \*/ )([^}]*)\}", s)
pairs = [x.strip() for x in m.group(2).split(',') if x.strip()]
keep = [x for x in pairs if not (IMG / f"bg_{x.split(':')[0].strip()}.jpg").exists()]
s = s[:m.start(2)] + ', '.join(keep) + (' ' if keep else '') + s[m.end(2):]
s, n2 = re.subn(r"(for \(const \[key, L\] of Object.entries\(STORY\)\) \{ let cur)", r"\1", s)
P.write_text(s, encoding='utf-8')
print('剧情图', ids, '；还在借的底图', keep)
