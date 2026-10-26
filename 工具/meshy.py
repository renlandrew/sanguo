#!/usr/bin/env python3
"""Meshy 接口的小工具（10-24）：多图建模、绑骨、套动作、下载。钥匙从环境变量 MESHY_KEY 读，不写进任何文件。

  MESHY_KEY=… python3 三国志/工具/meshy.py balance
  MESHY_KEY=… python3 三国志/工具/meshy.py multi 正面.png 侧面.png 背面.png            → 任务号（第一张必须是正面）
  MESHY_KEY=… python3 三国志/工具/meshy.py wait multi-image-to-3d <任务号> <存放目录>    等它做完，下载 glb 和预览图
  MESHY_KEY=… python3 三国志/工具/meshy.py rig <建模任务号> [身高米]                    → 绑骨任务号（自带走、跑两段动作）
  MESHY_KEY=… python3 三国志/工具/meshy.py wait rigging <任务号> <存放目录>
  MESHY_KEY=… python3 三国志/工具/meshy.py anim <绑骨任务号> <动作号>                   → 动作任务号
  MESHY_KEY=… python3 三国志/工具/meshy.py anims <绑骨任务号> 510,4,7                   → 几段动作合在一个文件
  MESHY_KEY=… python3 三国志/工具/meshy.py wait animations <任务号> <存放目录>
每个任务的回复原样存成 <存放目录>/<种类>-<任务号>.json，花了多少点数看里面的 consumed_credits。
"""
import base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

API = 'https://api.meshy.ai/openapi/v1/'


def call(method, path, body=None):
    key = os.environ.get('MESHY_KEY')
    if not key: sys.exit('先设 MESHY_KEY')
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        sys.exit('Meshy 回 %d：%s' % (e.code, e.read().decode()[:500]))


def data_uri(p):
    mt = mimetypes.guess_type(p)[0] or 'image/png'
    return 'data:%s;base64,%s' % (mt, base64.b64encode(open(p, 'rb').read()).decode())


def fetch(url, dst):
    with urllib.request.urlopen(url, timeout=300) as r, open(dst, 'wb') as f: f.write(r.read())
    print('  下载', dst, os.path.getsize(dst) // 1024, 'KB')


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == 'balance': print(call('GET', 'balance'))
    elif cmd == 'multi':
        r = call('POST', 'multi-image-to-3d', {
            'image_urls': [data_uri(p) for p in a[1:5]], 'ai_model': 'latest', 'pose_mode': 'a-pose',
            'should_remesh': True, 'topology': 'triangle', 'target_polycount': int(os.environ.get('POLY', '20000')),   # 10-26 用户：「要最精细」——POLY=100000
            'should_texture': True, 'enable_pbr': False, 'remove_lighting': True, 'target_formats': ['glb']})
        print(r.get('result', r))
    elif cmd == 'rig':
        body = {'input_task_id': a[1]}
        if len(a) > 2: body['height_meters'] = float(a[2])
        print(call('POST', 'rigging', body).get('result'))
    elif cmd == 'anim':
        print(call('POST', 'animations', {'rig_task_id': a[1], 'action_id': int(a[2])}).get('result'))
    elif cmd == 'anims':                                    # 一次套几段动作，合在一个文件里（每段一个 clip）
        print(call('POST', 'animations', {'rig_task_id': a[1], 'action_ids': [int(x) for x in a[2].split(',')]}).get('result'))
    elif cmd == 'wait':
        kind, tid, out = a[1], a[2], a[3]; os.makedirs(out, exist_ok=True); t0 = time.time()
        while True:
            r = call('GET', '%s/%s' % (kind, tid)); st = r.get('status')
            print('  %4d 秒 %s %s%%' % (time.time() - t0, st, r.get('progress')), flush=True)
            if st in ('SUCCEEDED', 'FAILED', 'CANCELED', 'EXPIRED'): break
            time.sleep(10)
        json.dump(r, open(os.path.join(out, '%s-%s.json' % (kind.split('-')[0], tid)), 'w'), ensure_ascii=False, indent=1)
        if st != 'SUCCEEDED': sys.exit('任务没成功：%s' % json.dumps(r.get('task_error'), ensure_ascii=False))
        res = r.get('result') or {}
        urls = dict((r.get('model_urls') or {}), **{('thumb' if k == 'thumbnail_url' else k): v for k, v in r.items() if k == 'thumbnail_url'})
        for k, v in (res.items() if isinstance(res, dict) else []):
            if isinstance(v, str) and v.startswith('http'): urls[k] = v
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if isinstance(vv, str) and vv.startswith('http'): urls[k + '_' + kk] = vv
        for k, v in urls.items():
            if not v: continue
            ext = os.path.splitext(v.split('?')[0])[1] or '.bin'
            fetch(v, os.path.join(out, k + ext))
        print('花了 %s 点' % r.get('consumed_credits', '?'))
    else: print(__doc__)


if __name__ == '__main__':
    main()
