// itch.io 版的前置脚本（make_itch.py 原样塞进 index.html，排在所有脚本前面）。只管三件事：存档、语言、图名。
(() => {
  // 一、存档：itch 把游戏放在别的域名的框里，浏览器关了第三方存储时一碰 localStorage 就报错——换成只在这次打开期间有效的内存存档，游戏照常能玩（进度靠存档码存到服务器）
  let ok = false; try { const k = 'sgz.__probe'; localStorage.setItem(k, '1'); localStorage.removeItem(k); ok = true; } catch (e) {}
  if (!ok) {
    const mem = {}, def = (k, v) => Object.defineProperty(mem, k, { value: v });   // 方法不可枚举：Object.keys(localStorage) 只数到存的东西
    // 11-10 同时记在 window.name 里：这个框自己刷新（输存档码之后要重进游戏）时还在；关掉页面就没了，下次来靠存档码
    const TAG = 'sgzmem:', keep = () => { try { window.name = TAG + JSON.stringify(mem); } catch (e) {} };
    try { if (String(window.name).startsWith(TAG)) { const o = JSON.parse(window.name.slice(TAG.length)); for (const k of Object.keys(o)) if (typeof o[k] === 'string') mem[k] = o[k]; } } catch (e) {}
    def('getItem', k => Object.prototype.hasOwnProperty.call(mem, k) ? mem[k] : null); def('setItem', (k, v) => { mem[k] = String(v); keep(); });
    def('removeItem', k => { delete mem[k]; keep(); }); def('clear', () => { for (const k of Object.keys(mem)) delete mem[k]; keep(); }); def('key', i => Object.keys(mem)[i] ?? null);
    Object.defineProperty(mem, 'length', { get: () => Object.keys(mem).length });
    try { Object.defineProperty(window, 'localStorage', { configurable: true, get: () => mem }); } catch (e) {}
    window.__memSave = true;
  }
  // 二、语言：itch 的框不带网址参数。浏览器是中文就中文，其余英文；?lang=zh / ?lang=en 可以强制（本机核对用）
  const q = /[?&]lang=(en|zh)\b/.exec(location.search);
  window.__en = q ? q[1] === 'en' : !/^zh\b/i.test(navigator.language || '');
  if (window.__en) document.documentElement.lang = 'en';
  // 三、图名：包里的 PNG 转成了 WebP，中文文件名改成了英文（有的压缩包工具和服务器不认中文名）。游戏里还是原来的名字，在这里换成包里的
  const MAP = /*MAP*/{};
  const d = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
  const fix = u => { if (typeof u !== 'string') return u; let p = u.replace(/[?#].*$/, ''); try { p = decodeURIComponent(p); } catch (e) {} return MAP[p] || p; };
  Object.defineProperty(HTMLImageElement.prototype, 'src', { configurable: true, enumerable: d.enumerable, get: d.get, set(u) { d.set.call(this, fix(u)); } });
})();
