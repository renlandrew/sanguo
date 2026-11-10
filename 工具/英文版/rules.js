// 手写的句式（make_en.py 原样接在 en.js 末尾）：中文数字的关号、「下一阶 · 某某」这类拼出来的句子
(() => {
  const E = window.EN, N = { 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9, 十: 10, 廿: 20, 卅: 30 };
  const cn = s => { if (/^\d+$/.test(s)) return +s; let v = 0, cur = 0; for (const c of s) { const d = N[c]; if (d >= 10) { v += (cur || 1) * d; cur = 0; } else cur = d; } return v + cur; };
  const t = s => window.__tr ? window.__tr(s) : (E[s] ?? s);
  const NUMS = '[一二三四五六七八九十廿卅\\d]+';
  // 11-10 关名：第三关、第二章第八关（存档码页、军务、神兵页都这样写）；list：顿号隔开的名字一个个翻；lc：接在半句后面的小写开头（人名开头的不动）
  const ST = `(第[一二]章)?第(${NUMS})关`, st = (c, n) => (c === '第二章' ? 'Ch.2 ' : c === '第一章' ? 'Ch.1 ' : '') + 'Stage ' + cn(n);
  const list = (xs, sep = ', ') => xs.split('、').map(t).join(sep);
  const LCW = /^(Save|Keep|Fish|Light|Interrupt|Burn|No|Wall|Both|Only|Let|The|Take|Win|Use|Your|Before|Carriage|Family|Ram|Roar-break)(?= |$)/, lc = s => LCW.test(s) ? s[0].toLowerCase() + s.slice(1) : s, lcn = s => /^(Carriage|Family|Ram|The)(?= |$)/.test(s) ? 'the ' + lc(s).replace(/^the /, '') : s;
  const stList = lvs => { const ps = lvs.split('、').map(p => new RegExp(`^${ST}$`).exec(p)), c2 = ps.every(p => p && p[1] === '第二章'), c1 = ps.every(p => p && !p[1]);
    if (!c1 && !c2) return ps.map((p, i) => p ? st(p[1], p[2]) : t(lvs.split('、')[i])).join(', ');
    return (c2 ? 'Ch.2 ' : '') + (ps.length > 1 ? 'stages ' : 'stage ') + ps.map(p => cn(p[2])).join(' & '); };
  window.EN_RX.push(
    // 11-10 关名带章号（「第二章第八关」）、拼在关名后面的军务和三星条件
    [/^[一二三四五六七八九十廿卅]{1,3}$/, n => String(cn(n))],   // 关印、波次里单写的数字
    [new RegExp(`^${ST}$`), (m, c, n) => st(c, n)],
    [new RegExp(`^${ST} · (.+)$`), (m, c, n, x) => `${st(c, n)} · ${t(x)}`],
    [new RegExp(`^${ST}打赢一次（掉(.+)）$`), (m, c, n, x) => `${st(c, n)}: win once (drops ${list(x)})`],
    [new RegExp(`^${ST}(.+)$`), (m, c, n, rest) => /、| · |：| 等 \d+ 项$/.test(rest) ? null : `${st(c, n)}: ${t(rest)}`],   // 后面还拼着别的句子的不归这条管
    [new RegExp(`^打${ST}之前晋阶$`), (m, c, n) => `Promote before ${st(c, n)}`],
    [new RegExp(`^打${ST}(.+)之前，最好先备上这个$`), (m, c, n, nm) => `Get this ready before ${st(c, n)}, "${t(nm)}"`],
    [new RegExp(`^(.+?)：打${ST}(.+)之前，最好先备上这个$`), (m, who, c, n, nm) => `${t(who)}: get this ready before ${st(c, n)}, "${t(nm)}"`],
    [new RegExp(`^先打到${ST}$`), (m, c, n) => `Reach ${st(c, n)} first`],
    [new RegExp(`^首通${ST}后加入$`), (m, c, n) => `Joins after ${st(c, n)}`],
    [new RegExp(`^(.+?)：((?:${ST}、?)+)打赢掉（今日 (\\d+)/(\\d+)）$`), (m, a, lvs, c0, n0, g, cap) => `${t(a)}: drops from ${stList(lvs)} (today ${g}/${cap})`],
    [new RegExp(`^第(${NUMS})波$`), (m, n) => `Wave ${cn(n)}`],
    [new RegExp(`^第(${NUMS})波的兵撞掉 (\\d+)$`), (m, w, n) => `Wave ${cn(w)} cost ${n}`],
    [new RegExp(`^· 第(${NUMS})波 (.+)从(左路|中路|右路)冲到城下，撞掉城防 (\\d+)$`), (m, w, foe, l, n) => `· Wave ${cn(w)}: ${t(foe)} via ${t(l).toLowerCase()} hit the wall for ${n}`],
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
    [/^打赢一次（掉(.+)）$/, (m, x) => `win once (drops ${list(x)})`],
    [/^存档码  (.+)$/, (m, c) => `Save code  ${c}`],   // 11-10 系统页云存档
    // 11-10 用户：「接着译完」——关卡目标、战斗横幅、状态条、军帐、备战、沙盘里拼出来的句子
    [/^(斩了敌将|打完所有敌人)，(我方城防（就是你们的血）|城防)不破、(.+)不毁$/, (m, a, w, x) => `${t(a)}; ${lc(t(w))} and ${lcn(t(x))} survive`],
    [/^(我方城防（就是你们的血）|城防)和(.+)都剩一半以上$/, (m, w, x) => `${t(w)} and ${lcn(t(x))} above half`],
    [/^(我方城防（就是你们的血）)都剩一半以上$/, (m, w) => `${t(w)} above half`],
    [/^两星之上，再(.+)$/, (m, x) => `2★ plus ${lc(t(x))}`],
    [/^(.+)保住一半血$/, (m, x) => `keep ${t(x)} above half HP`],
    [/^(.+)保住八成$/, (m, x) => `keep ${lcn(t(x))} above 80%`],
    [/^(.+)（剩 (\d+)%）$/, (m, a, n) => `${t(a)} (now ${n}%)`],
    [/^斩(.+)！溃散 (\d+)$/, (m, x, n) => `${t(x)} slain! ${n} routed`],
    [/^(.+) 加入$/, (m, x) => `${t(x)} joins`],
    [/^(.+)阵亡$/, (m, x) => `${t(x)} has fallen`],
    [/^(.+)被斩$/, (m, x) => `${t(x)} is cut down`],
    [/^(.+)倒下了$/, (m, x) => `${t(x)} is down`],
    [/^(.+)一斧劈倒一片$/, (m, x) => `${t(x)}'s axe fells a swath`],
    [/^又来 (\d+) 个(.+)$/, (m, n, x) => `${n} more: ${t(x)}`],
    [/^(.+?)：小心，(.+?)要用(.+?)——(.+)$/, (m, a, c, k, tell) => `${t(a)}: careful — ${t(c)} will use ${t(k)}: ${t(tell)}`],
    [/^(.+) (\d+) 秒$/, (m, a, n) => `${t(a)} ${n}s`],
    [/^(.+) 好了，快放！$/, (m, xs) => `${list(xs)} ready — cast now!`],
    [/^(.+) · 已有(\d+)$/, (m, a, n) => `${t(a)} · ×${n}`],
    [/^伤害 ([\d.]+[kM]?)$/, (m, x) => `Dmg ${x}`],
    [/^达成功绩：(.+)$/, (m, xs) => `Deeds done: ${list(xs)}`],
    [/^今天(.+)已领满，明天再掉$/, (m, xs) => `${list(xs)} capped today — more tomorrow`],
    [/^今天(.+)已领满$/, (m, xs) => `${list(xs)} capped today`],
    [/^(.+) 等 (\d+) 项$/, (m, a, n) => `${t(a)} +${n - 1} more`],
    [/^出外探访 · 派(.+)$/, (m, x) => `Scouting · send ${t(x)}`],
    [/^晋阶(.+)后可以继续精炼$/, (m, x) => `Promote to ${t(x)} to refine further`],
    [/^(.+) 要 \+(\d+)（现在 \+(\d+)）$/, (m, a, n, h) => `${t(a)} needs +${n} (now +${h})`],
    [/^还差 (.+)$/, (m, xs) => 'Short: ' + xs.split('、').map(p => { const k = /^(.+) (\d+)$/.exec(p); return k ? `${t(k[1])} ${k[2]}` : t(p); }).join(', ')],
    [/^打(.+)之前要先晋阶(.+)$/, (m, a, r) => `Promote to ${t(r)} before "${t(a)}"`],
    [/^友军 · (.+)，每 (\d+) 秒一轮$/, (m, x, n) => `Ally · ${t(x)}, every ${n}s`],
    [/^敌军师 (.+)（(.+) · 智 (\d+)）每局随机用 (\d+) 个计$/, (m, a, ti, z, n) => `Enemy advisor ${t(a)} (${t(ti)} · INT ${z}): ${n} random ploys per battle`],
    [/^计策·(.+?)：(.+)$/, (m, a, b) => `Ploy · ${t(a)}: ${t(b)}`],
    [/^(.+)冲得快：试试带「拒马」让他在城前慢一半，或换个出手顺序让一喝先放$/, (m, x) => `${t(x)} charge fast: try "Barricade" to halve their speed at the wall, or reorder skills so Roar goes first`],
    [/^(.+)成片走到城下：「拒马」让城前的慢一半、多挨几刀，「滚木」碾一路；他举盾挡刀气剑气，矛刺、青龙斩照常$/, (m, x) => `${t(x)} reach the wall in droves: "Barricade" halves their speed there so they take more hits, "Logs" roll down a lane; their shields block blade and sword waves, but spear thrusts and Dragon Slash hit as usual`],
    [/^(.+)漏得最多：换个锦囊或出手顺序再推一遍$/, (m, x) => `${t(x)} get through most: change the pouch or skill order and run again`],
    [/^(左路|中路|右路) 漏 (\d+)$/, (m, l, n) => `${t(l)}: ${n} through`],
    [/^(左路|中路|右路) 没漏$/, (m, l) => `${t(l)}: none`],
    [/^上次在(.+)页面被手机关掉重开（图片约 (\d+)MB）$/, (m, a, n) => `Last time the phone reloaded the page on ${t(a)} (images ~${n}MB)`],
    [/^画布 (\d+) 张约 (\d+)MB · ([\d.]+) 倍(?: · 当时：(.+))?$/, (m, a, b, c, ev) => `${a} canvases ~${b}MB · ${c}×${ev ? ' · then: ' + ev : ''}`],
    [/^[^、，。：；！？（）「」\n]+(?:、[^、，。：；！？（）「」\n]+)+$/, (m) => { const ps = m.split('、'); return ps.every(p => E[p] !== undefined) ? ps.map(p => E[p]).join(', ') : null; }],   // 「甲、乙、丙」：每样都有译名才这样接
    [/^(.+) · (.+)$/, (m, a, b) => `${t(a)} · ${t(b)}`],
    // 11-10 名字后面跟个数（血量、数量、阶数）、名字前后加个记号的：只翻名字
    [/^(第[一二]章) ([^ 、，。：；！？（）「」\n]+)$/, (m, c, x) => `${t(c)} · ${t(x)}`],
    [/^军师 ([^ 、，。：；！？（）「」\n]+)$/, (m, a) => `Advisor ${t(a)}`],
    [/^谋略·([^ 、，。：；！？（）「」\n]+)$/, (m, a) => `Strategy · ${t(a)}`],
    [/^([^ 、，。：；！？（）「」\n]+)被打回来了$/, (m, a) => `${t(a)} beaten back`],
    [/^([^、，。：；！？（）「」\n]+) ▸$/, (m, a) => `${t(a)} ▸`],
    [/^([^ 、，。：；！？（）「」\n]+) ([一二三四五六七八九十]{1,2})$/, (m, a, n) => `${t(a)} ${cn(n)}`],
    [/^([^ 、，。：；！？（）「」\n]+) (×?\d+(?:\/\d+)?)$/, (m, a, n) => `${t(a)} ${n}`],
  );
})();
