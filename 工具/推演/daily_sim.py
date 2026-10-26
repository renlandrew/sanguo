"""物品掉落、每日点卯和军务的节奏推演（10-25，用户：「还要考虑物品掉落，每日登录，这些物品都是增强的必要，也就是说，你至少一天要登录，完成一些任务」）。
按天推几种玩家（每天玩多久、哪几天上线不同）打第一章 30 关：每天点卯、做军务、打新关、剩下的时间重打刷材料；
材料每天有上限，漏掉的天补给最多存 SAVE 天。关卡有「破题门槛」（没有对症的东西打不过，见设计文档 5.6），看每种玩家第几天过哪道门、第几天打完第一章。
每关用时取机器人实测（实测_每关放招普攻_20261025.json 的 t，游戏秒）＋1 分钟出阵、结算。
用法：python3 三国志/工具/推演/daily_sim.py [方案名]
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.load(open(HERE / '实测_每关放招普攻_20261025.json', encoding='utf-8'))
SEC = {}
for r in M: SEC.setdefault(r['lv'], []).append(r['t'])
MIN = {lv: sum(ts) / len(ts) / 60 + 1 for lv, ts in SEC.items()}            # 每关几分钟（含出阵、结算）
# 10-25 夜晋升减到每关 3–5 次、血量重调后的每关秒数（第一章设定.md 5.5，会搭配 6 种子），给新方案用
SEC2 = [118, 188, 182, 196, 71, 160, 104, 316, 214, 169, 95, 159, 153, 148, 83, 144, 117, 159, 163, 46, 165, 192, 154, 95, 211, 124, 166, 169, 191, 56]
MIN2 = {i + 1: t / 60 + 1 for i, t in enumerate(SEC2)}

# 破题门槛：打第 lv 关之前手里要有什么（买得起就马上买）；每个方案一套
GATES_V1 = [
    (11, '破盾', {'残页': 6}, '关羽青龙斩二阶「龙鳞破甲」'),
    (20, '破罩', {'精铁': 12}, '兵器精炼到 +2（温酒斩第 19 关剧情给）'),
    (22, '制骑群', {'残页': 6}, '张飞一喝二阶「怒雷」'),
    (25, '破罩二', {'精铁': 12}, '兵器精炼到 +3'),
    (30, '吕布', {'精铁': 16, '将印': 2}, '兵器 +4、一人觉醒'),
]
GATES_V2 = [                                                                            # 门排匀：两三关一道，残页只从军务来
    (5, '邓茂', {'精铁': 4}, '兵器 +1'),
    (9, '禁术', {'残页': 6}, '刘备双股剑二阶「剑印」（定住术士）'),
    (11, '破盾', {'残页': 12}, '关羽青龙斩二阶「龙鳞破甲」'),
    (15, '胡轸', {'精铁': 8}, '兵器 +2'),
    (20, '华雄', {'精铁': 12}, '兵器 +3（温酒斩第 19 关剧情给）'),
    (22, '制骑群', {'残页': 18}, '张飞一喝二阶「怒雷」'),
    (25, '李傕', {'精铁': 16}, '兵器 +4'),
    (27, '护民', {'残页': 18}, '刘备剑印终阶（光幕里不误伤百姓）'),
    (30, '吕布', {'精铁': 20, '将印': 2}, '兵器 +5、一人觉醒'),
]
GATES_V3 = [(lv, nm, ({**req, '神兵': 1} if lv in (15, 20, 25, 30) else req), why) for lv, nm, req, why in GATES_V2]   # 十二道军务：兵器 +2 起每级多要一块神兵材料
PLANS = {
    # 点卯：每天 精铁 2；军务三道：每道 残页 2、精铁 1；重打：每次 精铁 1、残页 0.5（第 9 关起有术士、头目），每天上限 精铁 3、残页 2；
    # 周常：一周里点卯满 5 天给将印 1；第 20 关首通给将印 1；漏掉的天点卯、军务最多补 2 天
    '初稿': dict(gates=GATES_V1, login={'精铁': 2}, task_n=3, task={'残页': 2, '精铁': 1}, task_min=3.5, replay={'精铁': 1, '残页': .5}, cap={'精铁': 3, '残页': 2},
               weekly=('将印', 1, 'login', 5), first={20: {'将印': 1}}, save=2),
    # 推了初稿以后改：将印按「一周做满 10 道军务」给（隔天、周末玩的也凑得齐）；残页只从军务来（每道 2）；精铁 点卯 2 ＋ 重打每天最多 2；门排匀
    '定稿': dict(gates=GATES_V2, login={'精铁': 2}, task_n=3, task={'残页': 2}, task_min=3.5, replay={'精铁': 1}, cap={'精铁': 2},
               weekly=('将印', 1, 'tasks', 10), first={20: {'将印': 1}}, save=2),
    # 10-25 用户：「每日军务可以增加 出外探访（政治高效果好），一定带回材料，有时会带回神兵材料……每日军务设置12个吧」：
    # 加出外探访两次（一键，刘备政治 72：精铁 2、机缘 15，满 100 得神兵材料一块）、日常杂务七项（一键，只给经验，不算材料）
    '十二道': dict(gates=GATES_V3, login={'精铁': 2}, task_n=3, task={'残页': 2}, task_min=3.5, replay={'精铁': 1}, cap={'精铁': 2},
               weekly=('将印', 1, 'tasks', 10), first={20: {'将印': 1}}, save=2, visit=dict(n=2, iron=2, luck=15, min=.3), chores_min=.2),
    # 10-25 夜用户：「这些不是得到经验，是得到物品奖励……一键完成要消耗体力的」：七项杂务一天给 精铁 3、残页 3、机缘 10（体力一天回得满，不卡）；
    # 杂务只算当天，漏掉的天不补；每关用时换成晋升减少后的新实测
    '杂务给物品': dict(gates=GATES_V3, login={'精铁': 2}, task_n=3, task={'残页': 2}, task_min=3.5, replay={'精铁': 1}, cap={'精铁': 2},
               weekly=('将印', 1, 'tasks', 10), first={20: {'将印': 1}}, save=2, visit=dict(n=2, iron=2, luck=15, min=.3), chores_min=.2,
               chores={'精铁': 3, '残页': 3}, chore_luck=10, mins=MIN2),
    # 10-26 推完上面那版第一章只要 10 天（陨铁快了），用户：「拉回2周」——探访和募集粮草给的机缘减少（试过满 133 换一块，效果相同但数字难看）
}
PLANS['两周'] = {**PLANS['杂务给物品'], 'visit': {**PLANS['杂务给物品']['visit'], 'luck': 12}, 'chore_luck': 6}   # 实际改法：机缘门槛不动，探访 15 → 12、募集粮草 10 → 6
# 10-26 用户：「神兵不能那么容易升级，必须和卡关卡同步」——兵器 +1…+5 精铁 8/20/30/40/50（原来 4/8/12/16/20），门槛只是军师建议，推演里当作「买齐了再打那关」（现行）
_WI = {5: 8, 15: 20, 20: 30, 25: 40, 30: 50}
PLANS['神兵同步'] = {**PLANS['两周'], 'gates': [(lv, nm, ({**req, '精铁': _WI[lv]} if lv in _WI else req), w) for lv, nm, req, w in PLANS['两周']['gates']]}
# 玩家：每周七天各玩几分钟（0 = 不上线）
PLAYERS = {
    '每天 45 分钟': [45] * 7,
    '每天 3 小时（爆肝）': [180] * 7,
    '每天 20 分钟': [20] * 7,
    '隔天 90 分钟': [90, 0] * 3 + [90],
    '只玩周末 2 小时': [0, 0, 0, 0, 0, 120, 120],
}


def run(P, week, days=60):
    GATES = P['gates']; MIN = P.get('mins', globals()['MIN']); LF = P.get('luck_full', 100); inv = {'精铁': 0, '残页': 0, '将印': 0, '神兵': 0}; luck = 0; need_left = [dict(g[2]) for g in GATES]
    nxt, owed, log, gate_day, total, login_days, task_days = 1, 0, [], {}, 0, [], []
    for d in range(days):
        mins = week[d % 7]
        if d % 7 == 0 and d:                                                            # 周常结算
            k, v, how, n = P['weekly']; got_n = sum(1 for x in login_days if x >= d - 7) if how == 'login' else sum(1 for x in task_days if x >= d - 7)
            if got_n >= n: inv[k] += v
        if not mins: owed = min(P['save'], owed + 1); continue
        login_days.append(d); total += mins; t = mins
        packs = 1 + owed; owed = 0                                                   # 今天的点卯、军务，加上补回来的
        for k, v in P['login'].items(): inv[k] += v * packs
        late = P['task_n'] * packs if nxt == 1 else 0                                 # 游戏里打通第一关以后当天就补出军务（10-26 对齐 dailyTick）
        tasks = P['task_n'] * packs if nxt > 1 else 0
        def do_tasks(n):
            nonlocal t
            while n and t >= P['task_min']:
                t -= P['task_min']; n -= 1; task_days.append(d)
                for k, v in P['task'].items(): inv[k] += v
        do_tasks(tasks)
        if 'visit' in P:                                                              # 出外探访、日常杂务：一键，先做（几乎不花时间）
            V = P['visit']
            for _ in range(V['n'] * packs):
                if t < V['min']: break
                t -= V['min']; inv['精铁'] += V['iron']; luck += V['luck']
                while luck >= LF: luck -= LF; inv['神兵'] += 1
            t -= P.get('chores_min', 0)
            for k, v in P.get('chores', {}).items(): inv[k] += v
            luck += P.get('chore_luck', 0)
            while luck >= LF: luck -= LF; inv['神兵'] += 1
        got = {k: 0 for k in P['cap']}
        def buy():                                                                    # 手里的材料够哪道门就先买哪道（门按关号排）
            for gi, g in enumerate(GATES):
                for k in list(need_left[gi]):
                    take = min(inv[k], need_left[gi][k]); inv[k] -= take; need_left[gi][k] -= take
                    if need_left[gi][k] <= 1e-9: del need_left[gi][k]
        buy()
        def advance():
            nonlocal t, nxt
            while t > 0 and nxt <= 30:
                gi = next((i for i, g in enumerate(GATES) if g[0] == nxt), None)
                if gi is not None and need_left[gi]: break                           # 卡在门前
                if t < MIN[nxt]: break
                t -= MIN[nxt]
                for k, v in P['first'].get(nxt, {}).items(): inv[k] += v
                if gi is not None: gate_day[GATES[gi][1]] = d + 1
                nxt += 1; buy()
                if late and nxt == 2: return
        advance()
        if late and nxt > 1: do_tasks(late); buy(); advance()
        while t >= 3 and nxt > 1 and any(got[k] < P['cap'][k] for k in got):         # 剩下的时间重打刷材料，到上限就不刷了
            lv = max(1, nxt - 1); t -= MIN[lv]
            for k, v in P['replay'].items():
                if k == '残页' and lv < 9: continue
                if k not in P['cap']: continue
                add = min(v, P['cap'][k] - got[k]); got[k] += add; inv[k] += add
            buy()
        log.append((d + 1, nxt - 1))
        if nxt > 30: return d + 1, gate_day, total, log
    return None, gate_day, total, log


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else '定稿'; P = PLANS[name]; GATES = P['gates']
    print(f'方案：{name}；第一章 30 关全打一遍约 {sum(P.get("mins", MIN).values()):.0f} 分钟')
    print('| 玩家 | 打完第一章 | ' + ' | '.join(f'过第 {g[0]} 关（{g[1]}）' for g in GATES) + ' | 一共玩了 |')
    print('|---|---|' + '---|' * len(GATES) + '---|')
    for pn, wk in PLAYERS.items():
        done, gd, total, log = run(P, wk)
        cells = [f'第 {gd[g[1]]} 天' if g[1] in gd else '—' for g in GATES]
        print(f'| {pn} | {"第 %d 天" % done if done else "60 天没打完"} | ' + ' | '.join(cells) + f' | {total / 60:.0f} 小时 |')
