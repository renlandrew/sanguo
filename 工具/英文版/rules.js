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
    [/^打赢一次（掉(.+)）$/, (m, x) => `win once (drops ${t(x)})`],
    [/^(.+) · (.+)$/, (m, a, b) => `${t(a)} · ${t(b)}`],
  );
})();
