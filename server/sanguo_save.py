#!/usr/bin/env python3
"""三国志守关 · 云存档（10-30，用户：「不是接了ec2吗，你做一个数据库啊，如同劫云」）。照劫云问道的 jieyun_save.py 做的独立一份：
自己的端口（8094）、自己的库（/var/lib/sanguo-save），和劫云互不相干。只用 Python 标准库和 SQLite。

比劫云多两件事（防改浏览器存档作弊）：
  1. 回复里带服务器时间 now 和建档以来第几天 day；游戏的「第几天」、体力恢复都按服务器时间算，改手机时间没用。
  2. 存档合理性检查（plausible）：按建档至今的天数，算官阶、兵器、各种材料最多可能到多少（放宽到正常最快的约一倍半）；
     超出就拒收（409），保留上一份正常存档；管理员存档不查（开发测试用）。

以下是劫云原来的说明：

玩家不注册：第一次打开，服务器发给这台设备一个凭证（长随机串，存在浏览器里）和一个存档码（9 位，显示成 XXX-XXX-XXX）；
进度自动存上来；换手机、换浏览器时输入存档码「认领」这份存档，新设备拿到自己的凭证，几台设备共用一份存档。
冲突：后存的为准（用户 10-25 定），每份存档留最近 30 个版本，误盖了能从服务器上找回。

数据库只存凭证和存档码的摘要（存档码加了服务器自己的盐），泄露了也不能拿去登录；不存 IP、名字、手机号。
存档码连错 5 次，这个 IP 锁 10 分钟（只在内存里计数）。

用法：
  python3 sanguo_save.py serve  --host 127.0.0.1 --port 8093 --state /var/lib/jieyun-save
  python3 sanguo_save.py stats  --state /var/lib/jieyun-save               多少份存档、今天、这周有多少人玩
  python3 sanguo_save.py backup --state /var/lib/jieyun-save --to /var/backups/jieyun-save --keep 14
  python3 sanguo_save.py history --state … --code XXX-XXX-XXX            看某份存档的历史版本（找回用）
  python3 sanguo_save.py admin   --state … --code XXX-XXX-XXX [--off]    把这份存档设成管理员（游戏里才有「换形象」），--off 取消
接口（nginx 把 /jieyun/api/ 转过来，前缀去掉；请求、回复都是 JSON）：
  POST /hello   {}                      → {token, code, rev: 0}              第一次打开
  GET  /save    Authorization: Bearer t → {rev, at, data}                    取最新
  PUT  /save    {data, at}              → {rev}                              存（后存的为准）
  POST /save    {token, data, at}       → {rev}                              同上，给切后台时的 sendBeacon（带不了头）
  POST /claim   {code}                  → {token, code, rev, at, data}       另一台设备认领
  POST /rotate  Authorization           → {code}                             换一个存档码（旧的作废）
跨域（10-25 用户同意）：英文版在 itch.io（*.itch.zone）上，直接调 https://theubai.cn/jieyun/api/，和中文网页版共用一个库；
本机调试的 localhost / 127.0.0.1 也放行。不带 cookie，凭证都在请求里，别的网站拿不到玩家的凭证。
"""
import argparse, datetime, glob, hashlib, hmac, json, os, re, secrets, socketserver, sqlite3, sys, threading, time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

ALPHA = '23456789ABCDEFGHJKMNPQRSTVWXYZ'          # 去掉 0 O 1 I L U，抄的时候不会认错；9 位约 2×10^13 种
KEY_OK = re.compile(r'^sgz\.(proto|proto2)\.(stars|roster|inv|daily)$')   # 只收正式存档的四个键（测试档 ?save= 不上云）
MAX_BODY = 192 * 1024
KEEP_HISTORY = 30
LOCK_FAILS, LOCK_SECS = 5, 600
HELLO_PER_HOUR = 40
CORS_OK = re.compile(r'^http://(localhost|127\.0\.0\.1)(:\d{1,5})?$')   # 正式站同源不用跨域；只放本机调试


class Store:
    def __init__(self, state):
        os.makedirs(state, exist_ok=True)
        pep = os.path.join(state, 'pepper')
        if not os.path.exists(pep):
            with open(pep, 'w') as f: f.write(secrets.token_hex(32))
            os.chmod(pep, 0o600)
        self.pepper = open(pep).read().strip().encode()
        self.db = sqlite3.connect(os.path.join(state, 'saves.sqlite'), check_same_thread=False, isolation_level=None)
        self.lock = threading.Lock()
        with self.lock:
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.executescript('''
              CREATE TABLE IF NOT EXISTS saves(id INTEGER PRIMARY KEY, code_hash TEXT UNIQUE NOT NULL, rev INTEGER NOT NULL DEFAULT 0,
                data TEXT NOT NULL DEFAULT '{}', at REAL NOT NULL DEFAULT 0, created REAL NOT NULL, updated REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS devices(token_hash TEXT PRIMARY KEY, save_id INTEGER NOT NULL, created REAL NOT NULL, seen REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS history(save_id INTEGER NOT NULL, rev INTEGER NOT NULL, data TEXT NOT NULL, at REAL NOT NULL, saved REAL NOT NULL,
                PRIMARY KEY(save_id, rev));
              CREATE INDEX IF NOT EXISTS devices_save ON devices(save_id);
              CREATE TABLE IF NOT EXISTS admins(save_id INTEGER PRIMARY KEY, since REAL NOT NULL);''')   # 10-25：管理员存档（按存档编号记，换存档码也还是管理员）

    @staticmethod
    def thash(token): return hashlib.sha256(token.encode()).hexdigest()
    def chash(self, code): return hmac.new(self.pepper, code.encode(), hashlib.sha256).hexdigest()
    @staticmethod
    def new_code(): return ''.join(secrets.choice(ALPHA) for _ in range(9))
    @staticmethod
    def norm_code(s):
        s = re.sub(r'[\s\-_]', '', str(s or '')).upper()
        return s if len(s) == 9 and all(c in ALPHA for c in s) else None
    @staticmethod
    def show(code): return code[:3] + '-' + code[3:6] + '-' + code[6:]

    def _new_device(self, save_id, now):
        token = secrets.token_urlsafe(32)
        self.db.execute('INSERT INTO devices(token_hash, save_id, created, seen) VALUES(?,?,?,?)', (self.thash(token), save_id, now, now))
        return token

    def hello(self):
        now = time.time()
        with self.lock:
            for _ in range(5):
                code = self.new_code()
                try: cur = self.db.execute('INSERT INTO saves(code_hash, created, updated) VALUES(?,?,?)', (self.chash(code), now, now)); break
                except sqlite3.IntegrityError: continue
            else: raise RuntimeError('存档码撞了五次')
            token = self._new_device(cur.lastrowid, now)
        return {'token': token, 'code': self.show(code), 'rev': 0, 'now': now * 1000, 'day': 1}

    def is_admin(self, sid): return self.db.execute('SELECT 1 FROM admins WHERE save_id=?', (sid,)).fetchone() is not None

    def _save_of(self, token):
        if not token: return None
        r = self.db.execute('SELECT save_id FROM devices WHERE token_hash=?', (self.thash(token),)).fetchone()
        if r: self.db.execute('UPDATE devices SET seen=? WHERE token_hash=?', (time.time(), self.thash(token)))
        return r[0] if r else None

    def days_of(self, sid):
        c = self.db.execute('SELECT created FROM saves WHERE id=?', (sid,)).fetchone()[0]
        return int((time.time() - c) // 86400) + 1          # 建档当天算第 1 天

    def get(self, token):
        with self.lock:
            sid = self._save_of(token)
            if sid is None: return None
            rev, data, at = self.db.execute('SELECT rev, data, at FROM saves WHERE id=?', (sid,)).fetchone()
            admin = self.is_admin(sid); day = self.days_of(sid)
        r = {'rev': rev, 'at': at, 'data': json.loads(data), 'now': time.time() * 1000, 'day': day}
        if admin: r['admin'] = True              # 只有管理员存档才带这一项
        return r

    def put(self, token, data, at):
        now = time.time()
        with self.lock:
            sid = self._save_of(token)
            if sid is None: return None
            if not self.is_admin(sid):
                cur_rev = self.db.execute('SELECT rev FROM saves WHERE id=?', (sid,)).fetchone()[0]
                if cur_rev == 0:                            # 第一份上传当迁移（上云前本地已有进度）：找出这份数据最少要玩几天才说得过去，把建档日期往前推到那天
                    need = next((d for d in range(1, 181) if plausible(data, d)[0]), None)
                    if need is None: return {'reject': '数值超出任何正常进度'}
                    self.db.execute('UPDATE saves SET created=? WHERE id=?', (now - (need - 1) * 86400 - 60, sid))
                else:
                    ok, why = plausible(data, self.days_of(sid))
                    if not ok: return {'reject': why}
            text = json.dumps(data, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
            self.db.execute('BEGIN')
            try:
                rev = self.db.execute('SELECT rev FROM saves WHERE id=?', (sid,)).fetchone()[0] + 1
                self.db.execute('UPDATE saves SET rev=?, data=?, at=?, updated=? WHERE id=?', (rev, text, at, now, sid))
                self.db.execute('INSERT INTO history(save_id, rev, data, at, saved) VALUES(?,?,?,?,?)', (sid, rev, text, at, now))
                self.db.execute('DELETE FROM history WHERE save_id=? AND rev<=?', (sid, rev - KEEP_HISTORY))
                self.db.execute('COMMIT')
            except Exception:
                self.db.execute('ROLLBACK'); raise
        return {'rev': rev, 'now': now * 1000}

    def claim(self, code):
        now = time.time()
        with self.lock:
            r = self.db.execute('SELECT id, rev, data, at FROM saves WHERE code_hash=?', (self.chash(code),)).fetchone()
            if not r: return None
            token = self._new_device(r[0], now); admin = self.is_admin(r[0])
        out = {'token': token, 'code': self.show(code), 'rev': r[1], 'at': r[3], 'data': json.loads(r[2]), 'now': now * 1000, 'day': self.days_of(r[0])}
        if admin: out['admin'] = True
        return out

    def rotate(self, token):
        with self.lock:
            sid = self._save_of(token)
            if sid is None: return None
            for _ in range(5):
                code = self.new_code()
                try: self.db.execute('UPDATE saves SET code_hash=? WHERE id=?', (self.chash(code), sid)); break
                except sqlite3.IntegrityError: continue
        return {'code': self.show(code)}


# ---- 合理性检查（数值照 守关.html 10-30：每天资历最多约 12＋节点功绩 8、精铁约 11、残页约 10、机缘 30→陨铁 0.3、专属材料每种 2；斗将首通各给陨铁 1）----
WPN_IRON = [4, 4, 10, 10, 15, 15, 20, 20, 25, 25]
PREP_CUM = [20, 40, 76, 124, 176, 232]                 # 晋到第 1…6 阶累计要的资历
SKILL_PAGES = {'liu2': 6, 'guan2': 12, 'zhang2': 18, 'liu3': 18}
MAT_NEED = {6: 2, 7: 2, 8: 3, 9: 3, 10: 4}
MATS = ['青龙鳞', '蛇纹镔铁', '雌雄剑胚']
def plausible(data, days):
    """建档第 days 天，这份存档的数值说得过去吗。返回 (ok, 原因)。上限故意放宽（正常最快的约一倍半再加一笔），只挡明显改出来的。"""
    for slot in ('proto', 'proto2'):
        raw = data.get('sgz.%s.inv' % slot)
        if not raw: continue
        try: inv = json.loads(raw)
        except Exception: return False, '背包格式不对'
        it, up = inv.get('it') or {}, inv.get('up') or {}
        num = lambda v: v if isinstance(v, (int, float)) and v == v else 0
        rank = int(num(inv.get('rank'))); prep_cap = 30 * days + 40
        if rank > 6 or (rank > 0 and PREP_CUM[rank - 1] > prep_cap): return False, '官阶比天数快太多（第 %d 天就第 %d 阶）' % (days, rank)
        lv = {h: int(num(up.get('wpn_' + h))) for h in ('guan', 'zhang', 'liu')}
        if any(v < 0 or v > 10 for v in lv.values()): return False, '兵器等级不对'
        iron_spent = sum(sum(-(-WPN_IRON[k] // 3) for k in range(v)) for v in lv.values())
        if num(it.get('精铁')) + iron_spent > 18 * days + 160: return False, '精铁比天数多太多'
        pages_spent = sum(c for k, c in SKILL_PAGES.items() if num(up.get(k)) > 0)
        if num(it.get('残页')) + pages_spent > 16 * days + 120: return False, '残页比天数多太多'
        met_spent = sum(1 for k in (4, 6, 8, 10) if max(lv.values()) >= k)
        met_cap = .5 * days + 12
        if num(it.get('陨铁')) + met_spent > met_cap: return False, '陨铁比天数多太多'
        h_of = dict(zip(MATS, ('guan', 'zhang', 'liu')))
        for m in MATS:
            spent = sum(MAT_NEED.get(k, 0) for k in range(1, lv[h_of[m]] + 1))
            if num(it.get(m)) + spent > 3 * days + 8 + met_cap / 3: return False, '%s比天数多太多' % m
        if num(it.get('将印')) > days // 7 + 4: return False, '将印比天数多太多'
    return True, ''


def valid_data(d):
    return isinstance(d, dict) and len(d) <= 16 and all(isinstance(k, str) and KEY_OK.match(k) and isinstance(v, str) for k, v in d.items())


class Limits:
    """存档码连错、新建太快：按 IP 在内存里计数（不落盘）。"""
    def __init__(self):
        self.fails, self.hellos, self.lock = {}, {}, threading.Lock()
    def locked(self, ip):
        with self.lock:
            n, t = self.fails.get(ip, (0, 0))
            if n >= LOCK_FAILS and time.time() - t < LOCK_SECS: return int(LOCK_SECS - (time.time() - t))
            if n >= LOCK_FAILS: self.fails.pop(ip, None)
            return 0
    def fail(self, ip):
        with self.lock: n, _ = self.fails.get(ip, (0, 0)); self.fails[ip] = (n + 1, time.time())
    def ok(self, ip):
        with self.lock: self.fails.pop(ip, None)
    def hello_ok(self, ip):
        with self.lock:
            now = time.time(); q = [t for t in self.hellos.get(ip, []) if now - t < 3600]
            if len(q) >= HELLO_PER_HOUR: self.hellos[ip] = q; return False
            q.append(now); self.hellos[ip] = q; return True


class Handler(BaseHTTPRequestHandler):
    server_version = 'sanguo-save/1'
    store = None; limits = None

    def log_message(self, fmt, *args):                  # 不记 IP，只记方法、路径、状态
        sys.stderr.write('%s %s\n' % (datetime.datetime.now().strftime('%m-%d %H:%M:%S'), fmt % args if '%' in fmt else fmt))
    def log_request(self, code='-', size='-'):
        self.log_message('%s %s %s', self.command, self.path.split('?')[0], code)

    def ip(self): return self.headers.get('X-Real-IP') or self.client_address[0]
    def token(self, body=None):
        h = self.headers.get('Authorization', '')
        if h.startswith('Bearer '): return h[7:].strip()
        return (body or {}).get('token') if isinstance(body, dict) else None

    def cors(self):                                     # 白名单里的来源原样回给它，别的不给（浏览器就不让读回复）
        o = self.headers.get('Origin', ''); ok = bool(CORS_OK.match(o))
        if ok: self.send_header('Access-Control-Allow-Origin', o)
        self.send_header('Vary', 'Origin'); return ok

    def reply(self, status, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store'); self.cors(); self.end_headers(); self.wfile.write(b)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > MAX_BODY: raise ValueError('存档太大')
        raw = self.rfile.read(n) if n else b''
        return json.loads(raw.decode() or '{}')

    def route(self, method):
        path = self.path.split('?')[0].rstrip('/') or '/'
        try:
            if method == 'GET' and path == '/save':
                r = self.store.get(self.token()); return self.reply(200, r) if r else self.reply(401, {'error': '凭证不对'})
            if method == 'GET' and path == '/ping': return self.reply(200, {'ok': True, 'now': time.time() * 1000})
            body = self.body()
            if method == 'POST' and path == '/hello':
                if not self.limits.hello_ok(self.ip()): return self.reply(429, {'error': '太频繁了，过一会儿再试'})
                return self.reply(200, self.store.hello())
            if path == '/save' and method in ('PUT', 'POST'):
                data, at = body.get('data'), body.get('at')
                if not valid_data(data): return self.reply(400, {'error': '存档格式不对'})
                at = float(at) if isinstance(at, (int, float)) else time.time() * 1000
                r = self.store.put(self.token(body), data, at)
                if r and 'reject' in r: return self.reply(409, {'error': '存档数值不合理：' + r['reject']})   # 客户端收到后恢复云端上一份
                return self.reply(200, r) if r else self.reply(401, {'error': '凭证不对'})
            if method == 'POST' and path == '/claim':
                wait = self.limits.locked(self.ip())
                if wait: return self.reply(429, {'error': '存档码错了太多次，%d 分钟后再试' % max(1, wait // 60)})
                code = Store.norm_code(body.get('code'))
                r = self.store.claim(code) if code else None
                if not r: self.limits.fail(self.ip()); return self.reply(404, {'error': '没有这个存档码'})
                self.limits.ok(self.ip()); return self.reply(200, r)
            if method == 'POST' and path == '/rotate':
                r = self.store.rotate(self.token(body)); return self.reply(200, r) if r else self.reply(401, {'error': '凭证不对'})
            return self.reply(404, {'error': '没有这个接口'})
        except ValueError as e:
            return self.reply(400, {'error': str(e)})
        except Exception as e:
            sys.stderr.write('出错：%r\n' % e); return self.reply(500, {'error': '服务器出错'})

    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PUT(self): self.route('PUT')
    def do_OPTIONS(self):                               # 跨域的预检
        self.send_response(204)
        if self.cors():
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization'); self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Content-Length', '0'); self.end_headers()


class Server(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


def cmd_serve(a):
    Handler.store, Handler.limits = Store(a.state), Limits()
    srv = Server((a.host, a.port), Handler)
    sys.stderr.write('三国志守关云存档在 %s:%d，数据 %s\n' % (a.host, a.port, a.state)); sys.stderr.flush()
    srv.serve_forever()

def cmd_stats(a):
    db = sqlite3.connect(os.path.join(a.state, 'saves.sqlite')); now = time.time()
    n = db.execute('SELECT COUNT(*) FROM saves').fetchone()[0]
    played = db.execute("SELECT COUNT(*) FROM saves WHERE rev > 0").fetchone()[0]
    day = db.execute('SELECT COUNT(DISTINCT save_id) FROM devices WHERE seen > ?', (now - 86400,)).fetchone()[0]
    week = db.execute('SELECT COUNT(DISTINCT save_id) FROM devices WHERE seen > ?', (now - 7 * 86400,)).fetchone()[0]
    dev = db.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
    print('存档 %d 份（存过进度的 %d 份），设备 %d 台；最近一天玩过 %d 份，最近一周 %d 份' % (n, played, dev, day, week))

def cmd_backup(a):
    os.makedirs(a.to, exist_ok=True)
    src = sqlite3.connect(os.path.join(a.state, 'saves.sqlite'))
    dst_path = os.path.join(a.to, 'saves-%s.sqlite' % datetime.datetime.now().strftime('%Y%m%d-%H%M'))
    dst = sqlite3.connect(dst_path)
    if hasattr(src, 'backup'): src.backup(dst)                           # 3.7 起有
    else: dst.executescript('\n'.join(src.iterdump()))                  # 3.6：导成 SQL 再灌进去（一致的快照）
    dst.execute('PRAGMA journal_mode=DELETE'); dst.close(); src.close()         # 备份是单个文件（不带 -wal、-shm），拷走就能用
    for x in (dst_path + '-wal', dst_path + '-shm'):                              # 关掉以后剩下的空壳
        if os.path.exists(x): os.remove(x)
    olds = sorted(glob.glob(os.path.join(a.to, 'saves-*.sqlite')))[:-a.keep] if a.keep > 0 else []
    for f in olds:
        for x in (f, f + '-wal', f + '-shm'):
            if os.path.exists(x): os.remove(x)
    print('备份到 %s，删了 %d 份旧的' % (dst_path, len(olds)))

def cmd_history(a):
    st = Store(a.state); code = Store.norm_code(a.code)
    r = st.db.execute('SELECT id FROM saves WHERE code_hash=?', (st.chash(code or ''),)).fetchone()
    if not r: print('没有这个存档码'); return
    for rev, at, saved, data in st.db.execute('SELECT rev, at, saved, data FROM history WHERE save_id=? ORDER BY rev DESC', (r[0],)):
        print(rev, datetime.datetime.fromtimestamp(saved).strftime('%m-%d %H:%M'), len(data), '字节')

def cmd_admin(a):
    # 10-25 用户：「除了管理员，不能换形象」——把某份存档记成管理员（游戏里才显示「换形象」）；--off 取消。存档码只在这里用来找存档，库里不存原文
    st = Store(a.state); code = Store.norm_code(a.code)
    r = st.db.execute('SELECT id FROM saves WHERE code_hash=?', (st.chash(code or ''),)).fetchone()
    if not r: print('没有这个存档码'); return
    if a.off: st.db.execute('DELETE FROM admins WHERE save_id=?', (r[0],)); print('已取消管理员，存档编号', r[0])
    else: st.db.execute('INSERT OR IGNORE INTO admins(save_id, since) VALUES(?,?)', (r[0], time.time())); print('已设为管理员，存档编号', r[0])
    print('现在的管理员存档编号：', [x[0] for x in st.db.execute('SELECT save_id FROM admins ORDER BY save_id')])

def main():
    ap = argparse.ArgumentParser(description='三国志守关 · 云存档')
    sub = ap.add_subparsers(dest='cmd')
    s = sub.add_parser('serve'); s.add_argument('--host', default='127.0.0.1'); s.add_argument('--port', type=int, default=8094); s.add_argument('--state', required=True)
    s = sub.add_parser('stats'); s.add_argument('--state', required=True)
    s = sub.add_parser('backup'); s.add_argument('--state', required=True); s.add_argument('--to', required=True); s.add_argument('--keep', type=int, default=14)
    s = sub.add_parser('history'); s.add_argument('--state', required=True); s.add_argument('--code', required=True)
    s = sub.add_parser('admin'); s.add_argument('--state', required=True); s.add_argument('--code', required=True); s.add_argument('--off', action='store_true')
    a = ap.parse_args()
    {'serve': cmd_serve, 'stats': cmd_stats, 'backup': cmd_backup, 'history': cmd_history, 'admin': cmd_admin}.get(a.cmd, lambda _: ap.print_help())(a)

if __name__ == '__main__':
    main()
