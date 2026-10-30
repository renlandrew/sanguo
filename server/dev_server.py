# 本机照线上的样子起三国：/sanguo/ 是 原型/ 的静态文件（守关.html 当首页），/sanguo/api/ 转给云存档服务（同线上 nginx）。顺手把存档服务也起在旁边（临时库）。
# 用法：python3 三国志/server/dev_server.py [原型目录] [端口 8771] [存档服务端口 18094]
import atexit, os, subprocess, sys, tempfile, urllib.request, urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '原型')
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8771; API = int(sys.argv[3]) if len(sys.argv) > 3 else 18094
save = subprocess.Popen([sys.executable, os.path.join(HERE, 'sanguo_save.py'), 'serve', '--port', str(API), '--state', tempfile.mkdtemp(prefix='sgsave-dev-')])
atexit.register(save.terminate)

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(self, *a): pass
    def translate_path(self, path):
        p = path.split('?')[0]
        if p in ('/sanguo/', '/sanguo/index.html'): p = '/守关.html'
        elif p.startswith('/sanguo/'): p = p[len('/sanguo'):]
        return super().translate_path(p)
    def end_headers(self): self.send_header('Cache-Control', 'no-cache'); super().end_headers()
    def proxy(self):
        n = int(self.headers.get('Content-Length') or 0); body = self.rfile.read(n) if n else None
        req = urllib.request.Request('http://127.0.0.1:%d%s' % (API, self.path[len('/sanguo/api'):]), data=body, method=self.command,
            headers={k: v for k, v in [('Content-Type', self.headers.get('Content-Type')), ('Authorization', self.headers.get('Authorization')), ('X-Real-IP', self.client_address[0])] if v})
        try: r = urllib.request.urlopen(req, timeout=10); code, data = r.status, r.read()
        except urllib.error.HTTPError as e: code, data = e.code, e.read()
        except Exception: code, data = 502, b'{"error":"bad gateway"}'
        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path.startswith('/sanguo/api/'): return self.proxy()
        return super().do_GET()
    def do_POST(self): return self.proxy() if self.path.startswith('/sanguo/api/') else self.send_error(405)
    def do_PUT(self): return self.proxy() if self.path.startswith('/sanguo/api/') else self.send_error(405)

class S(ThreadingMixIn, HTTPServer): daemon_threads = True
print('三国 http://127.0.0.1:%d/sanguo/  （存档服务 %d）' % (PORT, API), flush=True)
S(('127.0.0.1', PORT), H).serve_forever()
