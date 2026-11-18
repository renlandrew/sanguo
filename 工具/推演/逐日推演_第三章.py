"""第三章逐日推演（11-18 用户：「做第三章，严格设计武器，技能等进阶」）——设计稿 `设计/第三章设定.md` 的数字从这里来。
接 逐日推演_第二章.py 推完那天手里剩的，按同样的每日收入，推「每天把日常做满」的玩家每天能打到哪一关、卡在什么上。

第二章推演暴露的问题：只有资历在卡人（十五天里十一天什么都解不开），精铁、专属材料、残页一路堆着用不掉。
第三章的规矩：
  1. 每一条线都要真卡一次：官阶（资历）、兵器（乌金、专属、陨铁）、招式（残页＋兵书）、觉醒（将印）；
  2. 卡点错开：同一段里先卡兵器、再卡招式、最后卡官阶，尽量每天都有一样东西解开；
  3. 新材料「乌金」只在第三章掉，第二章堆下的精铁按 4 换 1、一天最多换 3，堆得多的人快一点、但跳不过卡点。
用法：python3 三国志/工具/推演/逐日推演_第三章.py [功绩=全/半/无]
"""
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('c2', Path(__file__).with_name('逐日推演_第二章.py')); c2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c2)
c1 = c2.c1

# ---- 第三章数字（设计稿第五节） ----
PREP_NEEDS = {9: 60, 10: 64, 11: 68}                    # 现在几阶 → 晋下一阶要的资历（同第二章：资历是一段五天的钟，其他线在这五天里错开卡）
NODES = {70: 10, 80: 11, 90: 12}                         # 打这关前要几阶
CAP = {9: 24, 10: 27, 11: 29, 12: 30}                    # 兵器上限跟官阶走（打完第二章、左将军 +24）
WU = [3, 3, 3, 3, 3, 3, 4, 4, 4, 4]                      # +21…+30 每人每级乌金：三人合计约一天半的乌金收入
ZS = [3, 3, 4, 4, 4, 4, 5, 5, 6, 6]                      # 每人每级专属
WIN_WPN = {63: 21, 65: 22, 67: 23, 70: 24, 72: 25, 75: 26, 78: 27, 80: 28, 86: 29, 90: 30}   # 门槛（三兄弟都要到）：两三关一档，兵器当每天的钟
STUDY = {  # 研习：门槛关 → (残页, 兵书)
    68: ('温酒斩将 · 冷艳锯', 50, 1),
    76: ('千里走单骑 · 过关', 70, 1),
    80: ('当阳一喝 · 三通鼓', 80, 1),
    85: ('七进七出 · 百鸟朝凤', 90, 1),
    87: ('仁德护阵 · 携民', 110, 1),
}
AWAKE2 = (90, 4)                                         # 第二次觉醒：门槛关、将印
BINGSHU_AT = {65: 1, 70: 1, 75: 1, 79: 1, 84: 1, 86: 1}   # 兵书：斗将关、节点前一关首通各给一卷（共 6 卷，研习用 5 卷）
ACH_NODE = {70: [67, 69], 80: [77, 79], 90: [87, 89]}    # 节点功绩（每阶两项）
WU_DROP, WU_DAY, WU_SIGN = 2, 4, 2                        # 第三章关打赢掉 2、一天最多 4；点卯 2
SMELT_RATE, SMELT_DAY = 4, 3                              # 精铁 4 换乌金 1，一天最多换 3


def run(share=1.0, verbose=True):
    log2 = c2.run(share, verbose=False)
    d0, _, _, _, inv2, _ = log2[-1]
    inv = dict(inv2); inv['资历'] = 0; inv['乌金'] = 0; inv['兵书'] = 0
    inv['残页'] = inv.get('残页', 0); inv['将印'] = inv.get('将印', 0)
    rank, wpn, cleared, studied, awake2 = 9, 20, 60, set(), False
    fort, log = 0, []
    for d in range(1, 31):
        for k, v in c1.DAILY.items(): inv[k] += v
        if rank < 12: inv['资历'] = min(inv['资历'], PREP_NEEDS[rank])
        fort += 2 * c1.FORT_PER_VISIT; inv['残页'] += fort // c1.FORT_FULL; fort %= c1.FORT_FULL
        if (d + 3) % 7 == 0: inv['将印'] += 1                                   # 每周十道军务
        inv['专属'] += 6
        while inv['机缘'] >= 100: inv['机缘'] -= 100; inv['陨铁'] += 1
        inv['乌金'] += WU_SIGN
        smelt = min(SMELT_DAY, int(inv['精铁'] // SMELT_RATE)); inv['精铁'] -= smelt * SMELT_RATE; inv['乌金'] += smelt
        wu_today, promoted, today, got, why = 0, False, [], [], ''
        while True:
            nxt = cleared + 1
            if nxt > 90: break
            if not promoted and rank < 12 and inv['资历'] >= PREP_NEEDS[rank]:
                inv['资历'] = 0; rank += 1; promoted = True; got.append(f'晋{rank}阶')
            need_w = WIN_WPN.get(nxt, 0)
            while wpn < min(need_w, CAP[rank]):
                k = wpn + 1 - 21
                c = dict(乌金=3 * WU[k], 专属=3 * ZS[k], 陨铁=3 if (wpn + 1) % 2 == 0 else 0)
                if all(inv[x] >= v for x, v in c.items()):
                    for x, v in c.items(): inv[x] -= v
                    wpn += 1; got.append(f'兵器+{wpn}')
                else: break
            if nxt in STUDY and nxt not in studied:
                nm, cy, bs = STUDY[nxt]
                if not any(x.startswith('研习') for x in got) and inv['残页'] >= cy and inv['兵书'] >= bs: inv['残页'] -= cy; inv['兵书'] -= bs; studied.add(nxt); got.append('研习' + nm)
            if nxt == AWAKE2[0] and not awake2 and inv['将印'] >= AWAKE2[1]: inv['将印'] -= AWAKE2[1]; awake2 = True; got.append('二次觉醒')
            need_rank = max([r for lv, r in NODES.items() if lv <= nxt] or [9])
            if rank < need_rank: why = f'官阶（资历 {inv["资历"]:.0f}/{PREP_NEEDS[rank]}）'; break
            if wpn < need_w: why = f'兵器+{need_w}（现+{wpn}，上限+{CAP[rank]}；乌金{inv["乌金"]:.0f} 专属{inv["专属"]:.0f} 陨铁{inv["陨铁"]:.0f}）'; break
            if nxt in STUDY and nxt not in studied: why = f'研习{STUDY[nxt][0]}（残页{inv["残页"]:.0f}/{STUDY[nxt][1]} 兵书{inv["兵书"]}/{STUDY[nxt][2]}）'; break
            if nxt == AWAKE2[0] and not awake2: why = f'二次觉醒（将印{inv["将印"]}/{AWAKE2[1]}）'; break
            cleared = nxt; today.append(nxt); inv['精铁'] += 2
            if wu_today < WU_DAY: g = min(WU_DROP, WU_DAY - wu_today); inv['乌金'] += g; wu_today += g
            inv['兵书'] += BINGSHU_AT.get(nxt, 0)
            if nxt in (65, 70, 75, 80, 85): inv['陨铁'] += 1; inv['将印'] += 0
            for lv, lvs in ACH_NODE.items():
                if nxt in lvs and NODES[lv] == rank + 1: inv['精铁'] += 2; inv['残页'] += 1; inv['资历'] += 4 * share
        log.append((d, today, rank, wpn, dict(inv), got, why if cleared < 90 else '通关'))
        if cleared >= 90: break
    if verbose:
        print(f'第二章推完（{d0} 天），带进第三章：精铁{inv2["精铁"]:.0f} 陨铁{inv2["陨铁"]:.0f} 专属{inv2["专属"]:.0f} 残页{inv2.get("残页", 0):.0f} 将印{inv2.get("将印", 0):.0f}')
        for d, t, r, w, iv, got, why in log:
            span = (f'{t[0]}–{t[-1]}' if len(t) > 1 else str(t[0])) if t else '—'
            print(f'第{d:>2}天 过 {span:>6}  {"、".join(got) or "（无新解锁）":<24} 官阶{r} 兵器+{w}  乌金{iv["乌金"]:.0f} 专属{iv["专属"]:.0f} 陨铁{iv["陨铁"]:.0f} 残页{iv["残页"]:.0f} 兵书{iv["兵书"]} 将印{iv["将印"]:.0f}  卡：{why}')
    return log


if __name__ == '__main__':
    run({'全': 1, '半': .5, '无': 0}.get(sys.argv[1] if len(sys.argv) > 1 else '全', 1))
