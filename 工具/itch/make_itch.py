#!/usr/bin/env python3
"""打 itch.io 上传包：python3 工具/itch/make_itch.py [--check]
不动 原型/ 里的任何文件。产物在 outbox/itch/（.gitignore 里已忽略）：build/ 是解开的包，sanguo-itch-<日期>.zip 是要上传的。
做的事（都只在包里）：
  1. 守关.html → index.html：固定为试玩版、来源记 itch、统计和存档码发到正式站、语言跟浏览器、图片不再每次重下
  2. PNG 转有损 WebP（透明通道不压），四张喂给 WebGL 的贴图保持 PNG
  3. 中文文件名改英文
--check 只核对替换点还在不在，不出包。"""
import json, os, re, shutil, subprocess, sys, time, zipfile, hashlib
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, '原型'); OUT = os.path.join(ROOT, 'outbox', 'itch'); BUILD = os.path.join(OUT, 'build'); CACHE = os.path.join(OUT, 'cache')
SKIP = {'守关.html', '动作.html', '墨流试样.html', '墨流.js'}
KEEP_PNG = {'img/fx_matter.png', 'img/fx_noise.png', 'img/fx_atlas.png', 'img/fx_paint.png'}   # 当 WebGL 贴图用，透明处的颜色也要准，不转
API = 'https://jieyunqiudao.com/sanguo/api'; EV_URL = API + '/ev'
Q = 90

# (原文, 换成, 说明)：每条必须在 守关.html 里正好出现一次，否则停下——守关.html 改了这几行就要回来对一下
SUBS = [
    ("const BUST = '?t=' + Date.now();", "const BUST = '';", '图片不再每次打开重下'),
    ("DEMO = QS.has('demo')", 'DEMO = true', '固定试玩版'),
    ("(QS.get('src') || '')", "(QS.get('src') || 'itch')", '来源记 itch'),
    ("const url = location.pathname.replace(/[^/]*$/, '') + 'api/ev', body", f"const url = '{EV_URL}', body", '统计发到正式站'),
    ("new Blob([body], { type: 'application/json' })", "new Blob([body], { type: 'text/plain' })", '跨域不触发预检'),
    ("fetch(url, { method: 'POST', body, headers: { 'Content-Type': 'application/json' }, keepalive: true })", "fetch(url, { method: 'POST', body, mode: 'no-cors', headers: { 'Content-Type': 'text/plain' }, keepalive: true })", '跨域不触发预检'),
    # 11-10 存档码：试玩档（demo）存到正式站的存档服务，和正式版同一套码、各存各的格
    ("const CLOUD_NS = ['proto', 'proto2'];", "const CLOUD_NS = ['demo'];", '存档码管试玩档'),
    ("const CLOUD_API = location.pathname.replace(/[^/]*$/, '') + 'api', CLOUD_KEYS", f"const CLOUD_API = '{API}', CLOUD_KEYS", '存档发到正式站'),
    ("slots: CLOUD_NS })], { type: 'application/json' })", "slots: CLOUD_NS })], { type: 'text/plain' })", '切后台时的存档跨域不触发预检'),
    ("if (/[?&]lang=en\\b/.test(location.search)) document.write(", 'if (window.__en) document.write(', '语言跟浏览器'),
    ("const LANG = /[?&]lang=en\\b/.test(location.search) && window.EN", 'const LANG = window.__en && window.EN', '语言跟浏览器'),
]
RX = [
    (r'<script src="墨流\.js\?v=\d+"></script>', '<script>\n%PRELUDE%</script>\n<script src="moliu.js"></script>', '前置脚本、墨流改名'),
    (r'en\.js\?v=\w+', 'en.js', '英文表不带版本号'),
]

def files():
    """git 里有的，加上没提交但 守关.html 里写着名字的（别的会话放进来、线上也在用的图）"""
    ls = subprocess.run(['git', '-c', 'core.quotepath=false', 'ls-files', '-z', '原型'], cwd=ROOT, capture_output=True, check=True).stdout.decode().split('\0')
    got = {p[len('原型/'):] for p in ls if p}
    html = open(os.path.join(SRC, '守关.html'), encoding='utf-8').read()
    for d, _, fs in os.walk(SRC):
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), SRC)
            if rel not in got and not f.startswith('.') and f in html: got.add(rel); print('  没提交但用到：', rel)
    return sorted(p for p in got if p not in SKIP and os.path.isfile(os.path.join(SRC, p)))

def to_webp(job):
    src, dst = job
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): return os.path.getsize(dst)
    im = Image.open(src); im.load()
    if max(im.size) > 16383: return -1
    if im.mode not in ('RGB', 'RGBA'): im = im.convert('RGBA' if ('A' in im.mode or 'transparency' in im.info) else 'RGB')
    im.save(dst, 'WEBP', quality=Q, method=6, alpha_quality=100, use_sharp_yuv=True)
    return os.path.getsize(dst)

def html_out(name_map):
    s = open(os.path.join(SRC, '守关.html'), encoding='utf-8').read()
    for a, b, why in SUBS:
        n = s.count(a)
        if n != 1: sys.exit(f'✗ 替换点「{why}」在 守关.html 里出现 {n} 次（要正好 1 次）：{a[:70]}')
        s = s.replace(a, b)
    pre = open(os.path.join(HERE, 'prelude.js'), encoding='utf-8').read()
    if pre.count('/*MAP*/{}') != 1: sys.exit('✗ prelude.js 里找不到 /*MAP*/{}')
    pre = pre.replace('/*MAP*/{}', json.dumps(name_map, ensure_ascii=False, separators=(',', ':')))
    for rx, b, why in RX:
        s, n = re.subn(rx, lambda m: b.replace('%PRELUDE%', pre), s)
        if n != 1: sys.exit(f'✗ 替换点「{why}」匹配到 {n} 处（要正好 1 处）')
    return s

def main():
    if '--check' in sys.argv: html_out({}); print('✓ 替换点都在'); return
    t0 = time.time(); fl = files(); os.makedirs(CACHE, exist_ok=True)
    if os.path.isdir(BUILD): shutil.rmtree(BUILD)
    taken = set(fl); name_map = {}; jobs = []; plan = []   # plan: (包里的名字, 来源文件)
    n_cn = 0
    for rel in fl:
        out = rel
        if not out.isascii():
            n_cn += 1; d, f = os.path.split(out); stem, ext = os.path.splitext(f)
            pre = re.match(r'[A-Za-z0-9_]*', stem).group(0)
            out = os.path.join(d, f'{pre}c{n_cn}{ext}')
            assert out not in taken, out
        src = os.path.join(SRC, rel)
        if rel.lower().endswith('.png') and rel not in KEEP_PNG:
            w = out[:-4] + '.webp'
            if w in taken: w = out[:-4] + '_p.webp'
            assert w not in taken, w
            taken.add(w)
            c = os.path.join(CACHE, hashlib.md5(rel.encode()).hexdigest()[:16] + f'_q{Q}.webp'); jobs.append((src, c)); plan.append([out, src, w, c, rel])
        else:
            plan.append([out, src, None, None, rel])
    with ProcessPoolExecutor() as ex: sizes = dict(zip([j[1] for j in jobs], ex.map(to_webp, jobs, chunksize=4)))
    total = 0; n_webp = 0; png_before = png_after = 0
    for out, src, w, c, rel in plan:
        if w and 0 < sizes[c] < os.path.getsize(src): dst, frm = w, c; n_webp += 1; png_before += os.path.getsize(src); png_after += sizes[c]
        else: dst, frm = out, src
        if dst != rel: name_map[rel] = dst
        p = os.path.join(BUILD, dst); os.makedirs(os.path.dirname(p), exist_ok=True); shutil.copyfile(frm, p); total += os.path.getsize(p)
    shutil.copyfile(os.path.join(SRC, '墨流.js'), os.path.join(BUILD, 'moliu.js'))
    open(os.path.join(BUILD, 'index.html'), 'w', encoding='utf-8').write(html_out(name_map))
    names = [os.path.relpath(os.path.join(d, f), BUILD) for d, _, fs in os.walk(BUILD) for f in fs]
    bad = [n for n in names if not n.isascii()]; assert not bad, bad
    z = os.path.join(OUT, 'sanguo-itch-' + time.strftime('%Y%m%d') + '.zip')
    if os.path.exists(z): os.remove(z)
    with zipfile.ZipFile(z, 'w') as zf:
        for n in sorted(names): zf.write(os.path.join(BUILD, n), n, zipfile.ZIP_DEFLATED if n.endswith(('.html', '.js', '.json')) else zipfile.ZIP_STORED)
    tot = sum(os.path.getsize(os.path.join(BUILD, n)) for n in names)
    print(f'✓ {len(names)} 个文件，解开 {tot/1e6:.1f} MB，压缩包 {os.path.getsize(z)/1e6:.1f} MB，用时 {time.time()-t0:.0f} 秒')
    print(f'  PNG 转 WebP {n_webp} 张：{png_before/1e6:.1f} → {png_after/1e6:.1f} MB；改名 {len(name_map)} 个（其中中文名 {n_cn} 个）')
    print(f'  最大的单个文件 {max(os.path.getsize(os.path.join(BUILD, n)) for n in names)/1e6:.1f} MB')
    print('  ' + z)

if __name__ == '__main__': main()
