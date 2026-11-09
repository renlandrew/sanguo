// 手写的句式（make_en.py 原样接在 en.js 末尾）：中文数字的关号、「下一阶 · 某某」这类拼出来的句子
(() => {
  const E = window.EN, N = { 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9, 十: 10, 廿: 20, 卅: 30 };
  const cn = s => { if (/^\d+$/.test(s)) return +s; let v = 0, cur = 0; for (const c of s) { const d = N[c]; if (d >= 10) { v += (cur || 1) * d; cur = 0; } else cur = d; } return v + cur; };
  const t = s => window.__tr ? window.__tr(s) : (E[s] ?? s);
  const NUMS = '[一二三四五六七八九十廿卅\\d]+';
  window.EN_RX.push(
    [new RegExp(`^第(${NUMS})关(.+)$`), (m, n, rest) => `Stage ${cn(n)}: ${t(rest)}`],
    [new RegExp(`^打第(${NUMS})关之前晋阶$`), (m, n) => `Promote before Stage ${cn(n)}`],
    [new RegExp(`^打第(${NUMS})关(.+)之前，最好先备上这个$`), (m, n, nm) => `Get this ready before Stage ${cn(n)}, "${t(nm)}"`],
    [new RegExp(`^(.+?)：打第(${NUMS})关(.+)之前，最好先备上这个$`), (m, who, n, nm) => `${t(who)}: get this ready before Stage ${cn(n)}, "${t(nm)}"`],
    [new RegExp(`^第(${NUMS})波，(.+)$`), (m, n, rest) => `Wave ${cn(n)}: ${t(rest)}`],
    [/^第一章 · (.+)$/, (m, x) => `Ch.1 · ${t(x)}`], [/^第二章 · (.+)$/, (m, x) => `Ch.2 · ${t(x)}`],
    [/^下一阶 · (.+)$/, (m, x) => `Next · ${t(x)}`],
    // 11-09 军师荐卡、报敌情（拼出来的句子）
    [/^需要 (.+)$/, (m, x) => `Needs: ${t(x)}`],
    [/^(.+)伤害、范围更大（(.+) (\d+) 级）$/, (m, nm, sh, n) => `${t(nm)}: more damage & range (${t(sh)} Lv ${n})`],
    [/^(.+)更强；(.+) (\d+) 级：(.+)——(.+)$/, (m, nm, sh, n, a, b) => `${t(nm)} stronger. ${t(sh)} Lv ${n}: ${t(a)} — ${t(b)}`],
    [/^(.+)（智 (\d+)）看不透(.+)的计策，只能见招拆招。$/, (m, a, n, b) => `${t(a)} (INT ${n}) can't read ${t(b)}'s plans — react as they come.`],
    [/^换智力高过 (\d+) 的军师，开战前就能看破。$/, (m, n) => `An advisor with INT above ${n} would see them before battle.`],
    [/^敌军师 · (.+)（智 (\d+)）$/, (m, a, n) => `Enemy advisor · ${t(a)} (INT ${n})`],
    [/^(.+)（智 (\d+)）看破了他的计策：$/, (m, a, n) => `${t(a)} (INT ${n}) sees through his plans:`],
    [/^(.+)（智 (\d+)）看得破：开战前报出他的计$/, (m, a, n) => `${t(a)} (INT ${n}) sees through: plans reported before battle`],
    [/^(.+)（智 (\d+)）看不透：开战后见招拆招$/, (m, a, n) => `${t(a)} (INT ${n}) can't read them: react in battle`],
    [/^· (.+?)：(.+)$/, (m, a, b) => `· ${t(a)}: ${t(b)}`],
    [/^破了(.+)的(.+)$/, (m, a, b) => `Broke ${t(a)}'s ${t(b)}`],
    [/^离间(.+)：他的招式被封 (\d+) 秒$/, (m, g, n) => `sows discord on ${t(g)}: his skill is sealed ${n}s`],
    [/^(?:第(.+)波)开始约 (\d+) 秒，(\d+) 骑从(左|右)侧杀出$/, (m, w, s, n, side) => `~${s}s into wave ${({一:1,二:2,三:3,四:4,五:5,六:6})[w] || w}, ${n} riders charge from the ${side === '左' ? 'left' : 'right'}`],
    [/^荐「(.+?)」：(.+)$/, (m, c, why) => `Take "${t(c)}": ${t(why)}`],
    [/^下次晋升先拿「(.+?)」：(.+)$/, (m, c, why) => `Next promotion, take "${t(c)}": ${t(why)}`],
    [/^后面还有：(.+)$/, (m, xs) => 'Still coming: ' + xs.split('、').map(t).join(', ')],
    [/^(骑兵|举盾|重甲|放箭|术士|头目敌将)：不清楚$/, (m, k) => `${t(k)}: unknown`],
    [/^(骑兵|举盾|重甲|放箭|术士|头目敌将) 约 (\d+)$/, (m, k, n) => `${t(k)} ~${n}`],
    [/^(骑兵|举盾|重甲|放箭|术士|头目敌将) (\d+)$/, (m, k, n) => `${t(k)} ${n}`],
    [/^(骑兵|举盾|重甲|放箭|术士|头目敌将)不少$/, (m, k) => `${t(k)}: many`],
    [/^(骑兵|举盾|重甲|放箭|术士|头目敌将)有几个$/, (m, k) => `${t(k)}: a few`],
    [/^接着捧(.+)$/, (m, g) => `Keep backing ${t(g)}.`],
    [/^(.+)这一路能打$/, (m, g) => `${t(g)}'s path is strong.`],
    [/^顺着(.+)的路子走$/, (m, g) => `Follow ${t(g)}'s path.`],
    [/^连携凑齐了：(.+)一起打$/, (m, gs) => `Combo ready: ${gs.split('、').map(t).join(' & ')} strike together.`],
    [/^(.+)要放火箭，摆了拒马也会被烧$/, (m, g) => `${t(g)} will loose fire arrows — barricades would just burn.`],
    [/^打赢一次（掉(.+)）$/, (m, x) => `win once (drops ${t(x)})`],
    [/^(.+) · (.+)$/, (m, a, b) => `${t(a)} · ${t(b)}`],
  );
})();
