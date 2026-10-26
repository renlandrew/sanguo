"""把 原型/守关.html 里的 STORY 表导出成 设计/第一章剧本.md（改了台词后重跑）。用法：python3 三国志/工具/export_script.py"""
import re
from pathlib import Path
R = Path(__file__).resolve().parents[1]
s = (R / '原型' / '守关.html').read_text(encoding='utf-8')
a = s.index('const STORY = {'); b = s.index('};\nconst SPEAK', a); blk = s[a:b]
SP = {'liu': '刘备', 'guan': '关羽', 'zhang': '张飞', 'zhangjiao': '张角', 'zoujing': '邹靖', 'jianyong': '简雍', 'luzhi': '卢植', 'dongzhuo': '董卓', 'caocao': '曹操', 'sunjian': '孙坚', 'huaxiong': '华雄', 'gongsun': '公孙瓒', 'lvbu': '吕布', '': ''}
LV = {int(m.group(1)): m.group(2) for m in re.finditer(r"\{ id: (\d+), name: '([^']+)'", s[s.index('const LEVELS = ['):])}
parts = re.split(r"\n\s+(open|l\d+): \[", '\n' + blk[blk.index('{') + 1:]); it = iter(parts[1:])
out = ['# 第一章 · 群雄逐鹿 · 完整剧本', '', '从游戏 `原型/守关.html` 的 `STORY` 表导出（`工具/export_script.py`）。每关第一次打赢、结算完演一场，画面是这一关的剧情图 `img/story_s<关>.jpg`。',
       '在游戏里翻看：`http://localhost:8766/原型/守关.html?story`（点左边往回、右边往下，底下可跳上一场/下一场），或系统页「翻看剧情」。', '']
n = 0
for key, body in zip(it, it):
    out += [f"## {'序章 · 桃园' if key == 'open' else f'第{int(key[1:])}关 · {LV[int(key[1:])]} 之后'}", '']
    for m in re.finditer(r"\[(?:null|'[^']*'), '(\w*)', (?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|`([^`]*)`)\]", body):
        who = SP[m.group(1)]; t = (m.group(2) or m.group(3) or m.group(4) or '').replace('${ORG}', '上影AI部'); n += 1
        out += [f'**{who}**：{t}' if who else f'*{t}*', '']
(R / '设计' / '第一章剧本.md').write_text('\n'.join(out), encoding='utf-8'); print(n, '句')
