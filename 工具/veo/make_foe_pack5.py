"""黄巾渠帅、张梁、西凉校尉、俞涉首录（10-30）。用户：「录」。原来渠帅借力士、张梁借程远志、校尉借西凉兵的图集，俞涉是程序画的小人。
首帧：美术/<名>/正面.png（Codex 画的透明版，人物占画面九成），铺纯中灰后由 ref() 按人物外框缩放、贴底居中，四周留白够用；镜头、反向提示词照 make_foe_pack2.py。
只录切图用得到的段：三个敌人各 3 段（朝镜头跑、出手、倒下），俞涉 2 段（朝城下跑、受伤倒下）；共 11 条 × 4 秒 × .15 ≈ 6.6 美元。
在 Cloud Shell 里：SHOTS=shots_foe5.json SECONDS=4 CAP_USD=8 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_foe_pack5.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
src = (HERE / 'make_foe_pack2.py').read_text(encoding='utf-8').split('\nSHOTS = {')[0]
g = {'__file__': str(HERE / 'make_foe_pack2.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src, g)
ref, BASE, TAIL, NEG, RUN, DIE = (g[k] for k in ('ref', 'BASE', 'TAIL', 'NEG', 'RUN', 'DIE'))
SHOTS = {
 'qushuai': ('黄巾渠帅', "a burly middle-aged Yellow Turban chieftain with a short full beard, a yellow headband with a bronze plate, bare-chested under a yellow-brown leather vest with a few large shoulder plates, a wide cloth sash, wrapped shins, gripping a broad heavy dao saber with both hands", [
   ('run', RUN),
   ('ram', "stops, raises the broad saber high over his head with both hands and hacks it down hard toward the camera, then swings it back across once more, roaring."),
   ('die', DIE)]),
 'zhangliang': ('张梁', "the Yellow Turban general Zhang Liang, a sturdy man in his thirties with a short beard, a yellow headband and small Taoist cap, yellow Taoist robes under ochre armor of large plates, a round yellow shield with a bagua symbol on his left arm and a long glaive in his right hand", [
   ('run', RUN),
   ('ram', "stops, raises the round shield and sweeps the long glaive down and across toward the camera in one heavy blow, then thrusts it forward once, shouting."),
   ('die', DIE.replace('drops his weapon', 'drops his glaive and shield'))]),
 'xiaowei': ('西凉校尉', "a lean young Xiliang cavalry officer with a tanned face and short beard, a dark-red battle robe under iron-gray armor of large plates with big pauldrons, a round iron helmet with a dark-red plume, a short cape, a long ji halberd in his right hand and a small round shield on his left arm", [
   ('run', RUN),
   ('ram', "stops, pulls the halberd back and thrusts it hard straight toward the camera, then sweeps it sideways once, behind his raised round shield."),
   ('die', DIE)]),
 'yushe': ('俞涉', "the young allied general Yu She with sharp brows and an eager brave face, an indigo battle robe under silver-gray armor of large plates, a silver helmet with an indigo plume, a small indigo back banner, gripping a long spear with both hands", [
   ('run', RUN.replace('charges straight toward the camera on foot at a heavy run', 'runs straight toward the camera on foot, fleeing in a hurry while looking briefly back over his shoulder')),
   ('die', "is struck from behind, stumbles forward, drops his spear, falls to one knee and collapses face-down on the floor.")]),
}
shots = []
for k, (_, who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
tmp = out / 'gray'; tmp.mkdir(exist_ok=True)
with tarfile.open(out / 'foe_pack5.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k, (nm, _, _) in SHOTS.items():
        im = Image.open(ROOT / '美术' / nm / '正面.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        p = tmp / f'{k}.png'; bg.convert('RGB').save(p)                                   # 透明的铺灰底（ref 读 RGB，透明处会变黑）
        data = ref(p); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe5.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack5.tar.gz', (out / 'foe_pack5.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
