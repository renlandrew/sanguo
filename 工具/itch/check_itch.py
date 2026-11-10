#!/usr/bin/env python3
"""核对 itch 包：python3 工具/itch/check_itch.py [地址，默认 http://127.0.0.1:8791/]  [截图目录]
先起一个本机服务指到 outbox/itch/build（例：cd outbox/itch && python3 -m http.server 8791 -d build --bind 127.0.0.1）。
统计请求一律在浏览器里截住、不发到正式站；存档请求一条也不许到正式站（戊项另起一个本机的存档服务来试）。查五件事：
  甲 第一次打开：多少请求、多少 MB、几秒到主页；开打第一关再加多少；统计发的是什么
  乙 英文、十关全开，把各页和前十关都走一遍：有没有读不到的文件、有没有报错
  丙 放进别的域名的框里、并且 localStorage 一碰就报错：还能不能玩
  丁 第二次打开：有多少走了缓存
  戊 存档码：本机起一份 server/sanguo_save.py（临时库），包里的存档地址换成它，真的跨域走一遍——
     打赢前不建档 → 打赢一关后领到码并上传 → 另一台「设备」（别的域名的框里、localStorage 报错）输错码、输对码接上进度 → 再打一关能传上去"""
import json, sys, time, os, re, socket, subprocess, tempfile, urllib.request
from playwright.sync_api import sync_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8791/'
SHOT = sys.argv[2] if len(sys.argv) > 2 else None
fails = []
ONLY = os.environ.get('ONLY', '')   # 只跑几项：ONLY=戊 python3 …
PROD = 'https://jieyunqiudao.com/sanguo/api'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def watch(pg, tag):
    st = {'recs': [], 'bad': [], 'errs': [], 'ev': [], 'cached': 0, 'prod': [], 'gone': []}
    def ev(route):
        r = route.request
        if '/api/ev' not in r.url: st['prod'].append(r.method + ' ' + r.url); return route.abort()   # 存档请求不许到正式站
        st['ev'].append({'url': r.url, 'method': r.method, 'ct': r.headers.get('content-type'), 'body': r.post_data}); route.fulfill(status=204, body='')
    pg.route('https://jieyunqiudao.com/**', ev)
    def on(resp):
        if '/api/ev' in resp.url: return
        try: n = int(resp.headers.get('content-length') or 0) or len(resp.body())
        except Exception: n = 0
        if resp.status == 304 or resp.from_service_worker: n = 0
        st['recs'].append((time.time(), n, resp.url)); 
        if resp.status >= 400: st['bad'].append(f'{resp.status} {resp.url}')
    pg.on('response', on)
    # 游戏会把暂时用不到的图放掉（relImg 去掉 src），正在下的那次请求就记成 ERR_ABORTED；这种另外记，报告时再取一遍确认文件在
    pg.on('requestfailed', lambda r: 'jieyunqiudao.com' in r.url or (st['gone'] if 'ERR_ABORTED' in str(r.failure) else st['bad']).append(r.url if 'ERR_ABORTED' in str(r.failure) else f'失败 {r.url} {r.failure}'))
    pg.on('pageerror', lambda e: st['errs'].append(str(e)[:300]))
    pg.on('console', lambda m: m.type == 'error' and st['errs'].append('console: ' + m.text[:300]))
    return st
def settle(pg, st, quiet=1.5, most=60):
    t0 = time.time()
    while time.time() - t0 < most:
        pg.wait_for_timeout(300)
        if st['recs'] and time.time() - st['recs'][-1][0] > quiet and pg.evaluate("() => !!(window.__sg && __sg.screen)"): break
    return time.time() - t0
mb = lambda st, a=0, b=None: sum(r[1] for r in st['recs'][a:b]) / 1e6
def shot(pg, name):
    if SHOT: os.makedirs(SHOT, exist_ok=True); pg.screenshot(path=os.path.join(SHOT, name + '.png'))
def report(tag, st):
    for u in dict.fromkeys(st['gone']):   # 下到一半被放掉的：文件本身取得到就不算读不到
        try: ok = urllib.request.urlopen(u, timeout=10).status == 200
        except Exception: ok = False
        if ok: print('  （下到一半被游戏放掉、文件取得到：' + u.rsplit('/', 1)[-1] + '）')
        else: st['bad'].append('中断且取不到 ' + u)
    if st['bad']: fails.append(tag + ' 读不到文件'); print('  ✗ 读不到：', *st['bad'][:20], sep='\n    ')
    if st['errs']: fails.append(tag + ' 页面报错'); print('  ✗ 报错：', *st['errs'][:20], sep='\n    ')
    if st['prod']: fails.append(tag + ' 有存档请求发往正式站'); print('  ✗ 发往正式站的存档请求（已截住）：', *st['prod'][:10], sep='\n    ')
    if not st['bad'] and not st['errs']: print('  ✓ 没有读不到的文件，没有报错')

with sync_playwright() as p:
    br = p.chromium.launch(channel='chrome', headless=True)
    if not ONLY or '甲' in ONLY:
        # 甲、丁
        print('甲 第一次打开（中文浏览器）')
        cx = br.new_context(viewport={'width': 360, 'height': 640}, device_scale_factor=2, locale='zh-CN'); pg = cx.new_page(); st = watch(pg, '甲')
        t0 = time.time(); pg.goto(BASE); t = settle(pg, st); n1 = len(st['recs'])
        print(f'  到主页 {time.time()-t0-1.5:.1f} 秒（本机），{n1} 个请求，{mb(st):.1f} MB；画面 {pg.evaluate("() => __sg.screen")}')
        pg.wait_for_timeout(1500); shot(pg, 'a_menu_zh')
        big = sorted(st['recs'], key=lambda r: -r[1])[:8]; print('  最大的：', ', '.join(f"{r[2].split('/')[-1]} {r[1]/1e6:.2f}" for r in big))
        pg.evaluate("() => { __sg.start(0); }"); pg.wait_for_timeout(9000); shot(pg, 'a_stage1_zh')
        print(f'  开打第一关 9 秒后：共 {len(st["recs"])} 个请求，{mb(st):.1f} MB（新增 {mb(st, n1):.1f} MB）；画面 {pg.evaluate("() => __sg.screen")}')
        print('  统计：', json.dumps(st['ev'], ensure_ascii=False)[:600])
        e0 = st['ev'][0] if st['ev'] else None
        if not e0 or not e0['url'].startswith('https://jieyunqiudao.com/sanguo/api/ev') or 'text/plain' not in (e0['ct'] or '') or '"src":"itch"' not in (e0['body'] or '') or '"lang":"zh"' not in e0['body']: fails.append('甲 统计格式不对')
        report('甲', st)
        print('丁 第二次打开（同一个浏览器）')
        pg2 = cx.new_page(); st2 = watch(pg2, '丁'); pg2.goto(BASE); settle(pg2, st2)
        net = pg2.evaluate("() => performance.getEntriesByType('resource').filter(e => e.transferSize > 0).reduce((s, e) => s + e.transferSize, 0)")
        allb = pg2.evaluate("() => performance.getEntriesByType('resource').length")
        print(f'  {allb} 个资源，实际走网络 {net/1e6:.2f} MB（本机服务没有长缓存头，itch 上以实测为准）'); report('丁', st2); cx.close()
    if not ONLY or '乙' in ONLY:
        # 乙
        print('乙 英文浏览器，十关全开，各页和前十关走一遍')
        cx = br.new_context(viewport={'width': 360, 'height': 640}, device_scale_factor=2, locale='en-US'); pg = cx.new_page(); st = watch(pg, '乙')
        pg.goto(BASE + '?all&save=titch'); settle(pg, st)
        print('  语言：', pg.evaluate("() => ({ en: window.__en, EN: !!window.EN, lang: document.documentElement.lang })"))
        if not pg.evaluate("() => window.__en && !!window.EN"): fails.append('乙 英文没开')
        pg.wait_for_timeout(1200); shot(pg, 'b_menu_en')
        for s in ('levels', 'roster', 'camp', 'armory', 'system', 'ach', 'storylist', 'menu'):
            pg.evaluate("s => { try { __sg.screen = s; __sg.draw(); } catch (e) { console.error('screen ' + s + ' ' + e); } }", s); pg.wait_for_timeout(700); pg.evaluate("() => __sg.draw()"); shot(pg, 'b_' + s + '_en')
        for i in range(10):
            r = pg.evaluate("""i => { __sg.seed = 7; __sg.auto = true; __sg.start(i); const G = __sg.G; let k = 0, d = 0;
                while (k++ < 22000 && __sg.G === G && __sg.screen === 'play' && G.state !== 'over') { __sg.step(1); G.teach = null; if (k % 6 === 0) { __sg.draw(); d++; } }
                __sg.draw(); return { st: __sg.G && __sg.G.state, t: __sg.G && Math.round(__sg.G.t), k, scr: __sg.screen }; }""", i)
            pg.wait_for_timeout(1500); pg.evaluate("() => __sg.draw()"); shot(pg, f'b_stage{i+1}_en'); print(f'  第 {i+1} 关', r)
        pg.wait_for_timeout(1500)
        print(f'  共 {len(st["recs"])} 个请求，{mb(st):.1f} MB'); report('乙', st); cx.close()
    if not ONLY or '丙' in ONLY:
        # 丙
        print('丙 别的域名的框里，localStorage 报错')
        cx = br.new_context(viewport={'width': 500, 'height': 800}, locale='en-US'); pg = cx.new_page(); st = watch(pg, '丙')
        cx.add_init_script("if (window.top !== window) Object.defineProperty(window, 'localStorage', { configurable: true, get() { throw new DOMException('denied', 'SecurityError'); } });")
        import http.server, threading   # 外面那页要真从本机另一个地址发出来（浏览器不让公网页面嵌本机地址）
        class Wrap(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = f'<body style="margin:0;background:#333"><iframe src="{BASE}" width="405" height="720" style="border:0;margin:20px" allowfullscreen></iframe></body>'.encode()
                self.send_response(200); self.send_header('Content-Type', 'text/html'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
            def log_message(self, *a): pass
        ws = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Wrap); threading.Thread(target=ws.serve_forever, daemon=True).start()
        host = 'localhost' if '127.0.0.1' in BASE else '127.0.0.1'
        pg.goto(f'http://{host}:{ws.server_address[1]}/'); fr = pg.frames[1]; t0 = time.time()
        while time.time() - t0 < 60:
            pg.wait_for_timeout(400)
            try:
                if fr.evaluate("() => !!(window.__sg && __sg.screen)") and st['recs'] and time.time() - st['recs'][-1][0] > 1.5: break
            except Exception: pass
        info = fr.evaluate("() => { let thrown = false; try { localStorage.setItem('sgz.t', '1'); } catch (e) { thrown = true; } return { mem: !!window.__memSave, thrown, back: localStorage.getItem('sgz.t'), keys: Object.keys(localStorage).length, scr: __sg.screen, cw: document.getElementById('cv').clientWidth, ch: document.getElementById('cv').clientHeight }; }")
        print('  ', info)
        if not info['mem'] or info['thrown'] or info['back'] != '1': fails.append('丙 内存存档没接上')
        fr.evaluate("() => { __sg.start(0); }"); pg.wait_for_timeout(6000); shot(pg, 'c_iframe')
        print('  统计：', json.dumps(st['ev'], ensure_ascii=False)[:300]); report('丙', st); cx.close()
    if not ONLY or '戊' in ONLY:
        # 戊
        print('戊 存档码（本机临时存档服务，真跨域）')
        so = socket.socket(); so.bind(('127.0.0.1', 0)); port = so.getsockname()[1]; so.close()
        state = tempfile.mkdtemp(prefix='sgsave_'); logf = open(os.path.join(state, 'log.txt'), 'w')
        srv = subprocess.Popen([sys.executable, os.path.join(ROOT, 'server', 'sanguo_save.py'), 'serve', '--port', str(port), '--state', state], stdout=logf, stderr=subprocess.STDOUT)
        api = f'http://127.0.0.1:{port}'   # 和游戏那页端口不同＝不同源
        for _ in range(50):
            try: urllib.request.urlopen(api + '/ping', timeout=1); break
            except Exception: time.sleep(0.1)
        import http.server as hs, threading as th
        class Proxy(hs.BaseHTTPRequestHandler):   # 转发 BASE；首页里正式站的地址（存档、统计）换成本机这份存档服务。这一项浏览器里不设拦截，跨域预检是真的
            def do_GET(self):
                if self.path == '/favicon.ico': self.send_response(204); self.end_headers(); return
                if self.path.startswith('/__frame'): body = f'<body style="margin:0;background:#333"><iframe src="http://127.0.0.1:{self.server.server_address[1]}/" width="405" height="720" style="border:0;margin:20px" allowfullscreen></iframe></body>'.encode(); ct = 'text/html'; code = 200
                else:
                    try: r = urllib.request.urlopen(BASE.rstrip('/') + self.path, timeout=20); body = r.read(); ct = r.headers.get('Content-Type') or 'application/octet-stream'; code = 200
                    except urllib.error.HTTPError as e: body = b''; ct = 'text/plain'; code = e.code
                    if self.path.split('?')[0] == '/':
                        t = body.decode(); n = t.count(PROD); t = t.replace(PROD, api); body = t.encode()
                        if n != 2 or 'jieyunqiudao' in t: fails.append(f'戊 首页里正式站地址 {n} 处（该是存档、统计各一处）'); body = b'stop'
                self.send_response(code); self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
            def log_message(self, *a): pass
        px = hs.ThreadingHTTPServer(('127.0.0.1', 0), Proxy); th.Thread(target=px.serve_forever, daemon=True).start(); PB = f'http://127.0.0.1:{px.server_address[1]}/'
        def watch2(pg):   # 不拦截，只记
            st = {'bad': [], 'errs': [], 'prod': [], 'calls': [], 'gone': []}
            pg.on('request', lambda r: st['prod'].append(r.url) if 'jieyunqiudao' in r.url else r.url.startswith(api) and not r.url.endswith('/ev') and st['calls'].append(r.method + ' ' + r.url[len(api):]))
            pg.on('response', lambda r: r.status >= 400 and not r.url.startswith(api) and st['bad'].append(f'{r.status} {r.url}'))
            pg.on('requestfailed', lambda r: st['gone'].append(r.url) if 'ERR_ABORTED' in str(r.failure) and not r.url.startswith(api) else st['bad'].append(f'失败 {r.url} {r.failure}'))   # 存档请求中断照样算失败
            pg.on('pageerror', lambda e: st['errs'].append(str(e)[:300])); pg.on('console', lambda m: m.type == 'error' and not (m.location or {}).get('url', '').startswith(api + '/claim') and st['errs'].append('console: ' + m.text[:300] + ' ' + (m.location or {}).get('url', '')))
            return st
        def ready(fr, most=60):
            t0 = time.time()
            while time.time() - t0 < most:
                pg.wait_for_timeout(400)
                try:
                    if fr.evaluate("() => !!(window.__sg && __sg.screen)"): return True
                except Exception: pass
            return False
        def win(fr, i=0, seed=7):
            return fr.evaluate("""([i, seed]) => { __sg.seed = seed; __sg.auto = true; __sg.start(i); const G = __sg.G; let k = 0;
                while (k++ < 22000 && __sg.G === G && G.state !== 'over') { __sg.step(1); G.teach = null; }
                __sg.auto = false; __sg.draw(); return !!(G.result && G.result.win); }""", [i, seed])
        def synced(fr, most=15):
            t0 = time.time()
            while time.time() - t0 < most:
                pg.wait_for_timeout(500)
                if fr.evaluate("() => (m => !!(m && m.code && !m.dirty && m.rev > 0))(__sg.cloud.me)"): return True
            return False
        def sysshot(fr, name):
            fr.evaluate("() => { __sg.screen = 'system'; __sg.draw(); }"); pg.wait_for_timeout(500); fr.evaluate("() => __sg.draw()"); shot(pg, name)
        try:
            # 第一台：普通打开，中文
            cx = br.new_context(viewport={'width': 360, 'height': 640}, device_scale_factor=2, locale='zh-CN'); pg = cx.new_page(); st = watch2(pg); calls = st['calls']
            pg.goto(PB); ready(pg); pg.wait_for_timeout(1500)
            a0 = pg.evaluate("() => (c => ({ on: c.on, st: c.st, me: !!c.me, ns: c.ns, api: c.api, framed: c.framed }))(__sg.cloud)"); print('  打赢前：', a0, '请求', calls)
            if not a0['on'] or a0['st'] != 'idle' or a0['me'] or calls or a0['ns'] != ['demo']: fails.append('戊 打赢前就建档了，或者存档码没开')
            sysshot(pg, 'e1_system_idle_zh')
            w = win(pg); ok = synced(pg); a1 = pg.evaluate("() => ({ st: __sg.cloud.st, code: __sg.cloud.me && __sg.cloud.me.code, rev: __sg.cloud.me && __sg.cloud.me.rev, stars: localStorage.getItem('sgz.demo.stars') })")
            print('  打赢第一关：', w, '；传上去：', ok, {**a1, 'code': bool(a1['code'])}, '请求', calls)
            if not w or not ok or not a1['code']: fails.append('戊 打赢后没领到码或没传上去')
            sysshot(pg, 'e2_system_code_zh'); code = a1['code'] or ''
            if not a1['code']: raise RuntimeError('没领到码，后面不用试了：' + json.dumps(st, ensure_ascii=False)[:600])
            tok = pg.evaluate("() => __sg.cloud.me && __sg.cloud.me.token")
            got = json.load(urllib.request.urlopen(urllib.request.Request(api + '/save', headers={'Authorization': 'Bearer ' + (tok or '')})))
            print('  服务器上这份存档的格：', sorted(got.get('data', {})))
            if not got.get('data') or any(not k.startswith('sgz.demo.') for k in got['data']): fails.append('戊 服务器上存的不只是试玩档')
            report('戊 第一台', st); cx.close()
            # 第二台：别的域名的框里，localStorage 报错，英文
            cx = br.new_context(viewport={'width': 500, 'height': 800}, locale='en-US'); pg = cx.new_page(); st = watch2(pg)
            cx.add_init_script("if (window.top !== window) Object.defineProperty(window, 'localStorage', { configurable: true, get() { throw new DOMException('denied', 'SecurityError'); } });")
            pg.goto(f'http://localhost:{px.server_address[1]}/__frame'); fr = pg.frames[1]; ready(fr); pg.wait_for_timeout(1500)
            b0 = fr.evaluate("() => ({ mem: !!window.__memSave, framed: __sg.cloud.framed, st: __sg.cloud.st, stars: localStorage.getItem('sgz.demo.stars') })"); print('  第二台打开：', b0)
            sysshot(fr, 'e3_system_idle_en_frame')
            dialogs = []; pg.on('dialog', lambda d: (dialogs.append(d.type), d.dismiss()))
            fr.evaluate("() => { __sg.cloud.claim(); }"); box = fr.locator('#cloudbox'); box.wait_for(timeout=3000); shot(pg, 'e4_claim_box_en')
            box.locator('input').fill('aaa-aaa-aaa'); box.locator('button').nth(1).click(); pg.wait_for_timeout(1200)
            bad = box.locator('div div').nth(1).inner_text(); print('  输错码：', repr(bad)); shot(pg, 'e5_claim_wrong_en')
            if not bad or re.search('[\u4e00-\u9fff]', bad): fails.append('戊 输错码的提示不对（空的或者还是中文）')
            box.locator('input').fill(code.lower()); box.locator('button').nth(1).click(); pg.wait_for_timeout(1500); ready(fr); pg.wait_for_timeout(1500)
            b1 = fr.evaluate("() => ({ mem: !!window.__memSave, st: __sg.cloud.st, same: __sg.cloud.me && __sg.cloud.me.code, rev: __sg.cloud.me && __sg.cloud.me.rev, stars: localStorage.getItem('sgz.demo.stars'), box: !!document.getElementById('cloudbox') })")
            print('  输对码、重进之后：', {**b1, 'same': b1['same'] == code}, '弹过的系统对话框：', dialogs)
            if b1['same'] != code or b1['stars'] != a1['stars'] or not b1['stars'] or dialogs: fails.append('戊 第二台没接上第一台的进度')
            sysshot(fr, 'e6_system_code_en_frame')
            fr.evaluate("() => { __sg.cloud.copy(); }"); box.wait_for(timeout=3000); box.locator('button').nth(1).click(); pg.wait_for_timeout(300)
            print('  复制小窗：', repr(box.locator('input').input_value() == code), repr(box.locator('div div').nth(1).inner_text())); shot(pg, 'e7_copy_box_en'); box.locator('button').nth(0).click()
            rev0 = b1['rev'] or 0; w = win(fr); t0 = time.time()
            while time.time() - t0 < 15 and not fr.evaluate("r => (m => !!(m && !m.dirty && m.rev > r))(__sg.cloud.me)", rev0): pg.wait_for_timeout(500)
            b2 = fr.evaluate("() => ({ st: __sg.cloud.st, rev: __sg.cloud.me.rev, dirty: __sg.cloud.me.dirty })"); print('  第二台再打赢一关：', w, b2)
            if not w or b2['dirty'] or b2['rev'] <= rev0: fails.append('戊 第二台打赢后没传上去')
            fr.evaluate("() => { __sg.cloud.me.dirty = true; Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' }); document.dispatchEvent(new Event('visibilitychange', { bubbles: true })); }"); pg.wait_for_timeout(1500)
            report('戊 第二台', st); cx.close()
        finally:
            srv.terminate(); srv.wait(); logf.close(); log = open(os.path.join(state, 'log.txt')).read()
            lines = [' '.join(l.split()[-3:]) for l in log.splitlines() if re.search(r'(OPTIONS|GET|POST|PUT) /', l)]
            print('  存档服务收到的：', '，'.join(lines))
            if st.get('prod'): fails.append('戊 有请求发往正式站')
            if not any(l.startswith('OPTIONS /save') for l in lines): fails.append('戊 没看到跨域预检')
            if 'POST /save 200' not in lines: fails.append('戊 切后台时的那次存档没收到')
    br.close()
print('结果：', '✓ 都过了' if not fails else '✗ ' + '；'.join(fails)); sys.exit(1 if fails else 0)
