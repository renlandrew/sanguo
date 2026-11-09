"""11-09 英文版：把 table*.py 的中英对照生成 原型/en.js（EN 整句表、EN_RX 带数字的句式）。用法：python3 三国志/工具/英文版/make_en.py"""
import json, re, sys, glob, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent; OUT = HERE.parents[1] / '原型' / 'en.js'
T = {}
for f in sorted(HERE.glob('table*.py')):
    sp = importlib.util.spec_from_file_location(f.stem, f); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); T.update(m.T)
exact, rx = {}, []
NUM = r'([+-]?\d+(?:\.\d+)?)'
for zh, en in T.items():
    if '#' not in zh: exact[zh] = en; continue
    pat = '^' + re.escape(zh).replace('\\#', '#').replace('#', NUM) + '$'
    k = [0]
    def sub(_): k[0] += 1; return '$%d' % k[0]
    rx.append((pat, re.sub('#', sub, en)))
rx.sort(key=lambda r: -len(r[0]))          # 长的先试，免得「伤害 #」吃掉「伤害 #%」
js = ['// 11-09 英文版文字表，由 三国志/工具/英文版/make_en.py 从 table*.py 生成，别手改。只在网址带 ?lang=en 时读。',
      'window.EN = ' + json.dumps(exact, ensure_ascii=False, indent=0) + ';',
      'window.EN_RX = [' + ',\n'.join('[new RegExp(%s), %s]' % (json.dumps(p, ensure_ascii=False), json.dumps(e, ensure_ascii=False)) for p, e in rx) + '];']
js.append((HERE / 'rules.js').read_text(encoding='utf-8'))
OUT.write_text('\n'.join(js) + '\n', encoding='utf-8')
print('写入', OUT, '整句', len(exact), '句式', len(rx))
