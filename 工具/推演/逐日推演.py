"""第一章逐日推演（10-29 用户：「逐日推演」）：按守关.html 现行的日常收入、功绩奖励、兵器／研习价格、晋阶资历，
推一个「每天把日常做满」的玩家第几天能打哪一关；能不能打过看机器人实测的「这关兵器最低几级能赢」（WIN_WPN，见同目录说明）。
用法：python3 三国志/工具/推演/逐日推演.py [功绩=全/半/无]
"""
import math, sys

# ---- 现行数字（守关.html，10-29） ----
DAILY = dict(精铁=2 + 2 + 2 * 2 + 3,   # 点卯 2、征战掉落上限 2、探访两次各 2（刘备武力 68）、杂务 3
             残页=3 * 2 + 3,           # 军务三道各 2、杂务 3
             机缘=2 * 12 + 6,          # 探访两次各 12（刘备政治 72）、杂务 6
             资历=3 + 2 + 7)           # 军务、探访、杂务各 +1
FORT_PER_VISIT, FORT_FULL = 92, 250     # 刘备魅力 92：攒满 250 多一页残页
WPN_IRON = [4, 4, 10, 10, 15, 15, 20, 20, 25, 25]
def wpn_cost(k):                        # 三人各升到 k 级合计
    return dict(精铁=3 * math.ceil(WPN_IRON[k - 1] / 3), 陨铁=3 if k >= 4 and k % 2 == 0 else 0)
SKILL = {'liu2': (9, 6), 'guan2': (11, 12), 'zhang2': (22, 18), 'liu3': (27, 18)}   # 门槛关、残页
NODES = {5: 1, 10: 2, 15: 3, 20: 4, 25: 5, 30: 6}                                     # 打这关前要几阶
ACH_NODE = {5: [3, 4], 10: [7, 9], 15: [12, 14], 20: [17, 19], 25: [22, 24], 30: [27, 29]}   # 每阶两项（三星／两星）：精铁 2、残页 1、资历 4
FEATS = dict(资历=4 * 4, 残页=5 * 4, 陨铁=3)                                           # 十五项战功里给物品的部分
# 每关兵器最低几级能赢（机器人 smart，3 个种子至少 2 胜；技能按推荐都学了）——由浏览器实测填入
WIN_WPN = {13: 2, 15: 4, 20: 6, 21: 2, 23: 6, 24: 2, 25: 8, 28: 2, 29: 4, 30: 10}   # 10-29 实测（其余关 +0 就能赢）
LEVELS_PER_DAY_CAP = 99                   # 一天最多打几关新关（体力不限关卡；这里只看材料、官阶）

def run(feat_share=1.0, days=16, verbose=True):
    inv = dict(精铁=0, 残页=0, 机缘=0, 陨铁=0, 将印=0, 资历=0); fort = 0
    rank, wpn, skills, cleared = 0, 0, set(), 0
    log = []
    feat_left = {k: v * feat_share for k, v in FEATS.items()}
    for d in range(1, days + 1):
        for k, v in DAILY.items(): inv[k] += v
        fort += 2 * FORT_PER_VISIT; inv['残页'] += fort // FORT_FULL; fort %= FORT_FULL
        if d % 7 == 4 or d == 4: pass
        if d >= 4 and (d - 4) % 7 == 0: inv['将印'] += 1                         # 每周十道军务：每天三道，第四天满
        while inv['机缘'] >= 100: inv['机缘'] -= 100; inv['陨铁'] += 1
        # 战功：按通关进度平均摊到第 5–25 关
        start = cleared; today = []
        while True:
            # 先花钱：晋阶、研习、兵器（够下一关要的就升）
            nxt = cleared + 1
            if nxt > 30: break
            need_rank = max([r for lv, r in NODES.items() if lv <= nxt] or [0])
            if rank < need_rank and inv['资历'] >= 20: inv['资历'] -= 20; rank += 1
            for sk, (lv, cost) in SKILL.items():
                if sk not in skills and nxt >= lv and inv['残页'] >= cost: inv['残页'] -= cost; skills.add(sk)
            need_w = WIN_WPN.get(nxt, 0)
            while wpn < need_w:
                c = wpn_cost(wpn + 1)
                if all(inv[k] >= v for k, v in c.items()):
                    for k, v in c.items(): inv[k] -= v
                    wpn += 1
                else: break
            need_sk = [sk for sk, (lv, _) in SKILL.items() if lv == nxt and sk not in skills]
            awake_ok = nxt < 30 or inv['将印'] >= 2
            if rank < need_rank or wpn < need_w or need_sk or not awake_ok or len(today) >= LEVELS_PER_DAY_CAP:
                why = '官阶' if rank < need_rank else f'兵器+{need_w}（现+{wpn}，差 精铁/陨铁）' if wpn < need_w else ('研习' + ','.join(need_sk)) if need_sk else '觉醒将印' if not awake_ok else '当天关数'
                break
            cleared = nxt; today.append(nxt)
            inv['精铁'] += 2                                                    # 首通
            if nxt == 20: inv['将印'] += 1
            for lv, lvs in ACH_NODE.items():
                if nxt in lvs and rank + 1 == list(NODES).index(lv) + 1: inv['精铁'] += 2; inv['残页'] += 1; inv['资历'] += 4
            if 5 <= nxt <= 25:
                for k in feat_left: inv[k] += FEATS[k] * feat_share / 21
            for s in (5, 15, 30, 50, 75):
                if (nxt - 1) * 2.3 < s <= nxt * 2.3: inv['残页'] += 5
        else: why = ''
        log.append((d, today, rank, wpn, dict(inv), why if cleared < 30 else '通关'))
        if cleared >= 30: break
    if verbose:
        for d, t, r, w, iv, why in log:
            print(f'第{d:>2}天 过 {(str(t[0]) + "–" + str(t[-1])) if t else "—":>6}  官阶{r} 兵器+{w}  精铁{iv["精铁"]:.0f} 残页{iv["残页"]:.0f} 陨铁{iv["陨铁"]:.1f} 资历{iv["资历"]:.0f}  卡：{why}')
    return log

if __name__ == '__main__':
    share = {'全': 1, '半': .5, '无': 0}.get(sys.argv[1] if len(sys.argv) > 1 else '全', 1)
    run(share)
