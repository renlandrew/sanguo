"""11-18 用户：「所有字体也要用宋体，思源宋体 Heavy」。手机上没有这款字，整套 2400 万字节太大，
只留游戏里用到的字（守关.html + en.js 里出现过的全部非 ASCII 字 + ASCII + 常用符号），裁成 原型/font/shs_heavy.woff2。
加了新文字后重跑一次：python3 工具/字体/subset_font.py
源字体：本机 ~/Library/Fonts/SourceHanSerifSC-Heavy.otf（Adobe 开源 OFL）。要 fontTools + brotli。
"""
from pathlib import Path
import subprocess, sys
R = Path(__file__).resolve().parents[2]
SRC = Path.home() / 'Library/Fonts/SourceHanSerifSC-Heavy.otf'
txt = (R / '原型/守关.html').read_text(encoding='utf-8') + (R / '原型/en.js').read_text(encoding='utf-8')
chars = {c for c in txt if ord(c) > 0x7f and not 0xD800 <= ord(c) <= 0xDFFF}
chars |= {chr(i) for i in range(0x20, 0x7f)}
chars |= set('★☆·「」『』…—–、。，！？：；（）《》〈〉“”‘’％＋－×÷①②③④⑤⑥⑦⑧⑨⑩〇零一二三四五六七八九十百千万廿卅')
tmp = R / '工具/字体/_chars.txt'; tmp.write_text(''.join(sorted(chars)), encoding='utf-8')
out = R / '原型/font/shs_heavy.woff2'; out.parent.mkdir(exist_ok=True)
subprocess.run([sys.executable, '-m', 'fontTools.subset', str(SRC), f'--text-file={tmp}', '--flavor=woff2', "--layout-features=*", f'--output-file={out}'], check=True)
tmp.unlink()
print(len(chars), '字 →', out.name, out.stat().st_size // 1024, 'KB')
