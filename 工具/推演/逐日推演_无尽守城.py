"""11-12 无尽守城经济推演（用户：「你先做经济推演」）：第一章，每天把日常做满的玩家，有／没有无尽守城（含每日扫荡）各推一遍，
看精铁、残页多出多少，兵器、通关天数变不变。数字按守关.html 11-12 现行：体力 120+20+20、打赢一关 10 体力掉精铁 1（刷材料关再掉 1 份专属）、
杂务 70 体力、资历 16/16/36/48/52/56 且一天只能晋一阶；兵器有钱就升（上限 +10）。首通、功绩、战功星的奖励沿用 逐日推演.py 的估法。
无尽守城：存的档数 ≈ 2×打过的非斗将关 + 2（机器人第十二关底卡在 65–70 波 ≈ 22 档）；每档精铁 1、逢五档残页 1；第二天起每天扫荡收回全部已存档。
用法：python3 三国志/工具/推演/逐日推演_无尽守城.py [体力=160/120] [每次精铁=1] [扫荡=1/0] [几档发一次=4]
"""
import math, sys
STA = int(sys.argv[1]) if len(sys.argv) > 1 else 160
CK_IRON = float(sys.argv[2]) if len(sys.argv) > 2 else 1
SWEEP = int(sys.argv[3]) if len(sys.argv) > 3 else 1
CK_EVERY = int(sys.argv[4]) if len(sys.argv) > 4 else 4   # 几档发一次（11-12 定四档一块；原来是 1）
WPN_IRON = [4, 4, 10, 10, 15, 15, 20, 20, 25, 25]
MAT_NEED = {6: 2, 7: 2, 8: 3, 9: 3, 10: 4}
def wpn_cost(k): return dict(精铁=3 * math.ceil(WPN_IRON[k - 1] / 3), 陨铁=1 if k >= 4 and k % 2 == 0 else 0, 专属=3 * MAT_NEED.get(k, 0))
SKILL = {'liu2': (9, 6), 'guan2': (11, 12), 'zhang2': (22, 18), 'liu3': (27, 18)}
PREP = [16, 16, 36, 48, 52, 56]; NODES = {5: 1, 10: 2, 15: 3, 20: 4, 25: 5, 30: 6}
ACH_NODE = {5: [3, 4], 10: [7, 9], 15: [12, 14], 20: [17, 19], 25: [22, 24], 30: [27, 29]}
FEATS = dict(资历=16, 残页=20, 陨铁=3, 专属=18)
WIN_WPN = {13: 2, 15: 4, 20: 6, 21: 2, 23: 6, 24: 2, 25: 8, 28: 2, 29: 4, 30: 10}
DUEL = {5, 15, 20, 25, 30}
def ck_of(cleared): return 0 if cleared < 3 else 2 * (cleared - len([d for d in DUEL if d <= cleared])) + 2
def ck_pay(a, b):   # 第 a+1…b 档
    return len([c for c in range(a + 1, b + 1) if c % CK_EVERY == 0]) * CK_IRON, len([c for c in range(a + 1, b + 1) if c % (5 * CK_EVERY) == 0])

def run(endless, days=20):
    inv = dict(精铁=0, 残页=0, 机缘=0, 陨铁=0, 将印=0, 资历=0, 专属=0); fort = 0
    rank = wpn = cleared = ck = 0; skills = set(); rows = []; got_end = [0, 0]; tot_iron = 0
    for d in range(1, days + 1):
        iron0 = inv['精铁']; spent = 0; promoted = False
        inv['精铁'] += 2 + 4 + 3; inv['残页'] += 6 + 3; inv['机缘'] += 30; inv['资历'] += 12   # 点卯、探访、杂务、军务
        fort += 184; inv['残页'] += fort // 250; fort %= 250
        if d >= 4 and (d - 4) % 7 == 0: inv['将印'] += 1
        while inv['机缘'] >= 100: inv['机缘'] -= 100; inv['陨铁'] += 1
        sta = STA - 70; today = []
        if endless and SWEEP and ck: a, b = ck_pay(0, ck); inv['精铁'] += a; inv['残页'] += b; got_end[0] += a; got_end[1] += b
        def spend():
            nonlocal wpn, rank, promoted, spent
            if rank < 6: inv['资历'] = min(inv['资历'], PREP[rank])
            if rank < 6 and inv['资历'] >= PREP[rank] and not promoted: inv['资历'] = 0; rank += 1; promoted = True
            for sk, (lv, cost) in SKILL.items():
                if sk not in skills and cleared + 1 >= lv and inv['残页'] >= cost: inv['残页'] -= cost; skills.add(sk)
            while wpn < 10:
                c = wpn_cost(wpn + 1)
                if all(inv[k] >= v for k, v in c.items()):
                    for k, v in c.items(): inv[k] -= v
                    spent += c['精铁']; wpn += 1
                else: break
        why = ''
        while cleared < 30:
            spend(); nxt = cleared + 1
            need_rank = max([r for lv, r in NODES.items() if lv <= nxt] or [0]); need_w = WIN_WPN.get(nxt, 0)
            need_sk = [sk for sk, (lv, _) in SKILL.items() if lv == nxt and sk not in skills]
            if sta < 10: why = '体力'; break
            if rank < need_rank: why = '官阶'; break
            if wpn < need_w: c = wpn_cost(wpn + 1); why = f'兵器+{need_w}（差' + '、'.join(k for k, v in c.items() if inv[k] < v) + '）'; break
            if need_sk: why = '研习残页'; break
            if nxt == 30 and inv['将印'] < 2: why = '将印'; break
            cleared = nxt; today.append(nxt); sta -= 10
            inv['精铁'] += 1 + 2
            if nxt == 20: inv['将印'] += 1
            if nxt in (5, 15, 20, 25): inv['陨铁'] += 1
            for lv, lvs in ACH_NODE.items():
                if nxt in lvs: inv['精铁'] += 2; inv['残页'] += 1; inv['资历'] += 4
            if 5 <= nxt <= 25:
                for k in FEATS: inv[k] += FEATS[k] / 21
            for s in (5, 15, 30, 50, 75):
                if (nxt - 1) * 2.3 < s <= nxt * 2.3: inv['残页'] += 5
        while sta >= 10 and cleared >= 3:        # 剩下的体力刷材料关
            sta -= 10; inv['精铁'] += 1; inv['专属'] += 1
        if endless:
            c1 = ck_of(cleared)
            if c1 > ck: a, b = ck_pay(ck, c1); inv['精铁'] += a; inv['残页'] += b; got_end[0] += a; got_end[1] += b; ck = c1
        spend()
        tot_iron += inv['精铁'] - iron0 + spent
        rows.append((d, today, rank, wpn, round(inv['精铁']), round(inv['残页']), round(inv['专属']), round(inv['陨铁'], 1), ck * 3, why if cleared < 30 else '通关', round(tot_iron)))
        if cleared >= 30 and wpn >= 10: break
    return rows, got_end

for tag, e in (('没有无尽守城', 0), ('有无尽守城' + ('＋每日扫荡' if SWEEP else '（不扫荡）') + f' 每档精铁 {CK_IRON:g}', 1)):
    rows, g = run(e)
    print(f'== {tag}（体力 {STA}）==')
    for d, t, r, w, fe, pg, mt, yt, wv, why, ti in rows:
        print(f'第{d:>2}天 过 {(str(t[0]) + "–" + str(t[-1])) if t else "—":>6} 官阶{r} 兵器+{w:<2} 余精铁{fe:>4} 余残页{pg:>3} 专属{mt:>3} 陨铁{yt:>4} 无尽{wv:>3}波 累计得精铁{ti:>4}  卡：{why}')
    if e: print(f'无尽守城一共给了：精铁 {g[0]:.0f}、残页 {g[1]}')
