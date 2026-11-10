#!/usr/bin/env python3
"""三国志云存档本机测试：起一个临时服务，走一遍新建、存、取、认领、换码、迁移、作弊被拒。用法：python3 三国志/server/test_save.py"""
import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 18094
state = tempfile.mkdtemp(prefix='sgsave-')
srv = subprocess.Popen([sys.executable, os.path.join(HERE, 'sanguo_save.py'), 'serve', '--port', str(PORT), '--state', state], stderr=subprocess.DEVNULL)
time.sleep(.8)
ok = fail = 0

def call(method, path, body=None, token=None):
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (PORT, path), method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header('Content-Type', 'application/json')
    if token: req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'{}')

def check(name, cond):
    global ok, fail
    print(('通过 ' if cond else '失败 ') + name); ok += cond; fail += (not cond)

def inv(rank=0, it=None, up=None): return json.dumps({'rank': rank, 'it': it or {}, 'up': up or {}})

try:
    st, h = call('POST', '/hello', {}); tok = h.get('token')
    check('新建存档拿到凭证和存档码', st == 200 and tok and len(h['code']) == 11 and h['day'] == 1 and h['now'] > 0)
    # 第一份当迁移：本地已经晋到第 3 阶、兵器 +6 → 服务器把建档日期往前推
    first = {'sgz.proto.inv': inv(3, {'精铁': 20, '残页': 10, '陨铁': 1}, {'wpn_guan': 6, 'wpn_zhang': 6, 'wpn_liu': 6, 'liu2': 1}), 'sgz.proto.stars': json.dumps({'1': 3})}
    st, r = call('PUT', '/save', {'data': first, 'at': 1}, tok); check('第一份上传（迁移）收下', st == 200 and r['rev'] == 1)
    st, g = call('GET', '/save', token=tok); check('迁移后建档日期往前推了（不再是第 1 天）', st == 200 and g['day'] > 1)
    d0 = g['day']
    # 正常小幅前进：收下
    nxt = dict(first); nxt['sgz.proto.inv'] = inv(3, {'精铁': 25, '残页': 12, '陨铁': 1}, {'wpn_guan': 6, 'wpn_zhang': 6, 'wpn_liu': 6, 'liu2': 1})
    st, r = call('PUT', '/save', {'data': nxt, 'at': 2}, tok); check('正常前进收下', st == 200 and r['rev'] == 2)
    # 作弊：一下子第 6 阶、兵器全 +10、精铁 9999 → 拒收，云上还是上一份
    cheat = dict(first); cheat['sgz.proto.inv'] = inv(6, {'精铁': 9999}, {'wpn_guan': 10, 'wpn_zhang': 10, 'wpn_liu': 10})
    st, r = call('PUT', '/save', {'data': cheat, 'at': 3}, tok); check('改出来的存档被拒（409）', st == 409 and '不合理' in r.get('error', ''))
    st, g = call('GET', '/save', token=tok); check('拒收后云上还是上一份', g['rev'] == 2 and json.loads(g['data']['sgz.proto.inv'])['it']['精铁'] == 25)
    # 不认的键
    st, r = call('PUT', '/save', {'data': {'sgz.t9.inv': '{}'}, 'at': 4}, tok); check('测试档的键不收', st == 400)
    # 另一台设备认领
    st, c = call('POST', '/claim', {'code': h['code']}); check('另一台设备用存档码认领', st == 200 and c['rev'] == 2 and c['token'] != tok)
    st, c2 = call('POST', '/claim', {'code': 'AAA-AAA-AAA'}); check('错的存档码 404', st == 404)
    st, rt = call('POST', '/rotate', {}, tok); check('换存档码', st == 200 and rt['code'] != h['code'])
    st, _ = call('GET', '/save', token='bad'); check('凭证不对 401', st == 401)
    st, p = call('GET', '/ping'); check('ping 带服务器时间', st == 200 and p['now'] > 0)
    # 新建档第 1 天就上传满级 → 迁移也说不过去？满级在 180 天内是说得过去的，所以收下；但精铁 99999 说不过去 → 拒
    st, h2 = call('POST', '/hello', {}); st, r = call('PUT', '/save', {'data': {'sgz.proto.inv': inv(1, {'精铁': 99999})}, 'at': 1}, h2['token'])
    check('第一份就离谱（精铁 99999）也拒', st == 409)
    # 11-10 itch 包：试玩档上云、itch 域名跨域
    st, h3 = call('POST', '/hello', {}); st, r = call('PUT', '/save', {'data': {'sgz.demo.stars': json.dumps({'1': 3}), 'sgz.demo.inv': inv(1, {'精铁': 6})}, 'at': 1, 'slots': ['demo']}, h3['token'])
    check('试玩档收下', st == 200 and r['rev'] == 1)
    st, r = call('PUT', '/save', {'data': {'sgz.demo.stars': json.dumps({'1': 3}), 'sgz.demo.inv': inv(2, {'精铁': 900})}, 'at': 2, 'slots': ['demo']}, h3['token']); check('试玩档不按天数卡（试玩不耗体力，一天能刷很多）', st == 200)
    st, r = call('PUT', '/save', {'data': {'sgz.demo.inv': inv(1), 'sgz.proto.inv': inv(6, {'精铁': 99999})}, 'at': 3, 'slots': ['demo', 'proto']}, h3['token']); check('同一份里的正式档照样查（409）', st == 409)
    # 一个存档码下既有正式档又有试玩档：各传各的，互不冲掉
    st, h4 = call('POST', '/hello', {}); t4 = h4['token']
    full = {'sgz.proto.inv': inv(1, {'精铁': 5}), 'sgz.proto.stars': json.dumps({'1': 3})}
    st, r = call('PUT', '/save', {'data': full, 'at': 1}, t4)                                                     # 正式站（老网页，不写 slots）
    st, r = call('PUT', '/save', {'data': {'sgz.demo.stars': json.dumps({'1': 2})}, 'at': 2, 'slots': ['demo']}, t4)   # itch 试玩包
    st, g = call('GET', '/save', token=t4); check('试玩包上传后正式档还在', st == 200 and g['rev'] == 2 and g['data'].get('sgz.proto.inv') == full['sgz.proto.inv'] and 'sgz.demo.stars' in g['data'])
    st, r = call('PUT', '/save', {'data': {'sgz.proto.inv': inv(1, {'精铁': 6})}, 'at': 3}, t4)                   # 正式站少传一个键＝那个键删了，试玩档不动
    st, g = call('GET', '/save', token=t4); check('正式站上传后试玩档还在、正式档按新的', g['rev'] == 3 and 'sgz.proto.stars' not in g['data'] and json.loads(g['data']['sgz.demo.stars']) == {'1': 2})
    st, r = call('PUT', '/save', {'data': {}, 'at': 4, 'slots': ['demo']}, t4); st, g = call('GET', '/save', token=t4)
    check('试玩档重置（传空）只清试玩那格', g['rev'] == 4 and list(g['data']) == ['sgz.proto.inv'])
    st, r = call('PUT', '/save', {'data': {'sgz.proto.inv': inv(1)}, 'at': 5, 'slots': ['demo']}, t4); check('声明只换试玩格却带正式档的键：不收', st == 400)
    st, r = call('PUT', '/save', {'data': {}, 'at': 5, 'slots': ['x']}, t4); check('不认的格：不收', st == 400)
    st, r = call('PUT', '/save', {'data': {}, 'at': 5, 'slots': 'demo'}, t4); check('slots 不是列表：不收', st == 400)
    st, c3 = call('POST', '/claim', {'code': h3['code']}); check('试玩档用存档码取回', st == 200 and json.loads(c3['data']['sgz.demo.stars']) == {'1': 3})
    def raw(method, path, origin, extra=None, data=None):
        req = urllib.request.Request('http://127.0.0.1:%d%s' % (PORT, path), method=method, data=data); req.add_header('Origin', origin)
        for k, v in (extra or {}).items(): req.add_header(k, v)
        try:
            with urllib.request.urlopen(req) as r_: return r_.status, r_.headers, r_.read()
        except urllib.error.HTTPError as e: return e.code, e.headers, e.read()
    ITCH = 'https://html-classic.itch.zone'
    st, hd, _ = raw('OPTIONS', '/save', ITCH, {'Access-Control-Request-Method': 'PUT', 'Access-Control-Request-Headers': 'authorization,content-type'})
    check('itch 域名的预检放行（带凭证头、PUT）', st == 204 and hd.get('Access-Control-Allow-Origin') == ITCH and 'PUT' in hd.get('Access-Control-Allow-Methods', '') and 'Authorization' in hd.get('Access-Control-Allow-Headers', ''))
    st, hd, _ = raw('GET', '/save', ITCH, {'Authorization': 'Bearer ' + h3['token']}); check('itch 域名取存档，回复带放行头', st == 200 and hd.get('Access-Control-Allow-Origin') == ITCH and 'Origin' in hd.get('Vary', ''))
    for bad in ('https://evil.example', 'https://itch.zone.evil.example', 'http://html-classic.itch.zone', 'https://html-classic.itch.zone.evil.example', 'https://xitch.zone'):
        st, hd, _ = raw('OPTIONS', '/save', bad, {'Access-Control-Request-Method': 'PUT'}); check('别的来源不放行：' + bad, hd.get('Access-Control-Allow-Origin') is None and hd.get('Access-Control-Allow-Methods') is None)
    st, hd, b = raw('POST', '/save', ITCH, {'Content-Type': 'text/plain'}, json.dumps({'token': h3['token'], 'data': {'sgz.demo.stars': json.dumps({'1': 3, '2': 2})}, 'at': 3, 'slots': ['demo']}).encode())
    check('切后台时的纯文本上传收下', st == 200 and json.loads(b)['rev'] == 3)
    # 11-09 试玩统计
    st, r = call('POST', '/ev', {'did': 'ab' * 12, 'ev': 'start', 'lv': 1, 'src': 'bili_a', 'lang': 'zh'}); check('试玩统计收下', st == 200 and r.get('ok'))
    st, r = call('POST', '/ev', {'did': 'ab' * 12, 'ev': 'hack', 'lv': 1}); check('不认的事件 400', st == 400)
    st, r = call('POST', '/ev', {'did': 'xyz', 'ev': 'win', 'lv': 1}); check('设备串不对 400', st == 400)
    st, r = call('POST', '/ev', {'did': 'ab' * 12, 'ev': 'win', 'lv': 1, 'src': 'Bad Src!'}); check('来源标签不对 400', st == 400)
    out = subprocess.run([sys.executable, os.path.join(HERE, 'sanguo_save.py'), 'funnel', '--state', state], capture_output=True, text=True).stdout
    check('漏斗能出数（1 台、开打第一关 1/1）', '试玩设备 1 台' in out and '1/1' in out)
finally:
    srv.terminate()
print('\n%d 项通过，%d 项失败' % (ok, fail)); sys.exit(1 if fail else 0)
