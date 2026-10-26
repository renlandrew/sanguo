"""第一章成长与招式推演（10-25，用户：「做过推演吗？」）。
用机器人实测的每关放招、普攻次数（实测_每关放招普攻_20261025.json，按推荐等级、两个种子平均），
逐关推三种玩家（每关首通一星／二星／三星，不重打）手里有什么：等级、自由点、辅助格、新招、战法书、熟练、觉醒；
再看每类新敌人出场时克它的东西到没到，战力比只靠五维时涨了多少（也就是血量还要再乘多少），交融反应会不会变成一直开着。
用法：python3 三国志/工具/推演/growth_sim.py [方案名]   方案在下面 PLANS 里
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.load(open(HERE / '实测_每关放招普攻_20261025.json', encoding='utf-8'))
GENS = ['guan', 'zhang', 'liu']
NAME = {'guan': '关羽', 'zhang': '张飞', 'liu': '刘备'}
BY = {}
for r in M: BY.setdefault(r['lv'], []).append(r)
CAST = {lv: {g: sum(r['cast'].get(g, 0) for r in rs) / len(rs) for g in GENS} for lv, rs in BY.items()}
SEC = {lv: sum(r['t'] for r in rs) / len(rs) for lv, rs in BY.items()}
FIGHT = {lv: [g for g in GENS if CAST[lv][g] > 0] for lv in BY}
GROW = {'guan': [.45, .4, .3, .25, .35], 'zhang': [.4, .35, .15, .1, .15], 'liu': [.3, .2, .25, .35, .25]}   # 统 武 智 政 魅
# 每类敌人第一次出场的关（实测出兵表）和它的难点
NEW = [(3, '远', '弓手停在远处放箭'), (4, '骑', '黄巾骑兵冲得快'), (9, '术', '术士回血加速'), (11, '盾', '西凉兵正面举盾'),
       (12, '快骑', '西凉铁骑'), (16, '远骑', '西凉弓骑边跑边射'), (19, '叫阵', '华雄叫阵'), (20, '护罩', '华雄护罩'),
       (21, '甲', '飞熊军重甲'), (22, '群骑', '并州狼骑成群'), (24, '不死', '打不死的吕布'), (25, '护罩', '李傕护罩'), (27, '民', '百姓')]
BOOKS = {5: '挺枪', 9: '妖风', 10: '太平雷法', 15: '双刀连斩', 20: '骁勇', 25: '劫掠', 29: '陷阵', 30: '飞将'}   # 首通哪关得哪本，下一关起能用

PLANS = {
  # 5.1b + 5.1c 原样（熟练每级要 need_k 次、每级 +6%；自由点每 5 级 5 点；新招从熟练 1 起；刘备觉醒看第 30 关）
  '原方案': dict(free_per5=5, free_eff=.015, prof_need=lambda k: 10 * k, prof_eff=.06, new_start='1', wake_lv=20, wake_story={'guan': 20, 'zhang': 24, 'liu': 30},
              wake_need='base', skill_lv=(10, 16), react_icd=0, mark_sec=3.0, react_mul=1.5),
  # 推演后改的（见设计文档 5.1d）
  '修正方案': dict(free_per5=2, free_eff=.015, prof_need=lambda k: 8 * k, prof_eff=.04, new_start='catch', wake_lv=18, wake_story={'guan': 20, 'zhang': 24, 'liu': 27},
              wake_need='any', skill_lv=(9, 15), react_icd=6.0, mark_sec=3.0, react_mul=1.5),
  # 再改：新招过剧情关就学会（不看等级，星数少的也赶得上）；新招从熟练「最高−2」起、追上之前熟练涨双倍；觉醒看这人所有招一共放了多少次
  '定稿方案': dict(free_per5=2, free_eff=.015, prof_need=lambda k: 8 * k, prof_eff=.04, new_start='catch2', wake_lv=18, wake_story={'guan': 20, 'zhang': 24, 'liu': 27},
              wake_need='casts', wake_casts=380, skill_story={'guan': (11, 19), 'zhang': (10, 18), 'liu': (12, 23)}, react_icd=6.0, mark_sec=3.0, react_mul=1.5),
}

def run(P, stars, swap_at=None):
    """stars：每关首通几星。swap_at：带新招的玩家从学会第二招那关起，多少比例的放招改用新招（0 = 一直用初始招）"""
    need = lambda L: 40 + 20 * L
    gain = lambda i: round((40 + 8 * i) * (.5 + .25 * stars) * 1.5)
    st = {g: dict(lv=1, exp=0, prof={0: 1}, pc={0: 0}, woke=False, slots=0, free=0) for g in GENS}
    rows, books = [], []
    for i in range(1, 31):
        snap = {g: dict(lv=st[g]['lv'], prof=dict(st[g]['prof']), woke=st[g]['woke'], free=st[g]['free']) for g in GENS}
        rows.append((i, snap, list(books)))
        for g in FIGHT[i]:
            s = st[g]; s['exp'] += gain(i)
            while s['exp'] >= need(s['lv']): s['exp'] -= need(s['lv']); s['lv'] += 1
            s['free'] = P['free_per5'] * (s['lv'] // 5)
            # 学新招
            gates = P.get('skill_story', {}).get(g)
            for n, L in enumerate(P.get('skill_lv', (99, 99)), 1):
                learn = (i >= gates[n - 1]) if gates else s['lv'] >= L
                if learn and n not in s['prof']:
                    base = max(s['prof'].values())
                    s['prof'][n] = 1 if P['new_start'] == '1' else max(1, base - 2); s['pc'][n] = 0
            # 熟练：这关放的招按比例分给各招
            c = CAST[i][g]; share = {0: 1.0}
            if swap_at is not None and len(s['prof']) > 1: newest = max(s['prof']); share = {0: 1 - swap_at, newest: swap_at}
            s['casts'] = s.get('casts', 0) + c
            for k, f in share.items():
                s['pc'][k] += c * f * (2 if P['new_start'] == 'catch2' and k and s['prof'][k] < max(s['prof'].values()) else 1)
                while s['prof'][k] < 10 and s['pc'][k] >= P['prof_need'](s['prof'][k]): s['pc'][k] -= P['prof_need'](s['prof'][k]); s['prof'][k] += 1
            ok_prof = s['prof'][0] >= 10 if P['wake_need'] == 'base' else s.get('casts', 0) >= P.get('wake_casts', 0) if P['wake_need'] == 'casts' else max(s['prof'].values()) >= 10
            if not s['woke'] and s['lv'] >= P['wake_lv'] and ok_prof and i >= P['wake_story'][g]: s['woke'] = True
        if i in BOOKS: books.append(BOOKS[i])
    return rows

def report(name):
    P = PLANS[name]; out = [f'## {name}\n']
    for stars in (1, 2, 3):
        rows = run(P, stars)
        out.append(f'### 每关首通 {stars} 星、只用初始招\n')
        out.append('| 关 | 关羽 级/熟练 | 张飞 级/熟练 | 刘备 级/熟练 | 自由点 | 辅助格 | 新招 | 觉醒 | 战法书 |')
        out.append('|---|---|---|---|---|---|---|---|---|')
        for i, snap, books in rows:
            if i not in (1, 5, 8, 11, 12, 16, 20, 22, 24, 27, 30): continue
            cell = lambda g: f"{snap[g]['lv']}/{snap[g]['prof'][0]}"
            slots = '/'.join(str((snap[g]['lv'] >= 5) + snap[g]['woke']) for g in GENS)
            newk = '/'.join(str(len(snap[g]['prof']) - 1) for g in GENS)
            woke = ''.join(NAME[g][0] for g in GENS if snap[g]['woke']) or '-'
            out.append(f"| {i} | {cell('guan')} | {cell('zhang')} | {cell('liu')} | {snap['guan']['free']} | {slots} | {newk} | {woke} | {len(books)} |")
        out.append('')
    # 克制到位：按二星路线
    rows = {i: (snap, books) for i, snap, books in run(P, 2)}
    rows1 = {i: (snap, books) for i, snap, books in run(P, 1)}
    L1, L2 = P.get('skill_lv', (99, 99))
    def has(i, g, what, R):
        snap, books = R[i]; s = snap[g]
        gates = P.get('skill_story', {}).get(g)
        if what == 'skill2': return i > gates[0] if gates else s['lv'] >= L1
        if what == 'skill3': return i > gates[1] if gates else s['lv'] >= L2
        if what == 'tier5': return s['prof'][0] >= 5
        if what == 'aux': return s['lv'] >= 5
    CNT = [('远', [('zhang', 'skill2', '火龙突'), ('liu', 'skill2', '追魂飞剑')]), ('快骑', [('guan', 'skill2', '青龙出海'), ('zhang', 'tier5', '怒雷')]),
           ('术', [('liu', 'tier5', '剑印')]), ('盾', [('guan', 'tier5', '龙鳞破甲')]), ('远骑', [('liu', 'skill2', '追魂飞剑'), ('zhang', 'skill2', '火龙突')]),
           ('护罩', [('guan', 'skill3', '温酒斩')]), ('甲', [('guan', 'tier5', '龙鳞破甲')]), ('群骑', [('zhang', 'skill3', '怒发冲冠'), ('guan', 'skill2', '青龙出海')]),
           ('不死', [('liu', 'skill3', '仁德金光')]), ('民', [('liu', 'skill3', '仁德金光')])]
    out.append('### 新敌人出场时，克它的招到没到（二星路线 / 一星路线）\n')
    out.append('| 关 | 难点 | 克它的招 | 二星 | 一星 |'); out.append('|---|---|---|---|---|')
    done = set()
    for i, tag, desc in NEW:
        for t, lst in CNT:
            if t != tag or (i, t) in done: continue
            done.add((i, t))
            for g, w, nm in lst:
                a, b = has(i, g, w, rows), has(i, g, w, rows1)
                out.append(f"| {i} | {desc} | {NAME[g]}{nm} | {'到了' if a else '**没到**'} | {'到了' if b else '**没到**'} |")
    out.append('')
    # 战力：比只靠五维时多出来的（熟练 + 自由点），二星路线、关羽为例；招式伤害占大头
    out.append('### 战力比「只靠五维」多出来多少（二星路线；招式伤害 × 普攻伤害各按实测占比加权，关羽招式约占他伤害的九成）\n')
    out.append('| 关 | 熟练加成 | 自由点全加统率 | 合计（血量还要再乘） |'); out.append('|---|---|---|---|')
    for i in (8, 12, 16, 20, 24, 28, 30):
        snap, _ = rows[i]; s = snap['guan']; prof = (1 + P['prof_eff'] * (s['prof'][0] - 1)); free = 1 + P['free_eff'] * s['free']
        out.append(f"| {i} | ×{prof:.2f} | ×{free:.2f} | ×{prof * free:.2f} |")
    out.append('')
    # 交融：放招间隔（实测）和印的时长 → 一招打到带别人印的敌人的比例
    gap = sum(SEC[i] / max(1, sum(CAST[i].values())) for i in range(1, 31)) / 30
    icd = P['react_icd']; per_enemy = 1.0 if icd == 0 else min(1.0, P['mark_sec'] / icd)
    up = min(1.0, P['mark_sec'] / (gap * 1)) * per_enemy
    out.append(f'### 交融会不会一直开着\n\n实测三人合起来平均每 {gap:.1f} 秒放一招，印留 {P["mark_sec"]:.0f} 秒，出手顺序又是三人轮流——'
               f'{"不设冷却时，几乎每一招都打在别人刚留的印上，反应等于常驻（伤害约 ×" + str(P["react_mul"]) + "）" if icd == 0 else f"同一个敌人 {icd:.0f} 秒内只起一次反应，约 {per_enemy:.0%} 的招能起反应"}。\n')
    # 新招一学会时和初始招差多少（只看熟练）
    snap, _ = rows[16]; out.append('### 新招刚学会时比初始招弱多少（只看熟练，二星路线）\n')
    for g in GENS:
        s = run(P, 2)[15][1][g]   # 第 16 关开打时
        if len(s['prof']) > 1: b, n = s['prof'][0], s['prof'][max(s['prof'])]; out.append(f"- {NAME[g]}：初始招熟练 {b}，最新的招 {n}，弱 {((1 + P['prof_eff'] * (b - 1)) / (1 + P['prof_eff'] * (n - 1)) - 1):.0%}")
    out.append('')
    # 换新招以后觉醒会不会卡住
    rows_sw = run(P, 2, swap_at=.6)
    woke = {g: next((i for i, snap, _ in rows_sw if snap[g]['woke']), None) for g in GENS}
    out.append('### 学会新招后六成时间用新招，觉醒在第几关\n')
    out.append('、'.join(f"{NAME[g]} {('第 ' + str(w) + ' 关后') if w else '第一章内觉醒不了'}" for g, w in woke.items()) + '\n')
    return '\n'.join(out)

if __name__ == '__main__':
    names = sys.argv[1:] or list(PLANS)
    print('\n\n'.join(report(n) for n in names))
