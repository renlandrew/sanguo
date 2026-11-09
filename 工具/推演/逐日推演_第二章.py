"""第二章逐日推演（11-08 用户：「先做官阶兵器」）：接着 逐日推演.py 第一章推完那天手里剩的，
按同样的每日收入，推「每天把日常做满」的玩家第几天打到第 60 关。
卡点：官阶（第 40、50、60 关前要别部司马、徐州牧、左将军，资历 60/64/68，一天只能晋一阶）、
兵器（斗将关门槛 35:+12、45:+14、50:+16、55:+18、60:+20，三人都要到；上限跟官阶走）。
用法：python3 三国志/工具/推演/逐日推演_第二章.py [功绩=全/半/无]
"""
import importlib.util, math, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('c1', Path(__file__).with_name('逐日推演.py')); c1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c1)

WPN_IRON = c1.WPN_IRON + [18, 18, 20, 20, 22, 22, 25, 25, 28, 28]
MAT_NEED = {**c1.MAT_NEED, 11: 2, 12: 2, 13: 3, 14: 3, 15: 3, 16: 3, 17: 4, 18: 4, 19: 4, 20: 4}
def wpn_cost(k):
    return dict(精铁=3 * math.ceil(WPN_IRON[k - 1] / 3), 陨铁=1 if k % 2 == 0 else 0, 专属=3 * MAT_NEED.get(k, 0))
PREP_NEEDS = {6: 60, 7: 64, 8: 68}                     # 现在几阶 → 晋下一阶要的资历
NODES = {40: 7, 50: 8, 60: 9}
CAP = {6: 12, 7: 15, 8: 18, 9: 20}
WIN_WPN = {35: 12, 45: 14, 50: 16, 55: 18, 60: 20}
ACH_NODE = {40: [37, 39], 50: [47, 49], 60: [57, 59]}

def run(share=1.0, verbose=True):
    log1 = c1.run(share, days=40, verbose=False)
    d0, _, _, _, inv1, _ = log1[-1]
    inv = dict(inv1); inv['资历'] = 0; rank, wpn, cleared = 6, 10, 30; fort = 0; log = []
    for d in range(1, 31):
        for k, v in c1.DAILY.items(): inv[k] += v
        if rank < 9: inv['资历'] = min(inv['资历'], PREP_NEEDS[rank])
        fort += 2 * c1.FORT_PER_VISIT; inv['残页'] += fort // c1.FORT_FULL; fort %= c1.FORT_FULL
        inv['专属'] += 6
        while inv['机缘'] >= 100: inv['机缘'] -= 100; inv['陨铁'] += 1
        promoted, today, why = False, [], ''
        while True:
            nxt = cleared + 1
            if nxt > 60: break
            if not promoted and rank < 9 and inv['资历'] >= PREP_NEEDS[rank]: inv['资历'] = 0; rank += 1; promoted = True   # 一天只晋一阶
            need_w = WIN_WPN.get(nxt, 0)
            while wpn < min(need_w, CAP[rank]):
                c = wpn_cost(wpn + 1)
                if all(inv[k] >= v for k, v in c.items()):
                    for k, v in c.items(): inv[k] -= v
                    wpn += 1
                else: break
            need_rank = max([r for lv, r in NODES.items() if lv <= nxt] or [6])
            if rank < need_rank: why = f'官阶（资历 {inv["资历"]:.0f}/{PREP_NEEDS[rank]}）'; break
            if wpn < need_w: why = f'兵器+{need_w}（现+{wpn}，上限+{CAP[rank]}）'; break
            cleared = nxt; today.append(nxt); inv['精铁'] += 2
            if nxt in (35, 40, 45, 50, 55): inv['陨铁'] += 1
            for lv, lvs in ACH_NODE.items():
                if nxt in lvs and NODES[lv] == rank + 1: inv['精铁'] += 2; inv['残页'] += 1; inv['资历'] += 4
        log.append((d, today, rank, wpn, dict(inv), why if cleared < 60 else '通关'))
        if cleared >= 60: break
    if verbose:
        print(f'第一章推到第 {d0} 天通关，带进第二章：精铁{inv1["精铁"]:.0f} 陨铁{inv1["陨铁"]:.1f} 专属{inv1["专属"]:.0f}')
        for d, t, r, w, iv, why in log:
            print(f'第二章第{d:>2}天 过 {(str(t[0]) + "–" + str(t[-1])) if t else "—":>6}  官阶{r} 兵器+{w}  精铁{iv["精铁"]:.0f} 陨铁{iv["陨铁"]:.1f} 专属{iv["专属"]:.0f} 资历{iv["资历"]:.0f}  卡：{why}')
    return log

if __name__ == '__main__':
    run({'全': 1, '半': .5, '无': 0}.get(sys.argv[1] if len(sys.argv) > 1 else '全', 1))
